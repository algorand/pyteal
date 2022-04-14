import pyteal as pt


def test_EqualityContext():
    expr1 = pt.Int(1)
    expr2 = pt.Int(1)

    op1 = pt.TealOp(expr1, pt.Op.int, 1)
    op2 = pt.TealOp(expr2, pt.Op.int, 1)

    assert op1 == op1
    assert op2 == op2
    assert op1 != op2
    assert op2 != op1

    with pt.TealComponent.Context.ignoreExprEquality():
        assert op1 == op1
        assert op2 == op2
        assert op1 == op2
        assert op2 == op1
