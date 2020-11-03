import pytest

from . import *
from .compiler import sortBlocks, flattenBlocks

def test_sort_single():
    block = TealSimpleBlock([TealOp(Op.int, 1)])
    block.addIncoming()
    block.validate()

    expected = [block]
    actual = sortBlocks(block)

    assert actual == expected

def test_sort_sequence():
    block5 = TealSimpleBlock([TealOp(Op.int, 5)])
    block4 = TealSimpleBlock([TealOp(Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = TealSimpleBlock([TealOp(Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = TealSimpleBlock([TealOp(Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = TealSimpleBlock([TealOp(Op.int, 1)])
    block1.setNextBlock(block2)
    block1.addIncoming()
    block1.validate()

    expected = [block1, block2, block3, block4, block5]
    actual = sortBlocks(block1)

    assert actual == expected

def test_sort_branch():
    blockTrue = TealSimpleBlock([TealOp(Op.byte, "\"true\"")])
    blockFalse = TealSimpleBlock([TealOp(Op.byte, "\"false\"")])
    block = TealConditionalBlock([TealOp(Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validate()

    expected = [block, blockFalse, blockTrue]
    actual = sortBlocks(block)

    assert actual == expected

def test_sort_multiple_branch():
    blockTrueTrue = TealSimpleBlock([TealOp(Op.byte, "\"true true\"")])
    blockTrueFalse = TealSimpleBlock([TealOp(Op.byte, "\"true false\"")])
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock([TealOp(Op.byte, "\"false\"")])
    block = TealConditionalBlock([TealOp(Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validate()

    expected = [block, blockFalse, blockTrue, blockTrueBranch, blockTrueFalse, blockTrueTrue]
    actual = sortBlocks(block)

    assert actual == expected

def test_sort_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(Op.return_)])
    blockTrue = TealSimpleBlock([TealOp(Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockEnd)
    blockFalse = TealSimpleBlock([TealOp(Op.byte, "\"false\"")])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validate()

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
        TealSimpleBlock([TealOp(Op.int, 1)])
    ]

    expected = [TealOp(Op.int, 1)]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_single_many():
    blocks = [
        TealSimpleBlock([
            TealOp(Op.int, 1),
            TealOp(Op.int, 2),
            TealOp(Op.int, 3),
            TealOp(Op.add),
            TealOp(Op.add)
        ])
    ]

    expected = [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.add),
        TealOp(Op.add)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_sequence():
    block5 = TealSimpleBlock([TealOp(Op.int, 5)])
    block4 = TealSimpleBlock([TealOp(Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = TealSimpleBlock([TealOp(Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = TealSimpleBlock([TealOp(Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = TealSimpleBlock([TealOp(Op.int, 1)])
    block1.setNextBlock(block2)
    block1.addIncoming()
    block1.validate()
    blocks = [block1, block2, block3, block4, block5]

    expected = [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.int, 4),
        TealOp(Op.int, 5)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_branch():
    blockTrue = TealSimpleBlock([TealOp(Op.byte, "\"true\""), TealOp(Op.return_)])
    blockFalse = TealSimpleBlock([TealOp(Op.byte, "\"false\""), TealOp(Op.return_)])
    block = TealConditionalBlock([TealOp(Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validate()
    blocks = [block, blockFalse, blockTrue]

    expected = [
        TealOp(Op.int, 1),
        TealOp(Op.bnz, "l2"),
        TealOp(Op.byte, "\"false\""),
        TealOp(Op.return_),
        TealLabel("l2"),
        TealOp(Op.byte, "\"true\""),
        TealOp(Op.return_)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(Op.return_)])
    blockTrue = TealSimpleBlock([TealOp(Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockEnd)
    blockFalse = TealSimpleBlock([TealOp(Op.byte, "\"false\"")])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validate()
    blocks = [block, blockFalse, blockTrue, blockEnd]

    expected = [
        TealOp(Op.int, 1),
        TealOp(Op.bnz, "l2"),
        TealOp(Op.byte, "\"false\""),
        TealOp(Op.b, "l3"),
        TealLabel("l2"),
        TealOp(Op.byte, "\"true\""),
        TealLabel("l3"),
        TealOp(Op.return_)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_multiple_branch():
    blockTrueTrue = TealSimpleBlock([TealOp(Op.byte, "\"true true\""), TealOp(Op.return_)])
    blockTrueFalse = TealSimpleBlock([TealOp(Op.byte, "\"true false\""), TealOp(Op.err)])
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock([TealOp(Op.byte, "\"false\""), TealOp(Op.return_)])
    block = TealConditionalBlock([TealOp(Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validate()
    blocks = [block, blockFalse, blockTrue, blockTrueBranch, blockTrueFalse, blockTrueTrue]
    
    expected = [
        TealOp(Op.int, 1),
        TealOp(Op.bnz, "l2"),
        TealOp(Op.byte, "\"false\""),
        TealOp(Op.return_),
        TealLabel("l2"),
        TealOp(Op.byte, "\"true\""),
        TealOp(Op.bnz, "l5"),
        TealOp(Op.byte, "\"true false\""),
        TealOp(Op.err),
        TealLabel("l5"),
        TealOp(Op.byte, "\"true true\""),
        TealOp(Op.return_)
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected

def test_flatten_multiple_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(Op.return_)])
    blockTrueTrue = TealSimpleBlock([TealOp(Op.byte, "\"true true\"")])
    blockTrueTrue.setNextBlock(blockEnd)
    blockTrueFalse = TealSimpleBlock([TealOp(Op.byte, "\"true false\""), TealOp(Op.err)])
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(Op.byte, "\"true\"")])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock([TealOp(Op.byte, "\"false\"")])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validate()
    blocks = [block, blockFalse, blockTrue, blockTrueBranch, blockTrueFalse, blockTrueTrue, blockEnd]
    
    expected = [
        TealOp(Op.int, 1),
        TealOp(Op.bnz, "l2"),
        TealOp(Op.byte, "\"false\""),
        TealOp(Op.b, "l6"),
        TealLabel("l2"),
        TealOp(Op.byte, "\"true\""),
        TealOp(Op.bnz, "l5"),
        TealOp(Op.byte, "\"true false\""),
        TealOp(Op.err),
        TealLabel("l5"),
        TealOp(Op.byte, "\"true true\""),
        TealLabel("l6"),
        TealOp(Op.return_)
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
