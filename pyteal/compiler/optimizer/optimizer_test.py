from pyteal.compiler.optimizer.optimizer import OptimizeOptions, _apply_slot_to_stack

import pyteal as pt


def test_optimize_single_block():
    slot1 = pt.ScratchSlot(1)
    slot2 = pt.ScratchSlot(2)

    # empty check
    empty_block = pt.TealSimpleBlock([])
    _apply_slot_to_stack(empty_block, empty_block, {})

    expected = pt.TealSimpleBlock([])
    assert empty_block == expected

    # basic optimization
    block = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.store, slot1),
            pt.TealOp(None, pt.Op.load, slot1),
        ]
    )
    _apply_slot_to_stack(block, block, {})

    expected = pt.TealSimpleBlock([])
    assert block == expected

    # iterate optimization
    block = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.store, slot1),
            pt.TealOp(None, pt.Op.store, slot2),
            pt.TealOp(None, pt.Op.load, slot2),
            pt.TealOp(None, pt.Op.load, slot1),
        ]
    )
    _apply_slot_to_stack(block, block, {})

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.store, slot1),
            pt.TealOp(None, pt.Op.load, slot1),
        ]
    )
    assert block == expected

    _apply_slot_to_stack(block, block, {})
    expected = pt.TealSimpleBlock([])
    assert block == expected

    # remove extraneous stores
    block = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.store, slot1),
            pt.TealOp(None, pt.Op.load, slot1),
            pt.TealOp(None, pt.Op.store, slot1),
        ]
    )
    _apply_slot_to_stack(block, block, {})

    expected = pt.TealSimpleBlock([])
    assert block == expected


def test_optimize_subroutine():
    @pt.Subroutine(pt.TealType.uint64)
    def add(a1: pt.Expr, a2: pt.Expr) -> pt.Expr:
        return a1 + a2

    program = pt.Seq(
        [
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                pt.Pop(add(pt.Int(1), pt.Int(2)))
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_scratchvar_arg():
    @pt.Subroutine(pt.TealType.uint64)
    def add(a1: pt.ScratchVar, a2: pt.Expr) -> pt.Expr:
        return a1.load() + a2

    arg = pt.ScratchVar(pt.TealType.uint64)

    program = pt.Seq(
        [
            arg.store(pt.Int(1)),
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                pt.Pop(add(arg, pt.Int(2)))
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, version=5, mode=pt.Mode.Application, optimize=optimize_options
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
    actual = pt.compileTeal(
        program, version=5, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_local_var():
    local_var = pt.ScratchVar(pt.TealType.uint64)

    @pt.Subroutine(pt.TealType.uint64)
    def add(a1: pt.Expr) -> pt.Expr:
        return pt.Seq(local_var.store(pt.Int(2)), local_var.load() + a1)

    program = pt.Seq(
        [
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                pt.Pop(add(pt.Int(1)))
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_global_var():
    global_var = pt.ScratchVar(pt.TealType.uint64)

    @pt.Subroutine(pt.TealType.uint64)
    def add(a1: pt.Expr) -> pt.Expr:
        return pt.Seq(global_var.store(pt.Int(2)), global_var.load() + a1)

    program = pt.Seq(
        [
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                pt.Pop(add(pt.Int(1)))
            ),
            global_var.store(pt.Int(5)),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # optimization should not apply to global vars
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_reserved_local_var():
    local_var = pt.ScratchVar(pt.TealType.uint64, 0)

    @pt.Subroutine(pt.TealType.uint64)
    def add(a1: pt.Expr) -> pt.Expr:
        return pt.Seq(local_var.store(pt.Int(2)), local_var.load() + a1)

    program = pt.Seq(
        [
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                pt.Pop(add(pt.Int(1)))
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # The optimization must skip over the reserved slot id so the expected result
    # hasn't changed.
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_subroutine_with_load_dependency():
    @pt.Subroutine(pt.TealType.uint64)
    def add(a1: pt.Expr, a2: pt.Expr) -> pt.Expr:
        return pt.Seq(pt.Pop(a1 + a2), a2)

    program = pt.Seq(
        [
            pt.If(pt.Txn.sender() == pt.Global.creator_address()).Then(
                pt.Pop(add(pt.Int(1), pt.Int(2)))
            ),
            pt.Approve(),
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_multi_value():
    # note: this is incorrect usage of the app_global_get_ex opcode
    program = pt.Seq(
        pt.MultiValue(
            pt.Op.app_global_get_ex,
            [pt.TealType.uint64, pt.TealType.uint64],
            immediate_args=[],
            args=[pt.Int(0), pt.Int(1)],
        ).outputReducer(lambda value, hasValue: pt.Pop(value + hasValue)),
        pt.Approve(),
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected


def test_optimize_dynamic_var():
    myvar = pt.DynamicScratchVar()
    regvar = pt.ScratchVar()
    program = pt.Seq(
        regvar.store(pt.Int(1)),
        myvar.set_index(regvar),
        regvar.store(pt.Int(2)),
        pt.Pop(regvar.load()),
        pt.Approve(),
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
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected

    # optimization should not change the code because the candidate slot
    # is used by the dynamic slot variable.
    optimize_options = OptimizeOptions(scratch_slots=True)
    actual = pt.compileTeal(
        program, version=4, mode=pt.Mode.Application, optimize=optimize_options
    )
    assert actual == expected
