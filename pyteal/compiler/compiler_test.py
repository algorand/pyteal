import inspect
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
    expr = If(Int(1)).Then(Int(2)).Else(Int(3))

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


def test_compile_branch_multiple():
    expr = If(Int(1)).Then(Int(2)).ElseIf(Int(3)).Then(Int(4)).Else(Int(5))

    expected = """
#pragma version 2
int 1
bnz main_l4
int 3
bnz main_l3
int 5
b main_l5
main_l3:
int 4
b main_l5
main_l4:
int 2
main_l5:
return
""".strip()
    actual_application = compileTeal(expr, Mode.Application)
    actual_signature = compileTeal(expr, Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_empty_branch():
    program = Seq(
        [
            If(Txn.application_id() == Int(0)).Then(Seq()),
            Approve(),
        ]
    )

    expected = """#pragma version 5
txn ApplicationID
int 0
==
bnz main_l1
main_l1:
int 1
return
    """.strip()
    actual = compileTeal(program, Mode.Application, version=5, assembleConstants=False)
    assert actual == expected


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
        compileTeal(expr, Mode.Signature, version=7)  # too large

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


def test_compile_version_5():
    expr = Int(1)
    expected = """
#pragma version 5
int 1
return
""".strip()
    actual = compileTeal(expr, Mode.Signature, version=5)
    assert actual == expected


def test_compile_version_6():
    expr = Int(1)
    expected = """
#pragma version 6
int 1
return
""".strip()
    actual = compileTeal(expr, Mode.Signature, version=6)
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

    expected = """
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
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual

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

    expected = """#pragma version 4
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

    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


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

    expected = """#pragma version 4
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
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual

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

    expected = """#pragma version 4
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
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


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

    expected = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 3
<
bz main_l4
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
int 1
return
            """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual

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

    expected = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 10
<
bz main_l4
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
int 1
return
        """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


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

    expected = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 3
<
bz main_l4
main_l2:
load 0
int 2
==
bnz main_l2
load 0
int 1
+
store 0
b main_l1
main_l4:
int 1
return
                """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual

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

    expected = """#pragma version 4
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
main_l4:
load 0
int 1
+
store 0
b main_l1
main_l5:
int 1
return
            """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


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

    expected = """#pragma version 4
int 0
store 0
load 0
int 10
<
bz main_l2
main_l1:
load 0
int 1
+
store 0
load 0
int 4
<
bnz main_l1
main_l2:
int 1
return
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual

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

    expected = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 10
<
bz main_l8
main_l2:
load 0
int 8
==
bnz main_l8
main_l3:
load 0
int 6
<
bnz main_l6
main_l4:
load 0
int 5
<
bnz main_l2
load 0
int 1
+
store 0
b main_l1
main_l6:
load 0
int 3
==
bnz main_l4
load 0
int 1
+
store 0
b main_l3
main_l8:
int 1
return
""".strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert expected == actual


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
callsub storeValue_0
main_l2:
int 1
return

// storeValue
storeValue_0:
store 0
byte "key"
load 0
app_global_put
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert actual == expected


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
callsub getValue_1
byte "fail"
==
bz main_l4
int 0
return
main_l3:
txna ApplicationArgs 0
callsub storeValue_0
b main_l1
main_l4:
int 1
return

// storeValue
storeValue_0:
store 0
byte "key"
load 0
app_global_put
retsub

// getValue
getValue_1:
byte "key"
app_global_get
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert actual == expected


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
callsub calculateSum_0
int 21
==
return

// calculateSum
calculateSum_0:
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
    assert actual == expected


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
callsub isEven_0
return

// isEven
isEven_0:
store 0
load 0
int 0
==
bnz isEven_0_l4
load 0
int 1
==
bnz isEven_0_l3
load 0
int 2
-
load 0
dig 1
callsub isEven_0
swap
store 0
swap
pop
b isEven_0_l5
isEven_0_l3:
int 0
b isEven_0_l5
isEven_0_l4:
int 1
isEven_0_l5:
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert actual == expected


def test_compile_subroutine_recursive_5():
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

    expected = """#pragma version 5
int 6
callsub isEven_0
return

// isEven
isEven_0:
store 0
load 0
int 0
==
bnz isEven_0_l4
load 0
int 1
==
bnz isEven_0_l3
load 0
int 2
-
load 0
swap
callsub isEven_0
swap
store 0
b isEven_0_l5
isEven_0_l3:
int 0
b isEven_0_l5
isEven_0_l4:
int 1
isEven_0_l5:
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=5, assembleConstants=False)
    assert actual == expected


def test_compile_subroutine_recursive_multiple_args():
    @Subroutine(TealType.uint64)
    def multiplyByAdding(a, b):
        return (
            If(a == Int(0))
            .Then(Return(Int(0)))
            .Else(Return(b + multiplyByAdding(a - Int(1), b)))
        )

    program = Return(multiplyByAdding(Int(3), Int(5)))

    expected = """#pragma version 4
int 3
int 5
callsub multiplyByAdding_0
return

// multiplyByAdding
multiplyByAdding_0:
store 1
store 0
load 0
int 0
==
bnz multiplyByAdding_0_l2
load 1
load 0
int 1
-
load 1
load 0
load 1
dig 3
dig 3
callsub multiplyByAdding_0
store 0
store 1
load 0
swap
store 0
swap
pop
swap
pop
+
retsub
multiplyByAdding_0_l2:
int 0
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert actual == expected


def test_compile_subroutine_recursive_multiple_args_5():
    @Subroutine(TealType.uint64)
    def multiplyByAdding(a, b):
        return (
            If(a == Int(0))
            .Then(Return(Int(0)))
            .Else(Return(b + multiplyByAdding(a - Int(1), b)))
        )

    program = Return(multiplyByAdding(Int(3), Int(5)))

    expected = """#pragma version 5
int 3
int 5
callsub multiplyByAdding_0
return

// multiplyByAdding
multiplyByAdding_0:
store 1
store 0
load 0
int 0
==
bnz multiplyByAdding_0_l2
load 1
load 0
int 1
-
load 1
load 0
load 1
uncover 3
uncover 3
callsub multiplyByAdding_0
cover 2
store 1
store 0
+
retsub
multiplyByAdding_0_l2:
int 0
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=5, assembleConstants=False)
    assert actual == expected


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
callsub isEven_0
return

// isEven
isEven_0:
store 0
load 0
int 0
==
bnz isEven_0_l2
load 0
int 1
-
load 0
dig 1
callsub isOdd_1
swap
store 0
swap
pop
!
b isEven_0_l3
isEven_0_l2:
int 1
isEven_0_l3:
retsub

// isOdd
isOdd_1:
store 1
load 1
int 0
==
bnz isOdd_1_l2
load 1
int 1
-
load 1
dig 1
callsub isEven_0
swap
store 1
swap
pop
!
b isOdd_1_l3
isOdd_1_l2:
int 0
isOdd_1_l3:
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert actual == expected


def test_compile_subroutine_mutually_recursive_5():
    @Subroutine(TealType.uint64)
    def isEven(i: Expr) -> Expr:
        return If(i == Int(0), Int(1), Not(isOdd(i - Int(1))))

    @Subroutine(TealType.uint64)
    def isOdd(i: Expr) -> Expr:
        return If(i == Int(0), Int(0), Not(isEven(i - Int(1))))

    program = Return(isEven(Int(6)))

    expected = """#pragma version 5
int 6
callsub isEven_0
return

// isEven
isEven_0:
store 0
load 0
int 0
==
bnz isEven_0_l2
load 0
int 1
-
load 0
swap
callsub isOdd_1
swap
store 0
!
b isEven_0_l3
isEven_0_l2:
int 1
isEven_0_l3:
retsub

// isOdd
isOdd_1:
store 1
load 1
int 0
==
bnz isOdd_1_l2
load 1
int 1
-
load 1
swap
callsub isEven_0
swap
store 1
!
b isOdd_1_l3
isOdd_1_l2:
int 0
isOdd_1_l3:
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=5, assembleConstants=False)
    assert actual == expected


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
callsub setState_0
int 1
return

// setState
setState_0:
store 0
int 0
store 1
setState_0_l1:
load 1
int 10
<
bz setState_0_l3
load 1
itob
load 0
app_global_put
load 1
int 1
+
store 1
b setState_0_l1
setState_0_l3:
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert actual == expected


def test_compile_subroutine_invalid_name():
    def tmp() -> Expr:
        return Int(1)

    tmp.__name__ = "invalid-;)"

    program = Subroutine(TealType.uint64)(tmp)()
    expected = """#pragma version 4
callsub invalid_0
return

// invalid-;)
invalid_0:
int 1
retsub
    """.strip()
    actual = compileTeal(program, Mode.Application, version=4, assembleConstants=False)
    assert actual == expected


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
callsub storeValue_0
main_l2:
intc_0 // 1
return

// storeValue
storeValue_0:
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
    assert actual == expected


def test_compile_wide_ratio():
    cases = (
        (
            WideRatio([Int(2), Int(100)], [Int(5)]),
            """#pragma version 5
int 2
int 100
mulw
int 0
int 5
divmodw
pop
pop
swap
!
assert
return
""",
        ),
        (
            WideRatio([Int(2), Int(100)], [Int(10), Int(5)]),
            """#pragma version 5
int 2
int 100
mulw
int 10
int 5
mulw
divmodw
pop
pop
swap
!
assert
return
""",
        ),
        (
            WideRatio([Int(2), Int(100), Int(3)], [Int(10), Int(5)]),
            """#pragma version 5
int 2
int 100
mulw
int 3
uncover 2
dig 1
*
cover 2
mulw
cover 2
+
swap
int 10
int 5
mulw
divmodw
pop
pop
swap
!
assert
return
""",
        ),
        (
            WideRatio([Int(2), Int(100), Int(3)], [Int(10), Int(5), Int(6)]),
            """#pragma version 5
int 2
int 100
mulw
int 3
uncover 2
dig 1
*
cover 2
mulw
cover 2
+
swap
int 10
int 5
mulw
int 6
uncover 2
dig 1
*
cover 2
mulw
cover 2
+
swap
divmodw
pop
pop
swap
!
assert
return
""",
        ),
        (
            WideRatio([Int(2), Int(100), Int(3), Int(4)], [Int(10), Int(5), Int(6)]),
            """#pragma version 5
int 2
int 100
mulw
int 3
uncover 2
dig 1
*
cover 2
mulw
cover 2
+
swap
int 4
uncover 2
dig 1
*
cover 2
mulw
cover 2
+
swap
int 10
int 5
mulw
int 6
uncover 2
dig 1
*
cover 2
mulw
cover 2
+
swap
divmodw
pop
pop
swap
!
assert
return
""",
        ),
    )

    for program, expected in cases:
        actual = compileTeal(
            program, Mode.Application, version=5, assembleConstants=False
        )
        assert actual == expected.strip()


from .source_map import tabulateSourceMap


def test_source_map1():
    # TODO: This is a BAD TEST. Asserting that the source map will look
    # as below. But the source map NEEDS SIGNIFICANT IMPROMENTS (AND CORRECTIONS)
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
callsub storeValue_0
main_l2:
intc_0 // 1
return

// storeValue
storeValue_0:
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
    actual, lines, sourceMap = compileTeal(
        program, Mode.Application, version=4, assembleConstants=True, sourceMap=True
    )
    assert actual == expected
    table = tabulateSourceMap(lines, sourceMap)

    expected_table = """
   TL | TEAL                  |   PTL | PyTeal                                                     | note                       | file
------+-----------------------+-------+------------------------------------------------------------+----------------------------+----------------------------------
    1 | #pragma version 4     |       |                                                            |                            |
    2 | intcblock 1           |  1577 | If(Txn.application_id() == Int(0)).Then(                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    3 | bytecblock 0x74657374 |  1577 | If(Txn.application_id() == Int(0)).Then(                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    4 | txn ApplicationID     |  1577 | If(Txn.application_id() == Int(0)).Then(                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    5 | pushint 0 // 0        |  1577 | If(Txn.application_id() == Int(0)).Then(                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    6 | ==                    |  1577 | If(Txn.application_id() == Int(0)).Then(                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    7 | bz main_l2            |  1579 | Concat(Bytes("test"), Bytes("test"), Bytes("a")),          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    8 | bytec_0 // "test"     |  1579 | Concat(Bytes("test"), Bytes("test"), Bytes("a")),          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    9 | bytec_0 // "test"     |  1579 | Concat(Bytes("test"), Bytes("test"), Bytes("a")),          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   10 | concat                |  1579 | Concat(Bytes("test"), Bytes("test"), Bytes("a")),          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   11 | pushbytes 0x61 // "a" |  1579 | Concat(Bytes("test"), Bytes("test"), Bytes("a")),          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   12 | concat                |  1579 | Concat(Bytes("test"), Bytes("test"), Bytes("a")),          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   13 | intc_0 // 1           |  1580 | Int(1),                                                    | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   14 | intc_0 // 1           |  1581 | Int(1),                                                    | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   15 | pushint 3 // 3        |  1582 | Int(3),                                                    | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   16 | callsub storeValue_0  |   143 | return SubroutineCall(self, args)                          | subroutine generated       | pyteal/ast/subroutine.py
   17 | main_l2:              |  1585 | Approve(),                                                 | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   18 | intc_0 // 1           |  1585 | Approve(),                                                 | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   19 | return                |  1585 | Approve(),                                                 | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   20 | // storeValue         |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
      | storeValue_0:         |       |                                                            |                            |
   21 | store 3               |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
   22 | store 2               |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
   23 | store 1               |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
   24 | store 0               |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
   25 | load 0                |   365 | loaded = argVar.load()                                     | subroutine generated       | pyteal/ast/subroutine.py
   26 | load 1                |   365 | loaded = argVar.load()                                     | subroutine generated       | pyteal/ast/subroutine.py
   27 | load 2                |   365 | loaded = argVar.load()                                     | subroutine generated       | pyteal/ast/subroutine.py
   28 | +                     |  1573 | return App.globalPut(key, t1 + t2 + t3 + Int(10))          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   29 | load 3                |   365 | loaded = argVar.load()                                     | subroutine generated       | pyteal/ast/subroutine.py
   30 | +                     |  1573 | return App.globalPut(key, t1 + t2 + t3 + Int(10))          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   31 | pushint 10 // 10      |  1573 | return App.globalPut(key, t1 + t2 + t3 + Int(10))          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   32 | +                     |  1573 | return App.globalPut(key, t1 + t2 + t3 + Int(10))          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   33 | app_global_put        |  1573 | return App.globalPut(key, t1 + t2 + t3 + Int(10))          | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   34 | retsub                |  1626 | actual, lines, sourceMap = compileTeal(                    | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
""".strip()

    assert expected_table == table.strip(), print(table)


def test_source_map2():
    # TODO: This is a BAD TEST. Asserting that the source map will look
    # as below. But the source map NEEDS SIGNIFICANT IMPROMENTS (AND CORRECTIONS)
    @Subroutine(TealType.none)
    def swap(x: ScratchVar, y: ScratchVar):
        z = ScratchVar(TealType.anytype)
        return Seq(
            z.store(x.load()),
            x.store(y.load()),
            y.store(z.load()),
        )

    @Subroutine(TealType.none)
    def cat(x, y):
        return Pop(Concat(x, y))

    def swapper():
        a = ScratchVar(TealType.bytes)
        b = ScratchVar(TealType.bytes)
        return Seq(
            a.store(Bytes("hello")),
            b.store(Bytes("goodbye")),
            cat(a.load(), b.load()),
            swap(a, b),
            Assert(a.load() == Bytes("goodbye")),
            Assert(b.load() == Bytes("hello")),
            Int(1000),
        )

    expected = """#pragma version 6
bytecblock 0x68656c6c6f 0x676f6f64627965
bytec_0 // "hello"
store 0
bytec_1 // "goodbye"
store 1
load 0
load 1
callsub cat_1
pushint 0 // 0
pushint 1 // 1
callsub swap_0
load 0
bytec_1 // "goodbye"
==
assert
load 1
bytec_0 // "hello"
==g
assert
pushint 1000 // 1000
return

// swap
swap_0:
store 3
store 2
load 2
loads
store 4
load 2
load 3
loads
stores
load 3
load 4
stores
retsub

// cat
cat_1:
store 6
store 5
load 5
load 6
concat
pop
retsub""".strip()
    actual, lines, sourceMap = compileTeal(
        swapper(), Mode.Application, version=6, assembleConstants=True, sourceMap=True
    )
    assert expected == actual.strip(), print(actual)

    table = tabulateSourceMap(lines, sourceMap)

    expected_table = """
   TL | TEAL                                     |   PTL | PyTeal                                                     | note                       | file
------+------------------------------------------+-------+------------------------------------------------------------+----------------------------+----------------------------------
    1 | #pragma version 6                        |       |                                                            |                            |
    2 | bytecblock 0x68656c6c6f 0x676f6f64627965 |  1695 | a.store(Bytes("hello")),                                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    3 | bytec_0 // "hello"                       |  1695 | a.store(Bytes("hello")),                                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    4 | store 0                                  |  1695 | a.store(Bytes("hello")),                                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    5 | bytec_1 // "goodbye"                     |  1696 | b.store(Bytes("goodbye")),                                 | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    6 | store 1                                  |  1696 | b.store(Bytes("goodbye")),                                 | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    7 | load 0                                   |  1697 | cat(a.load(), b.load()),                                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    8 | load 1                                   |  1697 | cat(a.load(), b.load()),                                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
    9 | callsub cat_1                            |   143 | return SubroutineCall(self, args)                          | subroutine generated       | pyteal/ast/subroutine.py
   10 | pushint 0 // 0                           |   230 | return arg.index() if isinstance(arg, ScratchVar) else arg | subroutine generated       | pyteal/ast/subroutine.py
   11 | pushint 1 // 1                           |   230 | return arg.index() if isinstance(arg, ScratchVar) else arg | subroutine generated       | pyteal/ast/subroutine.py
   12 | callsub swap_0                           |   143 | return SubroutineCall(self, args)                          | subroutine generated       | pyteal/ast/subroutine.py
   13 | load 0                                   |  1699 | Assert(a.load() == Bytes("goodbye")),                      | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   14 | bytec_1 // "goodbye"                     |  1699 | Assert(a.load() == Bytes("goodbye")),                      | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   15 | ==                                       |  1699 | Assert(a.load() == Bytes("goodbye")),                      | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   16 | assert                                   |  1699 | Assert(a.load() == Bytes("goodbye")),                      | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   17 | load 1                                   |  1700 | Assert(b.load() == Bytes("hello")),                        | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   18 | bytec_0 // "hello"                       |  1700 | Assert(b.load() == Bytes("hello")),                        | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   19 | ==                                       |  1700 | Assert(b.load() == Bytes("hello")),                        | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   20 | assert                                   |  1700 | Assert(b.load() == Bytes("hello")),                        | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   21 | pushint 1000 // 1000                     |  1701 | Int(1000),                                                 | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   22 | return                                   |  1752 | actual, lines, sourceMap = compileTeal(                    | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   23 | // swap                                  |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
      | swap_0:                                  |       |                                                            |                            |
   24 | store 3                                  |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
   25 | store 2                                  |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
   26 | load 2                                   |  1682 | z.store(x.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   27 | loads                                    |  1682 | z.store(x.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   28 | store 4                                  |  1682 | z.store(x.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   29 | load 2                                   |  1683 | x.store(y.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   30 | load 3                                   |  1683 | x.store(y.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   31 | loads                                    |  1683 | x.store(y.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   32 | stores                                   |  1683 | x.store(y.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   33 | load 3                                   |  1684 | y.store(z.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   34 | load 4                                   |  1684 | y.store(z.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   35 | stores                                   |  1684 | y.store(z.load()),                                         | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   36 | retsub                                   |  1752 | actual, lines, sourceMap = compileTeal(                    | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   37 | // cat                                   |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
      | cat_1:                                   |       |                                                            |                            |
   38 | store 6                                  |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
   39 | store 5                                  |   384 | bodyOps = [var.slot.store() for var in argumentVars[::-1]] | subroutine generated       | pyteal/ast/subroutine.py
   40 | load 5                                   |   365 | loaded = argVar.load()                                     | subroutine generated       | pyteal/ast/subroutine.py
   41 | load 6                                   |   365 | loaded = argVar.load()                                     | subroutine generated       | pyteal/ast/subroutine.py
   42 | concat                                   |  1689 | return Pop(Concat(x, y))                                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   43 | pop                                      |  1689 | return Pop(Concat(x, y))                                   | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
   44 | retsub                                   |  1752 | actual, lines, sourceMap = compileTeal(                    | PyTeal Unit Test generated | pyteal/compiler/compiler_test.py
""".strip()

    assert expected_table.strip() == table.strip(), print(table)
