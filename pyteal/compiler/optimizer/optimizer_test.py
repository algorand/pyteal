from pickletools import optimize
from .optimizer import OptimizeOptions, apply_optimizations
from .optimizer import apply_local_optimizations

from pyteal.ir.tealop import TealOp
from pyteal.ir.ops import Op

from pyteal import *
from pyteal.ast.subroutine import evaluateSubroutine

import pytest


def test_optimize_slots_basic():
    teal = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.load, 1),
    ]

    options = OptimizeOptions(useSlotToStack=True)
    result_teal = apply_local_optimizations(teal, options)

    expected = []
    assert result_teal == expected

    options = OptimizeOptions()
    result_teal = apply_local_optimizations(teal, options)

    expected = teal
    assert result_teal == expected


def test_optimize_slots_iteration():
    teal = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.store, 2),
        TealOp(None, Op.load, 2),
        TealOp(None, Op.load, 1),
    ]

    options = OptimizeOptions(useSlotToStack=True, iterateOptimizations=True)
    result_teal = apply_local_optimizations(teal, options)

    expected = []
    assert result_teal == expected

    options = OptimizeOptions(useSlotToStack=True)
    result_teal = apply_local_optimizations(teal, options)

    expected = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.load, 1),
    ]
    assert result_teal == expected


def test_optimize_slots_with_dependency():
    teal = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.store, 2),
        TealOp(None, Op.load, 2),
        TealOp(None, Op.load, 1),
        TealOp(None, Op.load, 1),
    ]

    options = OptimizeOptions(useSlotToStack=True, iterateOptimizations=True)
    result_teal = apply_local_optimizations(teal, options)

    expected = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.load, 1),
        TealOp(None, Op.load, 1),
    ]
    assert result_teal == expected

    teal = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.store, 2),
        TealOp(None, Op.load, 2),
        TealOp(None, Op.load, 1),
        TealOp(None, Op.load, 2),
    ]

    options = OptimizeOptions(useSlotToStack=True, iterateOptimizations=True)
    result_teal = apply_local_optimizations(teal, options)

    expected = teal
    assert result_teal == expected


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

    # single pass optimization
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
load 1
+
retsub
    """.strip()
    optimize_options.use_slot_to_stack = True
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # iterative optimization
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
    optimize_options.use_slot_to_stack = True
    optimize_options.iterate_optimizations = True
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
store 1
int 2
load 1
+
retsub
    """.strip()
    optimize_options.use_slot_to_stack = True
    optimize_options.iterate_optimizations = True
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_global_var_dependency():
    global_var = ScratchVar(TealType.uint64)

    @Subroutine(TealType.uint64)
    def add(a1: Expr) -> Expr:
        return Seq(global_var.store(Int(2)), global_var.load() + a1)

    program = Seq(
        [
            If(Txn.sender() == Global.creator_address()).Then(Pop(add(Int(1)))),
            Pop(global_var.load()),
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
load 0
pop
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

    # optimization shouldn't apply because of the dependency on the
    # slot belonging to the global var.
    optimize_options.use_slot_to_stack = True
    optimize_options.iterate_optimizations = True
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

    # fully optimized
    expected = """#pragma version 4
int 0
int 1
app_global_get_ex
+
pop
int 1
return""".strip()
    optimize_options.use_slot_to_stack = True
    optimize_options.iterate_optimizations = True
    actual = compileTeal(
        program, version=4, mode=Mode.Application, optimize=optimize_options
    )
    assert actual == expected
