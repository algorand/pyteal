import bisect
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import unified_diff
from functools import partial
from itertools import count
import re
from typing import Any, Final, Literal, Mapping, OrderedDict, TypedDict, cast

from tabulate import tabulate  # type: ignore

from algosdk.source_map import SourceMap as PCSourceMap  # disambiguate
from algosdk.v2client.algod import AlgodClient

import pyteal as pt
from pyteal.errors import TealInternalError
from pyteal.stack_frame import (
    PT_GENERATED,
    NatalStackFrame,
    PyTealFrame,
    PyTealFrameStatus,
)
from pyteal.util import algod_with_assertion

# ### ---- R3SourceMap is based on mjpieters code snippets ---- ### #
#
#     Modified from the original `SourceMap` available under MIT License here (as of Nov. 12, 2022): https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
#    `R3` is a nod to "Revision 3" of John Lenz's Source Map Proposal: https://docs.google.com/document/d/1U1RGAehQwRypUTovF1KRlpiOFze0b-_2gc6fAH0KY0k/edit?hl=en_US&pli=1&pli=1
#
# ###

_b64chars = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_b64table = [-1] * (max(_b64chars) + 1)
for i, b in enumerate(_b64chars):
    _b64table[b] = i

shiftsize, flag, mask = 5, 1 << 5, (1 << 5) - 1


def _base64vlq_decode(vlqval: str) -> list[int]:
    """Decode Base64 VLQ value"""
    results = []
    shift = value = 0
    # use byte values and a table to go from base64 characters to integers
    for v in map(_b64table.__getitem__, vlqval.encode("ascii")):
        v = cast(int, v)
        value += (v & mask) << shift
        if v & flag:
            shift += shiftsize
            continue
        # determine sign and add to results
        results.append((value >> 1) * (-1 if value & 1 else 1))
        shift = value = 0
    return results


def _base64vlq_encode(*values: int) -> str:
    """Encode integers to a VLQ value"""
    results: list[int] = []
    add = results.append
    for v in values:
        # add sign bit
        v = (abs(v) << 1) | int(v < 0)
        while True:
            toencode, v = v & mask, v >> shiftsize
            add(toencode | (v and flag))
            if not v:
                break
    # TODO: latest version of gist avoids the decode() step
    return bytes(map(_b64chars.__getitem__, results)).decode()


class autoindex(defaultdict):
    def __init__(self, *args, **kwargs):
        super().__init__(partial(next, count()), *args, **kwargs)


@dataclass(frozen=False)
class R3SourceMapping:
    line: int
    # line_end: Optional[int] = None #### NOT PROVIDED (AND NOT CONFORMING WITH R3 SPEC) AS TARGETS ARE ASSUMED TO SPAN AT MOST ONE LINE ####
    column: int
    source: str | None = None
    source_line: int | None = None
    source_column: int | None = None
    source_content: list[str] | None = None
    source_extract: str | None = None
    target_extract: str | None = None
    name: str | None = None
    source_line_end: int | None = None
    source_column_end: int | None = None
    column_end: int | None = None

    def __post_init__(self):
        if self.source is not None and (
            self.source_line is None or self.source_column is None
        ):
            raise TypeError(
                "Invalid source mapping; missing line and column for source file"
            )
        if self.name is not None and self.source is None:
            raise TypeError(
                "Invalid source mapping; name entry without source location info"
            )

    def __lt__(self, other: "R3SourceMapping") -> bool:
        assert isinstance(other, type(self)), f"received incomparable {type(other)}"

        return (self.line, self.column) < (other.line, other.column)

    def __ge__(self, other: "R3SourceMapping") -> bool:
        return not self < other

    def location(self, source=False) -> tuple[str, int, int]:
        return (
            (
                self.source if self.source else "",
                self.source_line if self.source_line else -1,
                self.source_column if self.source_column else -1,
            )
            if source
            else ("", self.line, self.column)
        )

    @classmethod
    def extract_window(
        cls,
        source_lines: list[str] | None,
        line: int,
        column: int,
        right_column: int | None,
    ) -> str | None:
        return (
            (
                source_lines[line][column:right_column]
                if right_column is not None
                else source_lines[line][column:]
            )
            if source_lines
            else None
        )

    def __str__(self) -> str:
        def swindow(file, line, col, rcol, extract):
            if file == "unknown":
                file = None
            if not rcol:
                rcol = ""
            if extract is None:
                extract = "?"
            return f"{file + '::' if file else ''}L{line}C{col}-{rcol}='{extract}'"

        return (
            f"{swindow(self.source, self.source_line, self.source_column, self.source_column_end, self.source_extract)} <- "
            f"{swindow(None, self.line, self.column, self.column_end, self.target_extract)}"
        )

    __repr__ = __str__


class R3SourceMapJSON(TypedDict, total=False):
    version: Literal[3]
    file: str | None
    sourceRoot: str | None
    sources: list[str]
    sourcesContent: list[str | None] | None
    names: list[str]
    mappings: str


@dataclass(frozen=True)
class R3SourceMap:
    """
    This class is renames
    `mjpieters' SourceMap <https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b#file-sourcemap-py-L62>`_.
    and tweaks it a bit, adding the following functionality:

    - adds fields :code:`file_lines`, :code:`source_files`, :code:`entries`
    - :code:`__post_init__` (new) - runs a sanity check validation on the ordering of provided entries
    - :code:`__repr__` - printing out :code:`R3SourceMap(...)` instead of :code:`MJPSourceMap(...)`
    - :code:`from_json` - accepting new params :code:`sources_override`, :code:`sources_content_override`, :code:`target`, :code:`add_right_bounds`
    - :code:`add_right_bounds` (new) - allow specifying the right column bounds
    - :code:`to_json` - accepting new param :code:`with_contents`

    The main methods for this class are :code:`from_json` and :code:`to_json` which
    follow the encoding conventions outlined in
    `the Source Map Revison 3 Proposal <https://docs.google.com/document/d/1U1RGAehQwRypUTovF1KRlpiOFze0b-_2gc6fAH0KY0k/edit?hl=en_US&pli=1&pli=1>`_.
    """

    filename: str | None
    source_root: str | None
    entries: Mapping[tuple[int, int], "R3SourceMapping"]
    index: list[tuple[int, ...]] = field(default_factory=list)
    file_lines: list[str] | None = None
    source_files: list[str] | None = None
    source_files_lines: list[list[str] | None] | None = None

    def __post_init__(self):
        entries = list(self.entries.values())
        for i, entry in enumerate(entries):
            if i + 1 >= len(entries):
                return

            if entry >= entries[i + 1]:
                raise TypeError(
                    f"Invalid source map as entries aren't properly ordered: entries[{i}] = {entry} >= entries[{i + 1}] = {entries[i + 1]}"
                )

    def __repr__(self) -> str:
        parts = []
        if self.filename is not None:
            parts += [f"file={self.filename!r}"]
        if self.source_root is not None:
            parts += [f"source_root={self.source_root!r}"]
        parts += [f"len={len(self.entries)}"]
        return f"<R3SourceMap({', '.join(parts)})>"

    @classmethod
    def from_json(
        cls,
        smap: R3SourceMapJSON,
        sources_override: list[str] | None = None,
        sources_content_override: list[str] = [],
        target: str | None = None,
        add_right_bounds: bool = True,
    ) -> "R3SourceMap":
        """
        Construct an :any:`R3SourceMap` from an :code:`R3SourceMapJSON` (a :code:`TypedDict`) object.

        Args:
            smap: The :code:`R3SourceMapJSON` object to construct from.
            sources_override: A list of source files to use instead of the ones in the :code:`R3SourceMapJSON`.
                STRICTLY SPEAKING :code:`sources` OUGHT NOT BE MISSING OR EMPTY in :code:`R3SourceMapJSON`.
                However, currently the :code:`POST v2/teal/compile` endpoint populates this field with an empty list, as it is not provided the name of the
                Teal file which is being compiled. In order comply with the R3 spec, this field is populated with :code:`["unknown"]`
                when either missing or empty in the JSON and not supplied during construction.
            sources_content_override: :code:`sourcesContent` is optional and this provides a way at runtime to supply the actual source.
                When provided, and the :code:`R3SourceMapJSON` is either missing or empty, this will be substituted.
                An error will be raised when attempting to replace a nonempty :code:`R3SourceMapJSON.sourcesContent`.
            target: The target source code. This is used to populate the :code:`target_extract` field of the :code:`R3SourceMapping`.
            add_right_bounds: Whether to add the right column bounds to the :code:`R3SourceMapping`.
        """
        if smap.get("version") != 3:
            raise ValueError("Only version 3 sourcemaps are supported ")
        entries: dict[tuple[int, int], R3SourceMapping] = {}
        index: list[list[int]] = []
        spos = npos = sline = scol = 0

        sources = smap.get("sources")
        if sources and sources_override:
            raise AssertionError("ambiguous sources from JSON and method argument")
        sources = sources or sources_override or ["unknown"]

        contents: list[str | None] | list[str] | None = smap.get("sourcesContent")
        if contents and sources_content_override:
            raise AssertionError(
                "ambiguous sourcesContent from JSON and method argument"
            )
        contents = contents or sources_content_override

        names = smap.get("names")

        tcont, sp_conts = (
            target.splitlines() if target else None,
            [c.splitlines() if c else None for c in contents],
        )

        if "mappings" in smap:
            for gline, vlqs in enumerate(smap["mappings"].split(";")):
                index += [[]]
                if not vlqs:
                    continue
                gcol = 0
                for gcd, *ref in map(_base64vlq_decode, vlqs.split(",")):
                    gcol += gcd
                    kwargs = {}
                    if len(ref) >= 3:
                        sd, sld, scd, *namedelta = ref
                        spos, sline, scol = spos + sd, sline + sld, scol + scd
                        scont = sp_conts[spos] if len(sp_conts) > spos else None  # type: ignore
                        # extract the referenced source till the end of the current line
                        extract = R3SourceMapping.extract_window
                        kwargs = {
                            "source": sources[spos] if spos < len(sources) else None,
                            "source_line": sline,
                            "source_column": scol,
                            "source_content": scont,
                            "source_extract": extract(scont, sline, scol, None),
                            "target_extract": extract(tcont, gline, gcol, None),
                        }
                        if namedelta and names:
                            npos += namedelta[0]
                            kwargs["name"] = names[npos]
                    entries[gline, gcol] = R3SourceMapping(
                        line=gline, column=gcol, **kwargs  # type: ignore
                    )
                    index[gline].append(gcol)

        sourcemap = cls(
            smap.get("file"),
            smap.get("sourceRoot"),
            entries,
            [tuple(cs) for cs in index],
            tcont,
            sources,
            sp_conts,
        )
        if add_right_bounds:
            sourcemap.add_right_bounds()
        return sourcemap

    def add_right_bounds(self) -> None:
        entries = list(self.entries.values())
        for i, entry in enumerate(entries):
            if i + 1 >= len(entries):
                continue

            next_entry = entries[i + 1]

            def same_line_less_than(lc, nlc):
                return (lc[0], lc[1]) == (nlc[0], nlc[1]) and lc[2] < nlc[2]

            if not same_line_less_than(entry.location(), next_entry.location()):
                continue
            entry.column_end = next_entry.column
            entry.target_extract = entry.extract_window(
                self.file_lines, entry.line, entry.column, entry.column_end
            )

            if not all(
                [
                    self.source_files,
                    self.source_files_lines,
                    next_entry.source,
                    same_line_less_than(
                        entry.location(source=True),
                        next_entry.location(source=True),
                    ),
                ]
            ):
                continue
            entry.source_column_end = next_entry.source_column
            try:
                fidx = self.source_files.index(next_entry.source)  # type: ignore
            except ValueError:
                continue
            if (
                self.source_files_lines
                and isinstance(entry.source_line, int)
                and isinstance(entry.source_column, int)
            ):
                entry.source_extract = entry.extract_window(
                    self.source_files_lines[fidx],
                    entry.source_line,
                    entry.source_column,
                    next_entry.source_column,
                )

    def to_json(self, with_contents: bool = False) -> R3SourceMapJSON:
        content: list[str | None] = []
        mappings: list[str] = []
        sources, names = autoindex(), autoindex()
        entries = self.entries
        spos = sline = scol = npos = 0
        for gline, cols in enumerate(self.index):
            gcol = 0
            mapping = []
            for col in cols:
                entry = entries[gline, col]
                ds, gcol = [col - gcol], col

                if entry.source is not None:
                    assert entry.source_line is not None
                    assert entry.source_column is not None
                    ds += (
                        sources[entry.source] - spos,
                        entry.source_line - sline,
                        entry.source_column - scol,
                    )
                    spos, sline, scol = (
                        spos + ds[1],
                        sline + ds[2],
                        scol + ds[3],
                    )
                    if spos == len(content):
                        c = entry.source_content
                        content.append("\n".join(c) if c else None)
                    if entry.name is not None:
                        ds += (names[entry.name] - npos,)
                        npos += ds[-1]
                mapping.append(_base64vlq_encode(*ds))

            mappings.append(",".join(mapping))

        encoded = {
            "version": 3,
            "sources": [s for s, _ in sorted(sources.items(), key=lambda si: si[1])],
            "names": [n for n, _ in sorted(names.items(), key=lambda ni: ni[1])],
            "mappings": ";".join(mappings),
        }
        if with_contents:
            encoded["sourcesContent"] = content
        if self.filename is not None:
            encoded["file"] = self.filename
        if self.source_root is not None:
            encoded["sourceRoot"] = self.source_root
        return encoded  # type: ignore

    def __getitem__(self, idx: int | tuple[int, int]):
        l: int
        c: int
        try:
            l, c = idx  # type: ignore   # The exception handler deals with the int case
        except TypeError:
            l, c = idx, 0  # type: ignore   # yes, idx is guaranteed to be an int
        try:
            return self.entries[l, c]
        except KeyError:
            # find the closest column
            if not (cols := self.index[l]):
                raise IndexError(idx)
            cidx = bisect.bisect(cols, c)
            return self.entries[l, cols[cidx and cidx - 1]]


R3SourceMap.__module__ = "pyteal"


# #### PyTeal Specific Classes below #### #

_TEAL_LINE_NUMBER = "TL"
_TEAL_COLUMN = "TC"
_TEAL_COLUMN_END = "TCE"
_TEAL_LINE = "Teal Line"
_PROGRAM_COUNTERS = "PC"
_PYTEAL_HYBRID_UNPARSED = "PyTeal Hybrid Unparsed"
_PYTEAL_NODE_AST_UNPARSED = "PyTeal AST Unparsed"
_PYTEAL_NODE_AST_QUALNAME = "PyTeal Qualname"
_PYTEAL_COMPONENT = "PyTeal Qualname"
_PYTEAL_NODE_AST_SOURCE_BOUNDARIES = "PT Window"
_PYTEAL_FILENAME = "PT path"
_PYTEAL_LINE_NUMBER = "PTL"
_PYTEAL_LINE_NUMBER_END = "PTLE"
_PYTEAL_COLUMN = "PTC"
_PYTEAL_COLUMN_END = "PTCE"
_PYTEAL_LINE = "PyTeal"
_PYTEAL_NODE_AST = "PT AST"
_PYTEAL_NODE_AST_NONE = "FAILED"
_STATUS_CODE = "Sourcemap Status Code"
_STATUS = "Sourcemap Status"


class TealMapItem(PyTealFrame):
    """
    TealMapItem extends PyTealFrame to add information about the teal code that
    corresponds to the purported pyteal source.
    It also encapsulates any program counter (PC) information, when given.

    The main consumers of TealMapItem are:
    * _PyTealSourceMapper._build_r3sourcemap() which calls `source_mapping()`
        and provides the result for constructing an R3SourceMap
    * _PyTealSourceMapper.tabulate() which calls `asdict()` and is useful for
        creating PyTeal (and PC) annotated *.teal files
    """

    def __init__(
        self,
        pt_frame: PyTealFrame,
        teal_lineno: int,
        teal_line: str,
        teal_component: "pt.TealComponent",
        pcs: list[int] | None = None,
        is_sentinel: bool = False,
    ):
        super().__init__(
            frame_info=pt_frame.frame_info,
            node=pt_frame.node,
            creator=pt_frame.creator,
            full_stack=pt_frame.full_stack,
            rel_paths=pt_frame.rel_paths,
            parent=pt_frame.parent,
        )
        self.teal_lineno: Final[int] = teal_lineno
        self.teal_line: Final[str] = teal_line
        self.teal_component: Final[pt.TealComponent] = teal_component
        self.pcs: Final[list[int] | None] = pcs if pcs else None
        self.is_sentinel: Final[bool] = is_sentinel

    def pcs_repr(self, prefix: str = "") -> str:
        if not self.pcs:
            return ""
        return f"{prefix}({self.pcs[0]})"

    def __repr__(self) -> str:
        P = " // "
        return f"TealLine({self.teal_lineno}: {self.teal_line}{self.pcs_repr(prefix=P)} // PyTeal: {self._hybrid_w_offset()[0]})"

    def teal_column(self) -> int:
        """Always returns 0 as the 0-index STARTING column offset"""
        return 0

    def teal_column_end(self) -> int:
        """The 0-index ENDING column offset"""
        return len(self.teal_line)

    _dict_lazy_attrs = {
        _TEAL_LINE_NUMBER: lambda tmi: tmi.teal_lineno,
        _TEAL_LINE: lambda tmi: tmi.teal_line,
        _TEAL_COLUMN: lambda tmi: tmi.teal_column(),
        _TEAL_COLUMN_END: lambda tmi: tmi.teal_column_end(),
        _PROGRAM_COUNTERS: lambda tmi: tmi.pcs_repr(),
        _PYTEAL_HYBRID_UNPARSED: lambda tmi: tmi.hybrid_unparsed(),
        _PYTEAL_NODE_AST_UNPARSED: lambda tmi: tmi.node_source(),
        _PYTEAL_NODE_AST_QUALNAME: lambda tmi: tmi.code_qualname(),
        _PYTEAL_COMPONENT: lambda tmi: tmi.teal_component,
        _PYTEAL_NODE_AST_SOURCE_BOUNDARIES: lambda tmi: tmi.node_source_window(),
        _PYTEAL_FILENAME: lambda tmi: tmi.file(),
        _PYTEAL_LINE_NUMBER: lambda tmi: tmi.lineno(),
        _PYTEAL_LINE_NUMBER_END: lambda tmi: tmi.node_end_lineno(),
        _PYTEAL_COLUMN: lambda tmi: tmi.column(),
        _PYTEAL_COLUMN_END: lambda tmi: tmi.node_end_col_offset(),
        _PYTEAL_LINE: lambda tmi: tmi.raw_code(),
        _PYTEAL_NODE_AST: lambda tmi: tmi.node,
        _PYTEAL_NODE_AST_NONE: lambda tmi: tmi.failed_ast(),
        _STATUS_CODE: lambda tmi: tmi.status_code(),
        _STATUS: lambda tmi: tmi.status(),
    }

    def asdict(self, **kwargs) -> OrderedDict[str, Any]:
        """kwargs serve as a rename mapping when present"""
        assert (
            kwargs.keys() <= (attrs := self._dict_lazy_attrs).keys()
        ), f"unrecognized parameters {kwargs.keys() - attrs.keys()}"

        return OrderedDict(((kwargs[k], attrs[k](self)) for k in kwargs))

    def validate_for_export(self) -> None:
        """
        Ensure providing necessary and unambiguous data before exporting.
        """
        if self.teal_lineno is None:
            raise ValueError("unable to export without valid target TEAL line number")
        if self.lineno() is None:
            raise ValueError("unable to export without valid target PyTEAL line number")

    def source_mapping(self) -> "R3SourceMapping":
        self.validate_for_export()
        return R3SourceMapping(
            line=cast(int, self.teal_lineno) - 1,
            column=self.teal_column(),
            column_end=self.teal_column_end(),
            source=self.file(),
            source_line=cast(int, self.lineno()) - 1,
            source_column=self.column(),
            source_line_end=nel - 1 if (nel := self.node_end_lineno()) else None,
            source_column_end=self.node_end_col_offset(),
            source_extract=self.hybrid_unparsed(),
            target_extract=self.teal_line,
        )


@dataclass(frozen=True)
class PyTealSourceMap:
    """
    Encapsulate Expr-less source mapping data.

    Fields:
        - :code:`teal_filename` - The filename of the TEAL source file, or ``None`` if not provided.
        - :code:`r3_sourcemap` - The :any:`R3SourceMap` object, or ``None`` if not provided.
        - :code:`pc_sourcemap` - The :code:`PCSourceMap` object (aka :code:`for algosdk.source_map.SourceMap`), or ``None`` if not provided.
        - :code:`annotated_teal` - The annotated TEAL code as a string, or ``None`` if not provided.

    NOTE: type ``PCSourceMap`` is an alias for `algosdk.source_map.SourceMap <https://github.com/algorand/py-algorand-sdk/blob/1b8ad21e372bfbe30bb4b7c7d5c4ec3cb90ff6c5/algosdk/source_map.py#L6-L49>`_
    """

    teal_filename: str | None
    r3_sourcemap: R3SourceMap | None
    pc_sourcemap: PCSourceMap | None
    annotated_teal: str | None


PyTealSourceMap.__module__ = "pyteal"


class _PyTealSourceMapper:
    """
    _PyTealSourceMapper is the workhorse class that runs the sourcemapping algorithm.

    User-safe Expr-less artifacts are provided by methods:
    * get_sourcemap()
    * as_r3sourcemap()
    * annotated_teal()

    Source Mapping Algorithm:

    INPUT: (teal_chunks, components) - these are present in the output object of
        pyteal.compiler.compiler.Copmilation._compile_impl()

    OUTPUT: (self._cached_tmis, _cached_r3sourcemap, self._cached_pc_sourcemap)

    PASS I. Deduce the Best Frame Candidate (BFC) from each individual `NatalStackFrame`

    NOTE: this logic actually occurs at creation of the PyTeal Expr which is responsible
    for each teal component. The `build()` method simply retrieves the result of this
    pre-computation through NatalStackFrame.best()

    for each component in components:
        # Deduce the "best" frame for the component's PyTeal source (@ Expr creation)

        # [1-8] Inside NatalStackFrame.__init__()
        1. call inspect.stack() to generate a full stack trace
        2. filter out "py crud" frames whose filename starts with "<" and don't have a code_context
        3. start searching at frame index i = 2 (right before Expr's NatalStackFrame was constructed)
        4. fast forward through PyTeal frames until the first non PyTeal frame is found
        5. back up looking for a compiler gateway and so signal that the expression was generated by pyteal itself
        6. in the case this was in import statement, back up until a known compiler generated line is discovered
        7. keep the last frame in the list
        8. convert this into a list[StackFrame] of size 1

        # [9] Inside _PyTealSourceMapper.build() @ source-map creation:
        9. self._best_frames[i] = the singleton StackFrame in 7 converted to PyTealFrame  # i == component's index of the component

    PASS II. Attempt to fill any "gaps" by inferring from adjacent BFC's
    This logic is contained in _PyTealSourceMapper.infer():

    NOTE: the mutations of self._best_framed described below are "sticky" in the sense
    that when this `pyteal_frame` is modified and referenced by `prev_pyteal_frame`
    in the next interation, it is the new _modified_ version that is used.

    for each pyteal_frame in self._best_frames:
        status = pyteal_frame.status()
        if status NOT in PyTealFrameStatus.{MISSING, MISSING_AST, MISSING_CODE, PYTEAL_GENERATED}
            NO-OP # we can't do any better

        else: # call local method _PyTealSourceMapper.infer.infer_source()
            prev_pyteal_frame, next_pyteal_frame <--- get these from self._best_frames (or None if doesn't exist)
            if both exist:
                if both are equal (have the equal `frame_info, node, rel_paths`):
                    replace this pyteal_frame by next_pyteal_frame

                if pyteal_frame is flagged as compiler generated:
                    if its reason is one of PT_GENERATED.{TYPE_ENUM_ONCOMPLETE, TYPE_ENUM_TXN, BRANCH_LABEL, BRANCH}:
                        # these occur when one of the # T2PT* comments is encountered
                        replace this pyteal_frame by next_pyteal_frame

            if ONLY prev_frame exists:
                replace this pyteal_frame by prev_pyteal_frame

            # NOTE: Coverage shows we never get past here.
            # I.e. the first frame never results in one of the PyTealFrameStatus'es listed above
            if ONLY next_frame exists:
                replace this pyteal_frame by next_pyteal_frame

            if NEITHER next_frame NOR pyteal_frame exist:
                # this is basically impossible
                NO-OP # we can't do any better

    """

    UNEXPECTED_ERROR_SUFFIX = """This is an unexpected error. Please report this to the PyTeal team or create an issue at:
    https://github.com/algorand/pyteal/issues"""

    def __init__(
        self,
        teal_chunks: list[str],
        components: list["pt.TealComponent"],
        *,
        teal_filename: str | None = None,
        include_pcs: bool = False,
        algod: AlgodClient | None = None,
        build: bool = True,
        verbose: bool = False,
        annotate_teal: bool = False,
        annotate_teal_headers: bool = False,
        annotate_teal_concise: bool = True,
    ):
        """
        Args:
            teal_chunks: strings -each possibly multi-line- which represent a chunk
                of TEAL code generated by the PyTeal compiler
            components: TealComponent object in 1-to-1 correspondence with
                `teal_chunks` and which generated the chunk in the PyTeal compiler
            teal_filename (optional): filename of TEAL source to be used in source mapping.
                This file isn't actually saved
            include_pcs (optional): specifies whether program counters
                should be included in the map
            algod (optional): when `include_pcs == True`, an algod client is required
                and calls the compile endpoint in order to retrieve the PC's.
                In the case `include_pcs == True` but `algod` isn't provided, an algod
                client will be bootstrapped via pyteal.util.algod_with_assertion
            build (default=True): when True, building the sourcemap occurs at initialization
            verbose (default=False): when True, more debugging information will be logged
            annotate_teal (default=False): when True, a TEAL file will be provided with
                annotated comments that give PyTeal (and optionally PC) source information
            annotate_teal_headers (default=False): when True, an extra line will be added
                to the top of the annotated TEAL file to indicate each annotation column
            annotate_teal_concise (default=True): when False, additional columns will be added
                to the annotated TEAL file
        """
        if include_pcs:
            # bootstrap an algod_client if not provided, and in either case, run a healthcheck
            algod = algod_with_assertion(
                algod, msg="Adding PC's to sourcemap requires live Algod"
            )

        if not teal_chunks:
            raise TealInternalError("Please provide non-empty teal_chunks")

        if not components:
            raise TealInternalError("Please provide non-empty components")

        self.teal_chunks: Final[list[str]] = teal_chunks
        self.components: Final[list["pt.TealComponent"]] = components

        self.algod: AlgodClient | None = algod

        self.include_pcs: bool = include_pcs

        self.teal_filename: str | None = teal_filename
        self.verbose: bool = verbose

        self._best_frames: list[PyTealFrame | None] = []
        self._cached_r3sourcemap: R3SourceMap | None = None

        self._cached_tmis: list[TealMapItem] = []
        self._cached_pc_sourcemap: PCSourceMap | None = None

        self._most_recent_omit_headers: bool | None = None

        # FOR DEBUGGING PURPOSES ONLY:
        self._inferred_frames_at: list[int] = []

        if annotate_teal or build:
            self.build()

        self._annotated_teal: str | None = None
        if annotate_teal:
            self._annotated_teal = self.annotated_teal(
                omit_headers=(oh := not annotate_teal_headers),
                concise=annotate_teal_concise,
            )
            self._most_recent_omit_headers = oh

    def get_sourcemap(self, teal_for_validation: str) -> PyTealSourceMap:
        if not self._built():
            raise self._unexpected_error("source map not built yet")

        if self._annotated_teal:
            if (oh := self._most_recent_omit_headers) is None:
                raise self._unexpected_error(
                    "_most_recent_omit_headers is None unexpectedly after calculating annotated_teal"
                )

            self._validate_annotated(
                oh, teal_for_validation.splitlines(), self._annotated_teal.splitlines()
            )

        return PyTealSourceMap(
            self.teal_filename,
            self._cached_r3sourcemap,
            self._cached_pc_sourcemap,
            self._annotated_teal,
        )

    def compiled_teal(self) -> str:
        return "\n".join(self.teal_chunks)

    def _built(self) -> bool:
        """
        If any portion of source map is missing, re-build it from scratch
        """
        return all(
            [
                not self.include_pcs or self._cached_pc_sourcemap,
                self._cached_r3sourcemap,
                self._cached_tmis,
            ]
        )

    @classmethod
    def _unexpected_error(cls, msg: str) -> TealInternalError:
        return TealInternalError(
            f"""{msg}
        {cls.UNEXPECTED_ERROR_SUFFIX}"""
        )

    def build(self) -> None:
        if self._built():
            return

        if self.include_pcs:
            self._build_pc_sourcemap()

        # Validation
        # sanity check teal_chunks, but discard them in the rest of the computation
        # assert teal_chunks <--1-to-1--> components

        if (n := len(self.teal_chunks)) != len(self.components):
            raise self._unexpected_error(
                f"expected same number of teal chunks ({n}) and components ({len(self.components)})"
            )

        if n == 0:
            raise self._unexpected_error(
                "cannot generate empty source map: no components"
            )

        # PASS I. Deduce the Best Frame Candidate (BFC) from each individual `NatalStackFrame`
        # See NatalStackFrame.__init__() for steps 1-7 which happen when an Expr is created
        # 8. the list comprehension below converts each element
        #   FROM: the component's NatalStackFrame._frames : list[StackFrame]
        #   TO:   a PyTealFrame
        # overall resulting in a list[PyTealFrame]
        self._best_frames = [
            tc.stack_frames()._best_frame_as_pyteal_frame() for tc in self.components
        ]

        if not self._best_frames:
            raise self._unexpected_error(
                f"This shouldn't have happened as we already checked! Check again: {len(self.components)=}"
            )

        # stand-in in the case of missing frames
        sentinel_frame = self._best_frames[0]
        assert (
            sentinel_frame
        ), "Abort source mapping as even the very first best frame is missing"

        # PASS II. Attempt to fill any "gaps" by inferring from adjacent BFC's
        self._best_frames, inferred = self._infer(self._best_frames)
        if inferred:
            self._inferred_frames_at = inferred

        lineno = 1
        for i, best_frame in enumerate(self._best_frames):
            teal_chunk = self.teal_chunks[i]
            for line in teal_chunk.splitlines():
                pcsm = cast(PCSourceMap, self._cached_pc_sourcemap)
                pcs = None
                if self.include_pcs:
                    pcs = pcsm.line_to_pc.get(lineno - 1, [])
                self._cached_tmis.append(
                    TealMapItem(
                        pt_frame=best_frame or sentinel_frame,
                        teal_lineno=lineno,
                        teal_line=line,  # type: ignore
                        teal_component=self.components[i],
                        pcs=pcs,
                        is_sentinel=(best_frame is None),
                    )
                )
                lineno += 1

        self._build_r3sourcemap()

        if not NatalStackFrame._debugging():
            # cf. https://stackoverflow.com/questions/850795/different-ways-of-clearing-lists#answer-44349418
            self._best_frames *= 0
            self._inferred_frames_at *= 0

        self._validate_build()

    def _validate_build(self):
        dechunked = [line for chunk in self.teal_chunks for line in chunk.splitlines()]

        if (ld := len(dechunked)) != (ltmi := len(self._cached_tmis)):
            raise self._unexpected_error(
                f"teal chunks has {ld} teal lines which doesn't match the number of cached TealMapItem's ({ltmi})"
            )

        if (lr3 := len(r3_target_lines := self._cached_r3sourcemap.file_lines)) != ltmi:
            raise self._unexpected_error(
                f"there are {ltmi} TealMapItem's which doesn't match the number of file_lines in the cached R3SourceMap ({lr3})"
            )

        for i, line in enumerate(dechunked):
            if line != (tmi_line := self._cached_tmis[i].teal_line):
                raise self._unexpected_error(
                    f"teal chunk lines don't match TealMapItem's at index {i}. ('{line}' v. '{tmi_line}')"
                )
            if tmi_line != (target_line := r3_target_lines[i]):
                raise self._unexpected_error(
                    f"TealMapItem's don't match R3SourceMap.file_lines at index {i}. ('{tmi_line}' v. '{target_line}')"
                )

        for tmi in self._cached_tmis:
            if not tmi.is_sentinel:
                continue
            print(
                f"""-----------------
WARNING: Source mapping is unknown for the following:
{tmi!r}
"""
            )

    def _build_r3sourcemap(self):
        assert self._cached_tmis, "Unexpected error: no cached TealMapItems found"

        root = self._cached_tmis[0].root()
        assert all(
            root == tmi.root() for tmi in self._cached_tmis
        ), "inconsistent sourceRoot - aborting"

        r3sms = [tmi.source_mapping() for tmi in self._cached_tmis]
        entries = {(r3sm.line, r3sm.column): r3sm for r3sm in r3sms}
        lines = [cast(str, r3sm.target_extract) for r3sm in r3sms]

        index_l: list[list[int]] = [[]]

        prev_line = 0
        for line, col in entries.keys():
            for _ in range(prev_line, line):
                index_l.append([])
            curr = index_l[-1]
            curr.append(col)
            prev_line = line

        index: list[tuple[int, ...]] = [tuple(cs) for cs in index_l]
        sources = []
        for tmi in self._cached_tmis:
            if (f := tmi.file()) not in sources:
                sources.append(f)

        self._cached_r3sourcemap = R3SourceMap(
            filename=self.teal_filename,
            source_root=root,
            entries=entries,
            index=index,
            file_lines=lines,
            source_files=sorted(sources),
        )

    def _build_pc_sourcemap(self):
        """
        Prereq: self.teal_chunks - a Final member
        """
        algod = algod_with_assertion(
            self.algod, msg="Adding PC's to sourcemap requires live Algod"
        )

        teal: str = self.compiled_teal()
        for placeholder in pt.Tmpl.session_templates():
            teal = teal.replace(placeholder, pt.Tmpl.zero(placeholder))

        algod_compilation = algod.compile(teal, source_map=True)
        raw_sourcemap = algod_compilation.get("sourcemap")
        if not raw_sourcemap:
            raise TealInternalError(
                f"algod compilation did not return 'sourcemap' as expected. {algod_compilation=}"
            )
        self._cached_pc_sourcemap = PCSourceMap(raw_sourcemap)

    def as_list(self) -> list[TealMapItem]:
        self.build()
        return self._cached_tmis

    def as_r3sourcemap(self) -> R3SourceMap | None:
        self.build()
        return self._cached_r3sourcemap

    @classmethod
    def _infer(
        cls, best_frames: list[PyTealFrame | None]
    ) -> tuple[list[PyTealFrame | None], list[int]]:
        inferred = []
        frames = list(best_frames)
        N = len(frames)

        def infer_source(i: int) -> PyTealFrame | None:
            frame = frames[i]
            if not frame:
                return None

            prev_frame = None if i <= 0 else frames[i - 1]
            next_frame = None if N <= i + 1 else frames[i + 1]
            if prev_frame and next_frame:
                if prev_frame == next_frame:
                    return prev_frame.clone(PyTealFrameStatus.PATCHED_BY_PREV_AND_NEXT)

                # PT Generated TypeEnum's presumably happened because of setting an transaction
                # field in the next step:
                reason = frame.compiler_generated_reason()
                if reason in [
                    PT_GENERATED.TYPE_ENUM_ONCOMPLETE,
                    PT_GENERATED.TYPE_ENUM_TXN,
                    PT_GENERATED.BRANCH_LABEL,
                    PT_GENERATED.BRANCH,
                ]:
                    return next_frame.clone(
                        PyTealFrameStatus.PATCHED_BY_NEXT_OVERRIDE_PREV
                    )

                # NO-OP otherwise:
                return None

            if prev_frame and frame:
                return prev_frame.clone(PyTealFrameStatus.PATCHED_BY_PREV)

            # TODO: We never get here because we have no trouble with the #pragma component
            # Either remove or make it useful
            if next_frame and frame:
                return next_frame.clone(PyTealFrameStatus.PATCHED_BY_NEXT)

            return None

        for i in range(N):
            f = frames[i]
            if f and f.status_code() <= PyTealFrameStatus.PYTEAL_GENERATED:
                ptf_or_none = infer_source(i)
                if ptf_or_none:
                    inferred.append(i)
                    frames[i] = ptf_or_none

        return frames, inferred

    def pure_teal(self) -> str:
        return "\n".join(tmi.teal_line for tmi in self.as_list())

    _tabulate_param_defaults: Final[dict[str, str]] = dict(
        teal=_TEAL_LINE,
        pyteal_hybrid_unparsed=_PYTEAL_HYBRID_UNPARSED,
        pyteal=_PYTEAL_NODE_AST_UNPARSED,
        teal_line_number=_TEAL_LINE_NUMBER,
        teal_column=_TEAL_COLUMN,
        teal_column_end=_TEAL_COLUMN_END,
        program_counters=_PROGRAM_COUNTERS,
        pyteal_component=_PYTEAL_COMPONENT,
        pyteal_node_ast_qualname=_PYTEAL_NODE_AST_QUALNAME,
        pyteal_filename=_PYTEAL_FILENAME,
        pyteal_line_number=_PYTEAL_LINE_NUMBER,
        pyteal_line_number_end=_PYTEAL_LINE_NUMBER_END,
        pyteal_column=_PYTEAL_COLUMN,
        pyteal_column_end=_PYTEAL_COLUMN_END,
        pyteal_line=_PYTEAL_LINE,
        pyteal_node_ast_source_boundaries=_PYTEAL_NODE_AST_SOURCE_BOUNDARIES,
        pyteal_node_ast_none=_PYTEAL_NODE_AST_NONE,
        status_code=_STATUS_CODE,
        status=_STATUS,
    )

    def tabulate(
        self,
        *,
        tablefmt="fancy_grid",
        numalign="right",
        omit_headers: bool = False,
        omit_repeating_col_except: list[str] | None = None,
        post_process_delete_cols: list[str] | None = None,
        **kwargs: dict[str, str],
    ) -> str:
        """
        Tabulate a sourcemap using Python's tabulate package: https://pypi.org/project/tabulate/

        Columns are named and ordered by the arguments provided

        Args:
            tablefmt (default 'fancy_grid'): format specifier used by tabulate.
                For choices see: https://github.com/astanin/python-tabulate#table-format

            numalign (default 'right'): alignment of numbers. Choices are 'left', 'right', 'decimal', 'center' or None.
                See: https://github.com/astanin/python-tabulate#column-alignment

            omit_headers (default `False`): Do not include the column headers when `True`

            omit_repeating_col_except (default None): specify columns for which repetitions should be printed out.
                The Teal source column and constant columns such as the comment "//" column are always repeated regardless of this setting

            post_process_delete_cols (default None): Specify columns to delete after tabulation

            **kwargs: Additional keyword arguments are passed to tabulate to represent desired columns.
                The order of these columns as arguments determines the column order. These MUST conform to the following parameters:

                teal (required): Teal target source code. This is the only mandatory column

                const_col_[.*] (optional): specify any number of columns to be treated as constant and always repeated

                pyteal_hybrid_unparsed (optional): PyTeal source via `executing.unparse` when available, or otherwise
                    via `FrameInfo.code_condext`

                pyteal (optional): PyTeal source via `executing.unparse` when available, or otherwise "" (empty string)

                teal_line_number (optional): Teal target's line number (1-based)

                teal_column (optional): Teal target's 0-indexed starting column (CURRENTLY THIS IS ALWAYS 0)

                teal_column_end (optional): Teal target's 0-indexed right boundary column (CURRENTLY THIS IS len(teal))

                program_counters (optional): starting program counter as assembled by algod

                pyteal_component (optional): representation of the PyTeal source component mapping to target

                pyteal_node_ast_qualname (optional): the Python qualname of the PyTeal source

                pyteal_filename (optional): the filename of the PyTeal source

                pyteal_line_number (optional): the PyTeal source's beginning line number

                pyteal_line_number_end (optional): the PyTeal source's ending line number

                pyteal_column (optional): the PyTeal source's starting 0-indexed column

                pyteal_column_end (optional): the PyTeal source's ending 0-indexed boundary column

                pyteal_line (optional): the PyTeal source as provided by `FrameInfo.code_context`

                pyteal_node_ast_source_boundaries (optional): formatted representation of the PyTeal source's line and column boundaries. Eg "L17:5-L42:3"

                pyteal_node_ast_none (optional): boolean indicator of whether the AST node was successfully extracted for the PyTeal source

                status_code (optional): `PyTealFrameStatus` int value indicating confidence level for locating the PyTeal source responsible for generated Teal

                status (optional): simlar to `status_code` but with a human readable string representation

        Returns:
            A ready to print string containing the table information.
        """

        assert (
            "teal" in kwargs
        ), "teal column must be specified, but 'teal' is missing in kwargs"

        # 0. e.g. suppose:
        #
        # kwargs == dict(
        #     teal                      =   "// TEAL",
        #     const_col_2               =   "//",
        #     pyteal_filename           =   "PATH",
        #     pyteal_line_number        =   "LINE",
        #     const_col_5               =   "|",
        #     pyteal_hybrid_unparsed    =   "PYTEAL",
        # )

        constant_columns = {}
        new_kwargs = {}
        for i, (k, v) in enumerate(kwargs.items()):
            if k.startswith("const_col_"):
                constant_columns[i] = v
            else:
                new_kwargs[k] = v

        # 1. now we have:
        #
        # new_kwargs == dict(
        #     teal                      =   "// TEAL",
        #     pyteal_filename           =   "PATH",
        #     pyteal_line_number        =   "LINE",
        #     pyteal_hybrid_unparsed    =   "PYTEAL",
        # )
        #
        # and
        #
        # constant_columns == {
        #     1: "//",
        #     4: "|",
        # }

        for k in new_kwargs:
            assert k in self._tabulate_param_defaults, f"unrecognized parameter '{k}'"

        # 2. now we know that all the provided keys were valid

        renames = {self._tabulate_param_defaults[k]: v for k, v in new_kwargs.items()}

        # 3. now we have:
        #
        # renames == {
        #     _TEAL_LINE:                 "// TEAL",
        #     _PYTEAL_FILENAME:           "PATH",
        #     _PYTEAL_LINE_NUMBER:        "LINE",
        #     _PYTEAL_HYBRID_UNPARSED:    "PYTEAL",
        # }

        rows = [teal_item.asdict(**renames) for teal_item in self.as_list()]

        # 4. now we've populated the rows:
        #
        # rows == [ {_TEAL_LINE: 1, _PYTEAL_FILENAME: "foo.py", _PYTEAL_LINE_NUMBER: 79, _PYTEAL_HYBRID_UNPARSED: "Int(42)"}, ... ]

        if constant_columns:

            def add_const_cols(row):
                i = 0
                new_row = {}
                for k, v in row.items():
                    if i in constant_columns:
                        new_row[f"_{i}"] = constant_columns[i]
                        i += 1
                    new_row[k] = v
                    i += 1
                return new_row

            rows = list(map(add_const_cols, rows))
            # 5. now we've added the constant columns to the rows:
            #
            # rows == [ {_TEAL_LINE: 1, "_1": "//", _PYTEAL_FILENAME: "foo.py", _PYTEAL_LINE_NUMBER: 79, "_4": "|", _PYTEAL_HYBRID_UNPARSED: "Int(42)"}, ... ]
            #                           ^^^^^^^^^^                                                       ^^^^^^^^^

            renames = add_const_cols(renames)
            # 6. and we've added the constant columns at the required ordering to the renames as well:
            #
            # renames == {
            #     _TEAL_LINE:                 "// TEAL",
            #     "_1":                       "//",
            #     _PYTEAL_FILENAME:           "PATH",
            #     _PYTEAL_LINE_NUMBER:        "LINE",
            #     "_4":                       "|",
            #     _PYTEAL_HYBRID_UNPARSED:    "PYTEAL",
            # }

        teal_col_name = renames[_TEAL_LINE]
        pt_simple_col_name = renames.get(_PYTEAL_COLUMN)
        pt_hybrid_col_name = renames.get(_PYTEAL_HYBRID_UNPARSED)
        pt_window_col_name = renames.get(_PYTEAL_NODE_AST_SOURCE_BOUNDARIES)
        if omit_repeating_col_except:
            # Assume the following column structure:
            # * col 0 is the generated source with column name stored in `teal_col`
            # * the source line number has column name stored in `pyteal_line_number`
            # * the pyteal source has column name stored in `pyteal` OR `pyteal_hybrid_unparsed`
            #
            # Consequently, when `teal_col` is repeating we need to take extra care NOT
            # to omit repeating source values, as these were likely coming from different portions of the source

            def reduction(row, next_row):
                drop_2nd_pyteal = True
                if pt_window_col_name and (
                    row[pt_window_col_name] or next_row[pt_window_col_name]
                ):
                    drop_2nd_pyteal = (
                        row[pt_window_col_name] == next_row[pt_window_col_name]
                    )
                else:
                    drop_2nd_pyteal = row[teal_col_name] != next_row[teal_col_name]
                return {
                    k: v2
                    for k, v in row.items()
                    if any(
                        [
                            (v2 := next_row[k]) != v,
                            k in omit_repeating_col_except,
                            k in (pt_hybrid_col_name, pt_simple_col_name)
                            and not drop_2nd_pyteal,
                        ]
                    )
                }

            rows = [rows[0]] + list(
                map(lambda r_and_n: reduction(*r_and_n), zip(rows[:-1], rows[1:]))
            )
            # 7. now we've removed repetitions of appropriate columns

        if post_process_delete_cols:
            for col in post_process_delete_cols:
                col_name = renames.pop(col)
                for row in rows:
                    if col_name in row:
                        del row[col_name]  # type: ignore
        # 8. now we've removed any columns requested for deletion

        calling_kwargs: dict[str, Any] = {"tablefmt": tablefmt, "numalign": numalign}
        if not omit_headers:
            calling_kwargs["headers"] = renames

        return tabulate(rows, **calling_kwargs)

    def annotated_teal(self, omit_headers: bool = True, concise: bool = True) -> str:
        """
        Helper function that hardcodes various tabulate parameters to produce a
        reasonably formatted annotated teal output.

        In theory, the output can be compiled.

        In practice the output maybe be very large and therefore unacceptable to Algod.

        In such cases, you should use the original accompanying Teal compilation.
        """
        if not self._built():
            raise ValueError(
                "not ready for annotated_teal() because build() has yet to be called"
            )

        if not (r3sm := cast(R3SourceMap, self._cached_r3sourcemap)):
            raise self._unexpected_error("R3SourceMap not available but should be")

        if not (file_lines := cast(list[str], r3sm.file_lines)):
            raise self._unexpected_error(
                "_cached_r3sourcemap.file_lines not available but should be"
            )

        teal_col = "// GENERATED TEAL"
        comment_col = "_1"
        kwargs = dict(
            tablefmt="plain",
            omit_headers=omit_headers,
            omit_repeating_col_except=[teal_col, comment_col],
            numalign="left",
            teal=teal_col,
            const_col_2="//",
        )

        if self.include_pcs:
            kwargs["program_counters"] = "PC"

        if not concise:
            kwargs["pyteal_filename"] = "PYTEAL PATH"
            kwargs["pyteal_line_number"] = "LINE"

        kwargs["pyteal_hybrid_unparsed"] = "PYTEAL"
        kwargs["pyteal_node_ast_source_boundaries"] = "PYTEAL RANGE"

        kwargs["post_process_delete_cols"] = [_PYTEAL_NODE_AST_SOURCE_BOUNDARIES]
        annotated = self.tabulate(**kwargs)  # type: ignore

        self._validate_annotated(omit_headers, file_lines, annotated.splitlines())

        return annotated

    @classmethod
    def _validate_annotated(
        cls, omit_headers: bool, teal_lines: list[str], annotated_lines: list[str]
    ):
        header_delta = 1 - bool(omit_headers)
        if (ltl := len(teal_lines)) + header_delta != (latl := len(annotated_lines)):
            raise cls._unexpected_error(
                f"mismatch between count of teal_lines ({ltl}) and annotated_lines ({latl}) for the case {omit_headers=}",
            )

        for i, (teal_line, annotated_line) in enumerate(
            zip(teal_lines, annotated_lines[header_delta:])
        ):
            if not annotated_line.startswith(teal_line):
                raise cls._unexpected_error(
                    f"annotated teal ought to begin exactly with the teal line but line {i + 1} [{annotated_line}] doesn't start with [{teal_line}]",
                )
            pattern = r"^\s*($|//.*)"
            if not re.match(pattern, annotated_line[len(teal_line) :]):
                raise cls._unexpected_error(
                    f"annotated teal ought to begin exactly with the teal line followed by annotation in comments but line {i + 1} [{annotated_line}] has non-commented out annotations"
                )

    @classmethod
    def _validate_teal_identical(
        cls,
        original_teal: str,
        new_teal: str,
        msg: str,
    ):
        if original_teal == new_teal:
            return

        diff = list(unified_diff(original_teal.splitlines(), new_teal.splitlines()))
        raise cls._unexpected_error(
            f"""{msg}. Original teal differs with new: 
    {''.join(diff)}"""
        )
