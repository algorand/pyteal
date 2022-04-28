import pytest

import pyteal as pt


def test_compile_single():
    expr = pt.Int(1)

    expected = """
#pragma version 2
int 1
return
""".strip()
    actual_application = pt.compileTeal(expr, pt.Mode.Application)
    actual_signature = pt.compileTeal(expr, pt.Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_compile_sequence():
    expr = pt.Seq([pt.Pop(pt.Int(1)), pt.Pop(pt.Int(2)), pt.Int(3) + pt.Int(4)])

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
    actual_application = pt.compileTeal(expr, pt.Mode.Application)
    actual_signature = pt.compileTeal(expr, pt.Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_compile_branch():
    expr = pt.If(pt.Int(1)).Then(pt.Int(2)).Else(pt.Int(3))

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
    actual_application = pt.compileTeal(expr, pt.Mode.Application)
    actual_signature = pt.compileTeal(expr, pt.Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_compile_branch_multiple():
    expr = (
        pt.If(pt.Int(1))
        .Then(pt.Int(2))
        .ElseIf(pt.Int(3))
        .Then(pt.Int(4))
        .Else(pt.Int(5))
    )

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
    actual_application = pt.compileTeal(expr, pt.Mode.Application)
    actual_signature = pt.compileTeal(expr, pt.Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_empty_branch():
    program = pt.Seq(
        [
            pt.If(pt.Txn.application_id() == pt.Int(0)).Then(pt.Seq()),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=5, assembleConstants=False
    )
    assert actual == expected


def test_compile_mode():
    expr = pt.App.globalGet(pt.Bytes("key"))

    expected = """
#pragma version 2
byte "key"
app_global_get
return
""".strip()
    actual_application = pt.compileTeal(expr, pt.Mode.Application)

    assert actual_application == expected

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(expr, pt.Mode.Signature)


def test_compile_version_invalid():
    expr = pt.Int(1)

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(expr, pt.Mode.Signature, version=1)  # too small

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(expr, pt.Mode.Signature, version=7)  # too large

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(expr, pt.Mode.Signature, version=2.0)  # decimal


def test_compile_version_2():
    expr = pt.Int(1)

    expected = """
#pragma version 2
int 1
return
""".strip()
    actual = pt.compileTeal(expr, pt.Mode.Signature, version=2)
    assert actual == expected


def test_compile_version_default():
    expr = pt.Int(1)

    actual_default = pt.compileTeal(expr, pt.Mode.Signature)
    actual_version_2 = pt.compileTeal(expr, pt.Mode.Signature, version=2)
    assert actual_default == actual_version_2


def test_compile_version_3():
    expr = pt.Int(1)

    expected = """
#pragma version 3
int 1
return
""".strip()
    actual = pt.compileTeal(expr, pt.Mode.Signature, version=3)
    assert actual == expected


def test_compile_version_4():
    expr = pt.Int(1)

    expected = """
#pragma version 4
int 1
return
""".strip()
    actual = pt.compileTeal(expr, pt.Mode.Signature, version=4)
    assert actual == expected


def test_compile_version_5():
    expr = pt.Int(1)
    expected = """
#pragma version 5
int 1
return
""".strip()
    actual = pt.compileTeal(expr, pt.Mode.Signature, version=5)
    assert actual == expected


def test_compile_version_6():
    expr = pt.Int(1)
    expected = """
#pragma version 6
int 1
return
""".strip()
    actual = pt.compileTeal(expr, pt.Mode.Signature, version=6)
    assert actual == expected


def test_slot_load_before_store():

    program = pt.AssetHolding.balance(pt.Int(0), pt.Int(0)).value()
    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(program, pt.Mode.Application, version=2)

    program = pt.AssetHolding.balance(pt.Int(0), pt.Int(0)).hasValue()
    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(program, pt.Mode.Application, version=2)

    program = pt.App.globalGetEx(pt.Int(0), pt.Bytes("key")).value()
    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(program, pt.Mode.Application, version=2)

    program = pt.App.globalGetEx(pt.Int(0), pt.Bytes("key")).hasValue()
    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(program, pt.Mode.Application, version=2)

    program = pt.ScratchVar().load()
    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(program, pt.Mode.Application, version=2)


def test_assign_scratch_slots():
    myScratch = pt.ScratchVar(pt.TealType.uint64)
    otherScratch = pt.ScratchVar(pt.TealType.uint64, 1)
    anotherScratch = pt.ScratchVar(pt.TealType.uint64, 0)
    lastScratch = pt.ScratchVar(pt.TealType.uint64)
    prog = pt.Seq(
        [
            myScratch.store(pt.Int(5)),  # Slot 2
            otherScratch.store(pt.Int(0)),  # Slot 1
            anotherScratch.store(pt.Int(7)),  # Slot 0
            lastScratch.store(pt.Int(9)),  # Slot 3
            pt.Approve(),
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
    actual = pt.compileTeal(prog, mode=pt.Mode.Signature, version=4)
    assert actual == expected


def test_scratchvar_double_assign_invalid():
    myvar = pt.ScratchVar(pt.TealType.uint64, 10)
    otherVar = pt.ScratchVar(pt.TealType.uint64, 10)
    prog = pt.Seq([myvar.store(pt.Int(5)), otherVar.store(pt.Int(0)), pt.Approve()])
    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(prog, mode=pt.Mode.Signature, version=4)


def test_assembleConstants():
    program = pt.Itob(pt.Int(1) + pt.Int(1) + pt.Tmpl.Int("TMPL_VAR")) == pt.Concat(
        pt.Bytes("test"), pt.Bytes("test"), pt.Bytes("test2")
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
    actualNoAssemble = pt.compileTeal(
        program, pt.Mode.Application, version=3, assembleConstants=False
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
    actualAssemble = pt.compileTeal(
        program, pt.Mode.Application, version=3, assembleConstants=True
    )
    assert expectedAssemble == actualAssemble

    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(program, pt.Mode.Application, version=2, assembleConstants=True)


def test_compile_while():
    i = pt.ScratchVar()
    program = pt.Seq(
        [
            i.store(pt.Int(0)),
            pt.While(i.load() < pt.Int(2)).Do(pt.Seq([i.store(i.load() + pt.Int(1))])),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual

    # nested
    i = pt.ScratchVar()
    j = pt.ScratchVar()

    program = pt.Seq(
        [
            i.store(pt.Int(0)),
            pt.While(i.load() < pt.Int(2)).Do(
                pt.Seq(
                    [
                        j.store(pt.Int(0)),
                        pt.While(j.load() < pt.Int(5)).Do(
                            pt.Seq([j.store(j.load() + pt.Int(1))])
                        ),
                        i.store(i.load() + pt.Int(1)),
                    ]
                )
            ),
            pt.Approve(),
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

    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual


def test_compile_for():
    i = pt.ScratchVar()
    program = pt.Seq(
        [
            pt.For(
                i.store(pt.Int(0)), i.load() < pt.Int(10), i.store(i.load() + pt.Int(1))
            ).Do(pt.Seq([pt.App.globalPut(pt.Itob(i.load()), i.load() * pt.Int(2))])),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual

    # nested
    i = pt.ScratchVar()
    j = pt.ScratchVar()
    program = pt.Seq(
        [
            pt.For(
                i.store(pt.Int(0)), i.load() < pt.Int(10), i.store(i.load() + pt.Int(1))
            ).Do(
                pt.Seq(
                    [
                        pt.For(
                            j.store(pt.Int(0)),
                            j.load() < pt.Int(4),
                            j.store(j.load() + pt.Int(2)),
                        ).Do(
                            pt.Seq(
                                [
                                    pt.App.globalPut(
                                        pt.Itob(j.load()), j.load() * pt.Int(2)
                                    )
                                ]
                            )
                        )
                    ]
                )
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual


def test_compile_break():

    # pt.While
    i = pt.ScratchVar()
    program = pt.Seq(
        [
            i.store(pt.Int(0)),
            pt.While(i.load() < pt.Int(3)).Do(
                pt.Seq(
                    [
                        pt.If(i.load() == pt.Int(2), pt.Break()),
                        i.store(i.load() + pt.Int(1)),
                    ]
                )
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual

    # pt.For
    i = pt.ScratchVar()
    program = pt.Seq(
        [
            pt.For(
                i.store(pt.Int(0)), i.load() < pt.Int(10), i.store(i.load() + pt.Int(1))
            ).Do(
                pt.Seq(
                    [
                        pt.If(i.load() == pt.Int(4), pt.Break()),
                        pt.App.globalPut(pt.Itob(i.load()), i.load() * pt.Int(2)),
                    ]
                )
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual


def test_compile_continue():
    # pt.While
    i = pt.ScratchVar()
    program = pt.Seq(
        [
            i.store(pt.Int(0)),
            pt.While(i.load() < pt.Int(3)).Do(
                pt.Seq(
                    [
                        pt.If(i.load() == pt.Int(2), pt.Continue()),
                        i.store(i.load() + pt.Int(1)),
                    ]
                )
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual

    # pt.For
    i = pt.ScratchVar()
    program = pt.Seq(
        [
            pt.For(
                i.store(pt.Int(0)), i.load() < pt.Int(10), i.store(i.load() + pt.Int(1))
            ).Do(
                pt.Seq(
                    [
                        pt.If(i.load() == pt.Int(4), pt.Continue()),
                        pt.App.globalPut(pt.Itob(i.load()), i.load() * pt.Int(2)),
                    ]
                )
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual


def test_compile_continue_break_nested():

    i = pt.ScratchVar()
    program = pt.Seq(
        [
            i.store(pt.Int(0)),
            pt.While(i.load() < pt.Int(10)).Do(
                pt.Seq(
                    [
                        i.store(i.load() + pt.Int(1)),
                        pt.If(i.load() < pt.Int(4), pt.Continue(), pt.Break()),
                    ]
                )
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual

    i = pt.ScratchVar()
    program = pt.Seq(
        [
            i.store(pt.Int(0)),
            pt.While(i.load() < pt.Int(10)).Do(
                pt.Seq(
                    [
                        pt.If(i.load() == pt.Int(8), pt.Break()),
                        pt.While(i.load() < pt.Int(6)).Do(
                            pt.Seq(
                                [
                                    pt.If(i.load() == pt.Int(3), pt.Break()),
                                    i.store(i.load() + pt.Int(1)),
                                ]
                            )
                        ),
                        pt.If(i.load() < pt.Int(5), pt.Continue()),
                        i.store(i.load() + pt.Int(1)),
                    ]
                )
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert expected == actual


def test_compile_subroutine_unsupported():
    @pt.Subroutine(pt.TealType.none)
    def storeValue(value: pt.Expr) -> pt.Expr:
        return pt.App.globalPut(pt.Bytes("key"), value)

    program = pt.Seq(
        [
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                storeValue(pt.Txn.application_args[0])
            ),
            pt.Approve(),
        ]
    )

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(program, pt.Mode.Application, version=3)


def test_compile_subroutine_no_return():
    @pt.Subroutine(pt.TealType.none)
    def storeValue(value: pt.Expr) -> pt.Expr:
        return pt.App.globalPut(pt.Bytes("key"), value)

    program = pt.Seq(
        [
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                storeValue(pt.Txn.application_args[0])
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_with_return():
    @pt.Subroutine(pt.TealType.none)
    def storeValue(value: pt.Expr) -> pt.Expr:
        return pt.App.globalPut(pt.Bytes("key"), value)

    @pt.Subroutine(pt.TealType.bytes)
    def getValue() -> pt.Expr:
        return pt.App.globalGet(pt.Bytes("key"))

    program = pt.Seq(
        [
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                storeValue(pt.Txn.application_args[0])
            ),
            pt.If(getValue() == pt.Bytes("fail")).Then(pt.Reject()),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_many_args():
    @pt.Subroutine(pt.TealType.uint64)
    def calculateSum(
        a1: pt.Expr, a2: pt.Expr, a3: pt.Expr, a4: pt.Expr, a5: pt.Expr, a6: pt.Expr
    ) -> pt.Expr:
        return a1 + a2 + a3 + a4 + a5 + a6

    program = pt.Return(
        calculateSum(pt.Int(1), pt.Int(2), pt.Int(3), pt.Int(4), pt.Int(5), pt.Int(6))
        == pt.Int(1 + 2 + 3 + 4 + 5 + 6)
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_recursive():
    @pt.Subroutine(pt.TealType.uint64)
    def isEven(i: pt.Expr) -> pt.Expr:
        return (
            pt.If(i == pt.Int(0))
            .Then(pt.Int(1))
            .ElseIf(i == pt.Int(1))
            .Then(pt.Int(0))
            .Else(isEven(i - pt.Int(2)))
        )

    program = pt.Return(isEven(pt.Int(6)))

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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_recursive_5():
    @pt.Subroutine(pt.TealType.uint64)
    def isEven(i: pt.Expr) -> pt.Expr:
        return (
            pt.If(i == pt.Int(0))
            .Then(pt.Int(1))
            .ElseIf(i == pt.Int(1))
            .Then(pt.Int(0))
            .Else(isEven(i - pt.Int(2)))
        )

    program = pt.Return(isEven(pt.Int(6)))

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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=5, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_recursive_multiple_args():
    @pt.Subroutine(pt.TealType.uint64)
    def multiplyByAdding(a, b):
        return (
            pt.If(a == pt.Int(0))
            .Then(pt.Return(pt.Int(0)))
            .Else(pt.Return(b + multiplyByAdding(a - pt.Int(1), b)))
        )

    program = pt.Return(multiplyByAdding(pt.Int(3), pt.Int(5)))

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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_recursive_multiple_args_5():
    @pt.Subroutine(pt.TealType.uint64)
    def multiplyByAdding(a, b):
        return (
            pt.If(a == pt.Int(0))
            .Then(pt.Return(pt.Int(0)))
            .Else(pt.Return(b + multiplyByAdding(a - pt.Int(1), b)))
        )

    program = pt.Return(multiplyByAdding(pt.Int(3), pt.Int(5)))

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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=5, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_mutually_recursive_4():
    @pt.Subroutine(pt.TealType.uint64)
    def isEven(i: pt.Expr) -> pt.Expr:
        return pt.If(i == pt.Int(0), pt.Int(1), pt.Not(isOdd(i - pt.Int(1))))

    @pt.Subroutine(pt.TealType.uint64)
    def isOdd(i: pt.Expr) -> pt.Expr:
        return pt.If(i == pt.Int(0), pt.Int(0), pt.Not(isEven(i - pt.Int(1))))

    program = pt.Return(isEven(pt.Int(6)))

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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_mutually_recursive_5():
    @pt.Subroutine(pt.TealType.uint64)
    def isEven(i: pt.Expr) -> pt.Expr:
        return pt.If(i == pt.Int(0), pt.Int(1), pt.Not(isOdd(i - pt.Int(1))))

    @pt.Subroutine(pt.TealType.uint64)
    def isOdd(i: pt.Expr) -> pt.Expr:
        return pt.If(i == pt.Int(0), pt.Int(0), pt.Not(isEven(i - pt.Int(1))))

    program = pt.Return(isEven(pt.Int(6)))

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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=5, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_mutually_recursive_different_arg_count_4():
    @pt.Subroutine(pt.TealType.uint64)
    def factorial(i: pt.Expr) -> pt.Expr:
        return pt.If(
            i <= pt.Int(1),
            pt.Int(1),
            factorial_intermediate(i - pt.Int(1), pt.Bytes("inconsequential")) * i,
        )

    @pt.Subroutine(pt.TealType.uint64)
    def factorial_intermediate(i: pt.Expr, j: pt.Expr) -> pt.Expr:
        return pt.Seq(pt.Pop(j), factorial(i))

    program = pt.Return(factorial(pt.Int(4)) == pt.Int(24))

    expected = """#pragma version 4
int 4
callsub factorial_0
int 24
==
return

// factorial
factorial_0:
store 0
load 0
int 1
<=
bnz factorial_0_l2
load 0
int 1
-
byte "inconsequential"
load 0
dig 2
dig 2
callsub factorialintermediate_1
swap
store 0
swap
pop
swap
pop
load 0
*
b factorial_0_l3
factorial_0_l2:
int 1
factorial_0_l3:
retsub

// factorial_intermediate
factorialintermediate_1:
store 2
store 1
load 2
pop
load 1
load 1
load 2
dig 2
callsub factorial_0
store 1
store 2
load 1
swap
store 1
swap
pop
retsub
    """.strip()
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_mutually_recursive_different_arg_count_5():
    @pt.Subroutine(pt.TealType.uint64)
    def factorial(i: pt.Expr) -> pt.Expr:
        return pt.If(
            i <= pt.Int(1),
            pt.Int(1),
            factorial_intermediate(i - pt.Int(1), pt.Bytes("inconsequential")) * i,
        )

    @pt.Subroutine(pt.TealType.uint64)
    def factorial_intermediate(i: pt.Expr, j: pt.Expr) -> pt.Expr:
        return pt.Seq(pt.Log(j), factorial(i))

    program = pt.Return(factorial(pt.Int(4)) == pt.Int(24))

    expected = """#pragma version 5
int 4
callsub factorial_0
int 24
==
return

// factorial
factorial_0:
store 0
load 0
int 1
<=
bnz factorial_0_l2
load 0
int 1
-
byte "inconsequential"
load 0
cover 2
callsub factorialintermediate_1
swap
store 0
load 0
*
b factorial_0_l3
factorial_0_l2:
int 1
factorial_0_l3:
retsub

// factorial_intermediate
factorialintermediate_1:
store 2
store 1
load 2
log
load 1
load 1
load 2
uncover 2
callsub factorial_0
cover 2
store 2
store 1
retsub
    """.strip()
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=5, assembleConstants=False
    )
    assert actual == expected


def test_compile_loop_in_subroutine():
    @pt.Subroutine(pt.TealType.none)
    def setState(value: pt.Expr) -> pt.Expr:
        i = pt.ScratchVar()
        return pt.For(
            i.store(pt.Int(0)), i.load() < pt.Int(10), i.store(i.load() + pt.Int(1))
        ).Do(pt.App.globalPut(pt.Itob(i.load()), value))

    program = pt.Seq([setState(pt.Bytes("value")), pt.Approve()])

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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_invalid_name():
    def tmp() -> pt.Expr:
        return pt.Int(1)

    tmp.__name__ = "invalid-;)"

    program = pt.Subroutine(pt.TealType.uint64)(tmp)()
    expected = """#pragma version 4
callsub invalid_0
return

// invalid-;)
invalid_0:
int 1
retsub
    """.strip()
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=False
    )
    assert actual == expected


def test_compile_subroutine_assemble_constants():
    @pt.Subroutine(pt.TealType.none)
    def storeValue(key: pt.Expr, t1: pt.Expr, t2: pt.Expr, t3: pt.Expr) -> pt.Expr:
        return pt.App.globalPut(key, t1 + t2 + t3 + pt.Int(10))

    program = pt.Seq(
        [
            pt.If(pt.Txn.application_id() == pt.Int(0)).Then(
                storeValue(
                    pt.Concat(pt.Bytes("test"), pt.Bytes("test"), pt.Bytes("a")),
                    pt.Int(1),
                    pt.Int(1),
                    pt.Int(3),
                )
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, pt.Mode.Application, version=4, assembleConstants=True
    )
    assert actual == expected


def test_compile_wide_ratio():
    cases = (
        (
            pt.WideRatio([pt.Int(2), pt.Int(100)], [pt.Int(5)]),
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
            pt.WideRatio([pt.Int(2), pt.Int(100)], [pt.Int(10), pt.Int(5)]),
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
            pt.WideRatio([pt.Int(2), pt.Int(100), pt.Int(3)], [pt.Int(10), pt.Int(5)]),
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
            pt.WideRatio(
                [pt.Int(2), pt.Int(100), pt.Int(3)], [pt.Int(10), pt.Int(5), pt.Int(6)]
            ),
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
            pt.WideRatio(
                [pt.Int(2), pt.Int(100), pt.Int(3), pt.Int(4)],
                [pt.Int(10), pt.Int(5), pt.Int(6)],
            ),
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
        actual = pt.compileTeal(
            program, pt.Mode.Application, version=5, assembleConstants=False
        )
        assert actual == expected.strip()
