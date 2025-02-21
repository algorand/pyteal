from typing import TYPE_CHECKING
from enum import Enum

from pyteal.types import TealType, require_type
from pyteal.errors import verifyFieldVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr
from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class BlockField(Enum):
    # fmt: off
    #                 id  |    name     |      type     | min version
    block_seed = (0, "BlkSeed",      TealType.bytes,  7)  # noqa: E222
    block_timestamp = (1, "BlkTimestamp", TealType.uint64, 7)  # noqa: E222
    block_proposer = (2, "BlkProposer", TealType.bytes, 11)  # noqa: E222
    block_fees_collected = (3, "BlkFeesCollected", TealType.uint64, 11)  # noqa: E222
    block_bonus = (4, "BlkBonus", TealType.uint64, 11)  # noqa: E222
    block_branch = (5, "BlkBranch", TealType.bytes, 11)  # noqa: E222
    block_fee_sink = (6, "BlkFeeSink", TealType.bytes, 11)  # noqa: E222
    block_protocol = (7, "BlkProtocol", TealType.bytes, 11)  # noqa: E222
    block_txn_counter = (8, "BlkTxnCounter", TealType.uint64, 11)  # noqa: E222
    block_proposer_payout = (9, "BlkProposerPayout", TealType.uint64, 11)  # noqa: E222

    # fmt: on

    def __init__(self, id: int, name: str, type: TealType, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.ret_type = type
        self.min_version = min_version

    def type_of(self) -> TealType:
        return self.ret_type


BlockField.__module__ = "pyteal"


class Block(LeafExpr):
    """An expression that accesses a block property."""

    def __init__(self, field: BlockField, block: Expr) -> None:
        super().__init__()
        self.field = field

        require_type(block, TealType.uint64)
        self.block = block

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        op = TealOp(self, Op.block, self.field.arg_name)
        return TealBlock.FromOp(options, op, self.block)

    def __str__(self):
        return "(Block {})".format(self.field.arg_name)

    def type_of(self):
        return self.field.type_of()

    @classmethod
    def seed(cls, block: Expr) -> Expr:
        """Get the seed of a block.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_seed, block)

    @classmethod
    def timestamp(cls, block: Expr) -> Expr:
        """Get the timestamp of a block.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_timestamp, block)

    @classmethod
    def proposer(cls, block: Expr) -> Expr:
        """Get the proposer of a block.

        Requires program version 11 or higher.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_proposer, block)

    @classmethod
    def fees_collected(cls, block: Expr) -> Expr:
        """Get the fees collected from all the transactions in a block.

        Requires program version 11 or higher.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_fees_collected, block)

    @classmethod
    def bonus(cls, block: Expr) -> Expr:
        """Get the bonus payout available for proposing the block.

        Requires program version 11 or higher.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_bonus, block)

    @classmethod
    def branch(cls, block: Expr) -> Expr:
        """Get the branch of a block.

        Requires program version 11 or higher.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_branch, block)

    @classmethod
    def fee_sink(cls, block: Expr) -> Expr:
        """Get the FeeSink address of a block.

        Requires program version 11 or higher.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_fee_sink, block)

    @classmethod
    def protocol(cls, block: Expr) -> Expr:
        """Get the protocol version of a block.

        Requires program version 11 or higher.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_protocol, block)

    @classmethod
    def txn_counter(cls, block: Expr) -> Expr:
        """Get the transaction counter of a block.

        Requires program version 11 or higher.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_txn_counter, block)

    @classmethod
    def proposer_payout(cls, block: Expr) -> Expr:
        """Get the amount earned by the proposer for proposing the block.

        Requires program version 11 or higher.

        Args:
            block: A block index that corresponds to the block to check,
                must be evaluated to uint64. Fails if the block index is not less than
                :code:`Txn.first_valid()` or more than 1001 rounds before :code:`Txn.last_valid()`.
        """
        return cls(BlockField.block_proposer_payout, block)


Block.__module__ = "pyteal"
