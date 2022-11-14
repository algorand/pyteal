import pytest
from typing import cast

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.util import substring_for_decoding
from pyteal.ast.abi.tuple import _encode_tuple
from pyteal.ast.abi.bool import _bool_sequence_length
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

    for length in range(256):
        staticBytesType = abi.StaticBytesTypeSpec(length)
        assert isinstance(staticBytesType.value_type_spec(), abi.ByteTypeSpec)
        assert not staticBytesType.is_length_dynamic()
        assert staticBytesType._stride() == 1
        assert staticBytesType.length_static() == length

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

    for length in range(256):
        assert str(abi.StaticBytesTypeSpec(length)) == f"byte[{length}]"


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

    for length in range(256):
        staticBytesType = abi.StaticBytesTypeSpec(length)
        instance = staticBytesType.new_instance()
        assert isinstance(instance, abi.StaticBytes)
        assert instance.type_spec() == staticBytesType


def test_StaticArrayTypeSpec_eq():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            assert staticArrayType == staticArrayType
            assert staticArrayType != abi.StaticArrayTypeSpec(elementType, length + 1)
            assert staticArrayType != abi.StaticArrayTypeSpec(
                abi.TupleTypeSpec(elementType), length
            )

    for length in range(256):
        staticBytesType = abi.StaticBytesTypeSpec(length)
        assert staticBytesType == staticBytesType
        assert staticBytesType != abi.StaticBytesTypeSpec(length + 1)
        assert staticBytesType != abi.StaticArrayTypeSpec(
            abi.TupleTypeSpec(abi.ByteTypeSpec()), length
        )


def test_StaticArrayTypeSpec_is_dynamic():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            assert not staticArrayType.is_dynamic()

    for length in range(256):
        assert not abi.StaticBytesTypeSpec(length).is_dynamic()

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
                expected = _bool_sequence_length(length)
            else:
                expected = elementType.byte_length_static() * length

            assert (
                actual == expected
            ), "failed with element type {} and length {}".format(elementType, length)

    for length in range(256):
        staticBytesType = abi.StaticBytesTypeSpec(length)
        actual = staticBytesType.byte_length_static()
        assert (
            actual == length
        ), f"failed with element type {staticBytesType.value_type_spec()} and length {length}"

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArrayTypeSpec(elementType, length)
            with pytest.raises(ValueError):
                staticArrayType.byte_length_static()


def test_StaticArray_decode():
    encoded = pt.Bytes("encoded")
    for start_index in (None, pt.Int(1)):
        for end_index in (None, pt.Int(2)):
            for length in (None, pt.Int(3)):
                value = abi.StaticArray(
                    abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10)
                )

                if end_index is not None and length is not None:
                    with pytest.raises(pt.TealInputError):
                        value.decode(
                            encoded,
                            start_index=start_index,
                            end_index=end_index,
                            length=length,
                        )
                    continue

                expr = value.decode(
                    encoded, start_index=start_index, end_index=end_index, length=length
                )
                assert expr.type_of() == pt.TealType.none
                assert not expr.has_return()

                expectedExpr = value._stored_value.store(
                    substring_for_decoding(
                        encoded,
                        start_index=start_index,
                        end_index=end_index,
                        length=length,
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

    expectedExpr = value._stored_value.store(_encode_tuple(values))
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
            pt.TealOp(
                None,
                pt.Op.load,
                cast(pt.ScratchVar, otherArray._stored_value).slot,
            ),
            pt.TealOp(
                None,
                pt.Op.store,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
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
            pt.TealOp(
                None,
                pt.Op.store,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
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


# AACS key recovery
BYTE_HEX_TEST_CASE = "09f911029d74e35bd84156c5635688c0"

BYTES_SET_TESTCASES = [
    bytes.fromhex(BYTE_HEX_TEST_CASE),
    bytearray.fromhex(BYTE_HEX_TEST_CASE),
]


@pytest.mark.parametrize("test_case", BYTES_SET_TESTCASES)
def test_StaticBytes_set_py_bytes(test_case: bytes | bytearray):
    value: abi.StaticBytes = abi.StaticBytes(abi.StaticBytesTypeSpec(len(test_case)))

    expr = value.set(test_case)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = actual.NormalizeBlocks(actual)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, "0x" + BYTE_HEX_TEST_CASE),
            pt.TealOp(
                None,
                pt.Op.store,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
        ]
    )

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        value.set(test_case[:-1])


@pytest.mark.parametrize("test_case", BYTES_SET_TESTCASES)
def test_StaticBytes_expr(test_case: bytes | bytearray):
    value: abi.StaticBytes = abi.StaticBytes(
        abi.StaticBytesTypeSpec(len(test_case) * 2)
    )
    set_expr = pt.Concat(pt.Bytes(test_case), pt.Bytes(test_case))

    expr = value.set(set_expr)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = actual.NormalizeBlocks(actual)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, "0x" + BYTE_HEX_TEST_CASE),
            pt.TealOp(None, pt.Op.byte, "0x" + BYTE_HEX_TEST_CASE),
            pt.TealOp(None, pt.Op.concat),
            pt.TealOp(
                None,
                pt.Op.store,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
            pt.TealOp(None, pt.Op.int, 32),
            pt.TealOp(
                None,
                pt.Op.load,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
            pt.TealOp(None, pt.Op.len),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.assert_),
        ]
    )

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_StaticArray_encode():
    value = abi.StaticArray(abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 10))
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(
                None,
                pt.Op.load,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
        ]
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
