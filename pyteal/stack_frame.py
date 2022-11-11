import os
import re
from ast import AST, unparse
from configparser import ConfigParser
from dataclasses import dataclass
from enum import IntEnum
from inspect import FrameInfo, stack
from typing import Optional, cast

from executing import Source  # type: ignore


@dataclass(frozen=True)
class StackFrame:
    frame_info: FrameInfo
    node: AST | None

    def as_pyteal_frame(
        self,
        rel_paths: bool = True,
        parent: Optional["PyTealFrame"] | None = None,
    ) -> "PyTealFrame":
        return PyTealFrame(
            frame_info=self.frame_info,
            node=self.node,
            rel_paths=rel_paths,
            parent=parent,
        )

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

    def _is_right_before_core(self) -> bool:
        return self._frame_info_is_right_before_core(self.frame_info)

    @classmethod
    def _frame_info_is_right_before_core(cls, f: FrameInfo) -> bool:
        return bool(code := f.code_context or []) and "Frames" in "".join(code)

    # 50% slower original method:
    # def _is_pyteal(self) -> bool:
    #     f = self.frame_info.filename
    #     return any(w in f for w in self._internal_paths)

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

    @classmethod
    def _init_or_drop(cls, f: FrameInfo) -> Optional["StackFrame"]:
        frame = StackFrame(f, cast(AST | None, Source.executing(f.frame).node))
        return frame if not frame._is_py_crud() else None

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


def _skip_all_frames() -> bool:
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


class Frames:
    _skip_all: bool = _skip_all_frames()

    @classmethod
    def skipping_all(cls, _force_refresh: bool = False) -> bool:
        """
        The `_force_refresh` parameter, is mainly for test validation purposes.
        It is discouraged for use in the wild because:
        * Frames are useful in an "all or nothing" capacity. For example, in preparing
            for a source mapping, it would be error prone to generate frames for
            a subset of analyzed PyTeal
        * Setting `_force_refresh = True` will cause a read from the file system every
            time Frames are initialized, and will result in significant performance degredation
        """
        if _force_refresh:
            cls._skip_all = _skip_all_frames()

        return cls._skip_all

    def __init__(
        self,
        keep_all: bool = False,
        keep_one_frame_only: bool = True,
        # DEPRECATED:
        immediate_stop_post_pyteal: bool = True,  # setting False doesn't work 90% of the time
    ):
        self.frames: list[StackFrame] = []
        if self.skipping_all():
            return

        frame_infos = [f for f in stack() if not StackFrame._frame_info_is_py_crud(f)]

        def make_frames(frame_infos):
            return [
                frame for f in frame_infos if (frame := StackFrame._init_or_drop(f))
            ]

        if keep_all:
            self.frames = make_frames(frame_infos)
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
                    if immediate_stop_post_pyteal:
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

        if keep_one_frame_only:
            frame_infos = frame_infos[-1:]

        self.frames = make_frames(frame_infos)

        # return self._fast_initializer(
        #     keep_all, keep_one_frame_only, immediate_stop_post_pyteal
        # )
        # return self._original_initializer_DEPRECATED(
        #     keep_all, keep_one_frame_only, immediate_stop_post_pyteal
        # )

    # def _fast_initializer(
    #     self, keep_all, keep_one_frame_only, immediate_stop_post_pyteal
    # ):
    #     frame_infos = [f for f in stack() if not StackFrame._frame_info_is_py_crud(f)]

    #     def make_frames(frame_infos):
    #         return [
    #             frame for f in frame_infos if (frame := StackFrame._init_or_drop(f))
    #         ]

    #     if keep_all:
    #         self.frames = make_frames(frame_infos)
    #         return

    #     last_drop_idx = -1
    #     for i, frame_info in enumerate(frame_infos):
    #         if StackFrame._frame_info_is_right_before_core(frame_info):
    #             last_drop_idx = i
    #             break

    #     penultimate_idx = last_drop_idx
    #     prev_file = ""
    #     in_first_post_pyteal = False
    #     for i in range(last_drop_idx + 1, len(frame_infos)):
    #         frame_info = frame_infos[i]
    #         curr_file = frame_info.filename
    #         if StackFrame._frame_info_is_pyteal(frame_info):
    #             penultimate_idx = i
    #         else:
    #             if penultimate_idx == i - 1:
    #                 in_first_post_pyteal = True
    #                 if immediate_stop_post_pyteal:
    #                     break
    #             elif in_first_post_pyteal:
    #                 in_first_post_pyteal = prev_file == curr_file
    #                 if not in_first_post_pyteal:
    #                     penultimate_idx = i - 2
    #                     break
    #         prev_file = curr_file

    #     last_keep_idx = penultimate_idx + 1

    #     if StackFrame._frame_info_is_pyteal_import(frame_infos[last_keep_idx]):
    #         # FAILURE CASE: Look for first pyteal generated code entry in stack trace:
    #         found = False
    #         i = -1
    #         for i in range(last_keep_idx - 1, -1, -1):
    #             if StackFrame._frame_info_compiler_generated(frame_infos[i]):
    #                 found = True
    #                 break

    #         if found and i >= 0:
    #             last_keep_idx = i

    #     frame_infos = frame_infos[last_drop_idx + 1 : last_keep_idx + 1]

    #     if keep_one_frame_only:
    #         frame_infos = frame_infos[-1:]

    #     self.frames = make_frames(frame_infos)

    # def _original_initializer_DEPRECATED(
    #     self, keep_all, keep_one_frame_only, immediate_stop_post_pyteal
    # ):
    #     # _init_or_drop does the heavy lifting of hydrating the AST node in the
    #     # case of a "promising" frame_info
    #     # BUT IT DOES NOT actually require the AST info for its logic
    #     frames = [frame for f in stack() if (frame := StackFrame._init_or_drop(f))]

    #     if keep_all:
    #         self.frames = frames
    #         return

    #     last_drop_idx = -1
    #     for i, f in enumerate(frames):
    #         if f._is_right_before_core():  # _is_right_before_core DOESN'T need AST
    #             last_drop_idx = i
    #             break

    #     penultimate_idx = last_drop_idx
    #     prev_file = ""
    #     in_first_post_pyteal = False
    #     for i in range(last_drop_idx + 1, len(frames)):
    #         f = frames[i]
    #         curr_file = f.frame_info.filename
    #         if f._is_pyteal():  # _is_pyteal DOESN'T need AST
    #             penultimate_idx = i
    #         else:
    #             if penultimate_idx == i - 1:
    #                 in_first_post_pyteal = True
    #                 if immediate_stop_post_pyteal:
    #                     break
    #             elif in_first_post_pyteal:
    #                 in_first_post_pyteal = prev_file == curr_file
    #                 if not in_first_post_pyteal:
    #                     penultimate_idx = i - 2
    #                     break
    #         prev_file = curr_file

    #     last_keep_idx = penultimate_idx + 1

    #     if frames[
    #         last_keep_idx
    #     ]._is_pyteal_import():  # _is_pyteal_import DOESN'T need AST
    #         # FAILURE CASE: Look for first pyteal generated code entry in stack trace:
    #         found = False
    #         i = -1
    #         for i in range(last_keep_idx - 1, -1, -1):
    #             if frames[
    #                 i
    #             ].compiler_generated():  # compiler_generated DOESN'T NEED AST
    #                 found = True
    #                 break

    #         if found and i >= 0:
    #             last_keep_idx = i

    #     self.frames = frames[last_drop_idx + 1 : last_keep_idx + 1]

    #     if keep_one_frame_only:
    #         self.frames = self.frames[-1:]

    def __len__(self) -> int:
        return len(self.frames)

    def __getitem__(self, index: int) -> StackFrame:
        return self.frames[index]

    def frame_infos(self) -> list[FrameInfo]:
        return [f.frame_info for f in self.frames]

    def nodes(self) -> list[AST | None]:
        return [f.node for f in self.frames]


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


class PyTealFrame(StackFrame):
    """
    TODO: Inherit from util::Frame and remove code duplications
    """

    def __init__(
        self,
        frame_info: FrameInfo,
        node: AST | None,
        rel_paths: bool = True,
        parent: Optional["PyTealFrame"] | None = None,
    ):
        super().__init__(frame_info, node)
        # self.frame_info = frame.frame_info
        # self.node = frame.node
        self.rel_paths = rel_paths
        self.parent = parent

        self._raw_code: str | None = None
        self._status: PytealFrameStatus | None = None

    # @classmethod
    # def convert(
    #     cls, frames: FrameSequence, rel_paths: bool = True
    # ) -> "PyTealFrameSequence":  # type: ignore
    #     if isinstance(frames, StackFrame):
    #         return cls(frames, rel_paths)
    #     return [cls.convert(f) for f in cast(Sequence[StackFrame], frames)]

    # def frame(self) -> StackFrame:
    #     return StackFrame(self.frame_info, self.node)

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

    def spawn(self, other: "PyTealFrame", status: "PytealFrameStatus") -> "PyTealFrame":
        assert isinstance(other, PyTealFrame)

        ptf = PyTealFrame(
            frame_info=other.frame_info,
            node=other.node,
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
        return self.frame_info.lineno if self.frame_info else None

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
        pt_line = self.node_source()
        if pt_line and len(pt_line.splitlines()) == 1:
            return pt_line

        return self.code()

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
