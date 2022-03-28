from .optimizer import OptimizeOptions

from pyteal.ir.ops import Op

from pyteal import *

import pytest


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


def test_optimize_subroutine_with_reserved_global_var():
    global_var = ScratchVar(TealType.uint64, 0)

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

    # The optimization must skip over the reserved slot id so the expected result
    # hasn't changed.
    optimize_options = OptimizeOptions(scratch_slots=True)
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
    optimize_options.scratch_slots = True
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
