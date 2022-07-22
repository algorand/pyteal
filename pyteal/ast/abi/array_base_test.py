from typing import List, cast
import pytest

import pyteal as pt
from pyteal import abi

options = pt.CompileOptions(version=5)

STATIC_TYPES: List[abi.TypeSpec] = [
    abi.BoolTypeSpec(),
    abi.Uint8TypeSpec(),
    abi.Uint16TypeSpec(),
    abi.Uint32TypeSpec(),
    abi.Uint64TypeSpec(),
    abi.TupleTypeSpec(),
    abi.TupleTypeSpec(abi.BoolTypeSpec(), abi.BoolTypeSpec(), abi.Uint64TypeSpec()),
    abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 10),
    abi.StaticArrayTypeSpec(abi.Uint8TypeSpec(), 10),
    abi.StaticArrayTypeSpec(abi.Uint16TypeSpec(), 10),
    abi.StaticArrayTypeSpec(abi.Uint32TypeSpec(), 10),
    abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10),
    abi.StaticArrayTypeSpec(
        abi.TupleTypeSpec(abi.BoolTypeSpec(), abi.BoolTypeSpec(), abi.Uint64TypeSpec()),
        10,
    ),
]

DYNAMIC_TYPES: List[abi.TypeSpec] = [
    abi.DynamicArrayTypeSpec(abi.BoolTypeSpec()),
    abi.DynamicArrayTypeSpec(abi.Uint8TypeSpec()),
    abi.DynamicArrayTypeSpec(abi.Uint16TypeSpec()),
    abi.DynamicArrayTypeSpec(abi.Uint32TypeSpec()),
    abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec()),
    abi.DynamicArrayTypeSpec(abi.TupleTypeSpec()),
    abi.DynamicArrayTypeSpec(
        abi.TupleTypeSpec(abi.BoolTypeSpec(), abi.BoolTypeSpec(), abi.Uint64TypeSpec())
    ),
    abi.DynamicArrayTypeSpec(abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 10)),
    abi.DynamicArrayTypeSpec(abi.StaticArrayTypeSpec(abi.Uint8TypeSpec(), 10)),
    abi.DynamicArrayTypeSpec(abi.StaticArrayTypeSpec(abi.Uint16TypeSpec(), 10)),
    abi.DynamicArrayTypeSpec(abi.StaticArrayTypeSpec(abi.Uint32TypeSpec(), 10)),
    abi.DynamicArrayTypeSpec(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10)),
    abi.DynamicArrayTypeSpec(
        abi.StaticArrayTypeSpec(
            abi.TupleTypeSpec(
                abi.BoolTypeSpec(), abi.BoolTypeSpec(), abi.Uint64TypeSpec()
            ),
            10,
        )
    ),
]


def test_ArrayElement_init():
    dynamicArrayType = abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec())
    array = dynamicArrayType.new_instance()
    index = pt.Int(6)

    element = abi.ArrayElement(array, index)
    assert element.array is array
    assert element.index is index

    with pytest.raises(pt.TealTypeError):
        abi.ArrayElement(array, pt.Bytes("abc"))

    with pytest.raises(pt.TealTypeError):
        abi.ArrayElement(array, pt.Assert(index))


def test_ArrayElement_store_into():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        staticArrayType = abi.StaticArrayTypeSpec(elementType, 100)
        staticArray = staticArrayType.new_instance()
        index = pt.Int(9)

        element = abi.ArrayElement(staticArray, index)
        output = elementType.new_instance()
        expr = element.store_into(output)

        encoded = staticArray.encode()
        stride = pt.Int(staticArray.type_spec()._stride())
        expectedLength = staticArray.length()
        if elementType == abi.BoolTypeSpec():
            expectedExpr = cast(abi.Bool, output).decode_bit(encoded, index)
        elif not elementType.is_dynamic():
            expectedExpr = output.decode(
                encoded, start_index=stride * index, length=stride
            )
        else:
            expectedExpr = output.decode(
                encoded,
                start_index=pt.ExtractUint16(encoded, stride * index),
                end_index=pt.If(index + pt.Int(1) == expectedLength)
                .Then(pt.Len(encoded))
                .Else(pt.ExtractUint16(encoded, stride * index + pt.Int(2))),
            )

        expected, _ = expectedExpr.__teal__(options)
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        with pytest.raises(pt.TealInputError):
            element.store_into(abi.Tuple(abi.TupleTypeSpec(elementType)))

    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        dynamicArray = dynamicArrayType.new_instance()
        index = pt.Int(9)

        element = abi.ArrayElement(dynamicArray, index)
        output = elementType.new_instance()
        expr = element.store_into(output)

        encoded = dynamicArray.encode()
        stride = pt.Int(dynamicArray.type_spec()._stride())
        expectedLength = dynamicArray.length()
        if elementType == abi.BoolTypeSpec():
            expectedExpr = cast(abi.Bool, output).decode_bit(
                encoded, index + pt.Int(16)
            )
        elif not elementType.is_dynamic():
            expectedExpr = output.decode(
                encoded, start_index=stride * index + pt.Int(2), length=stride
            )
        else:
            expectedExpr = output.decode(
                encoded,
                start_index=pt.ExtractUint16(encoded, stride * index + pt.Int(2))
                + pt.Int(2),
                end_index=pt.If(index + pt.Int(1) == expectedLength)
                .Then(pt.Len(encoded))
                .Else(
                    pt.ExtractUint16(encoded, stride * index + pt.Int(2) + pt.Int(2))
                    + pt.Int(2)
                ),
            )

        expected, _ = expectedExpr.__teal__(options)
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            with pt.TealComponent.Context.ignoreScratchSlotEquality():
                assert actual == expected

        assert pt.TealBlock.MatchScratchSlotReferences(
            pt.TealBlock.GetReferencedScratchSlots(actual),
            pt.TealBlock.GetReferencedScratchSlots(expected),
        )

        with pytest.raises(pt.TealInputError):
            element.store_into(abi.Tuple(abi.TupleTypeSpec(elementType)))
