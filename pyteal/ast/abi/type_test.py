from ... import *

options = CompileOptions(version=5)


class ContainerType(abi.ComputedValue):
    def __init__(self, type_spec: abi.TypeSpec, encodings: Expr):
        self.type_spec = type_spec
        self.encodings = encodings

    def produced_type_spec(self) -> abi.TypeSpec:
        return self.type_spec

    def store_into(self, output: abi.BaseType) -> Expr:
        if output.type_spec() != self.type_spec:
            raise TealInputError(
                f"expected type_spec {self.type_spec} but get {output.type_spec()}"
            )
        return output.stored_value.store(self.encodings)


def test_ComputedType_use():
    for value in (0, 1, 2, 3, 12345):
        dummyComputedType = ContainerType(abi.Uint64TypeSpec(), Int(value))
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
