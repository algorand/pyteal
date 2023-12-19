from feature_gates import FeatureGates

from ast import AST, FunctionDef, unparse
from contextlib import contextmanager
from dataclasses import dataclass
from enum import IntEnum
from inspect import FrameInfo, stack
from typing import Callable, Final, cast
import os
import re

from executing import Source


class SourceMapStackFramesError(RuntimeError):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg


@dataclass(frozen=True)
class StackFrame:
    """
    StackFrame is an _internal_ PyTeal class and is
    the first ancestor in the following linear class hierarchy:
                        StackFrame
                            |
                        PyTealFrame
                            |
    compiler.sourcemap.TealMapItem

    Somewhat confusingly, NatalStackFrame is _NOT_ in this hierarchy
    so not "is-a" StackFrame, but it pretends to be and "has-a" list of StackFrame's.

    Its most important members are:
        * frame_info of type inspect.FrameInfo
        * node of type ast.AST
    The first is a python representation of a stack frame, and the
    second represents a python AST node. The imported package `executing`
    features the method `Source.executing` which when run shortly after
    the frame_info's creation, _usually_ succeeds in recovering the
    associated AST node.

    In the current usage, there is a `creator` member which is a `NatalStackFrame`
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
    * User generated code that includes the pattern `NatalStackFrame` may produce degraded results
    """

    frame_info: FrameInfo
    node: AST | None
    creator: "NatalStackFrame"

    # for debugging purposes:
    full_stack: list[FrameInfo] | None = None

    @classmethod
    def _init_or_drop(
        cls, creator: "NatalStackFrame", f: FrameInfo, full_stack: list[FrameInfo]
    ) -> "StackFrame | None":
        """
        Attempt to create a StackFrame object.
        However, if the resulting is considered "Python Crud" abandon and return None.
        When debugging, also persist the full_stack that was provided.
        """
        node = cast(AST | None, Source.executing(f.frame).node)
        frame = StackFrame(
            f, node, creator, full_stack if NatalStackFrame._debugging() else None
        )
        return frame if frame._not_py_crud() else None

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

    def as_pyteal_frame(self) -> "PyTealFrame":
        """
        Downcast one level in the class hierarchy
        """
        return PyTealFrame(
            frame_info=self.frame_info,
            node=self.node,
            creator=self.creator,
            full_stack=self.full_stack,
            rel_paths=True,
            parent=None,
        )

    @classmethod
    def _frame_info_is_right_before_core(cls, f: FrameInfo) -> bool:
        # We keep this method around to be used in a test . Originally,
        # it was actually used in the __init__ method of StackFrame
        # to calculate `last_drop_idx`. However, as -at the time of writing-
        # last_drop_idx =ALWAYS= 1, the logic was simplified and
        # this method was removed from the live calculation.
        return bool(code := f.code_context or []) and "NatalStackFrame" in "".join(code)

    def _is_pyteal(self) -> bool:
        return self._frame_info_is_pyteal(self.frame_info)

    @classmethod
    def _frame_info_is_pyteal(cls, f: FrameInfo) -> bool:
        return bool(cls._internal_paths_re.search(f.filename))

    @classmethod
    def _frame_info_is_pyteal_import(cls, f: FrameInfo) -> bool:
        """
        This method is used to determine if a FrameInfo is associated to a pyteal import.
        It does so by splitting its joined code context on whitespace and periods.
        For example, the following joined code context
            'from pyteal.ast.abi import Uint64 as Positive'
        becomes
            ['from', 'pyteal', 'ast', 'abi', 'import', 'Uint64', 'as', 'Positive']
        and we can verify that this is a pyteal import by checking that
        'pyteal' and 'import' are both in the list.
        This works for other imports such as
            'import pyteal.ast.abi as my_abi'
            'import pyteal as pt'
            'from pyteal import *'
        """
        cc = f.code_context
        if not cc:
            return False

        code = re.split(r"\s|\.", " ".join(cc))
        return "import" in code and "pyteal" in code

    def _not_py_crud(self) -> bool:
        return self._frame_info_not_py_crud(self.frame_info)

    @classmethod
    def _frame_info_not_py_crud(cls, f: FrameInfo) -> bool:
        return bool(f.code_context) or not f.filename.startswith("<")

    def __repr__(self) -> str:
        node = unparse(n) if (n := self.node) else None
        context = "".join(cc) if (cc := (fi := self.frame_info).code_context) else None
        return f"{node=}; {context=}; frame_info={fi}"

    def compiler_generated(self) -> bool | None:
        return self._frame_info_compiler_generated(self.frame_info)

    @classmethod
    def _frame_info_compiler_generated(cls, f: FrameInfo) -> bool | None:
        if not (cc := f.code_context):
            return None  # we don't know / NA

        return "# T2PT" in "".join(cc)

    _compilation_gateways = {
        "_compile_impl": "pyteal/compiler/compiler.py",
        "_build_program": "pyteal/ast/router.py",
    }

    @classmethod
    def _is_compilation_gateway(cls, f: FrameInfo) -> bool:
        return (k := f.function) in cls._compilation_gateways and f.filename.endswith(
            cls._compilation_gateways[k]
        )


@contextmanager
def sourcemapping_off_context():
    """Context manager that turns off sourcemapping for the duration of the context"""
    from feature_gates import FeatureGates

    _sourcemap_before = FeatureGates.sourcemap_enabled()
    _sourcemap_debug_before = FeatureGates.sourcemap_debug()
    FeatureGates.set_sourcemap_enabled(False)
    FeatureGates.set_sourcemap_debug(False)
    assert (
        NatalStackFrame.sourcemapping_is_off()
    ), "Unexpected error. Please report to PyTeal team."
    assert (
        not NatalStackFrame._debugging()
    ), "Unexpected error. Please report to PyTeal team."

    try:
        yield

    finally:
        FeatureGates.set_sourcemap_debug(_sourcemap_debug_before)
        FeatureGates.set_sourcemap_enabled(_sourcemap_before)
        assert (
            NatalStackFrame.sourcemapping_is_off() is not _sourcemap_before
        ), "Unexpected error. Please report to PyTeal team."
        assert (
            NatalStackFrame._debugging() is _sourcemap_debug_before
        ), "Unexpected error. Please report to PyTeal team."


class NatalStackFrame:
    """
    PyTeal's source mapper deduces the code-location of a user's Expr
    via a NatalStackFrame object that is associated with the Expr object.

    When source mapping is disabled (cf. `pyteal.ini`), NatalStackFrame'
    constructor is a no-op.

    When source mapping is enabled, it wraps a list of StackFrame's.

    Under normal operations, only the "best" frame is kept in the list, so
    the name is misleading.
    """

    _keep_all_debugging = False

    @staticmethod
    def sourcemapping_is_off() -> bool:
        return not FeatureGates.sourcemap_enabled()  # type: ignore[attr-defined]

    @staticmethod
    def _debugging() -> bool:
        return FeatureGates.sourcemap_debug()  # type: ignore[attr-defined]

    def __init__(
        self,
    ):
        self._pyteal_gen: bool = False
        self._frames: list[StackFrame] = []

        if self.sourcemapping_is_off():
            return

        # 1. get the full stack trace
        full_stack = stack()

        # 2. discard frames whose filename begins with "<"
        frame_infos = list(filter(StackFrame._frame_info_not_py_crud, full_stack))

        def _make_stack_frames(fis):
            return [
                frame
                for f in fis
                if (frame := StackFrame._init_or_drop(self, f, full_stack))
            ]

        if self._keep_all_debugging or len(frame_infos) <= 1:
            self._frames = _make_stack_frames(frame_infos)
            return

        # 3. start the best frame search right after where NatalStackFrame() was constructed
        # For more details see the unit test:
        # tests/unit/sourcemap_monkey_unit_test.py::test_frame_info_is_right_before_core_last_drop_idx
        i = 2  # formerly this was `last_drop_idx = 1; i = last_drop_idx + 1`

        # 4. fast forward the right bound until we're out of pyteal-library code
        # This sets last_keep_idx to the first frame index which isn't pyteal
        while i < len(frame_infos) and StackFrame._frame_info_is_pyteal(frame_infos[i]):
            i += 1
        last_keep_idx = i

        # 5. back up looking for a compiler gateway and so signal that the expression was generated by pyteal itself
        for i in range(last_keep_idx, -1, -1):
            if StackFrame._is_compilation_gateway(frame_infos[i]):
                self._pyteal_gen = True
                break

        # 6. if the pyteal-library exit point was an import, the expression was
        # generated by pyteal itself. So let's back up and look for a "# T2PT*" comment
        # which will give us a clue for what to do with this expression
        if StackFrame._frame_info_is_pyteal_import(frame_infos[last_keep_idx]):
            found = False
            i = -1
            for i in range(last_keep_idx - 1, -1, -1):
                if StackFrame._frame_info_compiler_generated(frame_infos[i]):
                    found = True
                    break

            if found and i >= 0:
                last_keep_idx = i

        # 7. Keep only the last frame in the list. We maintain _as_ a list
        # since in the case of `self._debug == True`, we'd like access to the full list.
        # TODO: this is likely obsolete since full_stack is available on the PyTealFrame object when debugging
        frame_infos = frame_infos[last_keep_idx : last_keep_idx + 1]

        # 8. we finish by constructing a list[StackFrame] from our one remaining frame_info
        self._frames = _make_stack_frames(frame_infos)

    def user_defined(self) -> bool:
        return not self._pyteal_gen

    def __len__(self) -> int:
        return len(self._frames)

    def _best_frame(self) -> StackFrame:
        """
        Return the best guess as to the user-authored birthplace of the associated StackFrame's.
        If self._frames is non-empty return the last frame in the stack trace.
        Otherwise, raise a SourceMapStackFramesError.
        """
        if not self._frames:
            raise SourceMapStackFramesError(
                f"expected to have some frames but currently {self._frames=}"
            )

        return self._frames[-1]

    def _best_frame_as_pyteal_frame(self) -> "PyTealFrame | None":
        """
        Return the best frame converted to a PyTealFrame, or None if there was an error.
        """
        try:
            return self._best_frame().as_pyteal_frame()
        except SourceMapStackFramesError as smsfe:
            print(
                f"""-------------------
WARNING: Error retrieving the best frame for source mapping.
This may occur because FeatureGates was imported and `FeatureGates.set_sourcemap_enabled(True)` called _AFTER_ pyteal was imported.
error: {smsfe}
"""
            )
        return None

    def __repr__(self) -> str:
        return f"NatalStackFrame({self._frames=})"

    def nodes(self) -> list[AST | None]:
        return [f.node for f in self._frames]

    @classmethod
    def _walk_asts(
        cls,
        func: "Callable[[Expr], bool]",  # type: ignore[name-defined]
        *exprs: "Expr",  # type: ignore[name-defined]
        skipping: bool = False,
    ) -> None:
        """
        General purpose, recursive Expr-AST visitor that applies logic to each visited Expr.

        When skipping is False, apply `func` to each Expr and recurse to its children
            as defined by the pattern-match.

        When skipping is True:
            * if the Expr is user defined, skip it and its children.
            * if not user defined, apply `func` to the Expr. Based on the output of `func`:
                * if True, skip the Expr and its children.
                * if False, visit the Expr's children as defined by the pattern-match.

        Args:
            func: the vistor function to apply.
            *exprs: Expr's to recursively visit.
            skipping: see the logic above.
        """
        from pyteal.ast import (
            Assert,
            BinaryExpr,
            Cond,
            Expr,
            Int,
            MethodSignature,
            Return,
            ScratchStackStore,
            ScratchStore,
            Seq,
            SubroutineCall,
            SubroutineDeclaration,
            TxnaExpr,
            UnaryExpr,
        )

        from pyteal.ast.frame import Proto
        from pyteal.ast.return_ import ExitProgram

        for e in exprs:
            expr = cast(Expr, e)

            if skipping:
                if e.stack_frames.user_defined() or func(expr):
                    continue
            else:
                func(expr)

            walker_args: list[Expr] = []
            match expr:
                case Assert():
                    walker_args = expr.cond
                case BinaryExpr():
                    walker_args = [expr.argLeft, expr.argRight]
                case Cond():
                    walker_args = [y for x in expr.args for y in x]
                case ExitProgram():
                    walker_args = [expr.success]
                case Proto():
                    walker_args = [expr.mem_layout]
                case Seq():
                    walker_args = cast(list[Expr], expr.args)
                case Return():
                    if expr.value:
                        walker_args = [expr.value]
                case SubroutineDeclaration():
                    walker_args = [expr.body]
                case ScratchStore():
                    walker_args = [expr.value]
                    if expr.index_expression:
                        walker_args.append(expr.index_expression)
                case SubroutineCall():
                    subdef = expr.subroutine.get_declaration_by_option(False)
                    if subdef:
                        walker_args.append(subdef)
                    subdef = expr.subroutine.get_declaration_by_option(True)
                    if subdef:
                        walker_args.append(subdef)
                case UnaryExpr():
                    walker_args = [expr.arg]
                case Int(), MethodSignature(), ScratchStackStore(), TxnaExpr():
                    pass
                case _:
                    pass

            if walker_args:
                cls._walk_asts(func, *walker_args, skipping=skipping)

    @classmethod
    def _debug_asts(cls, *exprs: "Expr") -> None:  # type: ignore
        """
        For deubgging purposes only!
        """
        from pyteal.ast import Expr

        if cls.sourcemapping_is_off():
            return

        def dbg(e: Expr) -> bool:
            try:
                finfo = e.stack_frames._best_frame().as_pyteal_frame().hybrid_unparsed()
            except SourceMapStackFramesError as smsfe:
                finfo = str(smsfe)
            print(type(e), ": ", finfo)
            return False

        cls._walk_asts(dbg, *exprs)

    def reframe(self, *exprs: "Expr") -> None:  # type: ignore
        """
        Re-frame the given ASTs to this NatalStackFrame.
        """
        self._reframe_asts(self, *exprs)

    @classmethod
    def _reframe_asts(cls, stack_frames: "NatalStackFrame", *exprs: "Expr") -> None:  # type: ignore
        """
        Recursively traverse a PyTeal AST starting from the given Exprs
        and re-frame each Expr to the given `stack_frames` object.
        Exit the traversal when we encounter a user-defined Expr or when we encounter an Expr
        that has already been re-framed. By exiting when a re-frame would have occured, we
        avoid an infinite loop.
        """
        from pyteal.ast import Expr

        if cls.sourcemapping_is_off():
            return

        def set_frames(e: Expr) -> bool:
            if e.stack_frames == stack_frames:
                return True
            e.stack_frames = stack_frames
            return False

        cls._walk_asts(set_frames, *exprs, skipping=True)

    @classmethod
    def reframe_ops_in_blocks(cls, root_expr: "Expr", start: "TealBlock") -> None:  # type: ignore
        start._sframes_container = root_expr
        for op in start.ops:
            op._sframes_container = root_expr

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


class PyTealFrameStatus(IntEnum):
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
    PyTealFrame is the middle generation in the StackFrame class hierarchy.

    It adds a richer and more polished set of methods to learn about the PyTeal source.
    """

    def __init__(
        self,
        frame_info: FrameInfo,
        node: AST | None,
        creator: NatalStackFrame,
        full_stack: list[FrameInfo] | None,
        rel_paths: bool = True,
        parent: "PyTealFrame | None" = None,
    ):
        super().__init__(frame_info, node, creator, full_stack)
        self.rel_paths: Final[bool] = rel_paths
        self.parent: "Final[PyTealFrame | None]" = parent

        self._raw_code: str | None = None
        self._status: PyTealFrameStatus | None = None
        self._file: str | None = None
        self._root: str | None = None

    def __repr__(self) -> str:
        """
        This repr isn't compliant, but keeping as it's useful for debugging in VSCode
        """
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

    def clone(self, status: PyTealFrameStatus) -> "PyTealFrame":
        ptf = PyTealFrame(
            frame_info=self.frame_info,
            node=self.node,
            creator=self.creator,
            full_stack=self.full_stack,
            rel_paths=self.rel_paths,
        )
        ptf._status = status

        return ptf

    def location(self) -> str:
        return f"{self.file()}:{self.lineno()}" if self.frame_info else ""

    def file(self) -> str:
        if self._file is None:
            if not self.frame_info:
                self._file = ""
            else:
                path = self.frame_info.filename
                self._file = os.path.relpath(path) if self.rel_paths else path

        return self._file

    def root(self) -> str:
        if self._root is None:
            self._root = os.getcwd()

        return self._root

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
        """Provide accurate 0-indexed column offset when available. Or 0 when not."""
        return self.node_col_offset() or 0

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
        Attempt to unparse the node and return the most apropos line,
        together with its offset in comparison with its raw code.
        """
        raw_code = self.raw_code()
        node = self.node
        pt_chunk = self.node_source()
        return self._hybrid_impl(raw_code, node, pt_chunk)

    @classmethod
    def _hybrid_impl(
        cls, code: str, node: AST | None, pt_chunk: str
    ) -> tuple[str, int]:
        """
        Given a chunk of PyTeal `pt_chunk` represending a node's source,
        and `code` representing a FrameInfo's code_context,
        return information about the most appropriate code to use in
        the source map.
        When the node source isn't available, return `code`
        and an offset of 0.
        When the node source is a single line, return `pt_chunk`
        and an offset of 0.
        When the node source is a multi-line chunk, in the case of
        a non-FunctionDef node, we assume that the offset is 0.
        Finally, in the case of a FunctionDef node, find the offset
        by finding where the prefix `def` appears in the chunk.
        """
        if pt_chunk:
            pt_lines = pt_chunk.splitlines()
            if len(pt_lines) == 1:
                return pt_chunk, 0

            offset = i = 0
            if pt_lines and isinstance(node, FunctionDef):
                code_idx = -1
                for i, line in enumerate(pt_lines):
                    if line.startswith(code):
                        code_idx = i
                    if line.startswith("def"):
                        if code_idx >= 0:
                            offset = i - code_idx
                        return pt_lines[i], offset
                if code_idx >= 0:
                    return pt_lines[code_idx], 0

        return code, 0

    # END OF VARIATIONS ON A THEME OF CODE
    def failed_ast(self) -> bool:
        return not self.node

    def status_code(self) -> PyTealFrameStatus:
        if self._status is not None:
            return self._status

        if self.frame_info is None:
            return PyTealFrameStatus.MISSING

        if self.node is None:
            return PyTealFrameStatus.MISSING_AST

        if self.compiler_generated():
            return PyTealFrameStatus.PYTEAL_GENERATED

        if not self.raw_code():
            return PyTealFrameStatus.MISSING_CODE

        return PyTealFrameStatus.COPACETIC

    def status(self) -> str:
        return self.status_code().human()

    def node_source(self) -> str:
        return unparse(self.node) if self.node else ""

    def node_lineno(self) -> int | None:
        return getattr(self.node, "lineno", None) if self.node else None

    def node_col_offset(self) -> int | None:
        """0-indexed BEGINNING column offset"""
        return getattr(self.node, "col_offset", None) if self.node else None

    def node_end_lineno(self) -> int | None:
        return getattr(self.node, "end_lineno", None) if self.node else None

    def node_end_col_offset(self) -> int | None:
        """0-indexed ENDING column offset"""
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
        short = f"<{self.raw_code()}>{spaces}@{self.location()}"
        if not verbose:
            return short

        return f"""{short}
{self.frame_info.index=}
{self.frame_info.function=}
{self.frame_info.frame=}"""
