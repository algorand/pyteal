import pytest

import pyteal as pt
from pyteal.ast.comment import CommentExpr

options = pt.CompileOptions()


def test_CommentExpr():
    for comment in ("", "hello world", " // a b c //    \t . "):
        expr = CommentExpr(comment)
        assert expr.comment_string == comment
        assert expr.type_of() == pt.TealType.none
        assert expr.has_return() is False

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(expr, pt.Op.comment, comment),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        assert actual == expected

    for newline in ("\n", "\r\n", "\r"):
        with pytest.raises(
            pt.TealInputError,
            match=r"Newlines should not be present in the CommentExpr constructor$",
        ):
            CommentExpr(f"one line{newline}two lines")


def test_Comment_empty():
    to_wrap = pt.Int(1)
    comment = ""
    expr = pt.Comment(comment, to_wrap)
    assert type(expr) is pt.Int

    assert expr is to_wrap


def test_Comment_single_line():
    to_wrap = pt.Int(1)
    comment = "just an int"
    expr = pt.Comment(comment, to_wrap)
    assert type(expr) is pt.Int

    assert expr is to_wrap

    version = 6
    expected_teal = f"""#pragma version {version}
int 1 // {comment}
return"""
    actual_teal = pt.compileTeal(
        pt.Return(expr), version=version, mode=pt.Mode.Application
    )
    assert actual_teal == expected_teal


def test_Comment_only():
    comment = """
    Sick section to follow
    dragons abound
    dont touch unless you want to break everything"""

    comment_parts = [
        "",
        "Sick section to follow",
        "dragons abound",
        "dont touch unless you want to break everything",
    ]

    expr = pt.Comment(comment)
    assert type(expr) is pt.Seq
    assert len(expr.args) == len(comment_parts)

    version = 6
    expected_teal = f"""#pragma version {version}
// 
//     Sick section to follow
//     dragons abound
//     dont touch unless you want to break everything
int 1
return"""
    actual_teal = pt.compileTeal(
        pt.Return(pt.Seq(expr, pt.Int(1))), mode=pt.Mode.Application, version=version
    )
    assert actual_teal == expected_teal


def test_Comment_multi_line():
    to_wrap = pt.Int(1)
    comment = """just an int
but its really more than that isnt it? an integer here is a uint64 stack type but looking further what does that mean? 
You might say its a 64 bit representation of an element of the set Z and comes from the latin `integer` meaning `whole`
since it has no fractional part. You might also say this run on comment has gone too far. See https://en.wikipedia.org/wiki/Integer for more details 
"""

    expr = pt.Comment(comment, to_wrap)
    assert type(expr) is pt.Int
    assert expr.comment == comment

    version = 6
    expected_teal = f"""#pragma version {version}
int 1 // just an int
// but its really more than that isnt it? an integer here is a uint64 stack type but looking further what does that mean? 
// You might say its a 64 bit representation of an element of the set Z and comes from the latin `integer` meaning `whole`
// since it has no fractional part. You might also say this run on comment has gone too far. See https://en.wikipedia.org/wiki/Integer for more details 
return"""
    actual_teal = pt.compileTeal(
        pt.Return(expr), version=version, mode=pt.Mode.Application
    )
    assert actual_teal == expected_teal
