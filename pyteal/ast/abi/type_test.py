import pyteal as pt
from pyteal import abi

options = pt.CompileOptions(version=5)


class ContainerType(abi.ComputedValue):
    def __init__(self, type_spec: abi.TypeSpec, encodings: pt.Expr):
        self.type_spec = type_spec
        self.encodings = encodings

    def produced_type_spec(self) -> abi.TypeSpec:
        return self.type_spec

    def store_into(self, output: abi.BaseType) -> pt.Expr:
        if output.type_spec() != self.type_spec:
            raise pt.TealInputError(
                f"expected type_spec {self.type_spec} but get {output.type_spec()}"
            )
        return output._stored_value.store(self.encodings)


def test_ComputedType_use():
    for value in (0, 1, 2, 3, 12345):
        dummyComputedType = ContainerType(abi.Uint64TypeSpec(), pt.Int(value))
        expr = dummyComputedType.use(lambda output: pt.Int(2) * output.get())
        assert expr.type_of() == pt.TealType.uint64
        assert not expr.has_return()

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        assert type(actual) is pt.TealSimpleBlock
        assert actual.ops[1].op == pt.Op.store
        assert type(actual.ops[1].args[0]) is pt.ScratchSlot
        actualSlot = actual.ops[1].args[0]

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.int, value),
                pt.TealOp(None, pt.Op.store, actualSlot),
                pt.TealOp(None, pt.Op.int, 2),
                pt.TealOp(None, pt.Op.load, actualSlot),
                pt.TealOp(None, pt.Op.mul),
            ]
        )

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected
