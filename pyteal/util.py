from ast import AST
from configparser import ConfigParser
from dataclasses import dataclass
import executing
from inspect import FrameInfo, stack
from typing import cast, Union

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
    frame_info: FrameInfo
    node: AST | None


FrameSequence = Union[Frame, list["FrameSequence"]]


def _skip_all_frames() -> bool:
    config = ConfigParser()
    config.read("pyteal.ini")
    return not config.getboolean("pyteal-source-mapper", "enabled")


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

    def __init__(self):
        self.frames: list[Frame] = []
        if self.skipping_all():
            return
        self.frames = [
            Frame(f, cast(AST | None, executing.Source.executing(f.frame).node))
            for f in stack()
        ]

    def __getitem__(self, index: int) -> Frame:
        return self.frames[index]

    def frame_infos(self) -> list[FrameInfo]:
        return [f.frame_info for f in self.frames]

    def nodes(self) -> list[AST | None]:
        return [f.node for f in self.frames]
