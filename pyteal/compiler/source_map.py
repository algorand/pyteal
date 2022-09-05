from dataclasses import dataclass
import inspect
import os
from typing import cast, Any, OrderedDict

from tabulate import tabulate

import pyteal as pt


class PyTealFrame:
    def __init__(self, frame: inspect.FrameInfo | None, rel_paths: bool = True):
        self.frame = frame
        self.rel_paths = rel_paths
        self.source = None
        self.ast = None
        self._raw_code = None

    commentary = {
        "# T2PT0": "PyTeal generated pragma",
        "# T2PT1": "PyTeal generated label",
        "# T2PT2": "PyTeal generated return for TealType.none",
        "# T2PT3": "PyTeal generated return for non-null TealType",
        "# T2PT4": "PyTeal generated subroutine parameter handler instruction",
    }

    def location(self) -> str:
        return f"{self.file()}:{self.lineno()}" if self.frame else ""

    def file(self) -> str:
        if not self.frame:
            return ""

        path = self.frame.filename
        return os.path.relpath(path) if self.rel_paths else path

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

        for k, v in self.commentary.items():
            if k in raw:
                return f"{v}: {raw}"

        return f"Unhandled # T2PT commentary: {raw}"

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
    def convert(cls, fs: inspect.FrameInfo | list):
        if isinstance(fs, inspect.FrameInfo):
            return cls(fs)
        assert isinstance(fs, list), f"expected list but got {type(fs)}"
        return [cls.convert(f) for f in cast(list, fs)]


@dataclass
class SourceMapItem:
    line: int
    teal: str
    component: pt.TealComponent
    frame: PyTealFrame
    extras: dict[str, Any] | None

    @classmethod
    def fields(cls) -> list[str]:
        return ["TL", "Teal", "PyTeal", "PT path", "PTL", "PT component", "PT frame"]

    def asdict(self, **kwargs) -> OrderedDict:
        """kwargs serve as a rename mapping when present
        TODO: is this overly complicated?
        """
        assert not kwargs.keys() - set(self.fields())

        attrs = {
            "TL": self.line,
            "Teal": self.teal,
            "PyTeal": self.frame.code(),
            "PT path": self.frame.file(),
            "PTL": self.frame.lineno(),
            "PT component": self.component,
            "PT frame": self.frame,
        }
        return OrderedDict(((kwargs[k], attrs[k]) for k in kwargs))


def get_source_map(
    teal_lines: list[str],
    teal_components: list[pt.TealComponent],
    add_extras: bool = False,
) -> dict:
    N = len(teal_lines)
    assert N == len(
        teal_components
    ), f"expected same number of teal lines {N} and components {len(teal_components)}"

    best_frames = []
    before, after = [], []
    for tc in teal_components:
        f, a, b = best_frame_and_more(tc)
        best_frames.append(f)
        before.append(b)
        after.append(a)

    def source_map_item(i, tc):
        extras: dict[str, Any] | None = None
        if add_extras:
            extras = {
                "after_frames": after[i],
                "before_frames": before[i],
            }
        return SourceMapItem(i + 1, teal_lines[i], tc, best_frames[i], extras)

    return {i + 1: source_map_item(i, tc) for i, tc in enumerate(teal_components)}


def best_frame_and_more(
    t: pt.TealComponent,
) -> tuple[inspect.FrameInfo | None, list[inspect.FrameInfo], list[inspect.FrameInfo]]:
    frames_reversed: list[inspect.FrameInfo]
    path_match: str
    match t:
        case pt.TealOp():
            assert t.expr is not None, f"provided TealOp {t} missing Expr"
            frames_reversed = t.expr.frames
            path_match = "pyteal/ast"
        case pt.TealLabel() | pt.TealPragma():
            frames_reversed = t.frames
            path_match = "pyteal/ir"
        case _:
            raise Exception(f"expected TealComponent but got {type(t)}")

    pyteals = [
        path_match,
        "tests/abi_roundtrip.py",
        "tests/blackbox.py",
        "tests/compilea_asserts.py",
        "tests/mock_version.py",
    ]

    pyteal_idx = [any(w in f.filename for w in pyteals) for f in frames_reversed]

    in_pt, first_pt_entrancy = False, None
    for i, is_pyteal in enumerate(pyteal_idx):
        if is_pyteal and not in_pt:
            in_pt = True
            continue
        if not is_pyteal and in_pt:
            first_pt_entrancy = i
            break

    if first_pt_entrancy is None:
        return None, [], []

    # TODO: probly don't need to keep `extras` param of SourceMapItem
    # nor the 2nd and 3rd elements of the following tuple being returned
    return tuple(
        PyTealFrame.convert(
            [
                frames_reversed[first_pt_entrancy],
                [frames_reversed[i] for i in range(first_pt_entrancy - 1, -1, -1)],
                [
                    frames_reversed[i]
                    for i in range(first_pt_entrancy + 1, len(frames_reversed))
                ],
            ]
        )  # type: ignore
    )


def tabulate_source_map(
    m: dict[int, SourceMapItem],
    columns=["TL", "Teal", "PyTeal", "PT path", "PTL", "PT component"],
    tablefmt="fancy_grid",
) -> str:
    headers = {col: col for col in columns}
    rows = (item.asdict(**headers) for item in m.values())
    return tabulate(rows, headers=headers, tablefmt=tablefmt)
