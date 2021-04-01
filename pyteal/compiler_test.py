import pytest

from . import *
from .compiler import sortBlocks, flattenBlocks

def test_sort_single():
    block = TealSimpleBlock([TealOp(None, Op.int, 1)])
    block.addIncoming()
    block.validateTree()

    expected = [block]
    actual = sortBlocks(block)

    assert actual == expected

def test_sort_sequence():
    block5 = TealSimpleBlock([TealOp(None, Op.int, 5)])
    block4 = TealSimpleBlock([TealOp(None, Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = TealSimpleBlock([TealOp(None, Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = TealSimpleBlock([TealOp(None, Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = TealSimpleBlock([TealOp(None, Op.int, 1)])
    block1.setNextBlock(block2)
    block1.addIncoming()
    block1.validateTree()

    expected = [block1, block2, block3, block4, block5]
    actual = sortBlocks(block1)

    assert actual == expected

def test_sort_branch():
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true\"")])
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"false\"")])
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()

    expected = [block, blockFalse, blockTrue]
    actual = sortBlocks(block)

    assert actual == expected

def test_sort_multiple_branch():
    blockTrueTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true true\"")])
    blockTrueFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"true false\"")])
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"false\"")])
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()

    expected = [block, blockFalse, blockTrue, blockTrueBranch, blockTrueFalse, blockTrueTrue]
    actual = sortBlocks(block)

    assert actual == expected

def test_sort_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(None, Op.return_)])
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockEnd)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"false\"")])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()

    expected = [block, blockFalse, blockTrue, blockEnd]
    actual = sortBlocks(block)

    assert actual == expected

def test_flatten_none():
    blocks = []

    expected = []
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_single_empty():
    blocks = [
        TealSimpleBlock([])
    ]

    expected = []
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_single_one():
    blocks = [
        TealSimpleBlock([TealOp(None, Op.int, 1)])
    ]

    expected = [TealOp(None, Op.int, 1)]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_single_many():
    blocks = [
        TealSimpleBlock([
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.add),
            TealOp(None, Op.add)
        ])
    ]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.add)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_sequence():
    block5 = TealSimpleBlock([TealOp(None, Op.int, 5)])
    block4 = TealSimpleBlock([TealOp(None, Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = TealSimpleBlock([TealOp(None, Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = TealSimpleBlock([TealOp(None, Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = TealSimpleBlock([TealOp(None, Op.int, 1)])
    block1.setNextBlock(block2)
    block1.addIncoming()
    block1.validateTree()
    blocks = [block1, block2, block3, block4, block5]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.int, 4),
        TealOp(None, Op.int, 5)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_branch():
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true\""), TealOp(None, Op.return_)])
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"false\""), TealOp(None, Op.return_)])
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockTrue]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, "l2"),
        TealOp(None, Op.byte, "\"false\""),
        TealOp(None, Op.return_),
        TealLabel(None, "l2"),
        TealOp(None, Op.byte, "\"true\""),
        TealOp(None, Op.return_)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(None, Op.return_)])
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockEnd)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"false\"")])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockTrue, blockEnd]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, "l2"),
        TealOp(None, Op.byte, "\"false\""),
        TealOp(None, Op.b, "l3"),
        TealLabel(None, "l2"),
        TealOp(None, Op.byte, "\"true\""),
        TealLabel(None, "l3"),
        TealOp(None, Op.return_)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_multiple_branch():
    blockTrueTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true true\""), TealOp(None, Op.return_)])
    blockTrueFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"true false\""), TealOp(None, Op.err)])
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"false\""), TealOp(None, Op.return_)])
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockTrue, blockTrueBranch, blockTrueFalse, blockTrueTrue]
    
    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, "l2"),
        TealOp(None, Op.byte, "\"false\""),
        TealOp(None, Op.return_),
        TealLabel(None, "l2"),
        TealOp(None, Op.byte, "\"true\""),
        TealOp(None, Op.bnz, "l5"),
        TealOp(None, Op.byte, "\"true false\""),
        TealOp(None, Op.err),
        TealLabel(None, "l5"),
        TealOp(None, Op.byte, "\"true true\""),
        TealOp(None, Op.return_)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_multiple_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(None, Op.return_)])
    blockTrueTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true true\"")])
    blockTrueTrue.setNextBlock(blockEnd)
    blockTrueFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"true false\""), TealOp(None, Op.err)])
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, "\"false\"")])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockTrue, blockTrueBranch, blockTrueFalse, blockTrueTrue, blockEnd]
    
    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, "l2"),
        TealOp(None, Op.byte, "\"false\""),
        TealOp(None, Op.b, "l6"),
        TealLabel(None, "l2"),
        TealOp(None, Op.byte, "\"true\""),
        TealOp(None, Op.bnz, "l5"),
        TealOp(None, Op.byte, "\"true false\""),
        TealOp(None, Op.err),
        TealLabel(None, "l5"),
        TealOp(None, Op.byte, "\"true true\""),
        TealLabel(None, "l6"),
        TealOp(None, Op.return_)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

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
        compileTeal(expr, Mode.Signature, version=1) # too small

    with pytest.raises(TealInputError):
        compileTeal(expr, Mode.Signature, version=4) # too large
    
    with pytest.raises(TealInputError):
        compileTeal(expr, Mode.Signature, version=2.0) # decimal

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
