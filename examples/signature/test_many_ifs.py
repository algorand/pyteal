#!/usr/bin/env python3

from pyteal import *

"""
Test with many If statements to trigger potential corner cases in code generation.
Previous versions of PyTeal took an exponential time to generate the TEAL code for this PyTEAL.
"""

sv = ScratchVar(TealType.uint64)
s = Seq(
    [
        If(
            Int(3 * i) == Int(3 * i),
            sv.store(Int(3 * i + 1)),
            sv.store(Int(3 * i + 2))
        )
        for i in range(30)
    ] +
    [
        Return(sv.load())
    ]
)

print(compileTeal(s, Mode.Signature))
