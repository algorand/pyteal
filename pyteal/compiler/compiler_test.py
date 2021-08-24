import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from ..ast import *


def test_compile_single():
    expr = Int(1)

    expected = """
#pragma version 2
int 1
return
""".strip()
    actual_application = compileTeal(expr, Mode.Application)
    actual_signature = compileTeal(expr, Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_compile_sequence():
    expr = Seq([Pop(Int(1)), Pop(Int(2)), Int(3) + Int(4)])

    expected = """
#pragma version 2
int 1
pop
int 2
pop
int 3
int 4
+
return
""".strip()
    actual_application = compileTeal(expr, Mode.Application)
    actual_signature = compileTeal(expr, Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_compile_branch():
    expr = If(Int(1), Int(2), Int(3))

    expected = """
#pragma version 2
int 1
bnz main_l2
int 3
b main_l3
main_l2:
int 2
main_l3:
return
""".strip()
    actual_application = compileTeal(expr, Mode.Application)
    actual_signature = compileTeal(expr, Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_compile_mode():
    expr = App.globalGet(Bytes("key"))

    expected = """
#pragma version 2
byte "key"
app_global_get
return
""".strip()
    actual_application = compileTeal(expr, Mode.Application)

    assert actual_application == expected

    with pytest.raises(TealInputError):
        compileTeal(expr, Mode.Signature)


def test_compile_version_invalid():
    expr = Int(1)

    with pytest.raises(TealInputError):
        compileTeal(expr, Mode.Signature, version=1)  # too small

    with pytest.raises(TealInputError):
        compileTeal(expr, Mode.Signature, version=5)  # too large

    with pytest.raises(TealInputError):
        compileTeal(expr, Mode.Signature, version=2.0)  # decimal


def test_compile_version_2():
    expr = Int(1)

    expected = """
#pragma version 2
int 1
return
""".strip()
    actual = compileTeal(expr, Mode.Signature, version=2)
    assert actual == expected


def test_compile_version_default():
    expr = Int(1)

    actual_default = compileTeal(expr, Mode.Signature)
    actual_version_2 = compileTeal(expr, Mode.Signature, version=2)
    assert actual_default == actual_version_2


def test_compile_version_3():
    expr = Int(1)

    expected = """
#pragma version 3
int 1
return
""".strip()
    actual = compileTeal(expr, Mode.Signature, version=3)
    assert actual == expected


def test_compile_version_4():
    expr = Int(1)

    expected = """
#pragma version 4
int 1
return
""".strip()
    actual = compileTeal(expr, Mode.Signature, version=4)
    assert actual == expected


def test_slot_load_before_store():

    program = AssetHolding.balance(Int(0), Int(0)).value()
    with pytest.raises(TealInternalError):
        compileTeal(program, Mode.Application, version=2)

    program = AssetHolding.balance(Int(0), Int(0)).hasValue()
    with pytest.raises(TealInternalError):
        compileTeal(program, Mode.Application, version=2)

    program = App.globalGetEx(Int(0), Bytes("key")).value()
    with pytest.raises(TealInternalError):
        compileTeal(program, Mode.Application, version=2)

    program = App.globalGetEx(Int(0), Bytes("key")).hasValue()
    with pytest.raises(TealInternalError):
        compileTeal(program, Mode.Application, version=2)

    program = ScratchVar().load()
    with pytest.raises(TealInternalError):
        compileTeal(program, Mode.Application, version=2)


def test_assign_scratch_slots():
    myScratch = ScratchVar(TealType.uint64)
    otherScratch = ScratchVar(TealType.uint64, 1)
    anotherScratch = ScratchVar(TealType.uint64, 0)
    lastScratch = ScratchVar(TealType.uint64)
    prog = Seq(
        [
            myScratch.store(Int(5)),  # Slot 2
            otherScratch.store(Int(0)),  # Slot 1
            anotherScratch.store(Int(7)),  # Slot 0
            lastScratch.store(Int(9)),  # Slot 3
            Approve(),
        ]
    )

    expected = """
#pragma version 4
int 5
store 2
int 0
store 1
int 7
store 0
int 9
store 3
int 1
return
""".strip()
    actual = compileTeal(prog, mode=Mode.Signature, version=4)
    assert actual == expected


def test_scratchvar_double_assign_invalid():
    myvar = ScratchVar(TealType.uint64, 10)
    otherVar = ScratchVar(TealType.uint64, 10)
    prog = Seq([myvar.store(Int(5)), otherVar.store(Int(0)), Approve()])
    with pytest.raises(TealInternalError):
        compileTeal(prog, mode=Mode.Signature, version=4)


def test_assembleConstants():
    program = Itob(Int(1) + Int(1) + Tmpl.Int("TMPL_VAR")) == Concat(
        Bytes("test"), Bytes("test"), Bytes("test2")
    )

    expectedNoAssemble = """
#pragma version 3
int 1
int 1
+
int TMPL_VAR
+
itob
byte "test"
byte "test"
concat
byte "test2"
concat
==
return
""".strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=3, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble

    expectedAssemble = """
#pragma version 3
intcblock 1
bytecblock 0x74657374
intc_0 // 1
intc_0 // 1
+
pushint TMPL_VAR // TMPL_VAR
+
itob
bytec_0 // "test"
bytec_0 // "test"
concat
pushbytes 0x7465737432 // "test2"
concat
==
return
""".strip()
    actualAssemble = compileTeal(
        program, Mode.Application, version=3, assembleConstants=True
    )
    assert expectedAssemble == actualAssemble

    with pytest.raises(TealInternalError):
        compileTeal(program, Mode.Application, version=2, assembleConstants=True)


def test_compile_while():
    i = ScratchVar()
    program = Seq(
        [
            i.store(Int(0)),
            While(i.load() < Int(2)).Do(Seq([i.store(i.load() + Int(1))])),
            Approve(),
        ]
    )

    expectedNoAssemble = """
    #pragma version 4
int 0
store 0
main_l1:
load 0
int 2
<
bz main_l3
load 0
int 1
+
store 0
b main_l1
main_l3:
int 1
return
    """.strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble

    # nested
    i = ScratchVar()
    j = ScratchVar()

    program = Seq(
        [
            i.store(Int(0)),
            While(i.load() < Int(2)).Do(
                Seq(
                    [
                        j.store(Int(0)),
                        While(j.load() < Int(5)).Do(Seq([j.store(j.load() + Int(1))])),
                        i.store(i.load() + Int(1)),
                    ]
                )
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 2
<
bz main_l6
int 0
store 1
main_l3:
load 1
int 5
<
bnz main_l5
load 0
int 1
+
store 0
b main_l1
main_l5:
load 1
int 1
+
store 1
b main_l3
main_l6:
int 1
return
    """.strip()

    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble


def test_compile_for():
    i = ScratchVar()
    program = Seq(
        [
            For(i.store(Int(0)), i.load() < Int(10), i.store(i.load() + Int(1))).Do(
                Seq([App.globalPut(Itob(i.load()), i.load() * Int(2))])
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """
    #pragma version 4
int 0
store 0
main_l1:
load 0
int 10
<
bz main_l3
load 0
itob
load 0
int 2
*
app_global_put
load 0
int 1
+
store 0
b main_l1
main_l3:
int 1
return
    """.strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble

    # nested
    i = ScratchVar()
    j = ScratchVar()
    program = Seq(
        [
            For(i.store(Int(0)), i.load() < Int(10), i.store(i.load() + Int(1))).Do(
                Seq(
                    [
                        For(
                            j.store(Int(0)),
                            j.load() < Int(4),
                            j.store(j.load() + Int(2)),
                        ).Do(Seq([App.globalPut(Itob(j.load()), j.load() * Int(2))]))
                    ]
                )
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """
        #pragma version 4
int 0
store 0
main_l1:
load 0
int 10
<
bz main_l6
int 0
store 1
main_l3:
load 1
int 4
<
bnz main_l5
load 0
int 1
+
store 0
b main_l1
main_l5:
load 1
itob
load 1
int 2
*
app_global_put
load 1
int 2
+
store 1
b main_l3
main_l6:
int 1
return
        """.strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble


def test_compile_break():

    # While
    i = ScratchVar()
    program = Seq(
        [
            i.store(Int(0)),
            While(i.load() < Int(3)).Do(
                Seq([If(i.load() == Int(2), Break()), i.store(i.load() + Int(1))])
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 3
<
bz main_l5
load 0
int 2
==
bnz main_l4
load 0
int 1
+
store 0
b main_l1
main_l4:
main_l5:
int 1
return
            """.strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble

    # For
    i = ScratchVar()
    program = Seq(
        [
            For(i.store(Int(0)), i.load() < Int(10), i.store(i.load() + Int(1))).Do(
                Seq(
                    [
                        If(i.load() == Int(4), Break()),
                        App.globalPut(Itob(i.load()), i.load() * Int(2)),
                    ]
                )
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 10
<
bz main_l5
load 0
int 4
==
bnz main_l4
load 0
itob
load 0
int 2
*
app_global_put
load 0
int 1
+
store 0
b main_l1
main_l4:
main_l5:
int 1
return
        """.strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble


def test_compile_continue():
    # While
    i = ScratchVar()
    program = Seq(
        [
            i.store(Int(0)),
            While(i.load() < Int(3)).Do(
                Seq([If(i.load() == Int(2), Continue()), i.store(i.load() + Int(1))])
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 3
<
bz main_l5
main_l2:
load 0
int 2
==
bnz main_l4
load 0
int 1
+
store 0
b main_l1
main_l4:
b main_l2
main_l5:
int 1
return
                """.strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble

    # For
    i = ScratchVar()
    program = Seq(
        [
            For(i.store(Int(0)), i.load() < Int(10), i.store(i.load() + Int(1))).Do(
                Seq(
                    [
                        If(i.load() == Int(4), Continue()),
                        App.globalPut(Itob(i.load()), i.load() * Int(2)),
                    ]
                )
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 10
<
bz main_l6
load 0
int 4
==
bnz main_l5
load 0
itob
load 0
int 2
*
app_global_put
main_l4:
load 0
int 1
+
store 0
b main_l1
main_l5:
b main_l4
main_l6:
int 1
return
            """.strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble


def test_compile_continue_break_nested():

    i = ScratchVar()
    program = Seq(
        [
            i.store(Int(0)),
            While(i.load() < Int(10)).Do(
                Seq(
                    [
                        i.store(i.load() + Int(1)),
                        If(i.load() < Int(4), Continue(), Break()),
                    ]
                )
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
load 0
int 10
<
bz main_l4
main_l1:
load 0
int 1
+
store 0
load 0
int 4
<
bnz main_l3
b main_l4
main_l3:
b main_l1
main_l4:
int 1
return
    """.strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble

    i = ScratchVar()
    program = Seq(
        [
            i.store(Int(0)),
            While(i.load() < Int(10)).Do(
                Seq(
                    [
                        If(i.load() == Int(8), Break()),
                        While(i.load() < Int(6)).Do(
                            Seq(
                                [
                                    If(i.load() == Int(3), Break()),
                                    i.store(i.load() + Int(1)),
                                ]
                            )
                        ),
                        If(i.load() < Int(5), Continue()),
                        i.store(i.load() + Int(1)),
                    ]
                )
            ),
            Approve(),
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 10
<
bz main_l12
main_l2:
load 0
int 8
==
bnz main_l11
main_l4:
load 0
int 6
<
bnz main_l8
main_l5:
load 0
int 5
<
bnz main_l7
load 0
int 1
+
store 0
b main_l1
main_l7:
b main_l2
main_l8:
load 0
int 3
==
bnz main_l10
load 0
int 1
+
store 0
b main_l4
main_l10:
b main_l5
main_l11:
main_l12:
int 1
return
""".strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble


def test_compile_subroutine_unsupported():
    @Subroutine(TealType.none)
    def storeValue(value: Expr) -> Expr:
        return App.globalPut(Bytes("key"), value)

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(
                storeValue(Txn.application_args[0])
            ),
            Approve(),
        ]
    )

    with pytest.raises(TealInputError):
        compileTeal(program, Mode.Application, version=3)


def test_compile_subroutine_no_return():
    @Subroutine(TealType.none)
    def storeValue(value: Expr) -> Expr:
        return App.globalPut(Bytes("key"), value)

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(
                storeValue(Txn.application_args[0])
            ),
            Approve(),
        ]
    )

    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
txna ApplicationArgs 0
callsub sub0
main_l2:
int 1
return
sub0: // storeValue
store 0
byte "key"
load 0
app_global_put
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


def test_compile_subroutine_with_return():
    @Subroutine(TealType.none)
    def storeValue(value: Expr) -> Expr:
        return App.globalPut(Bytes("key"), value)

    @Subroutine(TealType.bytes)
    def getValue() -> Expr:
        return App.globalGet(Bytes("key"))

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(
                storeValue(Txn.application_args[0])
            ),
            If(getValue() == Bytes("fail")).Then(Reject()),
            Approve(),
        ]
    )

    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bnz main_l3
main_l1:
callsub sub1
byte "fail"
==
bz main_l4
int 0
return
main_l3:
txna ApplicationArgs 0
callsub sub0
b main_l1
main_l4:
int 1
return
sub0: // storeValue
store 0
byte "key"
load 0
app_global_put
retsub
sub1: // getValue
byte "key"
app_global_get
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


def test_compile_subroutine_many_args():
    @Subroutine(TealType.uint64)
    def calculateSum(
        a1: Expr, a2: Expr, a3: Expr, a4: Expr, a5: Expr, a6: Expr
    ) -> Expr:
        return a1 + a2 + a3 + a4 + a5 + a6

    program = Return(
        calculateSum(Int(1), Int(2), Int(3), Int(4), Int(5), Int(6))
        == Int(1 + 2 + 3 + 4 + 5 + 6)
    )

    expected = """#pragma version 4
int 1
int 2
int 3
int 4
int 5
int 6
callsub sub0
int 21
==
return
sub0: // calculateSum
store 5
store 4
store 3
store 2
store 1
store 0
load 0
load 1
+
load 2
+
load 3
+
load 4
+
load 5
+
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


def test_compile_subroutine_recursive():
    @Subroutine(TealType.uint64)
    def isEven(i: Expr) -> Expr:
        return (
            If(i == Int(0))
            .Then(Int(1))
            .ElseIf(i == Int(1))
            .Then(Int(0))
            .Else(isEven(i - Int(2)))
        )

    program = Return(isEven(Int(6)))

    expected = """#pragma version 4
int 6
callsub sub0
return
sub0: // isEven
store 0
load 0
int 0
==
bnz sub0_l5
load 0
int 1
==
bnz sub0_l4
load 0
int 2
-
load 0
dig 1
callsub sub0
swap
store 0
swap
pop
sub0_l3:
b sub0_l6
sub0_l4:
int 0
b sub0_l3
sub0_l5:
int 1
sub0_l6:
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


def test_compile_subroutine_mutually_recursive():
    @Subroutine(TealType.uint64)
    def isEven(i: Expr) -> Expr:
        return If(i == Int(0), Int(1), Not(isOdd(i - Int(1))))

    @Subroutine(TealType.uint64)
    def isOdd(i: Expr) -> Expr:
        return If(i == Int(0), Int(0), Not(isEven(i - Int(1))))

    program = Return(isEven(Int(6)))

    expected = """#pragma version 4
int 6
callsub sub0
return
sub0: // isEven
store 0
load 0
int 0
==
bnz sub0_l2
load 0
int 1
-
load 0
dig 1
callsub sub1
swap
store 0
swap
pop
!
b sub0_l3
sub0_l2:
int 1
sub0_l3:
retsub
sub1: // isOdd
store 1
load 1
int 0
==
bnz sub1_l2
load 1
int 1
-
load 1
dig 1
callsub sub0
swap
store 1
swap
pop
!
b sub1_l3
sub1_l2:
int 0
sub1_l3:
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


def test_compile_loop_in_subroutine():
    @Subroutine(TealType.none)
    def setState(value: Expr) -> Expr:
        i = ScratchVar()
        return For(i.store(Int(0)), i.load() < Int(10), i.store(i.load() + Int(1))).Do(
            App.globalPut(Itob(i.load()), value)
        )

    program = Seq([setState(Bytes("value")), Approve()])

    expected = """#pragma version 4
byte "value"
callsub sub0
int 1
return
sub0: // setState
store 0
int 0
store 1
sub0_l1:
load 1
int 10
<
bz sub0_l3
load 1
itob
load 0
app_global_put
load 1
int 1
+
store 1
b sub0_l1
sub0_l3:
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


def test_compile_subroutine_assemble_constants():
    @Subroutine(TealType.none)
    def storeValue(key: Expr, t1: Expr, t2: Expr, t3: Expr) -> Expr:
        return App.globalPut(key, t1 + t2 + t3 + Int(10))

    program = Seq(
        [
            If(Txn.application_id() == Int(0)).Then(
                storeValue(
                    Concat(Bytes("test"), Bytes("test"), Bytes("a")),
                    Int(1),
                    Int(1),
                    Int(3),
                )
            ),
            Approve(),
        ]
    )

    expected = """#pragma version 4
intcblock 1
bytecblock 0x74657374
txn ApplicationID
pushint 0 // 0
==
bz main_l2
bytec_0 // "test"
bytec_0 // "test"
concat
pushbytes 0x61 // "a"
concat
intc_0 // 1
intc_0 // 1
pushint 3 // 3
callsub sub0
main_l2:
intc_0 // 1
return
sub0: // storeValue
store 3
store 2
store 1
store 0
load 0
load 1
load 2
+
load 3
+
pushint 10 // 10
+
app_global_put
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=True)
    assert expected == actual
