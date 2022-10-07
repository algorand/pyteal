import ast
from dataclasses import dataclass
from executing import Source
import inspect
import os
from typing import cast, Any, List, OrderedDict

from tabulate import tabulate

import pyteal as pt


class PyTealFrame:
    def __init__(
        self,
        frame: inspect.FrameInfo | None,
        node: ast.AST | None,
        rel_paths: bool = True,
    ):
        self.frame = frame
        self.rel_paths = rel_paths
        self.node = node
        self.source = None
        self.ast = None
        self._raw_code = None

    pt_generated = {
        "# T2PT0": "PyTeal generated pragma",
        "# T2PT1": "PyTeal generated subroutine label",
        "# T2PT2": "PyTeal generated return for TealType.none",
        "# T2PT3": "PyTeal generated return for non-null TealType",
        "# T2PT4": "PyTeal generated subroutine parameter handler instruction",
        "# T2PT5": "PyTeal generated branching",
        "# T2PT6": "PyTeal generated branching label",
        "# T2PT7": "PyTeal generated transaction Type Enum",
        "# T2PT8": "PyTeal generated OnComplete Type Enum",
    }

    def location(self) -> str:
        return f"{self.file()}:{self.lineno()}" if self.frame else ""

    def file(self) -> str:
        if not self.frame:
            return ""

        path = self.frame.filename
        return os.path.relpath(path) if self.rel_paths else path

    def code_qualname(self) -> str:
        return Source.executing(self.frame.frame).code_qualname() if self.frame else ""

    def lineno(self) -> int | None:
        return self.frame.lineno if self.frame else None

    def raw_code(self) -> str:
        if self._raw_code is None:
            self._raw_code = (
                ("".join(self.frame.code_context)).strip()
                if self.frame and self.frame.code_context
                else ""
            )

        return self._raw_code

    def compiler_generated(self) -> bool | None:
        """None indicates "unknown"."""
        if not self.raw_code():
            return None  # we don't know / NA

        return "# T2PT" in self.raw_code()

    def code(self) -> str:
        raw = self.raw_code()
        if not self.compiler_generated():
            return raw

        for k, v in self.pt_generated.items():
            if k in raw:
                return f"{v}: {raw}"

        return f"Unhandled # T2PT commentary: {raw}"

    def failed_ast(self) -> bool:
        return not self.node

    def status(self) -> str:
        return "Failed AST (do not trust)" if self.failed_ast() else "AST Found"

    def node_source(self) -> str:
        return ast.unparse(self.node) if self.node else ""

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
        if not self.frame:
            return "None"

        spaces = "\n\t\t\t"
        short = f"<{self.code()}>{spaces}@{self.location()}"
        if not verbose:
            return short

        return f"""{short}
{self.source=}
{self.ast=}
{self.frame.index=}
{self.frame.function=}
{self.frame.frame=}"""

    def __repr__(self) -> str:
        """TODO: this repr isn't compliant. Should we keep it anyway for convenience?"""
        return self.__str__(verbose=False)

    @classmethod
    def convert(
        cls, frame_n_nodes: tuple[inspect.FrameInfo | None, ast.AST | None] | list
    ):
        if isinstance(frame_n_nodes, tuple):
            return cls(*frame_n_nodes)
        assert isinstance(
            frame_n_nodes, list
        ), f"expected list but got {type(frame_n_nodes)}"
        return [cls.convert(f_and_n) for f_and_n in cast(list, frame_n_nodes)]


_TL = "TL"
_Teal = "Teal"
_PTE = "PTE"
_PTQ = "PTQ"
_PTC = "PTC"
_PTCW = "PTCW"
_PT_path = "PT path"
_PTL = "PTL"
_PTCC = "PTCC"
_PT_AST = "PT AST"
_PT_frame = "PT frame"
_failed = "FAILED"
_status = "Sourcemap Status"


@dataclass
class SourceMapItem:
    line: int
    teal: str
    component: "pt.TealComponent"
    frame: PyTealFrame
    extras: dict[str, Any] | None

    def asdict(self, **kwargs) -> OrderedDict:
        """kwargs serve as a rename mapping when present
        TODO: is this overly complicated?
        """
        attrs = {
            _TL: self.line,
            _Teal: self.teal,
            _PTE: self.frame.node_source(),
            _PTQ: self.frame.code_qualname(),
            _PTC: self.component,
            _PTCW: self.frame.node_source_window(),
            _PT_path: self.frame.file(),
            _PTL: self.frame.lineno(),
            _PTCC: self.frame.code(),
            _PT_AST: self.frame.node,
            _PT_frame: self.frame,
            _failed: self.frame.failed_ast(),
            _status: self.frame.status(),
        }

        assert (
            kwargs.keys() <= attrs.keys()
        ), f"unrecognized parameters {kwargs.keys() - attrs.keys()}"

        return OrderedDict(((kwargs[k], attrs[k]) for k in kwargs))


class PyTealSourceMap:
    def __init__(
        self,
        lines: list[str],
        components: list["pt.TealComponent"],
        build: bool = False,
        x: bool = False,
    ):
        self.teal_lines: list[str] = lines
        self.components: list["pt.TealComponent"] = components
        self.add_extras: bool = x
        self._cached_source_map: dict[int, SourceMapItem] = {}

        if build:
            self.get_map()

    def get_map(self) -> dict[int, SourceMapItem]:
        if not self._cached_source_map:
            N = len(self.teal_lines)
            assert N == len(
                self.components
            ), f"expected same number of teal lines {N} and components {len(self.components)}"

            best_frames = []
            before, after = [], []
            for tc in self.components:
                f, a, b = self.best_frame_and_windows_around_it(tc)
                best_frames.append(f)
                before.append(b)
                after.append(a)

            def source_map_item(i, tc):
                extras: dict[str, Any] | None = None
                if self.add_extras:
                    extras = {
                        "after_frames": after[i],
                        "before_frames": before[i],
                    }
                return SourceMapItem(
                    i + 1, self.teal_lines[i], tc, best_frames[i], extras
                )

            self._cached_source_map = {
                i + 1: source_map_item(i, tc) for i, tc in enumerate(self.components)
            }

        return self._cached_source_map

    @classmethod
    def best_frame_and_windows_around_it(
        cls, t: "pt.TealComponent"
    ) -> tuple[
        inspect.FrameInfo | None, list[inspect.FrameInfo], list[inspect.FrameInfo]
    ]:
        # TODO: probly need to trim down the extra before and afters before merging
        # TODO: this is too complicated!!!
        path_match: str
        # TODO: match is overkill now that TealComponent has methods frames() and frame_nodes()
        match t:
            case pt.TealOp():
                path_match = "pyteal/ast"
            case pt.TealLabel() | pt.TealPragma():
                path_match = "pyteal/ir"
            case _:
                raise Exception(f"expected TealComponent but got {type(t)}")

        # TODO: Refactor using a generic version of cast that un-optionalizes any optional type
        frames = t.frames()
        frame_nodes = t.frame_nodes()

        def call_out_emptys(xs):
            f"The following indices were empty {[x for x in xs if not x]}"

        frames = cast(List[inspect.FrameInfo], frames)
        frame_nodes = cast(List[ast.AST | None], frame_nodes)
        assert all(frames), call_out_emptys(frames)
        assert len(frame_nodes) == len(frames)

        pyteals = [
            path_match,
            "pyteal/__init__.py",
            "tests/abi_roundtrip.py",
            "tests/blackbox.py",
            "tests/compile_asserts.py",
            "tests/mock_version.py",
        ]

        pyteal_idx = [any(w in f.filename for w in pyteals) for f in frames]

        def is_code_file(idx):
            f = frames[idx].filename
            return not (f.startswith("<") and f.endswith(">"))

        in_pt, first_pt_entrancy = False, None
        for i, is_pyteal in enumerate(pyteal_idx):
            if is_pyteal and not in_pt:
                in_pt = True
                continue
            if not is_pyteal and in_pt and is_code_file(i):
                first_pt_entrancy = i
                break

        if first_pt_entrancy is None:
            return None, [], []

        if frame_nodes[first_pt_entrancy] is None:
            # failure. Look for first pyteal generated code entry in stack trace:
            found = False
            i = -1
            for i in range(len(frames) - 1, -1, -1):
                f = frames[i]
                if not f.code_context:
                    continue

                cc = "".join(f.code_context)
                if "# T2PT" in cc:
                    found = True
                    break

            if found and i >= 0:
                first_pt_entrancy = i

        frames_n_nodes = list(zip(frames, frame_nodes))
        # TODO: probly don't need to keep `extras` param of SourceMapItem
        # nor the 2nd and 3rd elements of the following tuple being returned
        return tuple(
            PyTealFrame.convert(
                [
                    frames_n_nodes[first_pt_entrancy],
                    [frames_n_nodes[i] for i in range(first_pt_entrancy - 1, -1, -1)],
                    [
                        frames_n_nodes[i]
                        for i in range(first_pt_entrancy + 1, len(frames))
                    ],
                ]
            )  # type: ignore
        )

    def teal(self) -> str:
        return "\n".join(smi.teal for smi in self.get_map().values())

    def tabulate(
        self,
        *,
        tablefmt="fancy_grid",
        **kwargs,
    ) -> str:
        defaults = dict(
            teal_line_col=_TL,
            teal_code_col=_Teal,
            pyteal_exec_col=_PTE,
            pyteal_qualname_col=_PTQ,
            pyteal_component_col=_PTC,
            pyteal_code_window=_PTCW,
            pyteal_path_col=_PT_path,
            pyteal_line_col=_PTL,
            pyteal_code_context_col=_PTCC,
            pyteal_ast_col=_PT_AST,
            linemap_failed=_failed,
            linemap_status=_status,
        )
        for k in kwargs:
            assert k in defaults, f"unrecognized parameter '{k}'"

        required = ["teal_line_col", "teal_code_col", "pyteal_exec_col"]
        renames = {defaults[k]: v for k, v in kwargs.items()}
        for r in required:
            if r not in kwargs:
                renames[defaults[r]] = defaults[r]

        rows = (item.asdict(**renames) for item in self.get_map().values())
        return tabulate(rows, headers=renames, tablefmt=tablefmt)
