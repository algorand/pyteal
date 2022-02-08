from typing import NamedTuple, List, Callable
import pytest

from ... import *
from .tuple import encodeTuple, indexTuple
from .bool import encodeBoolSequence

# this is not necessary but mypy complains if it's not included
from ... import CompileOptions

options = CompileOptions(version=5)


def test_encodeTuple():
    class EncodeTest(NamedTuple):
        types: List[abi.Type]
        expected: Expr

    # variables used to construct the tests
    uint64_a = abi.Uint64()
    uint64_b = abi.Uint64()
    bool_a = abi.Bool()
    bool_b = abi.Bool()
    tuple_a = abi.Tuple(abi.Bool(), abi.Bool())

    tests: List[EncodeTest] = [
        EncodeTest(types=[uint64_a], expected=uint64_a.encode()),
        EncodeTest(
            types=[uint64_a, uint64_b],
            expected=Concat(uint64_a.encode(), uint64_b.encode()),
        ),
        EncodeTest(types=[bool_a], expected=bool_a.encode()),
        EncodeTest(
            types=[bool_a, bool_b], expected=encodeBoolSequence([bool_a, bool_b])
        ),
        EncodeTest(
            types=[bool_a, bool_b, uint64_a],
            expected=Concat(encodeBoolSequence([bool_a, bool_b]), uint64_a.encode()),
        ),
        EncodeTest(
            types=[uint64_a, bool_a, bool_b],
            expected=Concat(uint64_a.encode(), encodeBoolSequence([bool_a, bool_b])),
        ),
        EncodeTest(
            types=[uint64_a, bool_a, bool_b, uint64_b],
            expected=Concat(
                uint64_a.encode(),
                encodeBoolSequence([bool_a, bool_b]),
                uint64_b.encode(),
            ),
        ),
        EncodeTest(
            types=[uint64_a, bool_a, uint64_b, bool_b],
            expected=Concat(
                uint64_a.encode(), bool_a.encode(), uint64_b.encode(), bool_b.encode()
            ),
        ),
        EncodeTest(types=[tuple_a], expected=tuple_a.encode()),
        EncodeTest(
            types=[uint64_a, tuple_a, bool_a, bool_b],
            expected=Concat(
                uint64_a.encode(),
                tuple_a.encode(),
                encodeBoolSequence([bool_a, bool_b]),
            ),
        ),
        # TODO: test encoding dynamic types. This is more complicated because temporary abi.Uint16s
        # and ScratchVars are created in the function to help with encoding, meaning a direct
        # comparison is not currently possible.
    ]

    for i, test in enumerate(tests):
        expr = encodeTuple(test.types)
        assert expr.type_of() == TealType.bytes
        assert not expr.has_return()

        expected, _ = test.expected.__teal__(options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)

    with pytest.raises(TealInputError):
        encodeTuple([])


def test_indexTuple():
    class IndexTest(NamedTuple):
        types: List[abi.Type]
        index: int
        expected: Callable[[abi.Type], Expr]

    # variables used to construct the tests
    uint64_a = abi.Uint64()
    uint64_b = abi.Uint64()
    byte_a = abi.Byte()
    bool_a = abi.Bool()
    bool_b = abi.Bool()
    tuple_a = abi.Tuple(abi.Bool(), abi.Bool())
    dynamic_array_a = abi.DynamicArray(abi.Uint64())
    dynamic_array_b = abi.DynamicArray(abi.Uint16())

    encoded = Bytes("encoded")

    tests: List[IndexTest] = [
        IndexTest(
            types=[uint64_a],
            index=0,
            expected=lambda output: output.decode(encoded, startIndex=Int(0)),
        ),
        IndexTest(
            types=[uint64_a, uint64_b],
            index=0,
            expected=lambda output: output.decode(encoded, startIndex=Int(0)),
        ),
        IndexTest(
            types=[uint64_a, uint64_b],
            index=1,
            expected=lambda output: output.decode(encoded, startIndex=Int(8)),
        ),
        IndexTest(
            types=[uint64_a, byte_a, uint64_b],
            index=1,
            expected=lambda output: output.decode(encoded, startIndex=Int(8)),
        ),
        IndexTest(
            types=[uint64_a, byte_a, uint64_b],
            index=2,
            expected=lambda output: output.decode(encoded, startIndex=Int(9)),
        ),
        IndexTest(
            types=[bool_a],
            index=0,
            expected=lambda output: output.decodeBit(encoded, Int(0)),
        ),
        IndexTest(
            types=[bool_a, bool_b],
            index=0,
            expected=lambda output: output.decodeBit(encoded, Int(0)),
        ),
        IndexTest(
            types=[bool_a, bool_b],
            index=1,
            expected=lambda output: output.decodeBit(encoded, Int(1)),
        ),
        IndexTest(
            types=[uint64_a, bool_a],
            index=1,
            expected=lambda output: output.decodeBit(encoded, Int(8 * 8)),
        ),
        IndexTest(
            types=[uint64_a, bool_a, bool_b],
            index=1,
            expected=lambda output: output.decodeBit(encoded, Int(8 * 8)),
        ),
        IndexTest(
            types=[uint64_a, bool_a, bool_b],
            index=2,
            expected=lambda output: output.decodeBit(encoded, Int(8 * 8 + 1)),
        ),
        IndexTest(
            types=[tuple_a], index=0, expected=lambda output: output.decode(encoded)
        ),
        IndexTest(
            types=[byte_a, tuple_a],
            index=1,
            expected=lambda output: output.decode(encoded, startIndex=Int(1)),
        ),
        IndexTest(
            types=[tuple_a, byte_a],
            index=0,
            expected=lambda output: output.decode(
                encoded, startIndex=Int(0), length=Int(tuple_a.byte_length_static())
            ),
        ),
        IndexTest(
            types=[byte_a, tuple_a, byte_a],
            index=1,
            expected=lambda output: output.decode(
                encoded, startIndex=Int(1), length=Int(tuple_a.byte_length_static())
            ),
        ),
        IndexTest(
            types=[dynamic_array_a],
            index=0,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(0))
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a],
            index=1,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(1))
            ),
        ),
        IndexTest(
            types=[dynamic_array_a, byte_a],
            index=0,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(0))
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, byte_a],
            index=1,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(1))
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, byte_a, dynamic_array_b],
            index=1,
            expected=lambda output: output.decode(
                encoded,
                startIndex=ExtractUint16(encoded, Int(1)),
                endIndex=ExtractUint16(encoded, Int(4)),
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, byte_a, dynamic_array_b],
            index=3,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(4))
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, tuple_a, dynamic_array_b],
            index=1,
            expected=lambda output: output.decode(
                encoded,
                startIndex=ExtractUint16(encoded, Int(1)),
                endIndex=ExtractUint16(encoded, Int(4)),
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, tuple_a, dynamic_array_b],
            index=3,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(4))
            ),
        ),
    ]

    for i, test in enumerate(tests):
        output = test.types[test.index].new_instance()
        expr = indexTuple(test.types, encoded, test.index, output)
        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        expected, _ = test.expected(output).__teal__(options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)

        with pytest.raises(ValueError):
            indexTuple(test.types, encoded, len(test.types), output)

        with pytest.raises(ValueError):
            indexTuple(test.types, encoded, -1, output)

        otherType = abi.Uint64
        if output.has_same_type_as(otherType):
            otherType = abi.Uint16
        with pytest.raises(TypeError):
            indexTuple(test.types, encoded, test.types, otherType)


def test_Tuple_has_same_type_as():
    pass


def test_Tuple_new_instance():
    pass


def test_Tuple_is_dynamic():
    pass


def test_tuple_str():
    pass


def test_Tuple_byte_length_static():
    pass


def test_Tuple_decode():
    pass


def test_Tuple_set():
    pass


def test_Tuple_encode():
    pass


def test_Tuple_length_static():
    pass


def test_Tuple_length():
    pass


def test_Tuple_getitem():
    pass


def test_TupleElement_store_into():
    pass
