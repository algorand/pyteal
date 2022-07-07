import pytest

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.util import substringForDecoding
from pyteal.ast.abi.tuple import encodeTuple
from pyteal.ast.abi.bool import boolSequenceLength
from pyteal.ast.abi.type_test import ContainerType
from pyteal.ast.abi.array_base_test import STATIC_TYPES, DYNAMIC_TYPES

options = pt.CompileOptions(version=5)


def test_StaticArrayTypeSpec_init():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            assert staticArrayType.value_type_spec() is elementType
            assert not staticArrayType.is_length_dynamic()
            assert staticArrayType._stride() == elementType.byte_length_static()
            assert staticArrayType.length_static() == length

        with pytest.raises(TypeError):
            abi.StaticArrayTypeSpec(elementType, -1)

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            assert staticArrayType.value_type_spec() is elementType
            assert not staticArrayType.is_length_dynamic()
            assert staticArrayType._stride() == 2
            assert staticArrayType.length_static() == length

        with pytest.raises(TypeError):
            abi.StaticArrayTypeSpec(elementType, -1)


def test_StaticArrayTypeSpec_str():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            assert str(staticArrayType) == "{}[{}]".format(elementType, length)


def test_StaticArrayTypeSpec_new_instance():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            instance = staticArrayType.new_instance()
            assert isinstance(
                instance,
                abi.StaticArray,
            )
            assert instance.type_spec() == staticArrayType


def test_StaticArrayTypeSpec_eq():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            assert staticArrayType == staticArrayType
            assert staticArrayType != abi.StaticArrayTypeSpec(elementType, length + 1)
            assert staticArrayType != abi.StaticArrayTypeSpec(
                abi.TupleTypeSpec(elementType), length
            )


def test_StaticArrayTypeSpec_is_dynamic():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            assert not staticArrayType.is_dynamic()

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            assert staticArrayType.is_dynamic()


def test_StaticArrayTypeSpec_byte_length_static():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            actual = staticArrayType.byte_length_static()

            if elementType == abi.BoolTypeSpec():
                expected = boolSequenceLength(length)
            else:
                expected = elementType.byte_length_static() * length

            assert (
                actual == expected
            ), "failed with element type {} and length {}".format(elementType, length)

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            with pytest.raises(ValueError):
                staticArrayType.byte_length_static()


def test_StaticArray_decode():
    encoded = pt.Bytes("encoded")
    for startIndex in (None, pt.Int(1)):
        for endIndex in (None, pt.Int(2)):
            for length in (None, pt.Int(3)):
                value = abi.StaticArray(
                    abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10)
                )

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


def test_StaticArray_set_values():
    value = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10))

    with pytest.raises(pt.TealInputError):
        value.set([])

    with pytest.raises(pt.TealInputError):
        value.set([abi.Uint64()] * 9)

    with pytest.raises(pt.TealInputError):
        value.set([abi.Uint64()] * 11)

    with pytest.raises(pt.TealInputError):
        value.set([abi.Uint16()] * 10)

    with pytest.raises(pt.TealInputError):
        value.set([abi.Uint64()] * 9 + [abi.Uint16()])

    values = [abi.Uint64() for _ in range(10)]
    expr = value.set(values)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expectedExpr = value.stored_value.store(encodeTuple(values))
    expected, _ = expectedExpr.__teal__(options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_StaticArray_set_copy():
    value = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10))
    otherArray = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10))

    with pytest.raises(pt.TealInputError):
        value.set(abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 11)))

    with pytest.raises(pt.TealInputError):
        value.set(abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint8TypeSpec(), 10)))

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


def test_StaticArray_set_computed():
    value = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10))
    computed = ContainerType(
        value.type_spec(), pt.Bytes("indeed this is hard to simulate")
    )
    expr = value.set(computed)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, '"indeed this is hard to simulate"'),
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
                abi.StaticArrayTypeSpec(abi.Uint16TypeSpec(), 40),
                pt.Bytes("well i am trolling"),
            )
        )


def test_StaticArray_encode():
    value = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10))
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


def test_StaticArray_length():
    for length in (0, 1, 2, 3, 1000):
        value = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), length))
        expr = value.length()
        assert expr.type_of() == pt.TealType.uint64
        assert not expr.has_return()

        expected = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, length)])

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_StaticArray_getitem():
    for length in (0, 1, 2, 3, 1000):
        value = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), length))

        for index in range(length):
            # dynamic indexes
            indexExpr = pt.Int(index)
            element = value[indexExpr]
            assert type(element) is abi.ArrayElement
            assert element.array is value
            assert element.index is indexExpr

        for index in range(length):
            # static indexes
            element = value[index]
            assert type(element) is abi.ArrayElement
            assert element.array is value
            assert type(element.index) is pt.Int
            assert element.index.value == index

        with pytest.raises(pt.TealInputError):
            value[-1]

        with pytest.raises(pt.TealInputError):
            value[length]
