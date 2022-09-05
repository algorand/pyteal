import pyteal as pt

# ### Begin Fixtures ### #

hello = pt.Seq(
    pt.Log(pt.Concat(pt.Bytes("hello"), pt.Bytes("world"))),
    pt.Int(1),
)

x1 = 42

simple_add = pt.Int(1) + pt.Int(2) + pt.Int(3) + pt.Int(4) + pt.Int(5) + pt.Int(x1)
simple_add_spacey_str = """(
    pt.Int(
        1
    ) 
    + 
    pt.Int(
        2
    ) 
    + 
    pt.Int(
        3
    ) 
    + 
    pt.Int(
        4
    ) 
    + 
    pt.Int(
        5
    )
    + 
    pt.Int(
        x1
    )
)"""
simple_add_linesep = (
    pt.Int(1)
    + pt.Int(2)
    + pt.Int(3)
    + pt.Int(4)
    + pt.Int(5)
    + pt.Int(x1)
    + pt.Int(2)
    + pt.Int(3)
    + pt.Int(4)
    + pt.Int(5)
    + pt.Int(x1)
)

pt_add_oneline = pt.Add(
    pt.Add(pt.Add(pt.Add(pt.Int(1), pt.Int(2)), pt.Int(3)), pt.Int(4)), pt.Int(5)
)

pt_add_oneline_str = """pt.Add(pt.Add(pt.Add(pt.Add(pt.Add(pt.Add(pt.Add(pt.Add(pt.Add(pt.Add(pt.Int(1), pt.Int(2)), pt.Int(3)), pt.Int(4)), pt.Int(5)), pt.Int(6)), pt.Int(7)), pt.Int(8)), pt.Int(9)), pt.Int(10)), pt.Int(11))"""

pt_add_linesep = pt.Add(
    pt.Add(
        pt.Add(
            pt.Add(
                pt.Int(1),
                pt.Int(2),
            ),
            pt.Int(3),
        ),
        pt.Int(4),
    ),
    pt.Int(5),
)

pt_add_spacey_str = """pt.Add(
    pt.Add(
        pt.Add(
            pt.Add(
                pt.Int(
                    1
                ),
                pt.Int(
                    2
                ),
            ),
            pt.Int(
                3
            ),
        ),
        pt.Int(
            4
        ),
    ),
    pt.Int(
        5
    ),
)"""

from source_map_imports_test import goodnum as greatnum

x2 = pt.ScratchVar(pt.TealType.uint64)
goodbye = pt.Return(pt.Int(42))

pure = pt.Seq(
    pt.Pop(hello),
    pt.Pop(greatnum),
    x2.store(pt.Int(1000)),
    pt.Pop(pt.Int(1337) - pt.Int(42)),
    goodbye,
)

pure_str = """x = pt.ScratchVar(TealType.uint64); pure = pt.Seq(pt.Pop(hello), pt.Pop(goodnum),x.store(pt.Int(1000)),pt.Pop(pt.Int(1337) - pt.Int(42)),goodbye)"""

from source_map_imports_test import double_exp, cat

some_subroutines = pt.Seq(
    pt.Log(cat(pt.Bytes("Mapping "), pt.Bytes("PyTeal"))),
    pt.Log(pt.Bytes("this compiles but it'll blow up when executed")),
    double_exp(),
)
some_subroutines_str = """pt.Seq(pt.Log(cat(pt.Bytes("Mapping "), pt.Bytes("PyTeal"))),pt.Log(pt.Bytes("this compiles but it'll blow up when executed")),double_exp())"""

# ### End Fixtures ### #
