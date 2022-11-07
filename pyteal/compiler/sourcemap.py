import base64
import bisect
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from itertools import count
from typing import (
    Any,
    Callable,
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

# from algosdk.source_map import R3SourceMap, R3SourceMapping
from algosdk.source_map import SourceMap as PCSourceMap
from algosdk.v2client.algod import AlgodClient
from tabulate import tabulate

import pyteal as pt
from pyteal.errors import TealInternalError
from pyteal.stack_frame import PT_GENERATED, PyTealFrame, PytealFrameStatus
from pyteal.util import algod_with_assertion

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


# TODO: move this to pyteal.errors
class SourceMapDisabledError(RuntimeError):
    msg = value = """
    Cannot calculate Teal to PyTeal source map because stack frame discovery is turned off.

    To enable source maps, set `enabled = True` in `pyteal.ini`'s [pyteal-source-mapper] section.
    """

    def __str__(self):
        return self.msg


class TealLine(PyTealFrame):
    def __init__(
        self,
        pt_frame: PyTealFrame,
        lineno: int,
        teal_line: str,
        pcs: list[int] | None = None,
    ):
        super().__init__(
            frame_info=pt_frame.frame_info,
            node=pt_frame.node,
            rel_paths=pt_frame.rel_paths,
            parent=pt_frame.parent,
        )
        self.lineno: int = lineno
        self.teal_line: str = teal_line
        self.pcs_hydrated: bool = pcs is not None
        self.pcs: list[int] | None = pcs if pcs else None

    def __repr__(self) -> str:
        pcs_repr = ""
        if self.pcs_hydrated:
            pcs_repr = " // PC[{}]"
            internal = ""
            if self.pcs:
                internal += str(self.pcs[0])
                if len(self.pcs) > 1:
                    internal += "-" + str(self.pcs[-1])
            pcs_repr = pcs_repr.format(internal)
        return f"TealLine({self.lineno}: {self.teal_line}{pcs_repr} // PyTeal: {self.hybrid_unparsed()}"


@dataclass
class SourceMapItemDEPRECATED:
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

        # if not self.frame.node:
        #     return

        # self.frame.node_lineno() doesn't seem as accurate as self.frame.node.end_lineno
        # OKAY - every once in a while, inspect.frame_info() disagrees with ast.node()
        # line number. For now, we'll just coe with inspect.frame_info()
        # if (_line := self.frame.node.end_lineno) and _line != line:
        #     raise ValueError(
        #         f"aborting: inconsistency in source line number found: {_line} != {line}"
        #     )

        # This can n ever happen because that's what col is!!!!
        # if (_col := self.frame.node_col_offset()) and _col != col:
        #     raise ValueError(
        #         f"aborting: inconsistency in source column number found: {_col} != {col}"
        #     )

    def source_mappings(self, hybrid: bool = True) -> list["R3SourceMapping"]:
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
        compiled_teal_lines: list[str],
        components: list["pt.TealComponent"],
        teal_file: str | None = None,
        annotate_teal: bool = False,
        include_pcs: bool = False,
        algod: AlgodClient | None = None,
        build: bool = True,
        verbose: bool = False,
        # deprecated:
        source_inference: bool = True,
        hybrid: bool = True,
        x: bool = False,
    ):
        if include_pcs:
            # bootstrap an algod_client if not provided, and in either case, run a healthcheck
            algod = algod_with_assertion(
                algod, msg="Adding PC's to sourcemap requires live Algod"
            )

        self.compiled_teal_lines: list[str] = compiled_teal_lines
        self.components: list["pt.TealComponent"] = components
        self.include_pcs: bool = include_pcs
        self.annotate_teal: bool = annotate_teal
        self.include_pcs: bool = include_pcs
        self.algod: AlgodClient | None = algod

        self.verbose: bool = verbose

        # --- deprecated fields BEGIN
        # TODO: get rid of x and add_extras ???
        self.hybrid: bool = hybrid
        self.source_inference: bool = source_inference
        self.add_extras: bool = x
        # --- deprecated fields END

        self._cached_sourcemap_items: dict[int, SourceMapItemDEPRECATED] = {}
        self._cached_r3sourcemap: R3SourceMap | None = None
        self.inferred_frames_at: list[int] = []
        self.teal_file: str | None = teal_file

        self._cached_teal_lines: list[TealLine] = []
        self._cached_pc_sourcemap: PCSourceMap | None = None

        if build:
            self._build()

    def compiled_teal(self) -> str:
        return "\n".join(self.compiled_teal_lines)

    def _build(self) -> None:
        if not self._cached_sourcemap_items:
            N = len(self.compiled_teal_lines)
            assert N == len(
                self.components
            ), f"expected same number of teal lines {N} and components {len(self.components)}"

            best_frames = []
            for i, tc in enumerate(self.components):
                if self.verbose:
                    print(f"{i}. {tc=}")

                frames = tc.frames()
                if not frames:
                    best_frames.append(None)
                    continue

                best_frames.append(frames[-1].as_pyteal_frame())

            if self.source_inference:
                mutated = self._search_for_better_frames_and_modify(best_frames)
                if mutated:
                    self.inferred_frames_at = mutated

            def source_map_item(line, i, tc):
                return SourceMapItemDEPRECATED(
                    line, self.compiled_teal_lines[i], tc, best_frames[i]
                )

            _map = {}
            line = 0
            for i, tc in enumerate(self.components):
                _map[line + 1] = (smi := source_map_item(line, i, tc))
                line += len(smi.teal.splitlines())

            self._cached_sourcemap_items = _map

        if not self._cached_r3sourcemap:
            smi_and_r3sms = [
                (smi, r3sm)
                for smi in self._cached_sourcemap_items.values()
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
            )

        if not self._cached_teal_lines:
            if self.include_pcs and not self._cached_pc_sourcemap:
                algod = algod_with_assertion(
                    self.algod, msg="Adding PC's to sourcemap requires live Algod"
                )
                # as uncommented portion of the annotated teal is identical
                # to the uncommented portion of the compiled teal, we can
                # always construct the PC -> Teal sourcemap from self.compiled_teal():
                algod_compilation = algod.compile(self.compiled_teal(), source_map=True)
                raw_sourcemap = algod_compilation.get("sourcemap")
                if not raw_sourcemap:
                    raise TealInternalError(
                        f"algod compilation did not return 'sourcemap' as expected. {algod_compilation=}"
                    )
                self._cached_pc_sourcemap = PCSourceMap(raw_sourcemap)

                # The rest of this scope is unnecessary:
                pbs = base64.b64decode(algod_compilation["result"])

                tl = self.compiled_teal().splitlines()
                # algod_disassembly = algod.disassemble(pbs)
                # disassembled = algod_disassembly["result"]
                # dlines = disassembled.splitlines()
                # ctor = [
                #     (i, x, y)
                #     for i, x in enumerate(self.compiled_teal_lines)
                #     if i < 200 and (y := dlines[i])
                # ]

                rfunc = lambda xs: f"{xs[0]}-{xs[-1]}" if xs else None
                hmmm = [
                    (i, l, rfunc(self._cached_pc_sourcemap.line_to_pc.get(i)))
                    for i, l in enumerate(tl)
                ]

            lineno = 0
            for i, smi in enumerate(self._cached_sourcemap_items.values()):
                teal_chunk = self.compiled_teal_lines[i]
                for line in teal_chunk.splitlines():
                    pcsm = cast(PCSourceMap, self._cached_pc_sourcemap)
                    self._cached_teal_lines.append(
                        TealLine(
                            pt_frame=smi.frame,
                            lineno=lineno,
                            teal_line=line,
                            pcs=pcsm.line_to_pc.get(lineno, [])
                            if self.include_pcs
                            else None,
                        )
                    )
                    lineno += 1

            x = 42

    # def get_r3sourcemap_DEPRECATED(self) -> R3SourceMap:
    #     if not self._cached_r3sourcemap:
    #         smi_and_r3sms = [
    #             (smi, r3sm)
    #             for smi in self.get_sourcemap_items_DEPRECATED().values()
    #             for r3sm in smi.source_mappings(hybrid=self.hybrid)
    #         ]

    #         assert smi_and_r3sms, "Unexpected error: no source mappings found"

    #         smis = [smi for smi, _ in smi_and_r3sms]
    #         root = smis[0].frame.root()
    #         assert all(
    #             root == r3sm.frame.root() for r3sm in smis
    #         ), "inconsistent sourceRoot - aborting"

    #         r3sms = [r3sm for _, r3sm in smi_and_r3sms]
    #         entries = {(r3sm.line, r3sm.column): r3sm for r3sm in r3sms}
    #         index = [[]]
    #         prev_line = 0
    #         for line, col in entries.keys():
    #             for _ in range(prev_line, line):
    #                 index.append([])
    #             curr = index[-1]
    #             curr.append(col)
    #             prev_line = line
    #         index = [tuple(cs) for cs in index]
    #         lines = [cast(str, r3sm.target_extract) for r3sm in r3sms]
    #         sources = []
    #         for smi in smis:
    #             if (f := smi.frame.file()) not in sources:
    #                 sources.append(f)

    #         # source_files_lines: Optional[list[list[str]]] = None
    #         # if with_source_lines:

    #         #     def get_file_lines(filename: str) -> list[str]:
    #         #         x = 42
    #         #         pass

    #         #     source_files_lines = list(map(get_file_lines, sources))

    #         self._cached_r3sourcemap = R3SourceMap(
    #             file=self.teal_file,
    #             source_root=root,
    #             entries=entries,
    #             index=index,
    #             file_lines=lines,
    #             source_files=sources,
    #             # source_files_lines=source_files_lines,
    #         )

    #     return self._cached_r3sourcemap

    # def get_sourcemap_items_DEPRECATED(self) -> dict[int, SourceMapItemDEPRECATED]:
    #     if not self._cached_sourcemap_items:
    #         N = len(self.compiled_teal_lines)
    #         assert N == len(
    #             self.components
    #         ), f"expected same number of teal lines {N} and components {len(self.components)}"

    #         best_frames = []
    #         before, after = [], []
    #         for i, tc in enumerate(self.components):
    #             print(f"{i}. {tc=}")
    #             f, a, b = self.best_frame_and_windows_around_it_DEPRECATED(tc)
    #             best_frames.append(f)
    #             before.append(b)
    #             after.append(a)

    #         if self.source_inference:
    #             mutated = self._search_for_better_frames_and_modify(best_frames)
    #             if mutated:
    #                 self.inferred_frames_at = mutated

    #         def source_map_item(line, i, tc):
    #             extras: dict[str, Any] | None = None
    #             if self.add_extras:
    #                 extras = {
    #                     "after_frames": after[line],
    #                     "before_frames": before[line],
    #                 }
    #             return SourceMapItemDEPRECATED(
    #                 line, self.compiled_teal_lines[i], tc, best_frames[i], extras
    #             )

    #         _map = {}
    #         line = 0
    #         for i, tc in enumerate(self.components):
    #             _map[line + 1] = (smi := source_map_item(line, i, tc))
    #             line += len(smi.teal.splitlines())

    #         self._cached_sourcemap_items = _map

    #     return self._cached_sourcemap_items

    # def as_list(self) -> list[SourceMapItemDEPRECATED]:
    #     return list(self.get_sourcemap_items_DEPRECATED().values())

    def as_list(self) -> list[SourceMapItemDEPRECATED]:
        self._build()
        return list(self._cached_sourcemap_items.values())

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

                # NO-OP otherwise:
                return None

            if prev_frame:
                return frame.spawn(prev_frame, PytealFrameStatus.PATCHED_BY_PREV)

            if next_frame:
                return frame.spawn(next_frame, PytealFrameStatus.PATCHED_BY_NEXT)

            return None

        for i in range(N):
            if frames[i].status_code() <= PytealFrameStatus.PYTEAL_GENERATED:
                ptf_or_none = infer_source(i)
                if ptf_or_none:
                    mutated.append(i)
                    frames[i] = ptf_or_none

        return mutated

    # @classmethod
    # def best_index_and_frame_DELETEME(
    #     cls, t: "pt.TealComponent"
    # ) -> tuple[int, PyTealFrame] | None:
    #     frames = t.frames()
    #     if not frames:
    #         return None

    #     best_idx = len(frames) - 1
    #     return best_idx, PyTealFrame.convert(frames[best_idx])  # type: ignore

    #     # def result(best_idx):
    #     #     # TODO: probly don't need to keep `extras` param of SourceMapItem
    #     #     # nor the 2nd and 3rd elements of the following tuple being returned
    #     #     return tuple(
    #     #         PyTealFrame.convert(
    #     #             [
    #     #                 frames[best_idx],  # type: ignore
    #     #                 [frames[i] for i in range(best_idx - 1, -1, -1)],
    #     #                 [frames[i] for i in range(best_idx + 1, len(frame_infos))],
    #     #             ]
    #     #         )
    #     #     )

    #     # return result(len(frames) - 1)

    # @classmethod
    # def best_frame_and_windows_around_it_DEPRECATED(
    #     cls, t: "pt.TealComponent"
    # ) -> tuple[FrameInfo | None, list[FrameInfo], list[FrameInfo]]:
    #     """
    #     # TODO: probly need to REMOVE the extra before and after
    #     # TODO: this is too complicated!!!
    #     """
    #     frames = t.frames()
    #     if not frames:
    #         return None, [], []

    #     frame_infos = frames.frame_infos()

    #     # TODO: at this point, result() is complete overkill
    #     def result(best_idx):
    #         # TODO: probly don't need to keep `extras` param of SourceMapItem
    #         # nor the 2nd and 3rd elements of the following tuple being returned
    #         return tuple(
    #             PyTealFrame.convert(
    #                 [
    #                     frames[best_idx],  # type: ignore
    #                     [frames[i] for i in range(best_idx - 1, -1, -1)],
    #                     [frames[i] for i in range(best_idx + 1, len(frame_infos))],
    #                 ]
    #             )
    #         )

    #     return result(len(frames) - 1)

    #     # THIS IS DUPLICATIVE CODE!!!!
    #     # if len(frames) == 1:
    #     #     return result(0)

    #     # pyteal_idx = [
    #     #     any(w in f.filename for w in cls._internal_paths) for f in frame_infos
    #     # ]

    #     # def is_code_file(idx):
    #     #     f = frame_infos[idx].filename
    #     #     return not (f.startswith("<") and f.endswith(">"))

    #     # in_pt, first_pt_entrancy = False, None
    #     # for i, is_pyteal in enumerate(pyteal_idx):
    #     #     if is_pyteal and not in_pt:
    #     #         in_pt = True
    #     #         continue
    #     #     if not is_pyteal and in_pt and is_code_file(i):
    #     #         first_pt_entrancy = i
    #     #         break

    #     # if first_pt_entrancy is None:
    #     #     return None, [], []

    #     # frame_nodes = frames.nodes()
    #     # if frame_nodes[first_pt_entrancy] is None:
    #     #     # FAILURE CASE: Look for first pyteal generated code entry in stack trace:
    #     #     found = False
    #     #     i = -1
    #     #     for i in range(len(frame_infos) - 1, -1, -1):
    #     #         f = frame_infos[i]
    #     #         if not f.code_context:
    #     #             continue

    #     #         cc = "".join(f.code_context)
    #     #         if "# T2PT" in cc:
    #     #             found = True
    #     #             break

    #     #     if found and i >= 0:
    #     #         first_pt_entrancy = i

    #     # return result(first_pt_entrancy)

    def teal(self) -> str:
        return "\n".join(
            # smi.teal for smi in self.get_sourcemap_items_DEPRECATED().values()
            smi.teal
            for smi in self.as_list()
        )

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

    def tabulate_DEPRECATED(
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
            smitem.asdict(**renames)
            # for smitem in self.get_sourcemap_items_DEPRECATED().values()
            for smitem in self.as_list()
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
        return self.tabulate_DEPRECATED(
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
        self,
        # deprecated:
        unparse_hybrid: bool = True,
        concise: bool = True,
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

        return self.tabulate_DEPRECATED(**kwargs, postprocessor=erase_sentinels)


"""
#### ---- Based on mjpieters CODE ---- ####

Source modified from: https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
"""

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
    results = []
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
    column_end: Optional[int] = None
    source: Optional[str] = None
    source_line: Optional[int] = None
    source_column: Optional[int] = None
    source_line_end: Optional[int] = None
    source_column_end: Optional[int] = None
    name: Optional[str] = None
    source_extract: Optional[str] = None
    target_extract: Optional[str] = None
    source_content: Optional[List[str]] = None

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

    @property
    def content_line(self) -> Optional[str]:
        try:
            # self.source_content.splitlines()[self.source_line]  # type: ignore
            self.source_content[self.source_line]  # type: ignore
        except (TypeError, IndexError):
            return None

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
    """
    Modified from the original `SourceMap` available under MIT License here (as of Oct. 12, 2022): https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
    `R3` is a nod to "Revision 3" of John Lenz's Source Map Proposal: https://docs.google.com/document/d/1U1RGAehQwRypUTovF1KRlpiOFze0b-_2gc6fAH0KY0k/edit?hl=en_US&pli=1&pli=1
    """

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
        entries, index = {}, []
        spos = npos = sline = scol = 0

        sources = smap.get("sources")
        if sources and sources_override:
            raise AssertionError("ambiguous sources from JSON and method argument")
        sources = sources or sources_override or ["unknown"]

        contents = smap.get("sourcesContent")
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
                        line=gline, column=gcol, **kwargs
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
        content, mappings = [], []
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
