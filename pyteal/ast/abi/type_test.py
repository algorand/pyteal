from typing import NamedTuple, List, Optional, Union, Any, cast
import pytest

from ... import *
from .type import ComputedType, substringForDecoding

# this is not necessary but mypy complains if it's not included
from ... import CompileOptions

options = CompileOptions(version=5)


class DummyComputedType(ComputedType[abi.Uint64]):
    def __init__(self, value: int) -> None:
        super().__init__(abi.Uint64())
        self._value = value

    def store_into(self, output: abi.Uint64) -> Expr:
        return output.set(self._value)


def test_ComputedType_use():
    for value in (0, 1, 2, 3, 12345):
        dummyComputedType = DummyComputedType(value)
        expr = dummyComputedType.use(lambda output: Int(2) * output.get())
        assert expr.type_of() == TealType.uint64
        assert not expr.has_return()

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        assert type(actual) is TealSimpleBlock
        assert actual.ops[1].op == Op.store
        assert type(actual.ops[1].args[0]) is ScratchSlot
        actualSlot = actual.ops[1].args[0]

        expected = TealSimpleBlock(
            [
                TealOp(None, Op.int, value),
                TealOp(None, Op.store, actualSlot),
                TealOp(None, Op.int, 2),
                TealOp(None, Op.load, actualSlot),
                TealOp(None, Op.mul),
            ]
        )

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_substringForDecoding():
    class SubstringTest(NamedTuple):
        startIndex: Optional[Expr]
        endIndex: Optional[Expr]
        length: Optional[Expr]
        expected: Union[Expr, Any]

    encoded = Bytes("encoded")

    tests: List[SubstringTest] = [
        SubstringTest(startIndex=None, endIndex=None, length=None, expected=encoded),
        SubstringTest(
            startIndex=None,
            endIndex=None,
            length=Int(4),
            expected=Extract(encoded, Int(0), Int(4)),
        ),
        SubstringTest(
            startIndex=None,
            endIndex=Int(4),
            length=None,
            expected=Substring(encoded, Int(0), Int(4)),
        ),
        SubstringTest(
            startIndex=None, endIndex=Int(4), length=Int(5), expected=TealInputError
        ),
        SubstringTest(
            startIndex=Int(4),
            endIndex=None,
            length=None,
            expected=Suffix(encoded, Int(4)),
        ),
        SubstringTest(
            startIndex=Int(4),
            endIndex=None,
            length=Int(5),
            expected=Extract(encoded, Int(4), Int(5)),
        ),
        SubstringTest(
            startIndex=Int(4),
            endIndex=Int(5),
            length=None,
            expected=Substring(encoded, Int(4), Int(5)),
        ),
        SubstringTest(
            startIndex=Int(4), endIndex=Int(5), length=Int(6), expected=TealInputError
        ),
    ]

    for i, test in enumerate(tests):
        if not isinstance(test.expected, Expr):
            with pytest.raises(test.expected):
                substringForDecoding(
                    encoded,
                    startIndex=test.startIndex,
                    endIndex=test.endIndex,
                    length=test.length,
                )
            continue

        expr = substringForDecoding(
            encoded,
            startIndex=test.startIndex,
            endIndex=test.endIndex,
            length=test.length,
        )
        assert expr.type_of() == TealType.bytes
        assert not expr.has_return()

        expected, _ = cast(Expr, test.expected).__teal__(options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)
