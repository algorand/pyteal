from typing import TYPE_CHECKING
from pyteal.errors import TealInputError

from pyteal.types import TealType, require_type
from pyteal.ir import TealOp, Op, TealBlock, TealSimpleBlock, TealConditionalBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions

class BoxCreate(Expr):
    """"""

    def __init__(self, name: Expr, size: Expr) -> None:
        """Create an assert statement that raises an error if the condition is false.

        Args:
            size: The number of bytes to reserve for this box. Must evaluate to a uint64.
            name: The key used to reference this box. Must evaluate to a bytes.
        """
        super().__init__()
        require_type(name, TealType.bytes)
        require_type(size, TealType.uint64)
        self.name = name
        self.size = size

    def __teal__(self, options: "CompileOptions"):
        if options.version < Op.box_create.min_version:
            raise TealInputError(
                f"BoxCreate not available on teal version {options.version} (first available {Op.box_create.min_version})"
            )

        return TealBlock.FromOp(
            options, TealOp(self, Op.box_create), self.size, self.name
        )

    def __str__(self):
        return "(box_create {})".format(self.size, self.name)

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


BoxCreate.__module__ = "pyteal"


class BoxDelete(Expr):
    """"""

    def __init__(self, name: Expr) -> None:
        """ """
        super().__init__()
        require_type(name, TealType.bytes)
        self.name = name

    def __teal__(self, options: "CompileOptions"):
        if options.version < Op.box_del.min_version:
            raise TealInputError(
                f"BoxDelete not available on teal version {options.version} (first available {Op.box_del.min_version})"
            )

        return TealBlock.FromOp(
            options, TealOp(self, Op.box_del),  self.name
        )

    def __str__(self):
        return "(box_del {})".format(self.name)

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


BoxDelete.__module__ = "pyteal"


class BoxReplace(Expr):
    """"""

    def __init__(self, name: Expr, start: Expr, value: Expr) -> None:
        """ """
        super().__init__()
        require_type(name, TealType.bytes)
        require_type(start, TealType.uint64)
        require_type(value, TealType.bytes)
        self.name = name
        self.start = start
        self.value = value

    def __teal__(self, options: "CompileOptions"):
        if options.version < Op.box_replace.min_version:
            raise TealInputError(
                f"BoxReplace not available on teal version {options.version} (first available {Op.box_del.min_version})"
            )

        return TealBlock.FromOp(
            options, TealOp(self, Op.box_replace), self.name, self.start, self.value
        )

    def __str__(self):
        return "(box_replace {} {} {})".format(self.name, self.start, self.value)

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


BoxReplace.__module__ = "pyteal"


class BoxExtract(Expr):
    """"""

    def __init__(self, name: Expr, start: Expr, stop: Expr) -> None:
        """ """
        super().__init__()
        require_type(name, TealType.bytes)
        require_type(start, TealType.uint64)
        require_type(stop, TealType.uint64)
        self.name = name
        self.start = start
        self.stop = stop

    def __teal__(self, options: "CompileOptions"):
        if options.version < Op.box_extract.min_version:
            raise TealInputError(
                f"BoxExtract not available on teal version {options.version} (first available {Op.box_extract.min_version})"
            )

        return TealBlock.FromOp(
            options, TealOp(self, Op.box_extract), self.name, self.start, self.stop
        )

    def __str__(self):
        return "(box_extract {} {} {})".format(self.name, self.start, self.stop)

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return True


BoxExtract.__module__ = "pyteal"
