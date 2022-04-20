from typing import List, cast
import pytest

import pyteal as pt

options = pt.CompileOptions(version=5)

STATIC_TYPES: List[pt.abi.TypeSpec] = [
    pt.abi.BoolTypeSpec(),
    pt.abi.Uint8TypeSpec(),
    pt.abi.Uint16TypeSpec(),
    pt.abi.Uint32TypeSpec(),
    pt.abi.Uint64TypeSpec(),
    pt.abi.TupleTypeSpec(),
    pt.abi.TupleTypeSpec(
        pt.abi.BoolTypeSpec(), pt.abi.BoolTypeSpec(), pt.abi.Uint64TypeSpec()
    ),
    pt.abi.StaticArrayTypeSpec(pt.abi.BoolTypeSpec(), 10),
    pt.abi.StaticArrayTypeSpec(pt.abi.Uint8TypeSpec(), 10),
    pt.abi.StaticArrayTypeSpec(pt.abi.Uint16TypeSpec(), 10),
    pt.abi.StaticArrayTypeSpec(pt.abi.Uint32TypeSpec(), 10),
    pt.abi.StaticArrayTypeSpec(pt.abi.Uint64TypeSpec(), 10),
    pt.abi.StaticArrayTypeSpec(
        pt.abi.TupleTypeSpec(
            pt.abi.BoolTypeSpec(), pt.abi.BoolTypeSpec(), pt.abi.Uint64TypeSpec()
        ),
        10,
    ),
]

DYNAMIC_TYPES: List[pt.abi.TypeSpec] = [
    pt.abi.DynamicArrayTypeSpec(pt.abi.BoolTypeSpec()),
    pt.abi.DynamicArrayTypeSpec(pt.abi.Uint8TypeSpec()),
    pt.abi.DynamicArrayTypeSpec(pt.abi.Uint16TypeSpec()),
    pt.abi.DynamicArrayTypeSpec(pt.abi.Uint32TypeSpec()),
    pt.abi.DynamicArrayTypeSpec(pt.abi.Uint64TypeSpec()),
    pt.abi.DynamicArrayTypeSpec(pt.abi.TupleTypeSpec()),
    pt.abi.DynamicArrayTypeSpec(
        pt.abi.TupleTypeSpec(
            pt.abi.BoolTypeSpec(), pt.abi.BoolTypeSpec(), pt.abi.Uint64TypeSpec()
        )
    ),
    pt.abi.DynamicArrayTypeSpec(pt.abi.StaticArrayTypeSpec(pt.abi.BoolTypeSpec(), 10)),
    pt.abi.DynamicArrayTypeSpec(pt.abi.StaticArrayTypeSpec(pt.abi.Uint8TypeSpec(), 10)),
    pt.abi.DynamicArrayTypeSpec(
        pt.abi.StaticArrayTypeSpec(pt.abi.Uint16TypeSpec(), 10)
    ),
    pt.abi.DynamicArrayTypeSpec(
        pt.abi.StaticArrayTypeSpec(pt.abi.Uint32TypeSpec(), 10)
    ),
    pt.abi.DynamicArrayTypeSpec(
        pt.abi.StaticArrayTypeSpec(pt.abi.Uint64TypeSpec(), 10)
    ),
    pt.abi.DynamicArrayTypeSpec(
        pt.abi.StaticArrayTypeSpec(
            pt.abi.TupleTypeSpec(
                pt.abi.BoolTypeSpec(), pt.abi.BoolTypeSpec(), pt.abi.Uint64TypeSpec()
            ),
            10,
        )
    ),
]


def test_ArrayElement_init():
    dynamicArrayType = pt.abi.DynamicArrayTypeSpec(pt.abi.Uint64TypeSpec())
    array = dynamicArrayType.new_instance()
    index = pt.Int(6)

    element = pt.abi.ArrayElement(array, index)
    assert element.array is array
    assert element.index is index

    with pytest.raises(pt.TealTypeError):
        pt.abi.ArrayElement(array, pt.Bytes("abc"))

    with pytest.raises(pt.TealTypeError):
        pt.abi.ArrayElement(array, pt.Assert(index))


def test_ArrayElement_store_into():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        staticArrayType = pt.abi.StaticArrayTypeSpec(elementType, 100)
        staticArray = staticArrayType.new_instance()
        index = pt.Int(9)

        element = pt.abi.ArrayElement(staticArray, index)
        output = elementType.new_instance()
        expr = element.store_into(output)

        encoded = staticArray.encode()
        stride = pt.Int(staticArray.type_spec()._stride())
        expectedLength = staticArray.length()
        if elementType == pt.abi.BoolTypeSpec():
            expectedExpr = cast(pt.abi.Bool, output).decodeBit(encoded, index)
        elif not elementType.is_dynamic():
            expectedExpr = output.decode(
                encoded, startIndex=stride * index, length=stride
            )
        else:
            expectedExpr = output.decode(
                encoded,
                startIndex=pt.ExtractUint16(encoded, stride * index),
                endIndex=pt.If(index + pt.Int(1) == expectedLength)
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
            element.store_into(pt.abi.Tuple(elementType))

    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = pt.abi.DynamicArrayTypeSpec(elementType)
        dynamicArray = dynamicArrayType.new_instance()
        index = pt.Int(9)

        element = pt.abi.ArrayElement(dynamicArray, index)
        output = elementType.new_instance()
        expr = element.store_into(output)

        encoded = dynamicArray.encode()
        stride = pt.Int(dynamicArray.type_spec()._stride())
        expectedLength = dynamicArray.length()
        if elementType == pt.abi.BoolTypeSpec():
            expectedExpr = cast(pt.abi.Bool, output).decodeBit(
                encoded, index + pt.Int(16)
            )
        elif not elementType.is_dynamic():
            expectedExpr = output.decode(
                encoded, startIndex=stride * index + pt.Int(2), length=stride
            )
        else:
            expectedExpr = output.decode(
                encoded,
                startIndex=pt.ExtractUint16(encoded, stride * index + pt.Int(2))
                + pt.Int(2),
                endIndex=pt.If(index + pt.Int(1) == expectedLength)
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
            element.store_into(pt.abi.Tuple(elementType))
