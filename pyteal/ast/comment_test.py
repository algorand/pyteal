import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_comment():
    to_wrap = pt.Int(1)
    comment = "just an int"
    expr = pt.Comment(to_wrap, comment)
    assert expr.type_of() == to_wrap.type_of()
    assert expr.has_return() == to_wrap.has_return()

    version = 6
    expected_teal = f"#pragma version {version};int 1 // {comment};return".replace(
        ";", "\n"
    )
    actual_teal = pt.compileTeal(
        pt.Return(expr), version=version, mode=pt.Mode.Application
    )
    assert actual_teal == expected_teal


def test_comment_no_simple():
    to_wrap = pt.Seq(pt.Int(1))
    comment = "just an int"
    expr = pt.Comment(to_wrap, comment)
    assert expr.type_of() == to_wrap.type_of()
    assert expr.has_return() == to_wrap.has_return()

    version = 6
    expected_teal = f"#pragma version {version};int 1 // {comment};return".replace(
        ";", "\n"
    )
    actual_teal = pt.compileTeal(
        pt.Return(expr), version=version, mode=pt.Mode.Application
    )
    assert actual_teal == expected_teal


def test_comment_empty_expr():
    to_wrap = pt.Seq()
    comment = "should fail"
    expr = pt.Comment(to_wrap, comment)
    assert expr.type_of() == to_wrap.type_of()

    with pytest.raises(pt.TealInputError):
        expr.__teal__(options)
