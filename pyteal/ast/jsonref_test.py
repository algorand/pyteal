import pytest

import pyteal as pt

avm6Options = pt.CompileOptions(version=6)
avm7Options = pt.CompileOptions(version=7)


def test_json_string():
    args = [pt.Bytes('{"foo":"bar"}'), pt.Bytes("foo")]
    expr = pt.JsonRef.as_string(*args)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{\\"foo\\":\\"bar\\"}"'),
            pt.TealOp(args[1], pt.Op.byte, '"foo"'),
            pt.TealOp(expr, pt.Op.json_ref, "JSONString"),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_json_uint64():
    args = [pt.Bytes('{"foo":123456789}'), pt.Bytes("foo")]
    expr = pt.JsonRef.as_uint64(*args)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{\\"foo\\":123456789}"'),
            pt.TealOp(args[1], pt.Op.byte, '"foo"'),
            pt.TealOp(expr, pt.Op.json_ref, "JSONUint64"),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_json_object():
    args = [pt.Bytes('{"foo":{"key": "value"}}'), pt.Bytes("foo")]
    expr = pt.JsonRef.as_object(*args)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{\\"foo\\":{\\"key\\": \\"value\\"}}"'),
            pt.TealOp(args[1], pt.Op.byte, '"foo"'),
            pt.TealOp(expr, pt.Op.json_ref, "JSONObject"),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_json_ref_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.JsonRef.as_object(pt.Int(0), pt.Bytes("a"))

    with pytest.raises(pt.TealTypeError):
        pt.JsonRef.as_string(pt.Bytes("a"), pt.Int(0))
