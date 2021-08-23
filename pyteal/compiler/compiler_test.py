import pytest

from .. import *


def test_compile_single():
    expr = Int(1)

    expected = """
#pragma version 2
int 1
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
""".strip()
    actual_application = compileTeal(expr, Mode.Application)
    actual_signature = compileTeal(expr, Mode.Signature)

    assert actual_application == actual_signature
    assert actual_application == expected


def test_compile_branch():
    expr = If(Int(1), Bytes("true"), Bytes("false"))

    expected = """
#pragma version 2
int 1
bnz l2
byte "false"
b l3
l2:
byte "true"
l3:
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
""".strip()
    actual = compileTeal(expr, Mode.Signature, version=3)
    assert actual == expected


def test_compile_version_4():
    expr = Int(1)

    expected = """
#pragma version 4
int 1
""".strip()
    actual = compileTeal(expr, Mode.Signature, version=4)
    assert actual == expected


# def test_slot_load_before_store():
#
#     program = AssetHolding.balance(Int(0), Int(0)).value()
#     with pytest.raises(TealInternalError):
#         compileTeal(program, Mode.Application, version=2)
#
#     program = AssetHolding.balance(Int(0), Int(0)).hasValue()
#     with pytest.raises(TealInternalError):
#         compileTeal(program, Mode.Application, version=2)
#
#     program = App.globalGetEx(Int(0), Bytes("key")).value()
#     with pytest.raises(TealInternalError):
#         compileTeal(program, Mode.Application, version=2)
#
#     program = App.globalGetEx(Int(0), Bytes("key")).hasValue()
#     with pytest.raises(TealInternalError):
#         compileTeal(program, Mode.Application, version=2)
#
#     program = ScratchVar().load()
#     with pytest.raises(TealInternalError):
#         compileTeal(program, Mode.Application, version=2)


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
""".strip()
    actual = compileTeal(prog, mode=Mode.Signature, version=4)
    assert actual == expected


def test_scratchvar_double_assign_invalid():
    myvar = ScratchVar(TealType.uint64, 10)
    otherVar = ScratchVar(TealType.uint64, 10)
    prog = Seq([myvar.store(Int(5)), otherVar.store(Int(0))])
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
        ]
    )

    expectedNoAssemble = """
    #pragma version 4
int 0
store 0
l1:
load 0
int 2
<
bz l3
load 0
int 1
+
store 0
b l1
l3:
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
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
l1:
load 0
int 2
<
bz l6
int 0
store 1
l3:
load 1
int 5
<
bnz l5
load 0
int 1
+
store 0
b l1
l5:
load 1
int 1
+
store 1
b l3
l6:
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
            )
        ]
    )

    expectedNoAssemble = """
    #pragma version 4
int 0
store 0
l1:
load 0
int 10
<
bz l3
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
b l1
l3:
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
            )
        ]
    )

    expectedNoAssemble = """
        #pragma version 4
int 0
store 0
l1:
load 0
int 10
<
bz l6
int 0
store 1
l3:
load 1
int 4
<
bnz l5
load 0
int 1
+
store 0
b l1
l5:
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
b l3
l6:
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
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
l1:
load 0
int 3
<
bz l5
load 0
int 2
==
bnz l4
load 0
int 1
+
store 0
b l1
l4:
l5:
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
            )
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
l1:
load 0
int 10
<
bz l5
load 0
int 4
==
bnz l4
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
b l1
l4:
l5:
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
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
l1:
load 0
int 3
<
bz l5
l2:
load 0
int 2
==
bnz l4
load 0
int 1
+
store 0
b l1
l4:
b l2
l5:
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
            )
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
l1:
load 0
int 10
<
bz l6
load 0
int 4
==
bnz l5
load 0
itob
load 0
int 2
*
app_global_put
l4:
load 0
int 1
+
store 0
b l1
l5:
b l4
l6:
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
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
load 0
int 10
<
bz l4
l1:
load 0
int 1
+
store 0
load 0
int 4
<
bnz l3
b l4
l3:
b l1
l4:
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
        ]
    )

    expectedNoAssemble = """#pragma version 4
int 0
store 0
l1:
load 0
int 10
<
bz l12
l2:
load 0
int 8
==
bnz l11
l4:
load 0
int 6
<
bnz l8
l5:
load 0
int 5
<
bnz l7
load 0
int 1
+
store 0
b l1
l7:
b l2
l8:
load 0
int 3
==
bnz l10
load 0
int 1
+
store 0
b l4
l10:
b l5
l11:
l12:  
""".strip()
    actualNoAssemble = compileTeal(
        program, Mode.Application, version=4, assembleConstants=False
    )
    assert expectedNoAssemble == actualNoAssemble
