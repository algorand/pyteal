import ast
import bisect
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from itertools import count
from typing import (
    Any,
    Final,
    List,
    Literal,
    Mapping,
    Optional,
    OrderedDict,
    Tuple,
    TypedDict,
    Union,
    cast,
)

from algosdk.source_map import SourceMap as PCSourceMap
from algosdk.v2client.algod import AlgodClient
from tabulate import tabulate  # type: ignore

import pyteal as pt
from pyteal.errors import TealInternalError
from pyteal.stack_frame import StackFrames, PT_GENERATED, PyTealFrame, PytealFrameStatus
from pyteal.util import algod_with_assertion


# ### ---- Based on mjpieters CODE ---- ### #
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


def _base64vlq_decode(vlqval: str) -> List[int]:
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
    source: Optional[str] = None
    source_line: Optional[int] = None
    source_column: Optional[int] = None
    source_content: Optional[List[str]] = None
    source_extract: Optional[str] = None
    target_extract: Optional[str] = None
    name: Optional[str] = None
    source_line_end: Optional[int] = None
    source_column_end: Optional[int] = None
    column_end: Optional[int] = None

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

    def location(self, source=False) -> Tuple[str, int, int]:
        return (
            (
                self.source if self.source else "",
                self.source_line if self.source_line else -1,
                self.source_column if self.source_column else -1,
            )
            if source
            else ("", self.line, self.column)
        )

    # TODO: THIS IS CURRENTLY BROKEN BUT USEFUL
    # @property
    # def content_line(self) -> Optional[str]:
    #     try:
    #         return self.source_content[self.source_line]
    #     except (TypeError, IndexError):
    #         return None

    @classmethod
    def extract_window(
        cls,
        source_lines: Optional[List[str]],
        line: int,
        column: int,
        right_column: Optional[int],
    ) -> Optional[str]:
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
    file: Optional[str]
    sourceRoot: Optional[str]
    sources: List[str]
    sourcesContent: Optional[List[Optional[str]]]
    names: List[str]
    mappings: str


@dataclass(frozen=True)
class R3SourceMap:
    file: Optional[str]
    source_root: Optional[str]
    entries: Mapping[Tuple[int, int], "R3SourceMapping"]
    index: List[Tuple[int, ...]] = field(default_factory=list)
    file_lines: Optional[List[str]] = None
    source_files: Optional[List[str]] = None
    source_files_lines: Optional[List[List[str] | None]] = None

    def __post_init__(self):
        entries = list(self.entries.values())
        for i, entry in enumerate(entries):
            if i + 1 >= len(entries):
                return

            if entry >= entries[i + 1]:
                raise TypeError(
                    f"Invalid source map as entries aren't properly ordered: entries[{i}] = {entry} >= entries[{i+1}] = {entries[i + 1]}"
                )

    def __repr__(self) -> str:
        parts = []
        if self.file is not None:
            parts += [f"file={self.file!r}"]
        if self.source_root is not None:
            parts += [f"source_root={self.source_root!r}"]
        parts += [f"len={len(self.entries)}"]
        return f"<MJPSourceMap({', '.join(parts)})>"

    @classmethod
    def from_json(
        cls,
        smap: R3SourceMapJSON,
        sources_override: Optional[List[str]] = None,
        sources_content_override: List[str] = [],
        target: Optional[str] = None,
        add_right_bounds: bool = True,
    ) -> "R3SourceMap":
        """
        NOTE about `*_if_missing` arguments
        * sources_override - STRICTLY SPEAKING `sources` OUGHT NOT BE MISSING OR EMPTY in R3SourceMapJSON.
            However, currently the POST v2/teal/compile endpoint populate this field with an empty list, as it is not provided the name of the
            Teal file which is being compiled. In order comply with the R3 spec, this field is populated with ["unknown"] when either missing or empty
            in the JSON and not supplied during construction.
            An error will be raised when attempting to replace a nonempty R3SourceMapJSON.sources.
        * sources_content_override - `sourcesContent` is optional and this provides a way at runtime to supply the actual source.
            When provided, and the R3SourceMapJSON is either missing or empty, this will be substituted.
            An error will be raised when attempting to replace a nonempty R3SourceMapJSON.sourcesContent.
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

        contents: List[str | None] | List[str] | None = smap.get("sourcesContent")
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
        if self.file is not None:
            encoded["file"] = self.file
        if self.source_root is not None:
            encoded["sourceRoot"] = self.source_root
        return encoded  # type: ignore

    def __getitem__(self, idx: Union[int, Tuple[int, int]]):
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


# #### PyTeal Specific Classes below #### #

_TEAL_LINE_NUMBER = "TL"
_TEAL_COLUMN = "TC"
_TEAL_COLUMN_END = "TCE"
_TEAL_LINE = "Teal Line"
_TABULATABLE_TEAL = "Tabulatable Teal"
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
_PYTEAL_FRAME = "PT Frame"
_PYTEAL_NODE_AST_NONE = "FAILED"
_STATUS_CODE = "Sourcemap Status Code"
_STATUS = "Sourcemap Status"


# TODO: move this to pyteal.errors
class SourceMapDisabledError(RuntimeError):
    msg = value = """
    Cannot calculate Teal to PyTeal source map because stack frame discovery is turned off.

    To enable source maps, set `enabled = True` in `pyteal.ini`'s [pyteal-source-mapper] section.
    """

    def __str__(self):
        return self.msg


class TealMapItem(PyTealFrame):
    def __init__(
        self,
        pt_frame: PyTealFrame,
        teal_lineno: int,
        teal_line: str,
        teal_component: "pt.TealComponent",
        pcs: list[int] | None = None,
    ):
        super().__init__(
            frame_info=pt_frame.frame_info,
            node=pt_frame.node,
            creator=pt_frame.creator,
            full_stack=pt_frame.full_stack,
            rel_paths=pt_frame.rel_paths,
            parent=pt_frame.parent,
        )
        self.teal_lineno: int = teal_lineno
        self.teal_line: str = teal_line
        self.teal_component: pt.TealComponent = teal_component
        self.pcs_hydrated: bool = pcs is not None
        self.pcs: list[int] | None = pcs if pcs else None

    def _hybrid_w_offset(self) -> tuple[str, int]:
        """
        Delegates to super except in the very special case that this is a Return()
        """
        if (
            isinstance(self.teal_component.expr, pt.Return)
            and isinstance(self.teal_component, pt.TealOp)
            and (teal_op := cast(pt.TealOp, self.teal_component))
            and teal_op.op is pt.Op.retsub
        ):
            node = self.node
            is_return = False
            while node and not (is_return := isinstance(node, ast.Return)):
                node = getattr(node, "parent", None)

            if node and is_return:  # and (node := getattr(node, "parent", None)):
                # if isinstance(node, ast.FunctionDef):
                code = self.code()
                pt_chunk = ast.unparse(node)
                return self._hybrid_impl(code, node, pt_chunk)

        return super()._hybrid_w_offset()

    def pcs_repr(self, prefix: str = "") -> str:
        if not self.pcs_hydrated:
            return ""

        pcs_repr = prefix + "PC[{}]"
        internal = ""
        if self.pcs:
            internal += str(self.pcs[0])
            if len(self.pcs) > 1:
                internal += "-" + str(self.pcs[-1])
        return pcs_repr.format(internal)

    def __repr__(self) -> str:
        P = " // "
        return f"TealLine({self.teal_lineno}: {self.teal_line}{self.pcs_repr(prefix=P)} // PyTeal: {self._hybrid_w_offset()[0]}"

    def asdict(self, **kwargs) -> OrderedDict[str, Any]:
        """kwargs serve as a rename mapping when present"""
        attrs = {
            _TEAL_LINE_NUMBER: self.teal_lineno,
            _TEAL_LINE: self.teal_line,
            _PROGRAM_COUNTERS: self.pcs_repr(),
            _PYTEAL_HYBRID_UNPARSED: self.hybrid_unparsed(),
            _PYTEAL_NODE_AST_UNPARSED: self.node_source(),
            _PYTEAL_NODE_AST_QUALNAME: self.code_qualname(),
            _PYTEAL_COMPONENT: self.teal_component,
            _PYTEAL_NODE_AST_SOURCE_BOUNDARIES: self.node_source_window(),
            _PYTEAL_FILENAME: self.file(),
            _PYTEAL_LINE_NUMBER: self.lineno(),
            _PYTEAL_LINE_NUMBER_END: self.node_end_lineno(),
            _PYTEAL_COLUMN: self.column(),
            _PYTEAL_COLUMN_END: self.node_end_col_offset(),
            _PYTEAL_LINE: self.code(),
            _PYTEAL_NODE_AST: self.node,
            _PYTEAL_NODE_AST_NONE: self.failed_ast(),
            _STATUS_CODE: self.status_code(),
            _STATUS: self.status(),
        }

        assert (
            kwargs.keys() <= attrs.keys()
        ), f"unrecognized parameters {kwargs.keys() - attrs.keys()}"

        return OrderedDict(((kwargs[k], attrs[k]) for k in kwargs))

    def validate_for_export(self) -> None:
        """
        Ensure providing necessary and unambiguous data before exporting.
        """
        if self.teal_lineno is None:
            raise ValueError("unable to export without valid line number: None")
        if (line := self.lineno()) is None or self.column() is None:
            col = self.column()
            raise ValueError(
                f"unable to export without valid line and column for SOURCE but got: {line=}, {col=}"
            )

    def source_mapping(self, _hybrid: bool = True) -> "R3SourceMapping":
        self.validate_for_export()
        return R3SourceMapping(
            line=cast(int, self.teal_lineno) - 1,
            column=0,
            column_end=len(self.teal_line) - 1,
            source=self.file(),
            source_line=cast(int, self.lineno()) - 1,
            source_column=self.column(),
            source_line_end=nel - 1 if (nel := self.node_end_lineno()) else None,
            source_column_end=self.node_end_col_offset(),
            source_extract=self.hybrid_unparsed() if _hybrid else self.code(),
            target_extract=self.teal_line,
        )


class PyTealSourceMap:
    def __init__(
        self,
        teal_chunks: list[str],
        components: list["pt.TealComponent"],
        *,
        teal_file: str | None = None,
        annotate_teal: bool = False,
        include_pcs: bool = False,
        algod: AlgodClient | None = None,
        build: bool = True,
        verbose: bool = False,
        # deprecated:
        _source_inference: bool = True,
        _hybrid: bool = True,
    ):
        if include_pcs:
            # bootstrap an algod_client if not provided, and in either case, run a healthcheck
            algod = algod_with_assertion(
                algod, msg="Adding PC's to sourcemap requires live Algod"
            )

        self.teal_chunks: Final[list[str]] = teal_chunks
        self.components: Final[list["pt.TealComponent"]] = components

        self.algod: AlgodClient | None = algod

        self.include_pcs: bool = include_pcs
        self.annotate_teal: bool = annotate_teal

        self.teal_file: str | None = teal_file
        self.verbose: bool = verbose

        # --- deprecated fields BEGIN
        self._hybrid: bool = _hybrid
        self._source_inference: bool = _source_inference
        # --- deprecated fields END

        self._best_frames: list[PyTealFrame] = []
        self._cached_r3sourcemap: R3SourceMap | None = None
        self._inferred_frames_at: list[int] = []

        self._cached_tmis: list[TealMapItem] = []
        self._cached_pc_sourcemap: PCSourceMap | None = None

        if build:
            self.build()

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

    def build(self) -> None:
        if self._built():
            return

        if self.include_pcs:
            self._build_pc_sourcemap()

        if (n := len(self.teal_chunks)) != len(self.components):
            raise TealInternalError(
                f"expected same number of teal chunks {n} and components {len(self.components)}"
            )
        self._best_frames = [
            tc.stack_frames()[-1].as_pyteal_frame() for tc in self.components
        ]

        if self._source_inference:
            # TODO: hard-code this deprecated field to always be True ASAP
            mutated = self._search_for_better_frames_and_modify(self._best_frames)
            if mutated:
                self._inferred_frames_at = mutated

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
                        pt_frame=best_frame,
                        teal_lineno=lineno,
                        teal_line=line,  # type: ignore
                        teal_component=self.components[i],
                        pcs=pcs,
                    )
                )
                lineno += 1

        self._build_r3sourcemap()

        if not StackFrames._debug:
            self._best_frames = []
            self._inferred_frames_at = []

    def _build_r3sourcemap(self):
        assert self._cached_tmis, "Unexpected error: no cached TealMapItems found"

        root = self._cached_tmis[0].root()
        assert all(
            root == tmi.root() for tmi in self._cached_tmis
        ), "inconsistent sourceRoot - aborting"

        r3sms = [tmi.source_mapping(_hybrid=self._hybrid) for tmi in self._cached_tmis]
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
            file=self.teal_file,
            source_root=root,
            entries=entries,
            index=index,
            file_lines=lines,
            source_files=list(sorted(sources)),
        )

    def _build_pc_sourcemap(self):
        """
        Prereq: self.teal_chunks - a Final member
        """
        algod = algod_with_assertion(
            self.algod, msg="Adding PC's to sourcemap requires live Algod"
        )
        algod_compilation = algod.compile(self.compiled_teal(), source_map=True)
        raw_sourcemap = algod_compilation.get("sourcemap")
        if not raw_sourcemap:
            raise TealInternalError(
                f"algod compilation did not return 'sourcemap' as expected. {algod_compilation=}"
            )
        self._cached_pc_sourcemap = PCSourceMap(raw_sourcemap)

    def as_list(self) -> list[TealMapItem]:
        # TODO: finer grained caching/building
        self.build()
        return self._cached_tmis

    def as_r3sourcemap(self) -> R3SourceMap | None:
        # TODO: finer grained caching/building
        self.build()
        return self._cached_r3sourcemap

    def _search_for_better_frames_and_modify(
        self, frames: list[PyTealFrame]
    ) -> list[int]:
        N = len(frames)
        mutated = []

        def infer_source(i: int) -> PyTealFrame | None:
            frame = frames[i]
            if not frame:
                return None

            prev_frame = None if i <= 0 else frames[i - 1]
            next_frame = None if N <= i + 1 else frames[i + 1]
            if prev_frame and next_frame:
                if prev_frame == next_frame:
                    return frame.spawn(
                        prev_frame, PytealFrameStatus.PATCHED_BY_PREV_AND_NEXT
                    )

                # PT Generated TypeEnum's presumably happened because of setting an transaction
                # field in the next step:
                reason = frame.compiler_generated_reason()
                if reason in [
                    PT_GENERATED.TYPE_ENUM_ONCOMPLETE,
                    PT_GENERATED.TYPE_ENUM_TXN,
                    PT_GENERATED.BRANCH_LABEL,
                    PT_GENERATED.BRANCH,
                ]:
                    return frame.spawn(
                        next_frame, PytealFrameStatus.PATCHED_BY_NEXT_OVERRIDE_PREV
                    )

                if reason == PT_GENERATED.FLAGGED_BY_DEV:
                    # TODO: does this hack have any false positivies?
                    return frame.spawn(
                        prev_frame, PytealFrameStatus.PATCHED_BY_PREV_OVERRIDE_NEXT
                    )

                # NO-OP otherwise:
                return None

            if prev_frame and frame:
                return frame.spawn(prev_frame, PytealFrameStatus.PATCHED_BY_PREV)

            if next_frame and frame:
                return frame.spawn(next_frame, PytealFrameStatus.PATCHED_BY_NEXT)

            return None

        for i in range(N):
            if (
                f := frames[i]
            ) and f.status_code() <= PytealFrameStatus.PYTEAL_GENERATED:
                ptf_or_none = infer_source(i)
                if ptf_or_none:
                    mutated.append(i)
                    frames[i] = ptf_or_none

        return mutated

    def pure_teal(self) -> str:
        return "\n".join(tmi.teal_line for tmi in self.as_list())

    _tabulate_param_defaults = dict(
        teal=_TEAL_LINE,
        tabulatable_teal=_TABULATABLE_TEAL,
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
        omit_repeating_col_except: list[str] = [],
        **kwargs,
    ) -> str:
        """
        Tabulate a sourcemap using Python's tabulate package: https://pypi.org/project/tabulate/

        Columns are named and ordered by the arguments provided

        Args:
            tablefmt (defaults to 'fancy_grid'): format specifier used by tabulate. For choices see: https://github.com/astanin/python-tabulate#table-format
            omit_headers (defaults to False): Explain this....
            numalign ... explain this...
            omit_repeating_col_except ... TODO: this is confusing. When empty, nothing is omitted. When non-empty, all reps other than this column are omitted
            const_col_* ... explain this
            teal: Column name and implicit order for the generated Teal
            pyteal (optional): Column name and implicit order for the PyTeal source mapping to target (this usually contains only the Python AST responsible for the generated Teal)
            pyteal_hybrid_unparsed (optional): ... explain
            teal_line_number (optional): Column name and implicit order for the Teal target line number
            teal_column (optional): Column name and implicit order for the generated Teal starting 0-based column number (defaults to 0 when unknown)
            teal_column_end (optional): Column name and implicit order for the generated Teal ending 0-based column (defaults to len(code) - 1 when unknown)
            program_counters (optional): Program counters assembled by algod
            pyteal_component (optional): Column name and implicit order for the PyTeal source component mapping to target
            pyteal_node_ast_qualname (optional): Column name and implicit order for the Python qualname of the PyTeal source mapping to target
            pyteal_filename (optional): Column name and implicit order for the filename whose PyTeal source is mapping to the target
            pyteal_line_number (optional): Column name and implicit order for starting line number of the PyTeal source mapping to target
            pyteal_line_number_end (optional): Column name and implicit order for the ending line number of the PyTeal source mapping to target
            pyteal_column (optional): Column name and implicit order for the PyTeal starting 0-based column number mapping to the target (defaults to 0 when unknown)
            pyteal_column_end (optional): Column name and implicit order for the PyTeal ending 0-based column number mapping to the target (defaults to len(code) - 1 when unknown)
            pyteal_line (optional): Column name and implicit order for the PyTeal source _line_ mapping to target (in general, this may only overlap with the PyTeal code which generated the Teal)
            pyteal_node_ast_source_boundaries (optional): Column name and implicit order for line and column boundaries of the PyTeal source mapping to target
            pyteal_node_ast_none (optional): Column name and implicit order for indicator of whether the AST node was extracted for the PyTEAL source mapping to target
            status_code (optional): Column name and implicit order for confidence level for locating the PyTeal source responsible for generated Teal
            status (optional): Column name and implicit order for descriptor of confidence level for locating the PyTeal source responsible for generated Teal

        Returns:
            A ready to print string containing the table information.
        """
        constant_columns = {}
        new_kwargs = {}
        for i, (k, v) in enumerate(kwargs.items()):
            if k.startswith("const_col_"):
                constant_columns[i] = v
            else:
                new_kwargs[k] = v
        kwargs = new_kwargs

        for k in kwargs:
            assert k in self._tabulate_param_defaults, f"unrecognized parameter '{k}'"

        # TODO: probly should just insist that printin sumn, not any particular column
        # DEAD CODE b/c required is empty
        # required = []
        renames = {self._tabulate_param_defaults[k]: v for k, v in kwargs.items()}
        rows = list(teal_item.asdict(**renames) for teal_item in self.as_list())

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
            renames = add_const_cols(renames)

        teal_col_name = renames[_TEAL_LINE]
        pt_simple_col_name = renames.get(_PYTEAL_COLUMN)
        pt_hybrid_col_name = renames.get(_PYTEAL_HYBRID_UNPARSED)
        if omit_repeating_col_except:
            # Assume the following column structure:
            # * col 0 is the generated source with column name stored in `teal_col`
            # * the source line number has column name stored in `pyteal_line_number`
            # * the pyteal source has column name stored in `pyteal` OR `pyteal_hybrid_unparsed`
            #
            # Consequently, when `teal_col` is repeating we need to take extra care NOT
            # to omit repeating source values, as these were likely coming from different portions of the source
            #
            # TODO: should also never omit the next line no. when the pyteal source isn't repeated

            def reduction(row, next_row):
                same_gen_teal = row[teal_col_name] == next_row[teal_col_name]
                return {
                    k: v2
                    for k, v in row.items()
                    if any(
                        [
                            (v2 := next_row[k]) != v,
                            k in omit_repeating_col_except,
                            same_gen_teal and k == pt_hybrid_col_name,
                            same_gen_teal and k == pt_simple_col_name,
                        ]
                    )
                }

            rows = [rows[0]] + list(
                map(lambda r_and_n: reduction(*r_and_n), zip(rows[:-1], rows[1:]))
            )

        calling_kwargs: dict[str, Any] = dict(tablefmt=tablefmt, numalign=numalign)
        if not omit_headers:
            calling_kwargs["headers"] = renames

        return tabulate(rows, **calling_kwargs)

    def annotated_teal(self, omit_headers: bool = True, concise: bool = True) -> str:
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

        return self.tabulate(**kwargs)  # type: ignore
