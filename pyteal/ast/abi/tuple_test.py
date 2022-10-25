from typing import NamedTuple, List, Callable, Literal
import pytest

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.tuple import _encode_tuple, _index_tuple, TupleElement
from pyteal.ast.abi.bool import _encode_bool_sequence
from pyteal.ast.abi.util import substring_for_decoding
from pyteal.ast.abi.type_test import ContainerType

options = pt.CompileOptions(version=5)


def test_encodeTuple():
    class EncodeTest(NamedTuple):
        types: List[abi.BaseType]
        expected: pt.Expr

    # variables used to construct the tests
    uint64_a = abi.Uint64()
    uint64_b = abi.Uint64()
    uint16_a = abi.Uint16()
    uint16_b = abi.Uint16()
    bool_a = abi.Bool()
    bool_b = abi.Bool()
    tuple_a = abi.Tuple(abi.TupleTypeSpec(abi.BoolTypeSpec(), abi.BoolTypeSpec()))
    dynamic_array_a = abi.DynamicArray(abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec()))
    dynamic_array_b = abi.DynamicArray(abi.DynamicArrayTypeSpec(abi.Uint16TypeSpec()))
    dynamic_array_c = abi.DynamicArray(abi.DynamicArrayTypeSpec(abi.BoolTypeSpec()))
    tail_holder = pt.ScratchVar()
    encoded_tail = pt.ScratchVar()

    tests: List[EncodeTest] = [
        EncodeTest(types=[], expected=pt.Bytes("")),
        EncodeTest(types=[uint64_a], expected=uint64_a.encode()),
        EncodeTest(
            types=[uint64_a, uint64_b],
            expected=pt.Concat(uint64_a.encode(), uint64_b.encode()),
        ),
        EncodeTest(types=[bool_a], expected=bool_a.encode()),
        EncodeTest(
            types=[bool_a, bool_b], expected=_encode_bool_sequence([bool_a, bool_b])
        ),
        EncodeTest(
            types=[bool_a, bool_b, uint64_a],
            expected=pt.Concat(
                _encode_bool_sequence([bool_a, bool_b]), uint64_a.encode()
            ),
        ),
        EncodeTest(
            types=[uint64_a, bool_a, bool_b],
            expected=pt.Concat(
                uint64_a.encode(), _encode_bool_sequence([bool_a, bool_b])
            ),
        ),
        EncodeTest(
            types=[uint64_a, bool_a, bool_b, uint64_b],
            expected=pt.Concat(
                uint64_a.encode(),
                _encode_bool_sequence([bool_a, bool_b]),
                uint64_b.encode(),
            ),
        ),
        EncodeTest(
            types=[uint64_a, bool_a, uint64_b, bool_b],
            expected=pt.Concat(
                uint64_a.encode(), bool_a.encode(), uint64_b.encode(), bool_b.encode()
            ),
        ),
        EncodeTest(types=[tuple_a], expected=tuple_a.encode()),
        EncodeTest(
            types=[uint64_a, tuple_a, bool_a, bool_b],
            expected=pt.Concat(
                uint64_a.encode(),
                tuple_a.encode(),
                _encode_bool_sequence([bool_a, bool_b]),
            ),
        ),
        EncodeTest(
            types=[dynamic_array_a],
            expected=pt.Concat(
                pt.Seq(
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
            expected=pt.Concat(
                uint64_a.encode(),
                pt.Seq(
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
            expected=pt.Concat(
                uint64_a.encode(),
                pt.Seq(
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
            expected=pt.Concat(
                uint64_a.encode(),
                pt.Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(8 + 2 + 1),
                    uint16_a.encode(),
                ),
                _encode_bool_sequence([bool_a, bool_b]),
                tail_holder.load(),
            ),
        ),
        EncodeTest(
            types=[uint64_a, dynamic_array_a, uint64_b, dynamic_array_b],
            expected=pt.Concat(
                uint64_a.encode(),
                pt.Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(8 + 2 + 8 + 2),
                    uint16_b.set(uint16_a.get() + pt.Len(encoded_tail.load())),
                    uint16_a.encode(),
                ),
                uint64_b.encode(),
                pt.Seq(
                    encoded_tail.store(dynamic_array_b.encode()),
                    tail_holder.store(
                        pt.Concat(tail_holder.load(), encoded_tail.load())
                    ),
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
            expected=pt.Concat(
                uint64_a.encode(),
                pt.Seq(
                    encoded_tail.store(dynamic_array_a.encode()),
                    tail_holder.store(encoded_tail.load()),
                    uint16_a.set(8 + 2 + 8 + 2 + 1 + 2),
                    uint16_b.set(uint16_a.get() + pt.Len(encoded_tail.load())),
                    uint16_a.encode(),
                ),
                uint64_b.encode(),
                pt.Seq(
                    encoded_tail.store(dynamic_array_b.encode()),
                    tail_holder.store(
                        pt.Concat(tail_holder.load(), encoded_tail.load())
                    ),
                    uint16_a.set(uint16_b),
                    uint16_b.set(uint16_a.get() + pt.Len(encoded_tail.load())),
                    uint16_a.encode(),
                ),
                _encode_bool_sequence([bool_a, bool_b]),
                pt.Seq(
                    encoded_tail.store(dynamic_array_c.encode()),
                    tail_holder.store(
                        pt.Concat(tail_holder.load(), encoded_tail.load())
                    ),
                    uint16_a.set(uint16_b),
                    uint16_a.encode(),
                ),
                tail_holder.load(),
            ),
        ),
    ]

    for i, test in enumerate(tests):
        expr = _encode_tuple(test.types)
        assert expr.type_of() == pt.TealType.bytes
        assert not expr.has_return()

        expected, _ = test.expected.__teal__(options)
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        if any(t.type_spec().is_dynamic() for t in test.types):
            with pt.TealComponent.Context.ignoreExprEquality():
                with pt.TealComponent.Context.ignoreScratchSlotEquality():
                    assert actual == expected, "Test at index {} failed".format(i)

            assert pt.TealBlock.MatchScratchSlotReferences(
                pt.TealBlock.GetReferencedScratchSlots(actual),
                pt.TealBlock.GetReferencedScratchSlots(expected),
            )
            continue

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)


def test_indexTuple():
    class IndexTest(NamedTuple):
        types: List[abi.TypeSpec]
        typeIndex: int
        expected: Callable[[abi.BaseType], pt.Expr]

    # variables used to construct the tests
    uint64_t = abi.Uint64TypeSpec()
    byte_t = abi.ByteTypeSpec()
    bool_t = abi.BoolTypeSpec()
    tuple_t = abi.TupleTypeSpec(abi.BoolTypeSpec(), abi.BoolTypeSpec())
    dynamic_array_t1 = abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec())
    dynamic_array_t2 = abi.DynamicArrayTypeSpec(abi.Uint16TypeSpec())

    encoded = pt.Bytes("encoded")

    tests: List[IndexTest] = [
        IndexTest(
            types=[uint64_t],
            typeIndex=0,
            expected=lambda output: output.decode(encoded),
        ),
        IndexTest(
            types=[uint64_t, uint64_t],
            typeIndex=0,
            expected=lambda output: output.decode(encoded, length=pt.Int(8)),
        ),
        IndexTest(
            types=[uint64_t, uint64_t],
            typeIndex=1,
            expected=lambda output: output.decode(encoded, start_index=pt.Int(8)),
        ),
        IndexTest(
            types=[uint64_t, byte_t, uint64_t],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded, start_index=pt.Int(8), length=pt.Int(1)
            ),
        ),
        IndexTest(
            types=[uint64_t, byte_t, uint64_t],
            typeIndex=2,
            expected=lambda output: output.decode(
                encoded, start_index=pt.Int(9), length=pt.Int(8)
            ),
        ),
        IndexTest(
            types=[bool_t],
            typeIndex=0,
            expected=lambda output: output.decode_bit(encoded, pt.Int(0)),
        ),
        IndexTest(
            types=[bool_t, bool_t],
            typeIndex=0,
            expected=lambda output: output.decode_bit(encoded, pt.Int(0)),
        ),
        IndexTest(
            types=[bool_t, bool_t],
            typeIndex=1,
            expected=lambda output: output.decode_bit(encoded, pt.Int(1)),
        ),
        IndexTest(
            types=[uint64_t, bool_t],
            typeIndex=1,
            expected=lambda output: output.decode_bit(encoded, pt.Int(8 * 8)),
        ),
        IndexTest(
            types=[uint64_t, bool_t, bool_t],
            typeIndex=1,
            expected=lambda output: output.decode_bit(encoded, pt.Int(8 * 8)),
        ),
        IndexTest(
            types=[uint64_t, bool_t, bool_t],
            typeIndex=2,
            expected=lambda output: output.decode_bit(encoded, pt.Int(8 * 8 + 1)),
        ),
        IndexTest(
            types=[bool_t, uint64_t],
            typeIndex=0,
            expected=lambda output: output.decode_bit(encoded, pt.Int(0)),
        ),
        IndexTest(
            types=[bool_t, uint64_t],
            typeIndex=1,
            expected=lambda output: output.decode(encoded, start_index=pt.Int(1)),
        ),
        IndexTest(
            types=[bool_t, bool_t, uint64_t],
            typeIndex=0,
            expected=lambda output: output.decode_bit(encoded, pt.Int(0)),
        ),
        IndexTest(
            types=[bool_t, bool_t, uint64_t],
            typeIndex=1,
            expected=lambda output: output.decode_bit(encoded, pt.Int(1)),
        ),
        IndexTest(
            types=[bool_t, bool_t, uint64_t],
            typeIndex=2,
            expected=lambda output: output.decode(encoded, start_index=pt.Int(1)),
        ),
        IndexTest(
            types=[tuple_t], typeIndex=0, expected=lambda output: output.decode(encoded)
        ),
        IndexTest(
            types=[byte_t, tuple_t],
            typeIndex=1,
            expected=lambda output: output.decode(encoded, start_index=pt.Int(1)),
        ),
        IndexTest(
            types=[tuple_t, byte_t],
            typeIndex=0,
            expected=lambda output: output.decode(
                encoded,
                start_index=pt.Int(0),
                length=pt.Int(tuple_t.byte_length_static()),
            ),
        ),
        IndexTest(
            types=[byte_t, tuple_t, byte_t],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded,
                start_index=pt.Int(1),
                length=pt.Int(tuple_t.byte_length_static()),
            ),
        ),
        IndexTest(
            types=[dynamic_array_t1],
            typeIndex=0,
            expected=lambda output: output.decode(
                encoded, start_index=pt.ExtractUint16(encoded, pt.Int(0))
            ),
        ),
        IndexTest(
            types=[byte_t, dynamic_array_t1],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded, start_index=pt.ExtractUint16(encoded, pt.Int(1))
            ),
        ),
        IndexTest(
            types=[dynamic_array_t1, byte_t],
            typeIndex=0,
            expected=lambda output: output.decode(
                encoded, start_index=pt.ExtractUint16(encoded, pt.Int(0))
            ),
        ),
        IndexTest(
            types=[byte_t, dynamic_array_t1, byte_t],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded, start_index=pt.ExtractUint16(encoded, pt.Int(1))
            ),
        ),
        IndexTest(
            types=[byte_t, dynamic_array_t1, byte_t, dynamic_array_t2],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded,
                start_index=pt.ExtractUint16(encoded, pt.Int(1)),
                end_index=pt.ExtractUint16(encoded, pt.Int(4)),
            ),
        ),
        IndexTest(
            types=[byte_t, dynamic_array_t1, byte_t, dynamic_array_t2],
            typeIndex=3,
            expected=lambda output: output.decode(
                encoded, start_index=pt.ExtractUint16(encoded, pt.Int(4))
            ),
        ),
        IndexTest(
            types=[byte_t, dynamic_array_t1, tuple_t, dynamic_array_t2],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded,
                start_index=pt.ExtractUint16(encoded, pt.Int(1)),
                end_index=pt.ExtractUint16(encoded, pt.Int(4)),
            ),
        ),
        IndexTest(
            types=[byte_t, dynamic_array_t1, tuple_t, dynamic_array_t2],
            typeIndex=3,
            expected=lambda output: output.decode(
                encoded, start_index=pt.ExtractUint16(encoded, pt.Int(4))
            ),
        ),
        IndexTest(
            types=[byte_t, dynamic_array_t2, bool_t, bool_t, dynamic_array_t2],
            typeIndex=1,
            expected=lambda output: output.decode(
                encoded,
                start_index=pt.ExtractUint16(encoded, pt.Int(1)),
                end_index=pt.ExtractUint16(encoded, pt.Int(4)),
            ),
        ),
        IndexTest(
            types=[byte_t, dynamic_array_t1, bool_t, bool_t, dynamic_array_t2],
            typeIndex=4,
            expected=lambda output: output.decode(
                encoded, start_index=pt.ExtractUint16(encoded, pt.Int(4))
            ),
        ),
    ]

    for i, test in enumerate(tests):
        output = test.types[test.typeIndex].new_instance()
        expr = _index_tuple(test.types, encoded, test.typeIndex, output)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected, _ = test.expected(output).__teal__(options)
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)

        with pytest.raises(ValueError):
            _index_tuple(test.types, encoded, len(test.types), output)

        with pytest.raises(ValueError):
            _index_tuple(test.types, encoded, -1, output)

        otherType = abi.Uint64()
        if output.type_spec() == otherType.type_spec():
            otherType = abi.Uint16()

        with pytest.raises(TypeError):
            _index_tuple(test.types, encoded, test.typeIndex, otherType)


def test_TupleTypeSpec_eq():
    tupleA = abi.TupleTypeSpec(
        abi.Uint64TypeSpec(), abi.Uint32TypeSpec(), abi.BoolTypeSpec()
    )
    tupleB = abi.TupleTypeSpec(
        abi.Uint64TypeSpec(), abi.Uint32TypeSpec(), abi.BoolTypeSpec()
    )
    tupleC = abi.TupleTypeSpec(
        abi.BoolTypeSpec(), abi.Uint64TypeSpec(), abi.Uint32TypeSpec()
    )
    assert tupleA == tupleA
    assert tupleA == tupleB
    assert tupleA != tupleC


def test_TupleTypeSpec_value_type_specs():
    assert abi.TupleTypeSpec(
        abi.Uint64TypeSpec(), abi.Uint32TypeSpec(), abi.BoolTypeSpec()
    ).value_type_specs() == [
        abi.Uint64TypeSpec(),
        abi.Uint32TypeSpec(),
        abi.BoolTypeSpec(),
    ]


def test_TupleTypeSpec_length_static():
    tests: List[List[abi.TypeSpec]] = [
        [],
        [abi.Uint64TypeSpec()],
        [
            abi.TupleTypeSpec(abi.Uint64TypeSpec(), abi.Uint64TypeSpec()),
            abi.Uint64TypeSpec(),
        ],
        [abi.BoolTypeSpec()] * 8,
    ]

    for i, test in enumerate(tests):
        actual = abi.TupleTypeSpec(*test).length_static()
        expected = len(test)
        assert actual == expected, "Test at index {} failed".format(i)


def test_TupleTypeSpec_new_instance():
    assert isinstance(
        abi.TupleTypeSpec(
            abi.Uint64TypeSpec(), abi.Uint32TypeSpec(), abi.BoolTypeSpec()
        ).new_instance(),
        abi.Tuple,
    )


def test_TupleTypeSpec_is_dynamic():
    assert not abi.TupleTypeSpec().is_dynamic()
    assert not abi.TupleTypeSpec(
        abi.Uint64TypeSpec(), abi.Uint32TypeSpec(), abi.BoolTypeSpec()
    ).is_dynamic()
    assert abi.TupleTypeSpec(
        abi.Uint16TypeSpec(), abi.DynamicArrayTypeSpec(abi.Uint8TypeSpec())
    ).is_dynamic()


def test_TupleTypeSpec_str():
    assert str(abi.TupleTypeSpec()) == "()"
    assert str(abi.TupleTypeSpec(abi.TupleTypeSpec())) == "(())"
    assert str(abi.TupleTypeSpec(abi.TupleTypeSpec(), abi.TupleTypeSpec())) == "((),())"
    assert (
        str(
            abi.TupleTypeSpec(
                abi.Uint64TypeSpec(), abi.Uint32TypeSpec(), abi.BoolTypeSpec()
            )
        )
        == "(uint64,uint32,bool)"
    )
    assert (
        str(
            abi.TupleTypeSpec(
                abi.BoolTypeSpec(), abi.Uint64TypeSpec(), abi.Uint32TypeSpec()
            )
        )
        == "(bool,uint64,uint32)"
    )
    assert (
        str(
            abi.TupleTypeSpec(
                abi.Uint16TypeSpec(), abi.DynamicArrayTypeSpec(abi.Uint8TypeSpec())
            )
        )
        == "(uint16,uint8[])"
    )


def test_TupleTypeSpec_byte_length_static():
    assert abi.TupleTypeSpec().byte_length_static() == 0
    assert abi.TupleTypeSpec(abi.TupleTypeSpec()).byte_length_static() == 0
    assert (
        abi.TupleTypeSpec(abi.TupleTypeSpec(), abi.TupleTypeSpec()).byte_length_static()
        == 0
    )
    assert (
        abi.TupleTypeSpec(
            abi.Uint64TypeSpec(), abi.Uint32TypeSpec(), abi.BoolTypeSpec()
        ).byte_length_static()
        == 8 + 4 + 1
    )
    assert (
        abi.TupleTypeSpec(
            abi.Uint64TypeSpec(),
            abi.Uint32TypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
        ).byte_length_static()
        == 8 + 4 + 1
    )
    assert (
        abi.TupleTypeSpec(
            abi.Uint64TypeSpec(),
            abi.Uint32TypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
            abi.BoolTypeSpec(),
        ).byte_length_static()
        == 8 + 4 + 2
    )

    with pytest.raises(ValueError):
        abi.TupleTypeSpec(
            abi.Uint16TypeSpec(), abi.DynamicArrayTypeSpec(abi.Uint8TypeSpec())
        ).byte_length_static()


def test_Tuple_decode():
    encoded = pt.Bytes("encoded")
    tupleValue = abi.Tuple(abi.TupleTypeSpec(abi.Uint64TypeSpec()))
    for start_index in (None, pt.Int(1)):
        for end_index in (None, pt.Int(2)):
            for length in (None, pt.Int(3)):
                if end_index is not None and length is not None:
                    with pytest.raises(pt.TealInputError):
                        tupleValue.decode(
                            encoded,
                            start_index=start_index,
                            end_index=end_index,
                            length=length,
                        )
                    continue

                expr = tupleValue.decode(
                    encoded, start_index=start_index, end_index=end_index, length=length
                )
                assert expr.type_of() == pt.TealType.none
                assert not expr.has_return()

                expectedExpr = tupleValue.stored_value.store(
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


def test_Tuple_set():
    tupleValue = abi.Tuple(
        abi.TupleTypeSpec(
            abi.Uint8TypeSpec(), abi.Uint16TypeSpec(), abi.Uint32TypeSpec()
        )
    )
    uint8 = abi.Uint8()
    uint16 = abi.Uint16()
    uint32 = abi.Uint32()

    with pytest.raises(pt.TealInputError):
        tupleValue.set()

    with pytest.raises(pt.TealInputError):
        tupleValue.set(uint8, uint16)

    with pytest.raises(pt.TealInputError):
        tupleValue.set(uint8, uint16, uint32, uint32)

    with pytest.raises(pt.TealInputError):
        tupleValue.set(uint8, uint32, uint16)

    with pytest.raises(pt.TealInputError):
        tupleValue.set(uint8, uint16, uint16)

    expr = tupleValue.set(uint8, uint16, uint32)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expectedExpr = tupleValue.stored_value.store(_encode_tuple([uint8, uint16, uint32]))
    expected, _ = expectedExpr.__teal__(options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Tuple_set_Computed():
    tupleValue = abi.Tuple(
        abi.TupleTypeSpec(
            abi.Uint8TypeSpec(), abi.Uint16TypeSpec(), abi.Uint32TypeSpec()
        )
    )
    computed = ContainerType(
        tupleValue.type_spec(), pt.Bytes("internal representation")
    )
    expr = tupleValue.set(computed)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, '"internal representation"'),
            pt.TealOp(None, pt.Op.store, tupleValue.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        tupleValue.set(computed, computed)

    with pytest.raises(pt.TealInputError):
        tupleValue.set(
            ContainerType(abi.TupleTypeSpec(abi.ByteTypeSpec()), pt.Bytes(b"a"))
        )


def test_Tuple_encode():
    tupleValue = abi.Tuple(abi.TupleTypeSpec(abi.Uint64TypeSpec()))
    expr = tupleValue.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.load, tupleValue.stored_value.slot)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Tuple_length():
    tests: List[List[abi.TypeSpec]] = [
        [],
        [abi.Uint64TypeSpec()],
        [
            abi.TupleTypeSpec(abi.Uint64TypeSpec(), abi.Uint64TypeSpec()),
            abi.Uint64TypeSpec(),
        ],
        [abi.BoolTypeSpec()] * 8,
    ]

    for i, test in enumerate(tests):
        tupleValue = abi.Tuple(abi.TupleTypeSpec(*test))
        expr = tupleValue.length()
        assert expr.type_of() == pt.TealType.uint64
        assert not expr.has_return()

        expectedLength = len(test)
        expected = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, expectedLength)])

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)


def test_Tuple_getitem():
    tests: List[List[abi.TypeSpec]] = [
        [],
        [abi.Uint64TypeSpec()],
        [
            abi.TupleTypeSpec(abi.Uint64TypeSpec(), abi.Uint64TypeSpec()),
            abi.Uint64TypeSpec(),
        ],
        [abi.BoolTypeSpec()] * 8,
    ]

    for i, test in enumerate(tests):
        tupleValue = abi.Tuple(abi.TupleTypeSpec(*test))
        for j in range(len(test)):
            element = tupleValue[j]
            assert type(element) is TupleElement, "Test at index {} failed".format(i)
            assert element.tuple is tupleValue, "Test at index {} failed".format(i)
            assert element.index == j, "Test at index {} failed".format(i)

        with pytest.raises(pt.TealInputError):
            tupleValue[-1]

        with pytest.raises(pt.TealInputError):
            tupleValue[len(test)]


def test_TupleElement_store_into():
    tests: List[List[abi.TypeSpec]] = [
        [],
        [abi.Uint64TypeSpec()],
        [
            abi.TupleTypeSpec(abi.Uint64TypeSpec(), abi.Uint64TypeSpec()),
            abi.Uint64TypeSpec(),
        ],
        [abi.BoolTypeSpec()] * 8,
    ]

    for i, test in enumerate(tests):
        tupleValue = abi.Tuple(abi.TupleTypeSpec(*test))
        for j in range(len(test)):
            element = TupleElement(tupleValue, j)
            output = test[j].new_instance()

            expr = element.store_into(output)
            assert expr.type_of() == pt.TealType.none
            assert not expr.has_return()

            expectedExpr = _index_tuple(test, tupleValue.encode(), j, output)
            expected, _ = expectedExpr.__teal__(options)
            expected.addIncoming()
            expected = pt.TealBlock.NormalizeBlocks(expected)

            actual, _ = expr.__teal__(options)
            actual.addIncoming()
            actual = pt.TealBlock.NormalizeBlocks(actual)

            with pt.TealComponent.Context.ignoreExprEquality():
                assert actual == expected, "Test at index {} failed".format(i)


def test_NamedTuple_init():
    with pytest.raises(pt.TealInputError, match=r"NamedTuple must be subclassed$"):
        abi.NamedTuple()

    class Empty(abi.NamedTuple):
        pass

    with pytest.raises(
        pt.TealInputError, match=r"Expected fields to be declared but found none$"
    ):
        Empty()

    class ValidField(abi.NamedTuple):
        name: abi.Field[abi.Uint16]

    ValidField()

    class NoField(abi.NamedTuple):
        name: abi.Uint16

    with pytest.raises(
        pt.TealInputError,
        match=r'Type annotation for attribute "name" must be a Field. Got ',
    ):
        NoField()


class NT_0(abi.NamedTuple):
    f0: abi.Field[abi.Uint64]
    f1: abi.Field[abi.Uint32]
    f2: abi.Field[abi.Uint16]
    f3: abi.Field[abi.Uint8]


class NT_1(abi.NamedTuple):
    f0: abi.Field[abi.StaticArray[abi.Bool, Literal[4]]]
    f1: abi.Field[abi.DynamicArray[abi.String]]
    f2: abi.Field[abi.String]
    f3: abi.Field[abi.Bool]
    f4: abi.Field[abi.Address]
    f5: abi.Field[NT_0]


class NT_2(abi.NamedTuple):
    f0: abi.Field[abi.Bool]
    f1: abi.Field[abi.Bool]
    f2: abi.Field[abi.Bool]
    f3: abi.Field[abi.Bool]
    f4: abi.Field[abi.Bool]
    f5: abi.Field[abi.Bool]
    f6: abi.Field[abi.Bool]
    f7: abi.Field[abi.Bool]
    f8: abi.Field[NT_1]


class NT_3(abi.NamedTuple):
    f0: abi.Field[NT_0]
    f1: abi.Field[NT_1]
    f2: abi.Field[NT_2]


@pytest.mark.parametrize("test_case", [NT_0, NT_1, NT_2, NT_3])
def test_NamedTuple_getitem(test_case: type[abi.NamedTuple]):
    tuple_value = test_case()
    tuple_len_static = tuple_value.type_spec().length_static()
    for i in range(tuple_len_static):
        elem_by_field: abi.TupleElement = getattr(tuple_value, f"f{i}")
        elem_by_index: abi.TupleElement = tuple_value[i]

        assert (
            type(elem_by_field) is abi.TupleElement
        ), f"Test case {test_case} at field f{i} must be TupleElement"
        assert (
            type(elem_by_index) is abi.TupleElement
        ), f"Test case {test_case} at index {i} must be TupleElement"

        assert (
            elem_by_field.index == i
        ), f"Test case {test_case} at field f{i} should have index {i}."
        assert (
            elem_by_index.index == i
        ), f"Test case {test_case} at index {i} should have index {i}."

        assert (
            elem_by_field.tuple is tuple_value
        ), f"Test case {test_case} at field f{i} should have attr tuple == {test_case}."
        assert (
            elem_by_index.tuple is tuple_value
        ), f"Test case {test_case} at index {i} should have attr tuple == {test_case}."

        assert (
            elem_by_field.produced_type_spec() == elem_by_index.produced_type_spec()
        ), f"Test case {test_case} at field f{i} type spec unmatching: {elem_by_field.produced_type_spec()} != {elem_by_index.produced_type_spec()}."

    with pytest.raises(KeyError):
        tuple_value.aaaaa

    with pytest.raises(pt.TealInputError):
        tuple_value.f0 = abi.Uint64()


def test_NamedTupleTypeSpec():
    from pyteal.ast.abi.util import type_spec_is_assignable_to

    class Point(abi.NamedTuple):
        x: abi.Field[abi.Uint64]
        y: abi.Field[abi.Uint64]

    class AccountRecord(abi.NamedTuple):
        algoBalance: abi.Field[abi.Uint64]
        assetBalance: abi.Field[abi.Uint64]

    p = Point()
    ar = AccountRecord()

    assert p.type_spec() == p.type_spec()
    assert ar.type_spec() == ar.type_spec()
    assert p.type_spec() != ar.type_spec()
    assert not type_spec_is_assignable_to(p.type_spec(), ar.type_spec())
    assert not type_spec_is_assignable_to(ar.type_spec(), p.type_spec())
