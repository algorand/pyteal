from ... import *

from .duplicate import getDependenciesForOp, detectDuplicatesInBlock

def test_dependencies_1():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
    ]
    
    complete, actual = getDependenciesForOp(ops, 1)
    expected = [
        TealOp(None, Op.int, 2),
    ]

    assert complete
    assert actual == expected

def test_dependencies_2():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.logic_not),
        TealOp(None, Op.int, 3),
    ]
    
    complete, actual = getDependenciesForOp(ops, 2)
    expected = [
        TealOp(None, Op.int, 2),
        TealOp(None, Op.logic_not),
    ]

    assert complete
    assert actual == expected

def test_dependencies_3():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 4),
    ]
    
    complete, actual = getDependenciesForOp(ops, 3)
    expected = [
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
    ]

    assert complete
    assert actual == expected

def test_dependencies_4():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.bitwise_not),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 4),
    ]
    
    complete, actual = getDependenciesForOp(ops, 4)
    expected = [
        TealOp(None, Op.int, 2),
        TealOp(None, Op.bitwise_not),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
    ]

    assert complete
    assert actual == expected

def test_dependencies_5():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.logic_not),
        TealOp(None, Op.app_local_put),
        TealOp(None, Op.int, 4),
    ]
    
    complete, actual = getDependenciesForOp(ops, 5)
    expected = [
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.logic_not),
        TealOp(None, Op.app_local_put),
    ]

    assert complete
    assert actual == expected

def test_dependencies_6():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.byte, "0xFF"),
        TealOp(None, Op.concat),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.app_local_put),
        TealOp(None, Op.int, 4),
    ]
    
    complete, actual = getDependenciesForOp(ops, 6)
    expected = [
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.byte, "0xFF"),
        TealOp(None, Op.concat),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.app_local_put),
    ]

    assert complete
    assert actual == expected

def test_dependencies_with_op_that_pushes_2():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.addw),
        TealOp(None, Op.int, 4),
    ]
    
    complete, actual = getDependenciesForOp(ops, 3)
    expected = [
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.addw),
    ]

    assert complete
    assert actual == expected

def test_dependencies_dig():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.dig, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 4),
    ]
    
    complete, actual = getDependenciesForOp(ops, 3)
    expected = [
        TealOp(None, Op.int, 2),
        TealOp(None, Op.dig, 1),
        TealOp(None, Op.add),
    ]

    assert not complete
    assert actual == expected

def test_detect_duplicates_none():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
    ])

    assert actual == expected


def test_detect_duplicates_single_depth_1():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 3),
    ])

    assert actual == expected

def test_detect_duplicates_single_depth_2():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.logic_not),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.logic_not),
            TealOp(None, Op.int, 3),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.logic_not),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 3),
    ])

    assert actual == expected

def test_detect_duplicates_single_depth_3():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.add),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.add),
            TealOp(None, Op.int, 4),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 4),
    ])

    assert actual == expected

def test_detect_duplicates_single_depth_4():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 1),
            TealOp(None, Op.byte, "\"o\""),
            TealOp(None, Op.gtxn, 2, "XferAsset"),
            TealOp(None, Op.itob),
            TealOp(None, Op.concat),
            TealOp(None, Op.byte, "\"o\""),
            TealOp(None, Op.gtxn, 2, "XferAsset"),
            TealOp(None, Op.itob),
            TealOp(None, Op.concat),
            TealOp(None, Op.app_global_get),
            TealOp(None, Op.gtxn, 2, "AssetAmount"),
            TealOp(None, Op.add),
            TealOp(None, Op.int, 100),
            TealOp(None, Op.minus),
            TealOp(None, Op.app_global_put),
            TealOp(None, Op.return_),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 1),
        TealOp(None, Op.byte, "\"o\""),
        TealOp(None, Op.gtxn, 2, "XferAsset"),
        TealOp(None, Op.itob),
        TealOp(None, Op.concat),
        TealOp(None, Op.dup),
        TealOp(None, Op.app_global_get),
        TealOp(None, Op.gtxn, 2, "AssetAmount"),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 100),
        TealOp(None, Op.minus),
        TealOp(None, Op.app_global_put),
        TealOp(None, Op.return_),
    ])

    assert actual == expected

def test_detect_duplicates_double_simple():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.dup2),
        TealOp(None, Op.int, 3),
    ])

    assert actual == expected

def test_detect_duplicates_double_complex():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.byte, "\"e\""),
            TealOp(None, Op.gtxn, 3, "XferAsset"),
            TealOp(None, Op.itob),
            TealOp(None, Op.concat),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.byte, "\"e\""),
            TealOp(None, Op.gtxn, 3, "XferAsset"),
            TealOp(None, Op.itob),
            TealOp(None, Op.concat),
            TealOp(None, Op.app_local_get),
            TealOp(None, Op.int, 100),
            TealOp(None, Op.add),
            TealOp(None, Op.gtxn, 3, "AssetAmount"),
            TealOp(None, Op.minus),
            TealOp(None, Op.app_local_put),
            TealOp(None, Op.int, 6),
        ])
    )
    detectDuplicatesInBlock(actual)

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.byte, "\"e\""),
        TealOp(None, Op.gtxn, 3, "XferAsset"),
        TealOp(None, Op.itob),
        TealOp(None, Op.concat),
        TealOp(None, Op.dup2),
        TealOp(None, Op.app_local_get),
        TealOp(None, Op.int, 100),
        TealOp(None, Op.add),
        TealOp(None, Op.gtxn, 3, "AssetAmount"),
        TealOp(None, Op.minus),
        TealOp(None, Op.app_local_put),
        TealOp(None, Op.int, 6),
    ])

    assert actual == expected

def test_detect_duplicates_dig():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 1),
            TealOp(None, Op.dig, 3),
            TealOp(None, Op.dig, 3),
            TealOp(None, Op.int, 3),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 1),
        TealOp(None, Op.dig, 3),
        TealOp(None, Op.dig, 3),
        TealOp(None, Op.int, 3),
    ])

    assert actual == expected

def test_detect_duplicates_stateful_write_identical():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 2),
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.byte, "0x01"),
            TealOp(None, Op.app_global_put),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.byte, "0x01"),
            TealOp(None, Op.app_global_put),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.byte, "0x01"),
        TealOp(None, Op.app_global_put),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.dup),
    ])

    assert actual == expected

def test_detect_duplicates_stateful_write_different():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 2),
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.byte, "0x01"),
            TealOp(None, Op.app_global_put),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.byte, "0x02"),
            TealOp(None, Op.app_global_put),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.byte, "0x01"),
        TealOp(None, Op.app_global_put),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.byte, "0x02"),
        TealOp(None, Op.app_global_put),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
    ])

    assert actual == expected

def test_detect_duplicates_stateful_read_write_identical():
    actual = detectDuplicatesInBlock(
        TealSimpleBlock([
            TealOp(None, Op.int, 2),
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.app_global_get),
            TealOp(None, Op.byte, "0x01"),
            TealOp(None, Op.concat),
            TealOp(None, Op.app_global_put),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.app_global_get),
            TealOp(None, Op.byte, "0x01"),
            TealOp(None, Op.concat),
            TealOp(None, Op.app_global_put),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
        ])
    )

    expected = TealSimpleBlock([
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.dup),
        TealOp(None, Op.app_global_get),
        TealOp(None, Op.byte, "0x01"),
        TealOp(None, Op.concat),
        TealOp(None, Op.app_global_put),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.dup),
        TealOp(None, Op.app_global_get),
        TealOp(None, Op.byte, "0x01"),
        TealOp(None, Op.concat),
        TealOp(None, Op.app_global_put),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add), # this opcode should not be deduplicated because the second occurrence of the stateful ops produces a different result than the first
    ])

    assert actual == expected
