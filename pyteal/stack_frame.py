from ast import AST, FunctionDef, unparse
from configparser import ConfigParser
from dataclasses import dataclass
from enum import IntEnum
from inspect import FrameInfo, stack
from typing import Callable, Optional, cast
import os
import re

from executing import Source  # type: ignore


@dataclass
class StackFrame:
    """
    StackFrame is an _internal_ PyTeal class and is
    the first ancestor in the following linear class hierarchy:
                        StackFrame
                            |
                        PyTealFrame
                            |
    compiler.sourcemap.TealMapItem

    Its most important members are:
        * frame_info of type inspect.FrameInfo
        * node of type ast.AST
    The first is a python representation of a stack frame, and the
    second represents a python AST node. The imported package `executing`
    features the method `Source.executing` which when run shortly after
    the frame_info's creation, _usually_ succeeds in recovering the
    associated AST node.

    In the current usage, there is a `creator` member which is a `StackFrames`
    object -usually belonging to a PyTeal Expr- and which is assumed to have called
    the private constructor `_init_or_drop()`.

    It is not recommended that this class be accessed directly.

    Of special note, is the class variable `_internal_paths`.
    This is a whitelist of file patterns which signal to the logic
    of method `_frame_info_is_pyteal()` that a particular
    frame was _NOT_ created by the user.

    QUIRKS:
    * Unfortunately, this means that if a user created file satisfies the above pattern,
    the performance of the source mapper will degrade.
    * User generated code that includes the pattern `StackFrames` may produce degraded results
    """

    frame_info: FrameInfo
    node: Optional[AST]
    creator: "StackFrames"

    # for debugging purposes:
    full_stack: Optional[list[FrameInfo]] = None

    @classmethod
    def _init_or_drop(
        cls, creator: "StackFrames", f: FrameInfo, full_stack: list[FrameInfo]
    ) -> Optional["StackFrame"]:
        node = cast(AST | None, Source.executing(f.frame).node)
        frame = StackFrame(f, node, creator, full_stack if StackFrames._debug else None)
        return frame if not frame._is_py_crud() else None

    # TODO: when a source mapper is instantiated, it ought to survey
    # the user's project files and warn in the case that some file
    # matches the _internal_paths pattern
    _internal_paths = [
        "beaker/__init__.py",
        "beaker/application.py",
        "beaker/consts.py",
        "beaker/decorators.py",
        "beaker/state.py",
        "pyteal/__init__.py",
        "pyteal/ast",
        "pyteal/compiler",
        "pyteal/ir",
        "pyteal/pragma",
        "pyteal/stack_frame.py",
        "tests/abi_roundtrip.py",
        "tests/blackbox.py",
        "tests/compile_asserts.py",
        "tests/mock_version.py",
    ]
    _internal_paths_re = re.compile("|".join(_internal_paths))

    def as_pyteal_frame(
        self,
        rel_paths: bool = True,
        parent: Optional["PyTealFrame"] | None = None,
    ) -> "PyTealFrame":
        """
        Downcast one level in the class hierarchy
        """
        return PyTealFrame(
            frame_info=self.frame_info,
            node=self.node,
            creator=self.creator,
            full_stack=self.full_stack,
            rel_paths=rel_paths,
            parent=parent,
        )

    @classmethod
    def _frame_info_is_right_before_core(cls, f: FrameInfo) -> bool:
        # TODO: this is a hack and the false positive surface area shuould be reduced
        return bool(code := f.code_context or []) and "StackFrames" in "".join(code)

    def _is_pyteal(self) -> bool:
        return self._frame_info_is_pyteal(self.frame_info)

    @classmethod
    def _frame_info_is_pyteal(cls, f: FrameInfo) -> bool:
        return bool(cls._internal_paths_re.search(f.filename))

    def _is_pyteal_import(self) -> bool:
        return self._frame_info_is_pyteal_import(self.frame_info)

    @classmethod
    def _frame_info_is_pyteal_import(cls, f: FrameInfo) -> bool:
        cc = f.code_context
        if not cc:
            return False

        code = "".join(cc)
        return "import" in code and "pyteal" in code

    def _is_py_crud(self) -> bool:
        """Hackery that depends on C-Python. Not sure how reliable."""
        return self._frame_info_is_py_crud(self.frame_info)

    @classmethod
    def _frame_info_is_py_crud(cls, f: FrameInfo) -> bool:
        return f.code_context is None and f.filename.startswith("<")

    def __repr__(self) -> str:
        node = unparse(n) if (n := self.node) else None
        context = "".join(cc) if (cc := (fi := self.frame_info).code_context) else None
        return f"{node=}; {context=}; frame_info={fi}"

    def compiler_generated(self) -> bool | None:
        if self.creator._compiler_gen:
            return True

        return self._frame_info_compiler_generated(self.frame_info)

    @classmethod
    def _frame_info_compiler_generated(cls, f: FrameInfo) -> bool | None:
        if not (cc := f.code_context):
            return None  # we don't know / NA

        return "# T2PT" in "".join(cc)


def _sourcmapping_is_off() -> bool:
    try:
        config = ConfigParser()
        config.read("pyteal.ini")
        enabled = config.getboolean("pyteal-source-mapper", "enabled")
        return not enabled
    except Exception as e:
        print(
            f"""Turning off frame capture and disabling sourcemaps. 
Could not read section (pyteal-source-mapper, enabled) of config "pyteal.ini": {e}"""
        )
    return True


def _debug_frames() -> bool:
    try:
        config = ConfigParser()
        config.read("pyteal.ini")
        return config.getboolean("pyteal-source-mapper", "debug")
    except Exception as e:
        print(
            f"""Disabling `debug` status for sourcemaps. 
Could not read section (pyteal-source-mapper, debug) of config "pyteal.ini": {e}"""
        )
    return False


class StackFrames:
    """
    PyTeal's source mapper deduces the code-location of a user's Expr
    via a StackFrames object that is associated with the Expr object.

    When source mapping is disabled (cf. `pyteal.ini`), StackFrames'
    constructor is a no-op.

    When source mapping is enabled, it wraps a list of StackFrame's.

    Under normal operations, only the "best" frame is kept in the list, so
    the name is misleading.

    TODO: Rename this to somethling less misleading. EG: NatalStackFrame
    TODO: Privatize frames member
    """

    _no_stackframes: bool = _sourcmapping_is_off()
    _debug: bool = _debug_frames()

    @classmethod
    def sourcemapping_is_off(cls, _force_refresh: bool = False) -> bool:
        """
        The `_force_refresh` parameter, is mainly for test validation purposes.
        It is discouraged for use in the wild because:
        * Frames are useful in an "all or nothing" capacity. For example, in preparing
            for a source mapping, it would be error prone to generate frames for
            a subset of analyzed PyTeal
        * Setting `_force_refresh = True` will cause a read from the file system every
            time Frames are initialized and will result in significant performance degredation
        """
        if _force_refresh:
            cls._no_stackframes = _sourcmapping_is_off()

        return cls._no_stackframes

    def __init__(
        self,
        _keep_all: bool = False,
    ):
        self._compiler_gen: bool = False
        self._frames: list[StackFrame] = []

        if self.sourcemapping_is_off():
            return

        full_stack = stack()
        frame_infos = [
            f for f in full_stack if not StackFrame._frame_info_is_py_crud(f)
        ]

        def _make_stack_frames(frame_infos):
            return [
                frame
                for f in frame_infos
                if (frame := StackFrame._init_or_drop(self, f, full_stack))
            ]

        # degugging only:
        if _keep_all:
            self._frames = _make_stack_frames(frame_infos)
            return

        last_drop_idx = -1
        for i, frame_info in enumerate(frame_infos):
            if StackFrame._frame_info_is_right_before_core(frame_info):
                last_drop_idx = i
                break

        penultimate_idx = last_drop_idx
        prev_file = ""
        in_first_post_pyteal = False
        for i in range(last_drop_idx + 1, len(frame_infos)):
            frame_info = frame_infos[i]
            curr_file = frame_info.filename
            if StackFrame._frame_info_is_pyteal(frame_info):
                penultimate_idx = i
            else:
                if penultimate_idx == i - 1:
                    in_first_post_pyteal = True
                    break
                elif in_first_post_pyteal:
                    in_first_post_pyteal = prev_file == curr_file
                    if not in_first_post_pyteal:
                        penultimate_idx = i - 2
                        break
            prev_file = curr_file

        last_keep_idx = penultimate_idx + 1

        if StackFrame._frame_info_is_pyteal_import(frame_infos[last_keep_idx]):
            # FAILURE CASE: Look for first pyteal generated code entry in stack trace:
            found = False
            i = -1
            for i in range(last_keep_idx - 1, -1, -1):
                if StackFrame._frame_info_compiler_generated(frame_infos[i]):
                    found = True
                    break

            if found and i >= 0:
                last_keep_idx = i

        frame_infos = frame_infos[last_drop_idx + 1 : last_keep_idx + 1]
        frame_infos = frame_infos[-1:]

        self._frames = _make_stack_frames(frame_infos)

    def __len__(self) -> int:
        return len(self._frames)

    def best(self) -> StackFrame:
        """
        Return the best guess as to the user-authored birthplace of the
        associated StackFrame's
        """
        assert (
            self._frames
        ), f"expected to have some frames but currently {self._frames=}"
        return self._frames[-1]

    def __repr__(self) -> str:
        return f"{'C' if self._compiler_gen else 'U'}{self._frames}"

    def nodes(self) -> list[AST | None]:
        return [f.node for f in self._frames]

    @classmethod
    def _walk_asts(cls, func: Callable[["Expr"], None], *exprs: "Expr") -> None:  # type: ignore
        from pyteal.ast import (
            Assert,
            BinaryExpr,
            Cond,
            Expr,
            Seq,
            SubroutineDeclaration,
        )
        from pyteal.ast.frame import Proto

        for expr in exprs:
            e = cast(Expr, expr)
            func(e)

            match e:
                case Assert():
                    cls._walk_asts(func, *e.cond)
                case BinaryExpr():
                    cls._walk_asts(func, e.argLeft, e.argRight)
                case Cond():
                    cls._walk_asts(func, *(y for x in e.args for y in x))
                case Proto():
                    cls._walk_asts(func, e.mem_layout)
                case Seq():
                    cls._walk_asts(func, *e.args)
                case SubroutineDeclaration():
                    cls._walk_asts(func, e.body)
                case _:
                    # TODO: implement more cases, but no need to error as this isn't used for functionality's sake.
                    pass

    @classmethod
    def _debug_asts(cls, *exprs: "Expr") -> None:  # type: ignore
        """
        For deubgging purposes only!
        """
        from pyteal.ast import Expr

        if cls.sourcemapping_is_off():
            return

        def dbg(e: Expr):
            print(
                type(e), ": ", e.stack_frames.best().as_pyteal_frame().hybrid_unparsed()
            )

        cls._walk_asts(dbg, *exprs)

    @classmethod
    def mark_asts_as_compiler_gen(cls, *exprs: "Expr") -> None:  # type: ignore
        from pyteal.ast import Expr

        if cls.sourcemapping_is_off():
            return

        def mark(e: Expr):
            e.stack_frames._compiler_gen = True

        cls._walk_asts(mark, *exprs)

    @classmethod
    def reframe_asts(cls, stack_frames: "StackFrames", *exprs: "Expr") -> None:  # type: ignore
        from pyteal.ast import Expr

        if cls.sourcemapping_is_off():
            return

        def set_frames(e: Expr):
            e.stack_frames = stack_frames

        cls._walk_asts(set_frames, *exprs)

    @classmethod
    def reframe_ops_in_blocks(cls, root_expr: "Expr", start: "TealBlock") -> None:  # type: ignore
        start._root_expr = root_expr
        for op in start.ops:
            op._root_expr = root_expr

        if nxt := start.nextBlock:
            cls.reframe_ops_in_blocks(root_expr, nxt)


class PT_GENERATED:
    PRAGMA = "PyTeal generated pragma"
    SUBR_LABEL = "PyTeal generated subroutine label"
    RETURN_NONE = "PyTeal generated return for TealType.none"
    RETURN_VALUE = "PyTeal generated return for non-null TealType"
    SUBR_PARAM = "PyTeal generated subroutine parameter handler instruction"
    BRANCH = "PyTeal generated branching"
    BRANCH_LABEL = "PyTeal generated branching label"
    TYPE_ENUM_TXN = "PyTeal generated transaction Type Enum"
    TYPE_ENUM_ONCOMPLETE = "PyTeal generated OnComplete Type Enum"
    FLAGGED_BY_DEV = "Developer has flagged expression as compiler generated"


_PT_GEN = {
    "# T2PT0": PT_GENERATED.PRAGMA,
    "# T2PT1": PT_GENERATED.SUBR_LABEL,
    "# T2PT2": PT_GENERATED.RETURN_NONE,
    "# T2PT3": PT_GENERATED.RETURN_VALUE,
    "# T2PT4": PT_GENERATED.SUBR_PARAM,
    "# T2PT5": PT_GENERATED.BRANCH,
    "# T2PT6": PT_GENERATED.BRANCH_LABEL,
    "# T2PT7": PT_GENERATED.TYPE_ENUM_TXN,
    "# T2PT8": PT_GENERATED.TYPE_ENUM_ONCOMPLETE,
}


class PytealFrameStatus(IntEnum):
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
    COPACETIC = 9  # currently, 90% confident is as good as it gets

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


class PyTealFrame(StackFrame):
    """
    TODO: Inherit from util::Frame and remove code duplications
    """

    def __init__(
        self,
        frame_info: FrameInfo,
        node: AST | None,
        creator: StackFrames,
        full_stack: list[FrameInfo] | None,
        rel_paths: bool = True,
        parent: Optional["PyTealFrame"] | None = None,
    ):
        super().__init__(frame_info, node, creator, full_stack)
        self.rel_paths = rel_paths
        self.parent = parent

        self._raw_code: str | None = None
        self._status: PytealFrameStatus | None = None

    def __repr__(self) -> str:
        """TODO: this repr isn't compliant. Should we keep it anyway for convenience?"""
        return self._str_impl(verbose=False)

    def __eq__(self, other: object) -> bool:
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

    def spawn(self, other: "PyTealFrame", status: PytealFrameStatus) -> "PyTealFrame":
        assert isinstance(other, PyTealFrame)

        ptf = PyTealFrame(
            frame_info=other.frame_info,
            node=other.node,
            creator=other.creator,
            full_stack=other.full_stack,
            rel_paths=other.rel_paths,
            parent=self,
        )
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
        naive_lineno = self.frame_info.lineno if self.frame_info else None
        if naive_lineno is None:
            return naive_lineno

        hybrid_line, offset = self._hybrid_w_offset()
        if hybrid_line.startswith(self.raw_code()):
            return naive_lineno

        return naive_lineno + offset

    def column(self) -> int:
        """Provide accurate column info when available. Or 0 when not."""
        return self.node_col_offset() or 0

    def compiler_generated_reason(self) -> str | None:
        """
        None indicates either "unkown" or "not compiler generated".
        To distinguish between these two usages, call `compiler_generated()` first.
        """
        if not self.compiler_generated():
            return None

        if self.creator._compiler_gen:
            return PT_GENERATED.FLAGGED_BY_DEV

        for k, v in _PT_GEN.items():
            if k in self.raw_code():
                return v

        raise AssertionError(
            "This should never happen as the call to self.compiler_generated() should have prevented this case."
        )

    # VARIATIONS ON THE THEME OF SOURCE CODE:

    def raw_code(self) -> str:
        if self._raw_code is None:
            self._raw_code = (
                ("".join(self.frame_info.code_context)).strip()
                if self.frame_info and self.frame_info.code_context
                else ""
            )

        return self._raw_code

    def hybrid_unparsed(self) -> str:
        """
        Attempt to unparse the node and return the most apropos line
        """
        return self._hybrid_w_offset()[0]

    def _hybrid_w_offset(self) -> tuple[str, int]:
        """
        Attempt to unparse the node and return the most apropos line, together with its offset
        """
        code = self.code()
        node = self.node
        pt_chunk = self.node_source()
        return self._hybrid_impl(code, node, pt_chunk)

    @classmethod
    def _hybrid_impl(
        cls, code: str, node: Optional[AST], pt_chunk: str
    ) -> tuple[str, int]:
        if pt_chunk:
            pt_lines = pt_chunk.splitlines()
            if len(pt_lines) == 1:
                return pt_chunk, 0

            if pt_lines and isinstance(
                node, FunctionDef
            ):  # >= 2 lines function definiton
                if getattr(node, "decorator_list", False):
                    return pt_lines[1], 1
                return pt_lines[0], 0

        return code, 0

    def code(self) -> str:
        """using _PT_GEN here is DEPRECATED"""
        raw = self.raw_code()
        if not self.compiler_generated():
            return raw

        for k, v in _PT_GEN.items():
            if k in raw:
                return f"{v}: {raw}"

        return f"Unhandled # T2PT commentary: {raw}"

    # END OF VARIATIONS ON A THEME OF CODE

    def failed_ast(self) -> bool:
        return not self.node

    def status_code(self) -> PytealFrameStatus:
        if self._status is not None:
            return self._status

        if self.frame_info is None:
            return PytealFrameStatus.MISSING

        if self.node is None:
            return PytealFrameStatus.MISSING_AST

        if self.compiler_generated():
            return PytealFrameStatus.PYTEAL_GENERATED

        if not self.raw_code():
            return PytealFrameStatus.MISSING_CODE

        return PytealFrameStatus.COPACETIC

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

    def __str__(self) -> str:
        return self._str_impl(verbose=True)

    def _str_impl(self, verbose: bool = True) -> str:
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
