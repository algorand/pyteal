import pytest
import pyteal as pt
from pyteal.types import TealType

avm7Options = pt.CompileOptions(version=7)
avm8Options = pt.CompileOptions(version=8)


@pytest.mark.parametrize("input_num, output_num", [(1, 1), (1, 0), (5, 5)])
def test_proto(input_num: int, output_num: int):
    expr = pt.Proto(input_num, output_num)
    assert not expr.has_return()
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.proto, input_num, output_num)])
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_proto_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Proto(-1, 1)

    with pytest.raises(pt.TealInputError):
        pt.Proto(1, -1)

    with pytest.raises(pt.TealInputError):
        pt.Proto(1, 1).__teal__(avm7Options)


@pytest.mark.parametrize("depth", [-1, 0, 1, 2])
def test_frame_dig(depth: int):
    expr = pt.FrameDig(depth)
    assert not expr.has_return()
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.frame_dig, depth)])
    actual, _ = expr.__teal__(avm8Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_frame_dig_invalid():
    with pytest.raises(pt.TealInputError):
        pt.FrameDig(1).__teal__(avm7Options)


def test_frame_bury():
    byte_expr = pt.Bytes("Astartes")
    expr = pt.FrameBury(byte_expr, 4)
    assert not expr.has_return()
    assert expr.type_of() == TealType.none

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
        pt.FrameBury(pt.Seq(), 1)

    with pytest.raises(pt.TealInputError):
        pt.FrameBury(pt.Int(1), 1).__teal__(avm7Options)


def test_dupn():
    byte_expr = pt.Bytes("Astartes")
    expr = pt.DupN(byte_expr, 4)
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
        pt.DupN(pt.Seq(), 1)

    with pytest.raises(pt.TealInputError):
        pt.DupN(pt.Int(1), -1)

    with pytest.raises(pt.TealInputError):
        pt.DupN(pt.Int(1), 1).__teal__(avm7Options)
