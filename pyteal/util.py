from ast import AST, unparse
from configparser import ConfigParser
from dataclasses import dataclass
import executing
from inspect import FrameInfo, stack
from typing import cast, Callable, Optional, Union

from pyteal.errors import TealInternalError


def escapeStr(s: str) -> str:
    """Escape a UTF-8 string for use in TEAL assembly.

    Args:
        s: A UTF-8 string to escape.

    Returns:
        An escaped version of the input string. This version will be surrounded in double quotes,
        all special characters (such as \\n) will be escaped with additional backslashes, and all
        Unicode characters beyond the latin-1 encoding will be encoded in hex escapes (e.g. \\xf0).
    """
    # The point of this conversion is to escape all special characters and turn all Unicode
    # characters into hex-escaped characters in the input string.
    #
    # The first step breaks up large Unicode characters into multiple UTF-8 hex characters:
    #     s_1 = s.encode("utf-8").decode("latin-1"), e.g. "\n 😀" => "\n ð\x9f\x98\x80"
    #
    # The next step escapes all special characters:
    #     s_1.encode("unicode-escape").decode("latin-1"), e.g. "\n ð\x9f\x98\x80" => "\\n \\xf0\\x9f\\x98\\x80"
    #
    # If we skipped the first step we would end up with Unicode codepoints instead of hex escaped
    # characters, which TEAL assembly cannot process:
    #     s.encode("unicode-escape").decode("latin-1"), e.g. "\n 😀" => "\\n \\U0001f600'"
    s = s.encode("utf-8").decode("latin-1").encode("unicode-escape").decode("latin-1")

    # Escape double quote characters (not covered by unicode-escape) but leave in single quotes
    s = s.replace('"', '\\"')

    # Surround string in double quotes
    return '"' + s + '"'


def unescapeStr(s: str) -> str:
    if len(s) < 2 or s[0] != '"' or s[-1] != '"':
        raise ValueError("Escaped string if of the wrong format")
    s = s[1:-1]
    s = s.replace('\\"', '"')
    s = s.encode("latin-1").decode("unicode-escape").encode("latin-1").decode("utf-8")
    return s


def correctBase32Padding(s: str) -> str:
    content = s.split("=")[0]
    trailing = len(content) % 8

    if trailing == 2:
        content += "=" * 6
    elif trailing == 4:
        content += "=" * 4
    elif trailing == 5:
        content += "=" * 3
    elif trailing == 7:
        content += "="
    elif trailing != 0:
        raise TealInternalError("Invalid base32 content")

    return content


@dataclass(frozen=True)
class Frame:
    _internal_paths = [
        # "pyteal/__init__.py",
        "pyteal/ast",
        "pyteal/compiler",
        "pyteal/ir",
        "pyteal/pragma",
        "tests/abi_roundtrip.py",
        "tests/blackbox.py",
        "tests/compile_asserts.py",
        "tests/mock_version.py",
    ]

    frame_info: FrameInfo
    node: AST | None

    def _is_right_before_core(self) -> bool:
        code = self.frame_info.code_context
        return "Frames()" in "".join(code) if code else False

    def _is_pyteal(self) -> bool:
        f = self.frame_info.filename
        return any(w in f for w in self._internal_paths)

    def _is_py_crud(self) -> bool:
        """Hackery that depends on C-Python. Not sure how reliable."""
        return (fi := self.frame_info).code_context is None and fi.filename.startswith(
            "<"
        )

    @classmethod
    def _init_or_drop(cls, f: FrameInfo) -> Optional["Frame"]:
        frame = Frame(f, cast(AST | None, executing.Source.executing(f.frame).node))
        return frame if not frame._is_py_crud() else None

    def __repr__(self) -> str:
        node = unparse(n) if (n := self.node) else None
        context = "".join(cc) if (cc := (fi := self.frame_info).code_context) else None
        return f"{node=}; {context=}; frame_info={fi}"


FrameSequence = Union[Frame, list["FrameSequence"]]


def _skip_all_frames() -> bool:
    try:
        config = ConfigParser()
        config.read("pyteal.ini")
        return not config.getboolean("pyteal-source-mapper", "enabled")
    except Exception as e:
        print(
            f"""Turning off frame capture and disabling sourcemaps. 
Could not read section (pyteal-source-mapper, enabled) of config "pyteal.ini": {e}"""
        )
    return True


class Frames:
    # TODO: I'm pretty sure I have a reasonable go-forward approach, but not sure
    # it's the most modern pythonic way to handle this issue.
    # TODO: BIG QUESTION: How can we configure Frames so that it defaults to a NO-OP ?
    # I believe this should involve a project level config. Some ideas.
    # source_map.ini config file a la: https://www.codeproject.com/Articles/5319621/Configuration-Files-in-Python
    # TOML config a la: https://realpython.com/python-toml/
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

    def __init__(self, keep_all: bool = False, TODO_experimental: bool = True):
        self.frames: list[Frame] = []
        if self.skipping_all():
            return

        frames = [frame for f in stack() if (frame := Frame._init_or_drop(f))]

        if keep_all:
            self.frames = frames
            return

        last_drop_idx = -1
        for i, f in enumerate(frames):
            if f._is_right_before_core():
                last_drop_idx = i
                break

        last_pyteal_idx = last_drop_idx
        prev_file = ""
        in_post_pyteal_streak = False
        last_post_pyteal_streak_idx = last_pyteal_idx + 1
        for i in range(last_drop_idx + 1, len(frames)):
            f = frames[i]
            curr_file = f.frame_info.filename
            if f._is_pyteal():
                last_pyteal_idx = i
            else:
                if last_pyteal_idx == i - 1:
                    in_post_pyteal_streak = True
                    last_post_pyteal_streak_idx = i
                elif in_post_pyteal_streak:
                    in_post_pyteal_streak = prev_file == curr_file
                    if in_post_pyteal_streak:
                        last_post_pyteal_streak_idx = i
            prev_file = curr_file

        last_keep_idx = (
            last_post_pyteal_streak_idx if TODO_experimental else last_pyteal_idx + 1
        )

        self.frames = frames[last_drop_idx + 1 : last_keep_idx + 1]

    def __getitem__(self, index: int) -> Frame:
        return self.frames[index]

    def frame_infos(self) -> list[FrameInfo]:
        return [f.frame_info for f in self.frames]

    def nodes(self) -> list[AST | None]:
        return [f.node for f in self.frames]
