import pytest
import pyteal as pt
from dataclasses import dataclass
from pyteal.ast.frame import (
    FrameBury,
    FrameDig,
    Proto,
    DupN,
    LocalTypeSegment,
    ProtoStackLayout,
)

avm7Options = pt.CompileOptions(version=7)
avm8Options = pt.CompileOptions(version=8)


@pytest.mark.parametrize("input_num, output_num", [(1, 1), (1, 0), (5, 5)])
def test_proto(input_num: int, output_num: int):
    expr = Proto(input_num, output_num)
    assert not expr.has_return()
    assert expr.type_of() == pt.TealType.none

    block = [pt.TealOp(expr, pt.Op.proto, input_num, output_num)]
    if output_num > 0:
        block.append(pt.TealOp(None, pt.Op.int, 0))
    if output_num > 1:
        block.append(pt.TealOp(None, pt.Op.dupn, output_num - 1))

    expected = pt.TealSimpleBlock(block)
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_proto_invalid():
    with pytest.raises(pt.TealInputError):
        Proto(-1, 1)

    with pytest.raises(pt.TealInputError):
        Proto(1, -1)

    with pytest.raises(pt.TealInputError):
        Proto(1, 1).__teal__(avm7Options)


@pytest.mark.parametrize("depth", [-1, 0, 1, 2])
def test_frame_dig(depth: int):
    expr = FrameDig(depth)
    assert not expr.has_return()
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.frame_dig, depth)])
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_frame_dig_invalid():
    with pytest.raises(pt.TealInputError):
        FrameDig(1).__teal__(avm7Options)


def test_frame_bury():
    byte_expr = pt.Bytes("Astartes")
    expr = FrameBury(byte_expr, 4)
    assert not expr.has_return()
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(byte_expr, pt.Op.byte, '"Astartes"'),
            pt.TealOp(expr, pt.Op.frame_bury, 4),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_frame_bury_invalid():
    with pytest.raises(pt.TealTypeError):
        FrameBury(pt.Seq(), 1)

    with pytest.raises(pt.TealInputError):
        FrameBury(pt.Int(1), 1).__teal__(avm7Options)


def test_dupn_zero():
    byte_expr = pt.Bytes("Astartes")
    expr = DupN(byte_expr, 0)
    assert not expr.has_return()
    assert expr.type_of() == byte_expr.type_of()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(byte_expr, pt.Op.byte, '"Astartes"'),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_dupn_single():
    byte_expr = pt.Bytes("Astartes")
    expr = DupN(byte_expr, 1)
    assert not expr.has_return()
    assert expr.type_of() == byte_expr.type_of()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(byte_expr, pt.Op.byte, '"Astartes"'),
            pt.TealOp(expr, pt.Op.dup),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_dupn_multiple():
    byte_expr = pt.Bytes("Astartes")
    expr = DupN(byte_expr, 4)
    assert not expr.has_return()
    assert expr.type_of() == byte_expr.type_of()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(byte_expr, pt.Op.byte, '"Astartes"'),
            pt.TealOp(expr, pt.Op.dupn, 4),
        ]
    )
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_dupn_invalid():
    with pytest.raises(pt.TealTypeError):
        DupN(pt.Seq(), 10)

    with pytest.raises(pt.TealInputError):
        DupN(pt.Int(1), -10)

    with pytest.raises(pt.TealInputError):
        DupN(pt.Int(1), 10).__teal__(avm7Options)


def test_local_type_segment_invalid():
    with pytest.raises(pt.TealInternalError) as tie:
        LocalTypeSegment(pt.TealType.anytype, 0)

    assert "segment length must be strictly greater than 0" in str(tie)

    with pytest.raises(pt.TealInternalError) as tie:
        LocalTypeSegment(pt.TealType.anytype, -1)

    assert "segment length must be strictly greater than 0" in str(tie)

    with pytest.raises(pt.TealInternalError) as tie:
        LocalTypeSegment(pt.TealType.none, 2)

    assert "Local variable in subroutine initialization must be typed." in str(tie)


@dataclass
class LocalTypeSegmentTestCase:
    local_type_segment: LocalTypeSegment
    expected: pt.TealSimpleBlock


@pytest.mark.parametrize(
    "testcase",
    [
        LocalTypeSegmentTestCase(
            LocalTypeSegment(pt.TealType.anytype, 1),
            pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 0)]),
        ),
        LocalTypeSegmentTestCase(
            LocalTypeSegment(pt.TealType.anytype, 5),
            pt.TealSimpleBlock(
                [
                    pt.TealOp(None, pt.Op.int, 0),
                    pt.TealOp(None, pt.Op.dupn, 4),
                ]
            ),
        ),
        LocalTypeSegmentTestCase(
            LocalTypeSegment(pt.TealType.uint64, 1),
            pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 0)]),
        ),
        LocalTypeSegmentTestCase(
            LocalTypeSegment(pt.TealType.uint64, 5),
            pt.TealSimpleBlock(
                [
                    pt.TealOp(None, pt.Op.int, 0),
                    pt.TealOp(None, pt.Op.dupn, 4),
                ]
            ),
        ),
        LocalTypeSegmentTestCase(
            LocalTypeSegment(pt.TealType.bytes, 1),
            pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '""')]),
        ),
        LocalTypeSegmentTestCase(
            LocalTypeSegment(pt.TealType.bytes, 5),
            pt.TealSimpleBlock(
                [
                    pt.TealOp(None, pt.Op.byte, '""'),
                    pt.TealOp(None, pt.Op.dupn, 4),
                ]
            ),
        ),
    ],
)
def test_local_type_segment_compilation(testcase: LocalTypeSegmentTestCase):
    actual, _ = testcase.local_type_segment.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == testcase.expected


def test_proto_stack_layout_invalid():
    with pytest.raises(pt.TealInternalError) as tie:
        ProtoStackLayout([pt.TealType.uint64, pt.TealType.bytes], [], -1)

    assert "Return allocation number should be non-negative." == str(tie.value)

    with pytest.raises(pt.TealInternalError) as tie:
        ProtoStackLayout([pt.TealType.uint64, pt.TealType.bytes], [], 1)

    assert "should not be greater than local allocations" in str(tie.value)

    with pytest.raises(pt.TealInternalError) as tie:
        ProtoStackLayout([pt.TealType.bytes, pt.TealType.none], [], 0)

    assert "must be typed" in str(tie.value)

    with pytest.raises(pt.TealInternalError) as tie:
        ProtoStackLayout(
            [pt.TealType.bytes, pt.TealType.uint64],
            [pt.TealType.uint64, pt.TealType.none],
            0,
        )

    assert "must be typed" in str(tie.value)


@dataclass
class SuccinctReprTestCase:
    local_types: list[pt.TealType]
    expected: list[LocalTypeSegment]


@pytest.mark.parametrize(
    "testcase",
    [
        SuccinctReprTestCase([], []),
        SuccinctReprTestCase(
            [pt.TealType.anytype], [LocalTypeSegment(pt.TealType.anytype, 1)]
        ),
        SuccinctReprTestCase(
            [pt.TealType.anytype, pt.TealType.uint64],
            [
                LocalTypeSegment(pt.TealType.anytype, 1),
                LocalTypeSegment(pt.TealType.uint64, 1),
            ],
        ),
        SuccinctReprTestCase(
            [pt.TealType.bytes, pt.TealType.anytype, pt.TealType.uint64],
            [
                LocalTypeSegment(pt.TealType.bytes, 1),
                LocalTypeSegment(pt.TealType.anytype, 1),
                LocalTypeSegment(pt.TealType.uint64, 1),
            ],
        ),
        SuccinctReprTestCase(
            [
                pt.TealType.anytype,
                pt.TealType.bytes,
                pt.TealType.anytype,
                pt.TealType.uint64,
            ],
            [
                LocalTypeSegment(pt.TealType.anytype, 1),
                LocalTypeSegment(pt.TealType.bytes, 1),
                LocalTypeSegment(pt.TealType.anytype, 1),
                LocalTypeSegment(pt.TealType.uint64, 1),
            ],
        ),
        SuccinctReprTestCase(
            [
                pt.TealType.anytype,
                pt.TealType.bytes,
                pt.TealType.anytype,
                pt.TealType.uint64,
                pt.TealType.anytype,
            ],
            [
                LocalTypeSegment(pt.TealType.anytype, 1),
                LocalTypeSegment(pt.TealType.bytes, 1),
                LocalTypeSegment(pt.TealType.anytype, 1),
                LocalTypeSegment(pt.TealType.uint64, 1),
                LocalTypeSegment(pt.TealType.anytype, 1),
            ],
        ),
        SuccinctReprTestCase(
            [
                pt.TealType.anytype,
                pt.TealType.bytes,
                pt.TealType.bytes,
                pt.TealType.uint64,
                pt.TealType.uint64,
                pt.TealType.uint64,
                pt.TealType.anytype,
                pt.TealType.anytype,
                pt.TealType.anytype,
                pt.TealType.anytype,
                pt.TealType.bytes,
                pt.TealType.bytes,
                pt.TealType.uint64,
                pt.TealType.uint64,
                pt.TealType.uint64,
            ],
            [
                LocalTypeSegment(pt.TealType.anytype, 1),
                LocalTypeSegment(pt.TealType.bytes, 2),
                LocalTypeSegment(pt.TealType.uint64, 3),
                LocalTypeSegment(pt.TealType.anytype, 4),
                LocalTypeSegment(pt.TealType.bytes, 2),
                LocalTypeSegment(pt.TealType.uint64, 3),
            ],
        ),
    ],
)
def test_proto_stack_layout_succinct_repr(testcase: SuccinctReprTestCase):
    actual = ProtoStackLayout([], testcase.local_types, False)._succinct_repr()
    assert actual == testcase.expected
