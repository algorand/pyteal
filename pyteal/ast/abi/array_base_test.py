from typing import List, cast
import pytest

from ... import *

options = CompileOptions(version=5)

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
    index = Int(6)

    element = abi.ArrayElement(array, index)
    assert element.array is array
    assert element.index is index

    with pytest.raises(TealTypeError):
        abi.ArrayElement(array, Bytes("abc"))

    with pytest.raises(TealTypeError):
        abi.ArrayElement(array, Assert(index))


def test_ArrayElement_store_into():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        staticArrayType = abi.StaticArrayTypeSpec(elementType, 100)
        staticArray = staticArrayType.new_instance()
        index = Int(9)

        element = abi.ArrayElement(staticArray, index)
        output = elementType.new_instance()
        expr = element.store_into(output)

        encoded = staticArray.encode()
        stride = Int(staticArray.type_spec()._stride())
        expectedLength = staticArray.length()
        if elementType == abi.BoolTypeSpec():
            expectedExpr = cast(abi.Bool, output).decodeBit(encoded, index)
        elif not elementType.is_dynamic():
            expectedExpr = output.decode(
                encoded, startIndex=stride * index, length=stride
            )
        else:
            expectedExpr = output.decode(
                encoded,
                startIndex=ExtractUint16(encoded, stride * index),
                endIndex=If(index + Int(1) == expectedLength)
                .Then(Len(encoded))
                .Else(ExtractUint16(encoded, stride * index + Int(2))),
            )

        expected, _ = expectedExpr.__teal__(options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        with pytest.raises(TealInputError):
            element.store_into(abi.Tuple(elementType))

    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        dynamicArray = dynamicArrayType.new_instance()
        index = Int(9)

        element = abi.ArrayElement(dynamicArray, index)
        output = elementType.new_instance()
        expr = element.store_into(output)

        encoded = dynamicArray.encode()
        stride = Int(dynamicArray.type_spec()._stride())
        expectedLength = dynamicArray.length()
        if elementType == abi.BoolTypeSpec():
            expectedExpr = cast(abi.Bool, output).decodeBit(encoded, index + Int(16))
        elif not elementType.is_dynamic():
            expectedExpr = output.decode(
                encoded, startIndex=stride * index + Int(2), length=stride
            )
        else:
            expectedExpr = output.decode(
                encoded,
                startIndex=ExtractUint16(encoded, stride * index + Int(2)) + Int(2),
                endIndex=If(index + Int(1) == expectedLength)
                .Then(Len(encoded))
                .Else(
                    ExtractUint16(encoded, stride * index + Int(2) + Int(2)) + Int(2)
                ),
            )

        expected, _ = expectedExpr.__teal__(options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            with TealComponent.Context.ignoreScratchSlotEquality():
                assert actual == expected

        assert TealBlock.MatchScratchSlotReferences(
            TealBlock.GetReferencedScratchSlots(actual),
            TealBlock.GetReferencedScratchSlots(expected),
        )

        with pytest.raises(TealInputError):
            element.store_into(abi.Tuple(elementType))
