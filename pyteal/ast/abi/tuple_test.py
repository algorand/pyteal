from typing import NamedTuple, List, Callable
import pytest

from ... import *
from .tuple import encodeTuple, indexTuple, TupleElement
from .bool import encodeBoolSequence
from .type import substringForDecoding

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
    uint16_a = abi.Uint16()
    uint16_b = abi.Uint16()
    bool_a = abi.Bool()
    bool_b = abi.Bool()
    tuple_a = abi.Tuple(abi.Bool(), abi.Bool())
    dynamic_array_a = abi.DynamicArray(abi.Uint64())
    dynamic_array_b = abi.DynamicArray(abi.Uint16())
    dynamic_array_c = abi.DynamicArray(abi.Bool())
    tail_holder = ScratchVar()
    encoded_tail = ScratchVar()

    tests: List[EncodeTest] = [
        EncodeTest(types=[], expected=Bytes("")),
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
        EncodeTest(
            types=[dynamic_array_a],
            expected=Concat(
                Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(2),
                    uint16_a.encode(),
                ),
                tail_holder.load(),
            ),
        ),
        EncodeTest(
            types=[uint64_a, dynamic_array_a],
            expected=Concat(
                uint64_a.encode(),
                Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(8 + 2),
                    uint16_a.encode(),
                ),
                tail_holder.load(),
            ),
        ),
        EncodeTest(
            types=[uint64_a, dynamic_array_a, uint64_b],
            expected=Concat(
                uint64_a.encode(),
                Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(8 + 2 + 8),
                    uint16_a.encode(),
                ),
                uint64_b.encode(),
                tail_holder.load(),
            ),
        ),
        EncodeTest(
            types=[uint64_a, dynamic_array_a, bool_a, bool_b],
            expected=Concat(
                uint64_a.encode(),
                Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(8 + 2 + 1),
                    uint16_a.encode(),
                ),
                encodeBoolSequence([bool_a, bool_b]),
                tail_holder.load(),
            ),
        ),
        EncodeTest(
            types=[uint64_a, dynamic_array_a, uint64_b, dynamic_array_b],
            expected=Concat(
                uint64_a.encode(),
                Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(8 + 2 + 8 + 2),
                    uint16_b.set(uint16_a.get() + Len(encoded_tail.load())),
                    uint16_a.encode(),
                ),
                uint64_b.encode(),
                Seq(
                    encoded_tail.store(dynamic_array_b.encode()),
                    tail_holder.store(Concat(tail_holder.load(), encoded_tail.load())),
                    uint16_a.set(uint16_b),
                    uint16_a.encode(),
                ),
                tail_holder.load(),
            ),
        ),
        EncodeTest(
            types=[
                uint64_a,
                dynamic_array_a,
                uint64_b,
                dynamic_array_b,
                bool_a,
                bool_b,
                dynamic_array_c,
            ],
            expected=Concat(
                uint64_a.encode(),
                Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(8 + 2 + 8 + 2 + 1 + 2),
                    uint16_b.set(uint16_a.get() + Len(encoded_tail.load())),
                    uint16_a.encode(),
                ),
                uint64_b.encode(),
                Seq(
                    encoded_tail.store(dynamic_array_b.encode()),
                    tail_holder.store(Concat(tail_holder.load(), encoded_tail.load())),
                    uint16_a.set(uint16_b),
                    uint16_b.set(uint16_a.get() + Len(encoded_tail.load())),
                    uint16_a.encode(),
                ),
                encodeBoolSequence([bool_a, bool_b]),
                Seq(
                    encoded_tail.store(dynamic_array_c.encode()),
                    tail_holder.store(Concat(tail_holder.load(), encoded_tail.load())),
                    uint16_a.set(uint16_b),
                    uint16_a.encode(),
                ),
                tail_holder.load(),
            ),
        ),
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

        if any(t.is_dynamic() for t in test.types):
            with TealComponent.Context.ignoreExprEquality():
                with TealComponent.Context.ignoreScratchSlotEquality():
                    assert actual == expected, "Test at index {} failed".format(i)

            assert TealBlock.MatchScratchSlotReferences(
                TealBlock.GetReferencedScratchSlots(actual),
                TealBlock.GetReferencedScratchSlots(expected),
            )
            continue

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)


def test_indexTuple():
    class IndexTest(NamedTuple):
        types: List[abi.Type]
        typeIndex: int
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
            typeIndex=0,
            expected=lambda output: output.decode(encoded),
        ),
        IndexTest(
            types=[uint64_a, uint64_b],
            typeIndex=0,
            expected=lambda output: output.decode(encoded, length=Int(8)),
        ),
        IndexTest(
            types=[uint64_a, uint64_b],
            typeIndex=1,
            expected=lambda output: output.decode(encoded, startIndex=Int(8)),
        ),
        IndexTest(
            types=[uint64_a, byte_a, uint64_b],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded, startIndex=Int(8), length=Int(1)
            ),
        ),
        IndexTest(
            types=[uint64_a, byte_a, uint64_b],
            typeIndex=2,
            expected=lambda output: output.decode(
                encoded, startIndex=Int(9), length=Int(8)
            ),
        ),
        IndexTest(
            types=[bool_a],
            typeIndex=0,
            expected=lambda output: output.decodeBit(encoded, Int(0)),
        ),
        IndexTest(
            types=[bool_a, bool_b],
            typeIndex=0,
            expected=lambda output: output.decodeBit(encoded, Int(0)),
        ),
        IndexTest(
            types=[bool_a, bool_b],
            typeIndex=1,
            expected=lambda output: output.decodeBit(encoded, Int(1)),
        ),
        IndexTest(
            types=[uint64_a, bool_a],
            typeIndex=1,
            expected=lambda output: output.decodeBit(encoded, Int(8 * 8)),
        ),
        IndexTest(
            types=[uint64_a, bool_a, bool_b],
            typeIndex=1,
            expected=lambda output: output.decodeBit(encoded, Int(8 * 8)),
        ),
        IndexTest(
            types=[uint64_a, bool_a, bool_b],
            typeIndex=2,
            expected=lambda output: output.decodeBit(encoded, Int(8 * 8 + 1)),
        ),
        IndexTest(
            types=[tuple_a], typeIndex=0, expected=lambda output: output.decode(encoded)
        ),
        IndexTest(
            types=[byte_a, tuple_a],
            typeIndex=1,
            expected=lambda output: output.decode(encoded, startIndex=Int(1)),
        ),
        IndexTest(
            types=[tuple_a, byte_a],
            typeIndex=0,
            expected=lambda output: output.decode(
                encoded, startIndex=Int(0), length=Int(tuple_a.byte_length_static())
            ),
        ),
        IndexTest(
            types=[byte_a, tuple_a, byte_a],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded, startIndex=Int(1), length=Int(tuple_a.byte_length_static())
            ),
        ),
        IndexTest(
            types=[dynamic_array_a],
            typeIndex=0,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(0))
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(1))
            ),
        ),
        IndexTest(
            types=[dynamic_array_a, byte_a],
            typeIndex=0,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(0))
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, byte_a],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(1))
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, byte_a, dynamic_array_b],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded,
                startIndex=ExtractUint16(encoded, Int(1)),
                endIndex=ExtractUint16(encoded, Int(4)),
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, byte_a, dynamic_array_b],
            typeIndex=3,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(4))
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, tuple_a, dynamic_array_b],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded,
                startIndex=ExtractUint16(encoded, Int(1)),
                endIndex=ExtractUint16(encoded, Int(4)),
            ),
        ),
        IndexTest(
            types=[byte_a, dynamic_array_a, tuple_a, dynamic_array_b],
            typeIndex=3,
            expected=lambda output: output.decode(
                encoded, startIndex=ExtractUint16(encoded, Int(4))
            ),
        ),
    ]

    for i, test in enumerate(tests):
        output = test.types[test.typeIndex].new_instance()
        expr = indexTuple(test.types, encoded, test.typeIndex, output)
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
    tupleA = abi.Tuple(abi.Uint64(), abi.Uint32(), abi.Bool())
    tupleB = abi.Tuple(abi.Uint64(), abi.Uint32(), abi.Bool())
    tupleC = abi.Tuple(abi.Bool(), abi.Uint64(), abi.Uint32())
    assert tupleA.has_same_type_as(tupleA)
    assert tupleA.has_same_type_as(tupleB)
    assert not tupleA.has_same_type_as(tupleC)


def test_Tuple_new_instance():
    tupleA = abi.Tuple(abi.Uint64(), abi.Uint32(), abi.Bool())
    newTuple = tupleA.new_instance()
    assert type(newTuple) is abi.Tuple
    assert newTuple.valueTypes == tupleA.valueTypes


def test_Tuple_is_dynamic():
    assert not abi.Tuple().is_dynamic()
    assert not abi.Tuple(abi.Uint64(), abi.Uint32(), abi.Bool()).is_dynamic()
    assert abi.Tuple(abi.Uint16(), abi.DynamicArray(abi.Uint8())).is_dynamic()


def test_tuple_str():
    assert str(abi.Tuple()) == "()"
    assert str(abi.Tuple(abi.Tuple())) == "(())"
    assert str(abi.Tuple(abi.Tuple(), abi.Tuple())) == "((),())"
    assert (
        str(abi.Tuple(abi.Uint64(), abi.Uint32(), abi.Bool())) == "(uint64,uint32,bool)"
    )
    assert (
        str(abi.Tuple(abi.Bool(), abi.Uint64(), abi.Uint32())) == "(bool,uint64,uint32)"
    )
    assert (
        str(abi.Tuple(abi.Uint16(), abi.DynamicArray(abi.Uint8())))
        == "(uint16,uint8[])"
    )


def test_Tuple_byte_length_static():
    assert abi.Tuple().byte_length_static() == 0
    assert abi.Tuple(abi.Tuple()).byte_length_static() == 0
    assert abi.Tuple(abi.Tuple(), abi.Tuple()).byte_length_static() == 0
    assert (
        abi.Tuple(abi.Uint64(), abi.Uint32(), abi.Bool()).byte_length_static()
        == 8 + 4 + 1
    )
    assert (
        abi.Tuple(
            abi.Uint64(),
            abi.Uint32(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
        ).byte_length_static()
        == 8 + 4 + 1
    )
    assert (
        abi.Tuple(
            abi.Uint64(),
            abi.Uint32(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
            abi.Bool(),
        ).byte_length_static()
        == 8 + 4 + 2
    )

    with pytest.raises(ValueError):
        abi.Tuple(abi.Uint16(), abi.DynamicArray(abi.Uint8())).byte_length_static()


def test_Tuple_decode():
    tupleType = abi.Tuple()
    for startIndex in (None, Int(1)):
        for endIndex in (None, Int(2)):
            for length in (None, Int(3)):
                encoded = Bytes("encoded")

                if endIndex is not None and length is not None:
                    with pytest.raises(TealInputError):
                        tupleType.decode(
                            encoded,
                            startIndex=startIndex,
                            endIndex=endIndex,
                            length=length,
                        )
                    continue

                expr = tupleType.decode(
                    encoded, startIndex=startIndex, endIndex=endIndex, length=length
                )
                assert expr.type_of() == TealType.none
                assert not expr.has_return()

                expectedExpr = tupleType.stored_value.store(
                    substringForDecoding(
                        encoded, startIndex=startIndex, endIndex=endIndex, length=length
                    )
                )
                expected, _ = expectedExpr.__teal__(options)
                expected.addIncoming()
                expected = TealBlock.NormalizeBlocks(expected)

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = TealBlock.NormalizeBlocks(actual)

                with TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_Tuple_set():
    tupleType = abi.Tuple(abi.Uint8(), abi.Uint16(), abi.Uint32())
    uint8 = abi.Uint8()
    uint16 = abi.Uint16()
    uint32 = abi.Uint32()

    with pytest.raises(TealInputError):
        tupleType.set()

    with pytest.raises(TealInputError):
        tupleType.set(uint8, uint16)

    with pytest.raises(TealInputError):
        tupleType.set(uint8, uint16, uint32, uint32)

    with pytest.raises(TealInputError):
        tupleType.set(uint8, uint32, uint16)

    with pytest.raises(TealInputError):
        tupleType.set(uint8, uint16, uint16)

    expr = tupleType.set(uint8, uint16, uint32)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expectedExpr = tupleType.stored_value.store(encodeTuple([uint8, uint16, uint32]))
    expected, _ = expectedExpr.__teal__(options)
    expected.addIncoming()
    expected = TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Tuple_encode():
    tupleType = abi.Tuple()
    expr = tupleType.encode()
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(None, Op.load, tupleType.stored_value.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Tuple_length_static():
    tests: List[List[abi.Type]] = [
        [],
        [abi.Uint64()],
        [abi.Tuple(abi.Uint64(), abi.Uint64()), abi.Uint64()],
        [abi.Bool()] * 8,
    ]

    for i, test in enumerate(tests):
        tupleType = abi.Tuple(*test)
        actual = tupleType.length_static()
        expected = len(test)
        assert actual == expected, "Test at index {} failed".format(i)


def test_Tuple_length():
    tests: List[List[abi.Type]] = [
        [],
        [abi.Uint64()],
        [abi.Tuple(abi.Uint64(), abi.Uint64()), abi.Uint64()],
        [abi.Bool()] * 8,
    ]

    for i, test in enumerate(tests):
        tupleType = abi.Tuple(*test)
        expr = tupleType.length()
        assert expr.type_of() == TealType.uint64
        assert not expr.has_return()

        expectedLength = len(test)
        expected = TealSimpleBlock([TealOp(None, Op.int, expectedLength)])

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)


def test_Tuple_getitem():
    tests: List[List[abi.Type]] = [
        [],
        [abi.Uint64()],
        [abi.Tuple(abi.Uint64(), abi.Uint64()), abi.Uint64()],
        [abi.Bool()] * 8,
    ]

    for i, test in enumerate(tests):
        tupleType = abi.Tuple(*test)
        for j in range(len(test)):
            element = tupleType[j]
            assert type(element) is TupleElement, "Test at index {} failed".format(i)
            assert element.tuple is tupleType, "Test at index {} failed".format(i)
            assert element.index == j, "Test at index {} failed".format(i)

        with pytest.raises(TealInputError):
            tupleType[-1]

        with pytest.raises(TealInputError):
            tupleType[len(test)]


def test_TupleElement_store_into():
    tests: List[List[abi.Type]] = [
        [],
        [abi.Uint64()],
        [abi.Tuple(abi.Uint64(), abi.Uint64()), abi.Uint64()],
        [abi.Bool()] * 8,
    ]

    for i, test in enumerate(tests):
        tupleType = abi.Tuple(*test)
        for j in range(len(test)):
            element = TupleElement(tupleType, j)
            output = tupleType.valueTypes[j]

            expr = element.store_into(output)
            assert expr.type_of() == TealType.none
            assert not expr.has_return()

            expectedExpr = indexTuple(
                tupleType.valueTypes, tupleType.encode(), j, output
            )
            expected, _ = expectedExpr.__teal__(options)
            expected.addIncoming()
            expected = TealBlock.NormalizeBlocks(expected)

            actual, _ = expr.__teal__(options)
            actual.addIncoming()
            actual = TealBlock.NormalizeBlocks(actual)

            with TealComponent.Context.ignoreExprEquality():
                assert actual == expected, "Test at index {} failed".format(i)
