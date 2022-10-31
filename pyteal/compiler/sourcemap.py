from ast import unparse
from dataclasses import dataclass
from enum import IntEnum
from executing import Source
from inspect import FrameInfo
import os
from typing import cast, Any, Callable, OrderedDict, Optional, Sequence, Union

from tabulate import tabulate

from algosdk.source_map import R3SourceMap, R3SourceMapping

from pyteal.util import Frame, FrameSequence
import pyteal as pt


class SourceMapItemStatus(IntEnum):
    """integer values indicate 'confidence' on a scale of 0 - 10"""

    MISSING = 0
    MISSING_AST = 1
    MISSING_CODE = 2
    PYTEAL_GENERATED = 3
    PATCHED_BY_PREV_OVERRIDE_NEXT = 4
    PATCHED_BY_NEXT_OVERRIDE_PREV = 5
    PATCHED_BY_PREV = 6
    PATCHED_BY_NEXT = 7
    PATCHED_BY_PREV_AND_NEXT = 8
    COPACETIC = 9  # currently, 90% confidient is as good as it gets

    def human(self) -> str:
        match self:
            case self.MISSING:
                return "sourcemapping line: total failure"
            case self.MISSING_AST:
                return "unreliable as missing AST"
            case self.MISSING_CODE:
                return "unreliable as couldn't retrieve source"
            case self.PYTEAL_GENERATED:
                return "INCOMPLETE"  # "incomplete as source not user generated"
            case self.PATCHED_BY_PREV_OVERRIDE_NEXT:
                return "previously INCOMPLETE- patched to previous frame (ambiguous)"
            case self.PATCHED_BY_NEXT_OVERRIDE_PREV:
                return "previously INCOMPLETE- patched to next frame (ambiguous)"
            case self.PATCHED_BY_PREV:
                return "previously INCOMPLETE- patched to previous frame"
            case self.PATCHED_BY_NEXT:
                return "previously INCOMPLETE- patched to next frame"
            case self.PATCHED_BY_PREV_AND_NEXT:
                return "previously INCOMPLETE- patched"
            case self.COPACETIC:
                return "COPACETIC"

        raise Exception(f"unrecognized {type(self)} - THIS SHOULD NEVER HAPPEN!")


PyTealFrameSequence = Union["PyTealFrame", list["PyTealFrameSequence"]]

PT_GENERATED_PRAGMA = "PyTeal generated pragma"
PT_GENERATED_SUBR_LABEL = "PyTeal generated subroutine label"
PT_GENERATED_RETURN_NONE = "PyTeal generated return for TealType.none"
PT_GENERATED_RETURN_VALUE = "PyTeal generated return for non-null TealType"
PT_GENERATED_SUBR_PARAM = "PyTeal generated subroutine parameter handler instruction"
PT_GENERATED_BRANCH = "PyTeal generated branching"
PT_GENERATED_BRANCH_LABEL = "PyTeal generated branching label"
PT_GENERATED_TYPE_ENUM_TXN = "PyTeal generated transaction Type Enum"
PT_GENERATED_TYPE_ENUM_ONCOMPLETE = "PyTeal generated OnComplete Type Enum"


_PT_GEN = {
    "# T2PT0": PT_GENERATED_PRAGMA,
    "# T2PT1": PT_GENERATED_SUBR_LABEL,
    "# T2PT2": PT_GENERATED_RETURN_NONE,
    "# T2PT3": PT_GENERATED_RETURN_VALUE,
    "# T2PT4": PT_GENERATED_SUBR_PARAM,
    "# T2PT5": PT_GENERATED_BRANCH,
    "# T2PT6": PT_GENERATED_BRANCH_LABEL,
    "# T2PT7": PT_GENERATED_TYPE_ENUM_TXN,
    "# T2PT8": PT_GENERATED_TYPE_ENUM_ONCOMPLETE,
}


class PyTealFrame:
    """
    TODO: Inherit from util::Frame and remove code duplications
    """

    def __init__(
        self,
        frame: Frame,
        rel_paths: bool = True,
        parent: Optional["PyTealFrame"] | None = None,
    ):
        self.frame_info = frame.frame_info
        self.node = frame.node
        self.rel_paths = rel_paths
        self.parent = parent

        self._raw_code: str | None = None
        self._status: SourceMapItemStatus | None = None

    def frame(self) -> Frame:
        return Frame(self.frame_info, self.node)

    def __eq__(self, other: "PyTealFrame") -> bool:
        """We don't care about parents here. TODO: this comment is too rude"""
        if not isinstance(other, PyTealFrame):
            return False

        return all(
            [
                self.frame_info == other.frame_info,
                self.node == other.node,
                self.rel_paths == other.rel_paths,
            ]
        )

    def spawn(
        self, other: "PyTealFrame", status: "SourceMapItemStatus"
    ) -> "PyTealFrame":
        assert isinstance(other, PyTealFrame)

        ptf = PyTealFrame(other.frame(), other.rel_paths, self)
        ptf._status = status

        return ptf

    def location(self) -> str:
        return f"{self.file()}:{self.lineno()}" if self.frame_info else ""

    def file(self) -> str:
        if not self.frame_info:
            return ""

        path = self.frame_info.filename
        return os.path.relpath(path) if self.rel_paths else path

    def root(self) -> str:
        if not self.frame_info:
            return ""

        path = self.frame_info.filename
        return path[: -len(self.file())]

    def code_qualname(self) -> str:
        return (
            Source.executing(self.frame_info.frame).code_qualname()
            if self.frame_info
            else ""
        )

    def lineno(self) -> int | None:
        return self.frame_info.lineno if self.frame_info else None

    def column(self) -> int:
        """Provide accurate column info when available. Or 0 when not."""
        return self.node_col_offset() or 0

    def raw_code(self) -> str:
        if self._raw_code is None:
            self._raw_code = (
                ("".join(self.frame_info.code_context)).strip()
                if self.frame_info and self.frame_info.code_context
                else ""
            )

        return self._raw_code

    def compiler_generated(self) -> bool | None:
        """
        None indicates "unknown".

        i.e. `not x.compiler_generated()` === NOT or UNKNOWN
        """
        # FORMER CODE:
        # if not self.raw_code():
        #     return None  # we don't know / NA

        # return "# T2PT" in self.raw_code()
        # TODO: this becomes obsolete as soon as inherit from Frame
        return Frame(self.frame_info, self.node).compiler_generated()

        return "# T2PT" in self.raw_code()

    def compiler_generated_reason(self) -> str | None:
        """
        None indicates either "unkown" or "not compiler generated".
        To distinguish between these two usages, call `compiler_generated()` first.
        """
        if not self.compiler_generated():
            return None

        for k, v in _PT_GEN.items():
            if k in self.raw_code():
                return v

        raise AssertionError(
            "This should never happen as the call to self.compiler_generated() should have prevented this case."
        )

    def code(self) -> str:
        raw = self.raw_code()
        if not self.compiler_generated():
            return raw

        for k, v in _PT_GEN.items():
            if k in raw:
                return f"{v}: {raw}"

        return f"Unhandled # T2PT commentary: {raw}"

    def failed_ast(self) -> bool:
        return not self.node

    def status_code(self) -> SourceMapItemStatus:
        if self._status is not None:
            return self._status

        if self.frame_info is None:
            return SourceMapItemStatus.MISSING

        if self.node is None:
            return SourceMapItemStatus.MISSING_AST

        if self.compiler_generated():
            return SourceMapItemStatus.PYTEAL_GENERATED

        if not self.raw_code():
            return SourceMapItemStatus.MISSING_CODE

        return SourceMapItemStatus.COPACETIC

    def status(self) -> str:
        return self.status_code().human()

    def node_source(self) -> str:
        return unparse(self.node) if self.node else ""

    def node_lineno(self) -> int | None:
        return getattr(self.node, "lineno", None) if self.node else None

    def node_col_offset(self) -> int | None:
        return getattr(self.node, "col_offset", None) if self.node else None

    def node_end_lineno(self) -> int | None:
        return getattr(self.node, "end_lineno", None) if self.node else None

    def node_end_col_offset(self) -> int | None:
        return getattr(self.node, "end_col_offset", None) if self.node else None

    def node_source_window(self) -> str:
        boundaries = (
            self.node_lineno(),
            self.node_col_offset(),
            self.node_end_lineno(),
            self.node_end_col_offset(),
        )
        if not all(b is not None for b in boundaries):
            return ""
        return "L{}:{}-L{}:{}".format(*boundaries)

    def __str__(self, verbose: bool = True) -> str:
        if not self.frame_info:
            return "None"

        spaces = "\n\t\t\t"
        short = f"<{self.code()}>{spaces}@{self.location()}"
        if not verbose:
            return short

        # {self.source=}
        # {self.ast=}
        return f"""{short}
{self.frame_info.index=}
{self.frame_info.function=}
{self.frame_info.frame=}"""

    def __repr__(self) -> str:
        """TODO: this repr isn't compliant. Should we keep it anyway for convenience?"""
        return self.__str__(verbose=False)

    @classmethod
    def convert(
        cls, frames: FrameSequence, rel_paths: bool = True
    ) -> "PyTealFrameSequence":  # type: ignore
        if isinstance(frames, Frame):
            return cls(frames, rel_paths)
        return [cls.convert(f) for f in cast(Sequence[Frame], frames)]


_TEAL_LINE_NUMBER = "TL"
_TEAL_COLUMN = "TC"
_TEAL_COLUMN_END = "TCE"
_TEAL_CHUNK = "Teal Chunk"
_TABULATABLE_TEAL = "Tabulatable Teal"
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


class SourceMapDisabledError(RuntimeError):
    msg = value = """
    Cannot calculate Teal to PyTeal source map because stack frame discovery is turned off.

    To enable source maps, set `enabled = True` in `pyteal.ini`'s [pyteal-source-mapper] section.
    """

    def __str__(self):
        return self.msg


@dataclass
class SourceMapItem:
    first_line: int  # 0-indexed
    teal: str
    component: "pt.TealComponent"
    frame: PyTealFrame
    extras: dict[str, Any] | None = None  # TODO: probly these shouldn't exist

    def _tabulatable_teal(self, prefix_for_empty="//#") -> str:
        return "\n".join((x or prefix_for_empty) for x in self.teal.splitlines())

    # def column(self) -> int:
    #     """TODO: this will need to be rewored when/if compiling to multi-opcode lines with ';'"""
    #     return 0

    # def column_rbound(self) -> int:
    #     """TODO: this will need to be rewored when/if compiling to multi-opcode lines with ';'"""
    #     return len(self.teal)

    def hybrid_unparsed(self) -> str:
        pt_line = self.frame.node_source()
        if pt_line and len(pt_line.splitlines()) == 1:
            return pt_line

        return self.frame.code()

    def asdict(self, **kwargs) -> OrderedDict:
        """kwargs serve as a rename mapping when present"""
        attrs = {
            _TEAL_LINE_NUMBER: self.first_line,
            # _TEAL_COLUMN: self.column(),
            # _TEAL_COLUMN_END: self.column_rbound(),
            _TEAL_CHUNK: self.teal,
            _TABULATABLE_TEAL: self._tabulatable_teal(),
            _PYTEAL_HYBRID_UNPARSED: self.hybrid_unparsed(),
            _PYTEAL_NODE_AST_UNPARSED: self.frame.node_source(),
            _PYTEAL_NODE_AST_QUALNAME: self.frame.code_qualname(),
            _PYTEAL_COMPONENT: self.component,
            _PYTEAL_NODE_AST_SOURCE_BOUNDARIES: self.frame.node_source_window(),
            _PYTEAL_FILENAME: self.frame.file(),
            _PYTEAL_LINE_NUMBER: self.frame.lineno(),
            _PYTEAL_LINE_NUMBER_END: self.frame.node_end_lineno(),
            _PYTEAL_COLUMN: self.frame.column(),
            _PYTEAL_COLUMN_END: self.frame.node_end_col_offset(),
            _PYTEAL_LINE: self.frame.code(),
            _PYTEAL_NODE_AST: self.frame.node,
            _PYTEAL_FRAME: self.frame,
            _PYTEAL_NODE_AST_NONE: self.frame.failed_ast(),
            _STATUS_CODE: self.frame.status_code(),
            _STATUS: self.frame.status(),
        }

        assert (
            kwargs.keys() <= attrs.keys()
        ), f"unrecognized parameters {kwargs.keys() - attrs.keys()}"

        return OrderedDict(((kwargs[k], attrs[k]) for k in kwargs))

    def validate_for_export(self) -> None:
        """
        Ensure providing necessary and unambiguous data before exporting.
        """
        # if self.first_line is None or self.column() is None:
        #     raise ValueError(
        #         f"unable to export without valid line and column for TARGET but got: {self.first_line=}, {self.column()=}"
        #     )
        if self.first_line is None:
            raise ValueError(
                f"unable to export without valid line number: {self.first_line=}"
            )
        if (line := self.frame.lineno()) is None or (
            col := self.frame.column()
        ) is None:
            raise ValueError(
                f"unable to export without valid line and column for SOURCE but got: {self.frame.lineno=}, {self.frame.column()=}"
            )
        if not self.frame.node:
            return

        # self.frame.node_lineno() doesn't seem as accurate as self.frame.node.end_lineno
        if (_line := self.frame.node.end_lineno) and _line != line:
            raise ValueError(
                f"aborting: inconsistency in source line number found: {_line} != {line}"
            )

        # This can n ever happen because that's what col is!!!!
        # if (_col := self.frame.node_col_offset()) and _col != col:
        #     raise ValueError(
        #         f"aborting: inconsistency in source column number found: {_col} != {col}"
        #     )

    def source_mappings(self, hybrid: bool = True) -> list[R3SourceMapping]:
        self.validate_for_export()
        return [
            R3SourceMapping(
                line=self.first_line + i,
                column=0,
                column_end=len(target_line),
                source=self.frame.file(),
                source_line=cast(int, self.frame.lineno()) - 1,
                source_column=self.frame.column(),
                source_line_end=self.frame.node_end_lineno(),
                source_column_end=self.frame.node_end_col_offset(),
                source_extract=self.hybrid_unparsed() if hybrid else self.frame.code(),
                target_extract=target_line,
            )
            for i, target_line in enumerate(self.teal.splitlines())
        ]


class PyTealSourceMap:
    def __init__(
        self,
        teal_chunks: list[str],
        components: list["pt.TealComponent"],
        build: bool = False,
        source_inference: bool = True,
        hybrid: bool = True,
        teal_file: str | None = None,
        x: bool = False,
    ):
        # TODO: get rid of x and add_extras ???
        self.teal_chunks: list[str] = teal_chunks
        self.components: list["pt.TealComponent"] = components
        self.source_inference: bool = source_inference
        self.hybrid: bool = hybrid
        self.add_extras: bool = x
        self._cached_sourcemap_items: dict[int, SourceMapItem] = {}
        self._cached_r3sourcemap: R3SourceMap | None = None
        self.inferred_frames_at: list[int] = []
        self.teal_file: str | None = teal_file

        if build:
            self.get_r3sourcemap()

    def get_r3sourcemap(self) -> R3SourceMap:
        if not self._cached_r3sourcemap:
            smi_and_r3sms = [
                (smi, r3sm)
                for smi in self.get_sourcemap_items().values()
                for r3sm in smi.source_mappings(hybrid=self.hybrid)
            ]

            assert smi_and_r3sms, "Unexpected error: no source mappings found"

            smis = [smi for smi, _ in smi_and_r3sms]
            root = smis[0].frame.root()
            assert all(
                root == r3sm.frame.root() for r3sm in smis
            ), "inconsistent sourceRoot - aborting"

            r3sms = [r3sm for _, r3sm in smi_and_r3sms]
            entries = {(r3sm.line, r3sm.column): r3sm for r3sm in r3sms}
            index = [[]]
            prev_line = 0
            for line, col in entries.keys():
                for _ in range(prev_line, line):
                    index.append([])
                curr = index[-1]
                curr.append(col)
                prev_line = line
            index = [tuple(cs) for cs in index]
            lines = [cast(str, r3sm.target_extract) for r3sm in r3sms]
            sources = []
            for smi in smis:
                if (f := smi.frame.file()) not in sources:
                    sources.append(f)

            self._cached_r3sourcemap = R3SourceMap(
                file=self.teal_file,
                source_root=root,
                entries=entries,
                index=index,
                file_lines=lines,
                source_files=sources,
                source_files_lines=None,
            )

        return self._cached_r3sourcemap

    def get_sourcemap_items(self) -> dict[int, SourceMapItem]:
        if not self._cached_sourcemap_items:
            N = len(self.teal_chunks)
            assert N == len(
                self.components
            ), f"expected same number of teal lines {N} and components {len(self.components)}"

            best_frames = []
            before, after = [], []
            for i, tc in enumerate(self.components):
                print(f"{i}. {tc=}")
                f, a, b = self.best_frame_and_windows_around_it(tc)
                best_frames.append(f)
                before.append(b)
                after.append(a)

            if self.source_inference:
                mutated = self._search_for_better_frames_and_modify(best_frames)
                if mutated:
                    self.inferred_frames_at = mutated

            def source_map_item(line, i, tc):
                extras: dict[str, Any] | None = None
                if self.add_extras:
                    extras = {
                        "after_frames": after[line],
                        "before_frames": before[line],
                    }
                return SourceMapItem(
                    line, self.teal_chunks[i], tc, best_frames[i], extras
                )

            _map = {}
            line = 0
            for i, tc in enumerate(self.components):
                _map[line + 1] = (smi := source_map_item(line, i, tc))
                line += len(smi.teal.splitlines())

            self._cached_sourcemap_items = _map

        return self._cached_sourcemap_items

    def as_list(self) -> list[SourceMapItem]:
        return list(self.get_sourcemap_items().values())

    def _search_for_better_frames_and_modify(
        self, frames: list[PyTealFrame]
    ) -> list[int]:
        N = len(frames)
        mutated = []

        def infer_source(i: int) -> PyTealFrame | None:
            frame = frames[i]
            prev_frame = None if i <= 0 else frames[i - 1]
            next_frame = None if N <= i + 1 else frames[i + 1]
            if prev_frame and next_frame:
                if prev_frame == next_frame:
                    return frame.spawn(
                        prev_frame, SourceMapItemStatus.PATCHED_BY_PREV_AND_NEXT
                    )

                # PT Generated TypeEnum's presumably happened because of setting an transaction
                # field in the next step:
                reason = frame.compiler_generated_reason()
                if reason in [
                    PT_GENERATED_TYPE_ENUM_ONCOMPLETE,
                    PT_GENERATED_TYPE_ENUM_TXN,
                    PT_GENERATED_BRANCH_LABEL,
                    PT_GENERATED_BRANCH,
                ]:
                    return frame.spawn(
                        next_frame, SourceMapItemStatus.PATCHED_BY_NEXT_OVERRIDE_PREV
                    )

                # NO-OP otherwise:
                return None

            if prev_frame:
                return frame.spawn(prev_frame, SourceMapItemStatus.PATCHED_BY_PREV)

            if next_frame:
                return frame.spawn(next_frame, SourceMapItemStatus.PATCHED_BY_NEXT)

            return None

        for i in range(N):
            if frames[i].status_code() <= SourceMapItemStatus.PYTEAL_GENERATED:
                ptf_or_none = infer_source(i)
                if ptf_or_none:
                    mutated.append(i)
                    frames[i] = ptf_or_none

        return mutated

    # _internal_paths = [
    #     "beaker/__init__.py",
    #     "beaker/application.py",
    #     "beaker/consts.py",
    #     "beaker/decorators.py",
    #     "beaker/state.py",
    #     # "pyteal/__init__.py",
    #     "pyteal/ast",
    #     "pyteal/compiler",
    #     "pyteal/ir",
    #     "pyteal/pragma",
    #     "tests/abi_roundtrip.py",
    #     "tests/blackbox.py",
    #     "tests/compile_asserts.py",
    #     "tests/mock_version.py",
    # ]

    @classmethod
    def best_frame_and_windows_around_it(
        cls, t: "pt.TealComponent"
    ) -> tuple[FrameInfo | None, list[FrameInfo], list[FrameInfo]]:
        """
        # TODO: probly need to REMOVE the extra before and after
        # TODO: this is too complicated!!!
        """
        frames = t.frames()
        if not frames:
            return None, [], []

        frame_infos = frames.frame_infos()

        # TODO: at this point, result() is complete overkill
        def result(best_idx):
            # TODO: probly don't need to keep `extras` param of SourceMapItem
            # nor the 2nd and 3rd elements of the following tuple being returned
            return tuple(
                PyTealFrame.convert(
                    [
                        frames[best_idx],  # type: ignore
                        [frames[i] for i in range(best_idx - 1, -1, -1)],
                        [frames[i] for i in range(best_idx + 1, len(frame_infos))],
                    ]
                )
            )

        return result(len(frames) - 1)

        # THIS IS DUPLICATIVE CODE!!!!
        # if len(frames) == 1:
        #     return result(0)

        # pyteal_idx = [
        #     any(w in f.filename for w in cls._internal_paths) for f in frame_infos
        # ]

        # def is_code_file(idx):
        #     f = frame_infos[idx].filename
        #     return not (f.startswith("<") and f.endswith(">"))

        # in_pt, first_pt_entrancy = False, None
        # for i, is_pyteal in enumerate(pyteal_idx):
        #     if is_pyteal and not in_pt:
        #         in_pt = True
        #         continue
        #     if not is_pyteal and in_pt and is_code_file(i):
        #         first_pt_entrancy = i
        #         break

        # if first_pt_entrancy is None:
        #     return None, [], []

        # frame_nodes = frames.nodes()
        # if frame_nodes[first_pt_entrancy] is None:
        #     # FAILURE CASE: Look for first pyteal generated code entry in stack trace:
        #     found = False
        #     i = -1
        #     for i in range(len(frame_infos) - 1, -1, -1):
        #         f = frame_infos[i]
        #         if not f.code_context:
        #             continue

        #         cc = "".join(f.code_context)
        #         if "# T2PT" in cc:
        #             found = True
        #             break

        #     if found and i >= 0:
        #         first_pt_entrancy = i

        # return result(first_pt_entrancy)

    def teal(self) -> str:
        return "\n".join(smi.teal for smi in self.get_sourcemap_items().values())

    _tabulate_param_defaults = dict(
        teal=_TEAL_CHUNK,
        tabulatable_teal=_TABULATABLE_TEAL,
        pyteal_hybrid_unparsed=_PYTEAL_HYBRID_UNPARSED,
        pyteal=_PYTEAL_NODE_AST_UNPARSED,
        teal_line_number=_TEAL_LINE_NUMBER,
        teal_column=_TEAL_COLUMN,
        teal_column_end=_TEAL_COLUMN_END,
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
        omit_rep_cols: set = set(),
        postprocessor: Optional[Callable[..., str]] = None,
        **kwargs,
    ) -> str:
        """
        Tabulate a sourcemap using Python's tabulate package: https://pypi.org/project/tabulate/

        Columns are named and ordered by the arguments provided

        Args:
            tablefmt (defaults to 'fancy_grid'): format specifier used by tabulate. For choices see: https://github.com/astanin/python-tabulate#table-format
            omit_headers (defaults to False): Explain this....
            numalign ... explain this...
            omit_rep_cols ... TODO: this is confusing. When empty, nothing is omitted. When non-empty, all reps other than this column are omitted
            const_col_* ... explain this
            teal: Column name and implicit order for the generated Teal
            pyteal (optional): Column name and implicit order for the PyTeal source mapping to target (this usually contains only the Python AST responsible for the generated Teal)
            pyteal_hybrid_unparsed (optional): ... explain
            teal_line_number (optional): Column name and implicit order for the Teal target line number
            teal_column (optional): Column name and implicit order for the generated Teal starting 0-based column number (defaults to 0 when unknown)
            teal_column_end (optional): Column name and implicit order for the generated Teal ending 0-based column (defaults to len(code) - 1 when unknown)
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
        required = []
        renames = {self._tabulate_param_defaults[k]: v for k, v in kwargs.items()}
        for r in required:
            if r not in kwargs:
                renames[
                    self._tabulate_param_defaults[r]
                ] = self._tabulate_param_defaults[r]

        rows = list(
            smitem.asdict(**renames) for smitem in self.get_sourcemap_items().values()
        )

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

            rows = list(map(add_const_cols, rows))  # can revert to pure map ???
            renames = add_const_cols(renames)

        if omit_rep_cols:

            def reduction(row, next_row):
                return {
                    k: v2
                    for k, v in row.items()
                    if (v2 := next_row[k]) != v or k in omit_rep_cols
                }

            rows = [rows[0]] + list(
                map(lambda r_and_n: reduction(*r_and_n), zip(rows[:-1], rows[1:]))
            )

        tabulated = (
            tabulate(rows, tablefmt=tablefmt, numalign=numalign)
            if omit_headers
            else tabulate(rows, headers=renames, tablefmt=tablefmt, numalign=numalign)
        )

        if postprocessor:
            tabulated = postprocessor(tabulated)

        return tabulated

    def _tabulate_for_dev(self) -> str:
        return self.tabulate(
            teal_line_number="line",
            teal="teal",
            status="line status",
            pyteal="pyteal AST",
            pyteal_filename="source",
            pyteal_node_ast_source_boundaries="rows & columns",
            pyteal_line_number="pt line",
            pyteal_line="pyteal line",
        )

    def annotated_teal(
        self, unparse_hybrid: bool = False, concise: bool = False
    ) -> str:
        teal_col = "// GENERATED TEAL"
        seperator_col = "_1"  # TODO: fix this ugly hack
        omit_rep_cols = {teal_col, seperator_col}
        kwargs = dict(
            tablefmt="plain",
            omit_headers=False,
            omit_rep_cols=omit_rep_cols,
            numalign="left",
            tabulatable_teal=teal_col,
            const_col_2="//",
            pyteal_filename="PYTEAL PATH",
        )
        if not concise:
            kwargs["pyteal_line_number"] = "LINE"

        if unparse_hybrid:
            kwargs["pyteal_hybrid_unparsed"] = "PYTEAL HYBRID UNPARSED"
        else:
            kwargs["pyteal_line"] = "PYTEAL SOURCE"

        def erase_sentinels(teal):
            sentinel = "//#"
            return "\n".join(
                x.replace(sentinel, "   ") if x.startswith(sentinel) else x
                for x in teal.splitlines()
            )

        return self.tabulate(**kwargs, postprocessor=erase_sentinels)
