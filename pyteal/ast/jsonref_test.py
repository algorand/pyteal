import pytest

import pyteal as pt

teal6Options = pt.CompileOptions(version=6)
teal7Options = pt.CompileOptions(version=7)


def test_json_string():
    args = [pt.Bytes('{"foo":"bar"}'), pt.Bytes("foo")]
    expr = pt.JsonRef(pt.JsonRef.json_string, *args)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{\\"foo\\":\\"bar\\"}"'),
            pt.TealOp(args[1], pt.Op.byte, '"foo"'),
            pt.TealOp(expr, pt.Op.json_ref, "JSONString"),
        ]
    )

    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal6Options)


def test_json_uint64():
    args = [pt.Bytes('{"foo":123456789}'), pt.Bytes("foo")]
    expr = pt.JsonRef(pt.JsonRef.json_uint64, *args)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{\\"foo\\":123456789}"'),
            pt.TealOp(args[1], pt.Op.byte, '"foo"'),
            pt.TealOp(expr, pt.Op.json_ref, "JSONUint64"),
        ]
    )

    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal6Options)


def test_json_object():
    args = [pt.Bytes('{"foo":{"key": "value"}}'), pt.Bytes("foo")]
    expr = pt.JsonRef(pt.JsonRef.json_object, *args)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"{\\"foo\\":{\\"key\\": \\"value\\"}}"'),
            pt.TealOp(args[1], pt.Op.byte, '"foo"'),
            pt.TealOp(expr, pt.Op.json_ref, "JSONObject"),
        ]
    )

    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal6Options)


def test_json_ref_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.JsonRef(pt.Bytes("my string"), pt.Bytes("a"), pt.Bytes("a"))

    with pytest.raises(pt.TealTypeError):
        pt.JsonRef(pt.JsonRef.json_object, pt.Int(0), pt.Bytes("a"))

    with pytest.raises(pt.TealTypeError):
        pt.JsonRef(pt.JsonRef.json_string, pt.Bytes("a"), pt.Int(0))
