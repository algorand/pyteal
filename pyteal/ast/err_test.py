import pyteal as pt


def test_err():
    expr = pt.Err()
    assert expr.type_of() == pt.TealType.none
    assert expr.has_return()
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.err)])
    actual, _ = expr.__teal__(pt.CompileOptions())
    assert actual == expected
