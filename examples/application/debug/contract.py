from pyteal import *
from util import thing

program = Seq(
    Pop(thing(Int(1), Int(2))), 
    Assert(Len(Bytes("ok")) > Int(0)), 
    thing(Int(2), Int(3))
)

print(
    compileTeal(
        program,
        mode=Mode.Application,
        version=6,
        debug=True,
        optimize=OptimizeOptions(scratch_slots=True),
    )
)
