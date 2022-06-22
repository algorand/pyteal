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
    expected_teal = f"#pragma version {version};int 1;// {comment};return".replace(
        ";", "\n"
    )
    actual_teal = pt.compileTeal(
        pt.Return(expr), version=version, mode=pt.Mode.Application
    )
    assert actual_teal == expected_teal


def test_long_comment():
    to_wrap = pt.Int(1)
    comment = """just an int
     but its really more than that isnt it? an integer here is a uint64 stack type but looking further what does that mean? 
     You might say its a 64 bit representation of an element of the set Z and comes from the latin `integer` meaning `whole`
     since it has no fractional part. You might also say this run on comment has gone too far. See https://en.wikipedia.org/wiki/Integer for more details 
    """
    expr = pt.Comment(to_wrap, comment)
    assert expr.type_of() == to_wrap.type_of()
    assert expr.has_return() == to_wrap.has_return()

    comment = " ".join(
        [i.strip() for i in comment.split("\n") if not (i.isspace() or len(i) == 0)]
    )

    version = 6
    expected_teal = f"#pragma version {version};int 1;// {comment};return".replace(
        ";", "\n"
    )
    actual_teal = pt.compileTeal(
        pt.Return(expr), version=version, mode=pt.Mode.Application
    )
    print(actual_teal)
    assert actual_teal == expected_teal


def test_comment_no_simple():
    to_wrap = pt.Seq(pt.Int(1))
    comment = "just an int"
    expr = pt.Comment(to_wrap, comment)
    assert expr.type_of() == to_wrap.type_of()
    assert expr.has_return() == to_wrap.has_return()

    version = 6
    expected_teal = f"#pragma version {version};int 1;// {comment};return".replace(
        ";", "\n"
    )
    actual_teal = pt.compileTeal(
        pt.Return(expr), version=version, mode=pt.Mode.Application
    )
    assert actual_teal == expected_teal


# def test_comment_empty_expr():
#     to_wrap = pt.Seq()
#     comment = "should fail"
#     expr = pt.Comment(to_wrap, comment)
#     assert expr.type_of() == to_wrap.type_of()
#
#     print(expr.__teal__(options))
#
#     with pytest.raises(pt.TealInputError):
#         expr.__teal__(options)
#
