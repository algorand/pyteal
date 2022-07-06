from typing import List
import pytest

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.util import substringForDecoding
from pyteal.ast.abi.tuple import encodeTuple
from pyteal.ast.abi.array_base_test import STATIC_TYPES, DYNAMIC_TYPES
from pyteal.ast.abi.type_test import ContainerType

options = pt.CompileOptions(version=5)


def test_DynamicArrayTypeSpec_init():
    for elementType in STATIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        assert dynamicArrayType.value_type_spec() is elementType
        assert dynamicArrayType.is_length_dynamic()
        assert dynamicArrayType._stride() == elementType.byte_length_static()

    for elementType in DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        assert dynamicArrayType.value_type_spec() is elementType
        assert dynamicArrayType.is_length_dynamic()
        assert dynamicArrayType._stride() == 2


def test_DynamicArrayTypeSpec_str():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        assert str(dynamicArrayType) == "{}[]".format(elementType)


def test_DynamicArrayTypeSpec_new_instance():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        instance = dynamicArrayType.new_instance()
        assert isinstance(instance, abi.DynamicArray)
        assert instance.type_spec() == dynamicArrayType


def test_DynamicArrayTypeSpec_eq():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        assert dynamicArrayType == dynamicArrayType
        assert dynamicArrayType != abi.TupleTypeSpec(dynamicArrayType)


def test_DynamicArrayTypeSpec_is_dynamic():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        assert dynamicArrayType.is_dynamic()


def test_DynamicArrayTypeSpec_byte_length_static():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArrayTypeSpec(elementType)
        with pytest.raises(ValueError):
            dynamicArrayType.byte_length_static()


def test_DynamicArray_decode():
    encoded = pt.Bytes("encoded")
    dynamicArrayType = abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec())
    for startIndex in (None, pt.Int(1)):
        for endIndex in (None, pt.Int(2)):
            for length in (None, pt.Int(3)):
                value = dynamicArrayType.new_instance()

                if endIndex is not None and length is not None:
                    with pytest.raises(pt.TealInputError):
                        value.decode(
                            encoded,
                            start_index=startIndex,
                            end_index=endIndex,
                            length=length,
                        )
                    continue

                expr = value.decode(
                    encoded, start_index=startIndex, end_index=endIndex, length=length
                )
                assert expr.type_of() == pt.TealType.none
                assert not expr.has_return()

                expectedExpr = value.stored_value.store(
                    substringForDecoding(
                        encoded, startIndex=startIndex, endIndex=endIndex, length=length
                    )
                )
                expected, _ = expectedExpr.__teal__(options)
                expected.addIncoming()
                expected = pt.TealBlock.NormalizeBlocks(expected)

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = pt.TealBlock.NormalizeBlocks(actual)

                with pt.TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_DynamicArray_set_values():
    valuesToSet: List[abi.Uint64] = [
        [],
        [abi.Uint64()],
        [abi.Uint64() for _ in range(10)],
    ]

    dynamicArrayType = abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec())
    for values in valuesToSet:
        value = dynamicArrayType.new_instance()
        expr = value.set(values)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        length_tmp = abi.Uint16()
        expectedExpr = value.stored_value.store(
            pt.Concat(
                pt.Seq(length_tmp.set(len(values)), length_tmp.encode()),
                encodeTuple(values),
            )
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


def test_DynamicArray_set_copy():
    dynamicArrayType = abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec())
    value = dynamicArrayType.new_instance()
    otherArray = dynamicArrayType.new_instance()

    with pytest.raises(pt.TealInputError):
        value.set(abi.DynamicArray(abi.DynamicArrayTypeSpec(abi.Uint8TypeSpec())))

    with pytest.raises(pt.TealInputError):
        value.set(abi.Uint64())

    expr = value.set(otherArray)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.load, otherArray.stored_value.slot),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_DynamicArray_set_computed():
    value = abi.DynamicArray(abi.DynamicArrayTypeSpec(abi.ByteTypeSpec()))
    computed = ContainerType(
        value.type_spec(), pt.Bytes("this should be a dynamic array")
    )
    expr = value.set(computed)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, '"this should be a dynamic array"'),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = actual.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        value.set(
            ContainerType(
                abi.DynamicArrayTypeSpec(abi.Uint16TypeSpec()),
                pt.Bytes("well i am trolling again"),
            )
        )


def test_DynamicArray_encode():
    dynamicArrayType = abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec())
    value = dynamicArrayType.new_instance()
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.load, value.stored_value.slot)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_DynamicArray_length():
    dynamicArrayType = abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec())
    value = dynamicArrayType.new_instance()
    expr = value.length()
    assert expr.type_of() == pt.TealType.uint64
    assert not expr.has_return()

    length_tmp = abi.Uint16()
    expectedExpr = pt.Seq(length_tmp.decode(value.encode()), length_tmp.get())
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


def test_DynamicArray_getitem():
    dynamicArrayType = abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec())
    value = dynamicArrayType.new_instance()

    for index in (0, 1, 2, 3, 1000):
        # dynamic indexes
        indexExpr = pt.Int(index)
        element = value[indexExpr]
        assert type(element) is abi.ArrayElement
        assert element.array is value
        assert element.index is indexExpr

    for index in (0, 1, 2, 3, 1000):
        # static indexes
        element = value[index]
        assert type(element) is abi.ArrayElement
        assert element.array is value
        assert type(element.index) is pt.Int
        assert element.index.value == index

    with pytest.raises(pt.TealInputError):
        value[-1]
