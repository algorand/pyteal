from .optimizer import OptimizeOptions, _apply_slot_to_stack

from ... import *

import pytest


def test_optimize_single_block():
    slot1 = ScratchSlot(1)
    slot2 = ScratchSlot(2)

    # empty check
    empty_block = TealSimpleBlock([])
    _apply_slot_to_stack(empty_block, empty_block, {})

    expected = TealSimpleBlock([])
    assert empty_block == expected

    # basic optimization
    block = TealSimpleBlock(
        [
            TealOp(None, Op.store, slot1),
            TealOp(None, Op.load, slot1),
        ]
    )
    _apply_slot_to_stack(block, block, {})

    expected = TealSimpleBlock([])
    assert block == expected

    # iterate optimization
    block = TealSimpleBlock(
        [
            TealOp(None, Op.store, slot1),
            TealOp(None, Op.store, slot2),
            TealOp(None, Op.load, slot2),
            TealOp(None, Op.load, slot1),
        ]
    )
    _apply_slot_to_stack(block, block, {})

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.store, slot1),
            TealOp(None, Op.load, slot1),
        ]
    )
    assert block == expected

    _apply_slot_to_stack(block, block, {})
    expected = TealSimpleBlock([])
    assert block == expected

    # remove extraneous stores
    block = TealSimpleBlock(
        [
            TealOp(None, Op.store, slot1),
            TealOp(None, Op.load, slot1),
            TealOp(None, Op.store, slot1),
        ]
    )
    _apply_slot_to_stack(block, block, {})

    expected = TealSimpleBlock([])
    assert block == expected


def test_optimize_subroutine():
    @Subroutine(TealType.uint64)
    def add(a1: Expr, a2: Expr) -> Expr:
        return a1 + a2

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(Pop(add(Int(1), Int(2)))),
            Approve(),
        ]
    )

    optimize_options = OptimizeOptions()

    # unoptimized
    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
int 1
int 2
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
store 1
store 0
load 0
load 1
+
retsub
    """.strip()
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # optimized
    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
int 1
int 2
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
+
retsub
    """.strip()
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_scratchvar_arg():
    @Subroutine(TealType.uint64)
    def add(a1: ScratchVar, a2: Expr) -> Expr:
        return a1.load() + a2

    arg = ScratchVar(TealType.uint64)

    program = Seq(
        [
            arg.store(Int(1)),
            If(Txn.sender() == Global.creator_address()).Then(Pop(add(arg, Int(2)))),
            Approve(),
        ]
    )

    optimize_options = OptimizeOptions()

    # unoptimized
    expected = """#pragma version 5
int 1
store 0
txn Sender
global CreatorAddress
==
bz main_l2
int 0
int 2
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
store 2
store 1
load 1
loads
load 2
+
retsub""".strip()
    actual = compileTeal(
        program, version=5, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # optimized
    expected = """#pragma version 5
int 1
store 0
txn Sender
global CreatorAddress
==
bz main_l2
int 0
int 2
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
store 1
loads
load 1
+
retsub""".strip()
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = compileTeal(
        program, version=5, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_local_var():
    local_var = ScratchVar(TealType.uint64)

    @Subroutine(TealType.uint64)
    def add(a1: Expr) -> Expr:
        return Seq(local_var.store(Int(2)), local_var.load() + a1)

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(Pop(add(Int(1)))),
            Approve(),
        ]
    )

    optimize_options = OptimizeOptions()

    # unoptimized
    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
int 1
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
store 1
int 2
store 0
load 0
load 1
+
retsub
    """.strip()
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # optimized
    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
int 1
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
store 0
int 2
load 0
+
retsub
    """.strip()
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_global_var():
    global_var = ScratchVar(TealType.uint64)

    @Subroutine(TealType.uint64)
    def add(a1: Expr) -> Expr:
        return Seq(global_var.store(Int(2)), global_var.load() + a1)

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(Pop(add(Int(1)))),
            global_var.store(Int(5)),
            Approve(),
        ]
    )

    optimize_options = OptimizeOptions()

    # unoptimized
    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
int 1
callsub add_0
pop
main_l2:
int 5
store 0
int 1
return

// add
add_0:
store 1
int 2
store 0
load 0
load 1
+
retsub
    """.strip()
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # optimization should not apply to global vars
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_reserved_local_var():
    local_var = ScratchVar(TealType.uint64, 0)

    @Subroutine(TealType.uint64)
    def add(a1: Expr) -> Expr:
        return Seq(local_var.store(Int(2)), local_var.load() + a1)

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(Pop(add(Int(1)))),
            Approve(),
        ]
    )

    optimize_options = OptimizeOptions()

    # unoptimized
    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
int 1
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
store 1
int 2
store 0
load 0
load 1
+
retsub
    """.strip()
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # The optimization must skip over the reserved slot id so the expected result
    # hasn't changed.
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_load_dependency():
    @Subroutine(TealType.uint64)
    def add(a1: Expr, a2: Expr) -> Expr:
        return Seq(Pop(a1 + a2), a2)

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(Pop(add(Int(1), Int(2)))),
            Approve(),
        ]
    )

    optimize_options = OptimizeOptions()

    # unoptimized
    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
int 1
int 2
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
store 1
store 0
load 0
load 1
+
pop
load 1
retsub""".strip()
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # slot 0 will get optimized but slot 1 won't because it has
    # a load dependency.
    expected = """#pragma version 4
txn Sender
global CreatorAddress
==
bz main_l2
int 1
int 2
callsub add_0
pop
main_l2:
int 1
return

// add
add_0:
store 0
load 0
+
pop
load 0
retsub""".strip()
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_multi_value():
    # note: this is incorrect usage of the app_global_get_ex opcode
    program = Seq(
        MultiValue(
            Op.app_global_get_ex,
            [TealType.uint64, TealType.uint64],
            immediate_args=[],
            args=[Int(0), Int(1)],
        ).outputReducer(lambda value, hasValue: Pop(value + hasValue)),
        Approve(),
    )

    optimize_options = OptimizeOptions()

    # unoptimized
    expected = """#pragma version 4
int 0
int 1
app_global_get_ex
store 1
store 0
load 0
load 1
+
pop
int 1
return""".strip()
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # optimized
    expected = """#pragma version 4
int 0
int 1
app_global_get_ex
+
pop
int 1
return""".strip()
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_dynamic_var():
    myvar = DynamicScratchVar()
    regvar = ScratchVar()
    program = Seq(
        regvar.store(Int(1)),
        myvar.set_index(regvar),
        regvar.store(Int(2)),
        Pop(regvar.load()),
        Approve(),
    )

    optimize_options = OptimizeOptions()

    # unoptimized
    expected = """#pragma version 4
int 1
store 1
int 1
store 0
int 2
store 1
load 1
pop
int 1
return""".strip()
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # optimization should not change the code because the candidate slot
    # is used by the dynamic slot variable.
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected
