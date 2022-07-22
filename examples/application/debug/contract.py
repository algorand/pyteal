from pyteal import Int, Assert, Seq, Pop, Bytes, Len, compileTeal, OptimizeOptions, Mode
from util import thing

program = Seq(
    # comments
    Pop(thing(Int(1), Int(2))),
    # stop black fmt
    Assert(Len(Bytes("ok")) > Int(0)),
    # from complaining
    thing(Int(2), Int(3)),
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
