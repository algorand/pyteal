import pytest

from ... import *

options = CompileOptions(version=5)


class DummyComputedType(abi.ComputedType[abi.Uint64]):
    def __init__(self, value: int) -> None:
        super().__init__()
        self._value = value

    def produced_type_spec(self) -> abi.Uint64TypeSpec:
        return abi.Uint64TypeSpec()

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
