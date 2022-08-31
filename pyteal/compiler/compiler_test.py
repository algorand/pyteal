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
        pt.compileTeal(expr, pt.Mode.Signature, version=9)  # too large

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
load 0
int 2
==
bnz main_l1
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

    # pt.While
    program = pt.Seq(
        i.store(pt.Int(0)),
        pt.While(i.load() < pt.Int(30)).Do(
            pt.Seq(
                i.store(i.load() + pt.Int(1)),
                pt.Continue(),
            )
        ),
        pt.Return(pt.Int(1)),
    )

    expected = """#pragma version 4
int 0
store 0
main_l1:
load 0
int 30
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
main_l1:
load 0
int 10
<
bz main_l3
load 0
int 1
+
store 0
load 0
int 4
<
bnz main_l1
main_l3:
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
bnz main_l1
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


def test_compile_subroutine_deferred_expr():
    @pt.Subroutine(pt.TealType.none)
    def deferredExample(value: pt.Expr) -> pt.Expr:
        return pt.Seq(
            pt.If(value == pt.Int(0)).Then(pt.Return()),
            pt.If(value == pt.Int(1)).Then(pt.Approve()),
            pt.If(value == pt.Int(2)).Then(pt.Reject()),
            pt.If(value == pt.Int(3)).Then(pt.Err()),
        )

    program = pt.Seq(deferredExample(pt.Int(10)), pt.Approve())

    expected_no_deferred = """#pragma version 6
int 10
callsub deferredExample_0
int 1
return

// deferredExample
deferredExample_0:
store 0
load 0
int 0
==
bnz deferredExample_0_l7
load 0
int 1
==
bnz deferredExample_0_l6
load 0
int 2
==
bnz deferredExample_0_l5
load 0
int 3
==
bz deferredExample_0_l8
err
deferredExample_0_l5:
int 0
return
deferredExample_0_l6:
int 1
return
deferredExample_0_l7:
retsub
deferredExample_0_l8:
retsub
    """.strip()
    actual_no_deferred = pt.compileTeal(
        program, pt.Mode.Application, version=6, assembleConstants=False
    )
    assert actual_no_deferred == expected_no_deferred

    # manually add deferred expression to SubroutineDefinition
    declaration = deferredExample.subroutine.get_declaration()
    declaration.deferred_expr = pt.Pop(pt.Bytes("deferred"))

    expected_deferred = """#pragma version 6
int 10
callsub deferredExample_0
int 1
return

// deferredExample
deferredExample_0:
store 0
load 0
int 0
==
bnz deferredExample_0_l7
load 0
int 1
==
bnz deferredExample_0_l6
load 0
int 2
==
bnz deferredExample_0_l5
load 0
int 3
==
bz deferredExample_0_l8
err
deferredExample_0_l5:
int 0
return
deferredExample_0_l6:
int 1
return
deferredExample_0_l7:
byte "deferred"
pop
retsub
deferredExample_0_l8:
byte "deferred"
pop
retsub
    """.strip()
    actual_deferred = pt.compileTeal(
        program, pt.Mode.Application, version=6, assembleConstants=False
    )
    assert actual_deferred == expected_deferred


def test_compile_subroutine_deferred_expr_empty():
    @pt.Subroutine(pt.TealType.none)
    def empty() -> pt.Expr:
        return pt.Return()

    program = pt.Seq(empty(), pt.Approve())

    expected_no_deferred = """#pragma version 6
callsub empty_0
int 1
return

// empty
empty_0:
retsub
    """.strip()
    actual_no_deferred = pt.compileTeal(
        program, pt.Mode.Application, version=6, assembleConstants=False
    )
    assert actual_no_deferred == expected_no_deferred

    # manually add deferred expression to SubroutineDefinition
    declaration = empty.subroutine.get_declaration()
    declaration.deferred_expr = pt.Pop(pt.Bytes("deferred"))

    expected_deferred = """#pragma version 6
callsub empty_0
int 1
return

// empty
empty_0:
byte "deferred"
pop
retsub
    """.strip()
    actual_deferred = pt.compileTeal(
        program, pt.Mode.Application, version=6, assembleConstants=False
    )
    assert actual_deferred == expected_deferred


def test_compileSubroutine_deferred_block_malformed():
    class BadRetsub(pt.Expr):
        def type_of(self) -> pt.TealType:
            return pt.TealType.none

        def has_return(self) -> bool:
            return True

        def __str__(self) -> str:
            return "(BadRetsub)"

        def __teal__(
            self, options: pt.CompileOptions
        ) -> tuple[pt.TealBlock, pt.TealSimpleBlock]:
            block = pt.TealSimpleBlock(
                [
                    pt.TealOp(self, pt.Op.int, 1),
                    pt.TealOp(self, pt.Op.pop),
                    pt.TealOp(self, pt.Op.retsub),
                ]
            )

            return block, block

    @pt.Subroutine(pt.TealType.none)
    def bad() -> pt.Expr:
        return BadRetsub()

    program = pt.Seq(bad(), pt.Approve())

    # manually add deferred expression to SubroutineDefinition
    declaration = bad.subroutine.get_declaration()
    declaration.deferred_expr = pt.Pop(pt.Bytes("deferred"))

    with pytest.raises(
        pt.TealInternalError,
        match=r"^Expected retsub to be the only op in the block, but there are 3 ops$",
    ):
        pt.compileTeal(program, pt.Mode.Application, version=6, assembleConstants=False)


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


def test_compile_abi_subroutine_return():
    @pt.ABIReturnSubroutine
    def abi_sum(
        toSum: pt.abi.DynamicArray[pt.abi.Uint64], *, output: pt.abi.Uint64
    ) -> pt.Expr:
        i = pt.ScratchVar(pt.TealType.uint64)
        valueAtIndex = pt.abi.Uint64()
        return pt.Seq(
            output.set(0),
            pt.For(
                i.store(pt.Int(0)),
                i.load() < toSum.length(),
                i.store(i.load() + pt.Int(1)),
            ).Do(
                pt.Seq(
                    toSum[i.load()].store_into(valueAtIndex),
                    output.set(output.get() + valueAtIndex.get()),
                )
            ),
        )

    program = pt.Seq(
        (to_sum_arr := pt.abi.make(pt.abi.DynamicArray[pt.abi.Uint64])).decode(
            pt.Txn.application_args[1]
        ),
        (res := pt.abi.Uint64()).set(abi_sum(to_sum_arr)),
        pt.abi.MethodReturn(res),
        pt.Approve(),
    )

    expected_sum = """#pragma version 6
txna ApplicationArgs 1
store 0
load 0
callsub abisum_0
store 1
byte 0x151f7c75
load 1
itob
concat
log
int 1
return

// abi_sum
abisum_0:
store 2
int 0
store 3
int 0
store 4
abisum_0_l1:
load 4
load 2
int 0
extract_uint16
store 6
load 6
<
bz abisum_0_l3
load 2
int 8
load 4
*
int 2
+
extract_uint64
store 5
load 3
load 5
+
store 3
load 4
int 1
+
store 4
b abisum_0_l1
abisum_0_l3:
load 3
retsub
    """.strip()

    actual_sum = pt.compileTeal(program, pt.Mode.Application, version=6)
    assert expected_sum == actual_sum

    @pt.ABIReturnSubroutine
    def conditional_factorial(
        _factor: pt.abi.Uint64, *, output: pt.abi.Uint64
    ) -> pt.Expr:
        i = pt.ScratchVar(pt.TealType.uint64)

        return pt.Seq(
            output.set(1),
            pt.If(_factor.get() <= pt.Int(1))
            .Then(pt.Return())
            .Else(
                pt.For(
                    i.store(_factor.get()),
                    i.load() > pt.Int(1),
                    i.store(i.load() - pt.Int(1)),
                ).Do(output.set(output.get() * i.load())),
            ),
        )

    program_cond_factorial = pt.Seq(
        (factor := pt.abi.Uint64()).decode(pt.Txn.application_args[1]),
        (res := pt.abi.Uint64()).set(conditional_factorial(factor)),
        pt.abi.MethodReturn(res),
        pt.Approve(),
    )

    expected_conditional_factorial = """#pragma version 6
txna ApplicationArgs 1
btoi
store 0
load 0
callsub conditionalfactorial_0
store 1
byte 0x151f7c75
load 1
itob
concat
log
int 1
return

// conditional_factorial
conditionalfactorial_0:
store 2
int 1
store 3
load 2
int 1
<=
bnz conditionalfactorial_0_l4
load 2
store 4
conditionalfactorial_0_l2:
load 4
int 1
>
bz conditionalfactorial_0_l5
load 3
load 4
*
store 3
load 4
int 1
-
store 4
b conditionalfactorial_0_l2
conditionalfactorial_0_l4:
load 3
retsub
conditionalfactorial_0_l5:
load 3
retsub
    """.strip()

    actual_conditional_factorial = pt.compileTeal(
        program_cond_factorial, pt.Mode.Application, version=6
    )
    assert actual_conditional_factorial == expected_conditional_factorial

    @pt.ABIReturnSubroutine
    def load_b4_set(*, output: pt.abi.Bool):
        return pt.Return()

    program_load_b4_set_broken = pt.Seq(
        (_ := pt.abi.Bool()).set(load_b4_set()), pt.Approve()
    )

    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(program_load_b4_set_broken, pt.Mode.Application, version=6)

    @pt.ABIReturnSubroutine
    def access_b4_store(magic_num: pt.abi.Uint64, *, output: pt.abi.Uint64):
        return pt.Seq(output.set(output.get() ^ magic_num.get()))

    program_access_b4_store_broken = pt.Seq(
        (other_party_magic := pt.abi.Uint64()).decode(pt.Txn.application_args[1]),
        (_ := pt.abi.Uint64()).set(access_b4_store(other_party_magic)),
        pt.Approve(),
    )

    with pytest.raises(pt.TealInternalError):
        pt.compileTeal(program_access_b4_store_broken, pt.Mode.Application, version=6)


def test_router_app():
    def add_methods_to_router(router: pt.Router):
        @pt.ABIReturnSubroutine
        def add(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() + b.get())

        meth = router.add_method_handler(add)
        assert meth.method_signature() == "add(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def sub(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() - b.get())

        meth = router.add_method_handler(sub)
        assert meth.method_signature() == "sub(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def mul(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() * b.get())

        meth = router.add_method_handler(mul)
        assert meth.method_signature() == "mul(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def div(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() / b.get())

        meth = router.add_method_handler(div)
        assert meth.method_signature() == "div(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def mod(
            a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64
        ) -> pt.Expr:
            return output.set(a.get() % b.get())

        meth = router.add_method_handler(mod)
        assert meth.method_signature() == "mod(uint64,uint64)uint64"

        @pt.ABIReturnSubroutine
        def all_laid_to_args(
            _a: pt.abi.Uint64,
            _b: pt.abi.Uint64,
            _c: pt.abi.Uint64,
            _d: pt.abi.Uint64,
            _e: pt.abi.Uint64,
            _f: pt.abi.Uint64,
            _g: pt.abi.Uint64,
            _h: pt.abi.Uint64,
            _i: pt.abi.Uint64,
            _j: pt.abi.Uint64,
            _k: pt.abi.Uint64,
            _l: pt.abi.Uint64,
            _m: pt.abi.Uint64,
            _n: pt.abi.Uint64,
            _o: pt.abi.Uint64,
            _p: pt.abi.Uint64,
            *,
            output: pt.abi.Uint64,
        ):
            return output.set(
                _a.get()
                + _b.get()
                + _c.get()
                + _d.get()
                + _e.get()
                + _f.get()
                + _g.get()
                + _h.get()
                + _i.get()
                + _j.get()
                + _k.get()
                + _l.get()
                + _m.get()
                + _n.get()
                + _o.get()
                + _p.get()
            )

        meth = router.add_method_handler(all_laid_to_args)
        assert (
            meth.method_signature()
            == "all_laid_to_args(uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64)uint64"
        )

        @pt.ABIReturnSubroutine
        def empty_return_subroutine() -> pt.Expr:
            return pt.Log(pt.Bytes("appear in both approval and clear state"))

        meth = router.add_method_handler(
            empty_return_subroutine,
            method_config=pt.MethodConfig(
                no_op=pt.CallConfig.CALL,
                opt_in=pt.CallConfig.ALL,
                clear_state=pt.CallConfig.CALL,
            ),
        )
        assert meth.method_signature() == "empty_return_subroutine()void"

        @pt.ABIReturnSubroutine
        def log_1(*, output: pt.abi.Uint64) -> pt.Expr:
            return output.set(1)

        meth = router.add_method_handler(
            log_1,
            method_config=pt.MethodConfig(
                no_op=pt.CallConfig.CALL,
                opt_in=pt.CallConfig.CALL,
                clear_state=pt.CallConfig.CALL,
            ),
        )

        assert meth.method_signature() == "log_1()uint64"

        @pt.ABIReturnSubroutine
        def log_creation(*, output: pt.abi.String) -> pt.Expr:
            return output.set("logging creation")

        meth = router.add_method_handler(
            log_creation, method_config=pt.MethodConfig(no_op=pt.CallConfig.CREATE)
        )
        assert meth.method_signature() == "log_creation()string"

        @pt.ABIReturnSubroutine
        def approve_if_odd(condition_encoding: pt.abi.Uint32) -> pt.Expr:
            return (
                pt.If(condition_encoding.get() % pt.Int(2))
                .Then(pt.Approve())
                .Else(pt.Reject())
            )

        meth = router.add_method_handler(
            approve_if_odd,
            method_config=pt.MethodConfig(
                no_op=pt.CallConfig.NEVER, clear_state=pt.CallConfig.CALL
            ),
        )
        assert meth.method_signature() == "approve_if_odd(uint32)void"

    on_completion_actions = pt.BareCallActions(
        opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes("optin call"))),
        clear_state=pt.OnCompleteAction.call_only(pt.Approve()),
    )

    _router_with_oc = pt.Router(
        "ASimpleQuestionablyRobustContract", on_completion_actions
    )
    add_methods_to_router(_router_with_oc)
    (
        actual_ap_with_oc_compiled,
        actual_csp_with_oc_compiled,
        _,
    ) = _router_with_oc.compile_program(version=6)

    expected_ap_with_oc = """#pragma version 6
txn NumAppArgs
int 0
==
bnz main_l20
txna ApplicationArgs 0
method "add(uint64,uint64)uint64"
==
bnz main_l19
txna ApplicationArgs 0
method "sub(uint64,uint64)uint64"
==
bnz main_l18
txna ApplicationArgs 0
method "mul(uint64,uint64)uint64"
==
bnz main_l17
txna ApplicationArgs 0
method "div(uint64,uint64)uint64"
==
bnz main_l16
txna ApplicationArgs 0
method "mod(uint64,uint64)uint64"
==
bnz main_l15
txna ApplicationArgs 0
method "all_laid_to_args(uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64)uint64"
==
bnz main_l14
txna ApplicationArgs 0
method "empty_return_subroutine()void"
==
bnz main_l13
txna ApplicationArgs 0
method "log_1()uint64"
==
bnz main_l12
txna ApplicationArgs 0
method "log_creation()string"
==
bnz main_l11
err
main_l11:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
==
&&
assert
callsub logcreation_8
store 67
byte 0x151f7c75
load 67
concat
log
int 1
return
main_l12:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
txn OnCompletion
int OptIn
==
txn ApplicationID
int 0
!=
&&
||
assert
callsub log1_7
store 65
byte 0x151f7c75
load 65
itob
concat
log
int 1
return
main_l13:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
txn OnCompletion
int OptIn
==
||
assert
callsub emptyreturnsubroutine_6
int 1
return
main_l14:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 30
txna ApplicationArgs 2
btoi
store 31
txna ApplicationArgs 3
btoi
store 32
txna ApplicationArgs 4
btoi
store 33
txna ApplicationArgs 5
btoi
store 34
txna ApplicationArgs 6
btoi
store 35
txna ApplicationArgs 7
btoi
store 36
txna ApplicationArgs 8
btoi
store 37
txna ApplicationArgs 9
btoi
store 38
txna ApplicationArgs 10
btoi
store 39
txna ApplicationArgs 11
btoi
store 40
txna ApplicationArgs 12
btoi
store 41
txna ApplicationArgs 13
btoi
store 42
txna ApplicationArgs 14
btoi
store 43
txna ApplicationArgs 15
store 46
load 46
int 0
extract_uint64
store 44
load 46
int 8
extract_uint64
store 45
load 30
load 31
load 32
load 33
load 34
load 35
load 36
load 37
load 38
load 39
load 40
load 41
load 42
load 43
load 44
load 45
callsub alllaidtoargs_5
store 47
byte 0x151f7c75
load 47
itob
concat
log
int 1
return
main_l15:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 24
txna ApplicationArgs 2
btoi
store 25
load 24
load 25
callsub mod_4
store 26
byte 0x151f7c75
load 26
itob
concat
log
int 1
return
main_l16:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 18
txna ApplicationArgs 2
btoi
store 19
load 18
load 19
callsub div_3
store 20
byte 0x151f7c75
load 20
itob
concat
log
int 1
return
main_l17:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 12
txna ApplicationArgs 2
btoi
store 13
load 12
load 13
callsub mul_2
store 14
byte 0x151f7c75
load 14
itob
concat
log
int 1
return
main_l18:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 6
txna ApplicationArgs 2
btoi
store 7
load 6
load 7
callsub sub_1
store 8
byte 0x151f7c75
load 8
itob
concat
log
int 1
return
main_l19:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 0
txna ApplicationArgs 2
btoi
store 1
load 0
load 1
callsub add_0
store 2
byte 0x151f7c75
load 2
itob
concat
log
int 1
return
main_l20:
txn OnCompletion
int OptIn
==
bnz main_l22
err
main_l22:
txn ApplicationID
int 0
!=
assert
byte "optin call"
log
int 1
return

// add
add_0:
store 4
store 3
load 3
load 4
+
store 5
load 5
retsub

// sub
sub_1:
store 10
store 9
load 9
load 10
-
store 11
load 11
retsub

// mul
mul_2:
store 16
store 15
load 15
load 16
*
store 17
load 17
retsub

// div
div_3:
store 22
store 21
load 21
load 22
/
store 23
load 23
retsub

// mod
mod_4:
store 28
store 27
load 27
load 28
%
store 29
load 29
retsub

// all_laid_to_args
alllaidtoargs_5:
store 63
store 62
store 61
store 60
store 59
store 58
store 57
store 56
store 55
store 54
store 53
store 52
store 51
store 50
store 49
store 48
load 48
load 49
+
load 50
+
load 51
+
load 52
+
load 53
+
load 54
+
load 55
+
load 56
+
load 57
+
load 58
+
load 59
+
load 60
+
load 61
+
load 62
+
load 63
+
store 64
load 64
retsub

// empty_return_subroutine
emptyreturnsubroutine_6:
byte "appear in both approval and clear state"
log
retsub

// log_1
log1_7:
int 1
store 66
load 66
retsub

// log_creation
logcreation_8:
byte 0x00106c6f6767696e67206372656174696f6e
store 68
load 68
retsub""".strip()

    assert expected_ap_with_oc == actual_ap_with_oc_compiled

    expected_csp_with_oc = """#pragma version 6
txn NumAppArgs
int 0
==
bnz main_l8
txna ApplicationArgs 0
method "empty_return_subroutine()void"
==
bnz main_l7
txna ApplicationArgs 0
method "log_1()uint64"
==
bnz main_l6
txna ApplicationArgs 0
method "approve_if_odd(uint32)void"
==
bnz main_l5
err
main_l5:
txna ApplicationArgs 1
int 0
extract_uint32
store 2
load 2
callsub approveifodd_2
int 1
return
main_l6:
callsub log1_1
store 1
byte 0x151f7c75
load 1
itob
concat
log
int 1
return
main_l7:
callsub emptyreturnsubroutine_0
int 1
return
main_l8:
int 1
return

// empty_return_subroutine
emptyreturnsubroutine_0:
byte "appear in both approval and clear state"
log
retsub

// log_1
log1_1:
int 1
store 0
load 0
retsub

// approve_if_odd
approveifodd_2:
store 3
load 3
int 2
%
bnz approveifodd_2_l2
int 0
return
approveifodd_2_l2:
int 1
return""".strip()
    assert expected_csp_with_oc == actual_csp_with_oc_compiled

    _router_without_oc = pt.Router("yetAnotherContractConstructedFromRouter")
    add_methods_to_router(_router_without_oc)
    (
        actual_ap_without_oc_compiled,
        actual_csp_without_oc_compiled,
        _,
    ) = _router_without_oc.compile_program(version=6)
    expected_ap_without_oc = """#pragma version 6
txna ApplicationArgs 0
method "add(uint64,uint64)uint64"
==
bnz main_l18
txna ApplicationArgs 0
method "sub(uint64,uint64)uint64"
==
bnz main_l17
txna ApplicationArgs 0
method "mul(uint64,uint64)uint64"
==
bnz main_l16
txna ApplicationArgs 0
method "div(uint64,uint64)uint64"
==
bnz main_l15
txna ApplicationArgs 0
method "mod(uint64,uint64)uint64"
==
bnz main_l14
txna ApplicationArgs 0
method "all_laid_to_args(uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64)uint64"
==
bnz main_l13
txna ApplicationArgs 0
method "empty_return_subroutine()void"
==
bnz main_l12
txna ApplicationArgs 0
method "log_1()uint64"
==
bnz main_l11
txna ApplicationArgs 0
method "log_creation()string"
==
bnz main_l10
err
main_l10:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
==
&&
assert
callsub logcreation_8
store 67
byte 0x151f7c75
load 67
concat
log
int 1
return
main_l11:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
txn OnCompletion
int OptIn
==
txn ApplicationID
int 0
!=
&&
||
assert
callsub log1_7
store 65
byte 0x151f7c75
load 65
itob
concat
log
int 1
return
main_l12:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
txn OnCompletion
int OptIn
==
||
assert
callsub emptyreturnsubroutine_6
int 1
return
main_l13:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 30
txna ApplicationArgs 2
btoi
store 31
txna ApplicationArgs 3
btoi
store 32
txna ApplicationArgs 4
btoi
store 33
txna ApplicationArgs 5
btoi
store 34
txna ApplicationArgs 6
btoi
store 35
txna ApplicationArgs 7
btoi
store 36
txna ApplicationArgs 8
btoi
store 37
txna ApplicationArgs 9
btoi
store 38
txna ApplicationArgs 10
btoi
store 39
txna ApplicationArgs 11
btoi
store 40
txna ApplicationArgs 12
btoi
store 41
txna ApplicationArgs 13
btoi
store 42
txna ApplicationArgs 14
btoi
store 43
txna ApplicationArgs 15
store 46
load 46
int 0
extract_uint64
store 44
load 46
int 8
extract_uint64
store 45
load 30
load 31
load 32
load 33
load 34
load 35
load 36
load 37
load 38
load 39
load 40
load 41
load 42
load 43
load 44
load 45
callsub alllaidtoargs_5
store 47
byte 0x151f7c75
load 47
itob
concat
log
int 1
return
main_l14:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 24
txna ApplicationArgs 2
btoi
store 25
load 24
load 25
callsub mod_4
store 26
byte 0x151f7c75
load 26
itob
concat
log
int 1
return
main_l15:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 18
txna ApplicationArgs 2
btoi
store 19
load 18
load 19
callsub div_3
store 20
byte 0x151f7c75
load 20
itob
concat
log
int 1
return
main_l16:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 12
txna ApplicationArgs 2
btoi
store 13
load 12
load 13
callsub mul_2
store 14
byte 0x151f7c75
load 14
itob
concat
log
int 1
return
main_l17:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 6
txna ApplicationArgs 2
btoi
store 7
load 6
load 7
callsub sub_1
store 8
byte 0x151f7c75
load 8
itob
concat
log
int 1
return
main_l18:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 0
txna ApplicationArgs 2
btoi
store 1
load 0
load 1
callsub add_0
store 2
byte 0x151f7c75
load 2
itob
concat
log
int 1
return

// add
add_0:
store 4
store 3
load 3
load 4
+
store 5
load 5
retsub

// sub
sub_1:
store 10
store 9
load 9
load 10
-
store 11
load 11
retsub

// mul
mul_2:
store 16
store 15
load 15
load 16
*
store 17
load 17
retsub

// div
div_3:
store 22
store 21
load 21
load 22
/
store 23
load 23
retsub

// mod
mod_4:
store 28
store 27
load 27
load 28
%
store 29
load 29
retsub

// all_laid_to_args
alllaidtoargs_5:
store 63
store 62
store 61
store 60
store 59
store 58
store 57
store 56
store 55
store 54
store 53
store 52
store 51
store 50
store 49
store 48
load 48
load 49
+
load 50
+
load 51
+
load 52
+
load 53
+
load 54
+
load 55
+
load 56
+
load 57
+
load 58
+
load 59
+
load 60
+
load 61
+
load 62
+
load 63
+
store 64
load 64
retsub

// empty_return_subroutine
emptyreturnsubroutine_6:
byte "appear in both approval and clear state"
log
retsub

// log_1
log1_7:
int 1
store 66
load 66
retsub

// log_creation
logcreation_8:
byte 0x00106c6f6767696e67206372656174696f6e
store 68
load 68
retsub""".strip()
    assert actual_ap_without_oc_compiled == expected_ap_without_oc

    expected_csp_without_oc = """#pragma version 6
txna ApplicationArgs 0
method "empty_return_subroutine()void"
==
bnz main_l6
txna ApplicationArgs 0
method "log_1()uint64"
==
bnz main_l5
txna ApplicationArgs 0
method "approve_if_odd(uint32)void"
==
bnz main_l4
err
main_l4:
txna ApplicationArgs 1
int 0
extract_uint32
store 2
load 2
callsub approveifodd_2
int 1
return
main_l5:
callsub log1_1
store 1
byte 0x151f7c75
load 1
itob
concat
log
int 1
return
main_l6:
callsub emptyreturnsubroutine_0
int 1
return

// empty_return_subroutine
emptyreturnsubroutine_0:
byte "appear in both approval and clear state"
log
retsub

// log_1
log1_1:
int 1
store 0
load 0
retsub

// approve_if_odd
approveifodd_2:
store 3
load 3
int 2
%
bnz approveifodd_2_l2
int 0
return
approveifodd_2_l2:
int 1
return""".strip()
    assert actual_csp_without_oc_compiled == expected_csp_without_oc
