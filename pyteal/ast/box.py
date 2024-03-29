from typing import TYPE_CHECKING
from pyteal.ast.maybe import MaybeValue
from pyteal.errors import verifyProgramVersion

from pyteal.types import TealType, require_type
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class BoxCreate(Expr):
    """Create a box with a given name and size."""

    def __init__(self, name: Expr, size: Expr) -> None:
        """
        Args:
            name: The key used to reference this box. Must evaluate to a bytes.
            size: The number of bytes to reserve for this box. Must evaluate to a uint64.
        """

        super().__init__()
        require_type(name, TealType.bytes)
        require_type(size, TealType.uint64)
        self.name = name
        self.size = size

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            minVersion=Op.box_create.min_version,
            version=options.version,
            msg=f"{Op.box_create} unavailable",
        )
        return TealBlock.FromOp(
            options, TealOp(self, Op.box_create), self.name, self.size
        )

    def __str__(self):
        return f"(box_create {self.name} {self.size})"

    def type_of(self):
        return TealType.uint64

    def has_return(self):
        return False


BoxCreate.__module__ = "pyteal"


class BoxResize(Expr):
    """Resize an existing box.

    If the new size is larger than the old size, zero bytes will be added to the end of the box.
    If the new size is smaller than the old size, the box will be truncated from the end.
    """

    def __init__(self, name: Expr, size: Expr) -> None:
        """
        Args:
            name: The key used to reference this box. Must evaluate to a bytes.
            size: The new number of bytes to reserve for this box. Must evaluate to a uint64.
        """

        super().__init__()
        require_type(name, TealType.bytes)
        require_type(size, TealType.uint64)
        self.name = name
        self.size = size

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            minVersion=Op.box_resize.min_version,
            version=options.version,
            msg=f"{Op.box_resize} unavailable",
        )
        return TealBlock.FromOp(
            options, TealOp(self, Op.box_resize), self.name, self.size
        )

    def __str__(self):
        return f"(box_resize {self.name} {self.size})"

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


BoxResize.__module__ = "pyteal"


class BoxDelete(Expr):
    """Deletes a box given its name."""

    def __init__(self, name: Expr) -> None:
        """
        Args:
            name: The key the box was created with. Must evaluate to bytes.
        """
        super().__init__()
        require_type(name, TealType.bytes)
        self.name = name

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            minVersion=Op.box_del.min_version,
            version=options.version,
            msg=f"{Op.box_del} unavailable",
        )
        return TealBlock.FromOp(options, TealOp(self, Op.box_del), self.name)

    def __str__(self):
        return f"(box_del {self.name})"

    def type_of(self):
        return TealType.uint64

    def has_return(self):
        return False


BoxDelete.__module__ = "pyteal"


class BoxReplace(Expr):
    """Replaces bytes in a box given its name, start index, and value.

    Also see BoxSplice.
    """

    def __init__(self, name: Expr, start: Expr, value: Expr) -> None:
        """
        Args:
            name: The key the box was created with. Must evaluate to bytes.
            start: The byte index into the box to start writing. Must evaluate to uint64.
            value: The value to start writing at start index. Must evaluate to bytes.
        """
        super().__init__()
        require_type(name, TealType.bytes)
        require_type(start, TealType.uint64)
        require_type(value, TealType.bytes)
        self.name = name
        self.start = start
        self.value = value

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            minVersion=Op.box_replace.min_version,
            version=options.version,
            msg=f"{Op.box_replace} unavailable",
        )
        return TealBlock.FromOp(
            options, TealOp(self, Op.box_replace), self.name, self.start, self.value
        )

    def __str__(self):
        return f"(box_replace {self.name} {self.start} {self.value})"

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


BoxReplace.__module__ = "pyteal"


class BoxExtract(Expr):
    """Extracts bytes in a box given its name, start index and stop index."""

    def __init__(self, name: Expr, start: Expr, length: Expr) -> None:
        """
        Args:
            name: The key the box was created with. Must evaluate to bytes.
            start: The byte index into the box to start reading. Must evaluate to uint64.
            length: The byte length into the box from start to stop reading. Must evaluate to uint64.
        """

        super().__init__()
        require_type(name, TealType.bytes)
        require_type(start, TealType.uint64)
        require_type(length, TealType.uint64)
        self.name = name
        self.start = start
        self.length = length

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            minVersion=Op.box_extract.min_version,
            version=options.version,
            msg=f"{Op.box_extract} unavailable",
        )
        return TealBlock.FromOp(
            options, TealOp(self, Op.box_extract), self.name, self.start, self.length
        )

    def __str__(self):
        return f"(box_extract {self.name} {self.start} {self.length})"

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return False


BoxExtract.__module__ = "pyteal"


class BoxSplice(Expr):
    """Splice content into a box."""

    def __init__(
        self, name: Expr, start: Expr, length: Expr, new_content: Expr
    ) -> None:
        """
        Replaces the range of bytes from `start` through `start + length` with `new_content`.

        Bytes after `start + length` will be shifted to the right.

        Recall that boxes are constant length, and this operation will not change the length of the
        box. Instead content may be adjusted as so:

            * If the length of the new content is less than `length`, the bytes following `start + length` will be shifted to the left, and the end of the box will be padded with zeros.

            * If the length of the new content is greater than `length`, the bytes following `start + length` will be shifted to the right and bytes exceeding the length of the box will be truncated.

        Args:
            name: The name of the box to modify. Must evaluate to bytes.
            start: The byte index into the box to start writing. Must evaluate to uint64.
            length: The length of the bytes to be replaced. Must evaluate to uint64.
            new_content: The new content to write into the box. Must evaluate to bytes.
        """
        super().__init__()
        require_type(name, TealType.bytes)
        require_type(start, TealType.uint64)
        require_type(length, TealType.uint64)
        require_type(new_content, TealType.bytes)
        self.name = name
        self.start = start
        self.length = length
        self.new_content = new_content

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            minVersion=Op.box_splice.min_version,
            version=options.version,
            msg=f"{Op.box_splice} unavailable",
        )
        return TealBlock.FromOp(
            options,
            TealOp(self, Op.box_splice),
            self.name,
            self.start,
            self.length,
            self.new_content,
        )

    def __str__(self):
        return f"(box_splice {self.name} {self.start} {self.length} {self.new_content})"

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


BoxSplice.__module__ = "pyteal"


def BoxLen(name: Expr) -> MaybeValue:
    """
    Get the byte length of the box specified by its name.

    Args:
        name: The key the box was created with. Must evaluate to bytes.
    """
    require_type(name, TealType.bytes)
    return MaybeValue(Op.box_len, TealType.uint64, args=[name])


def BoxGet(name: Expr) -> MaybeValue:
    """
    Get the full contents of a box given its name.

    Args:
        name: The key the box was created with. Must evaluate to bytes.
    """
    require_type(name, TealType.bytes)
    return MaybeValue(Op.box_get, TealType.bytes, args=[name])


class BoxPut(Expr):
    """Write all contents to a box given its name."""

    def __init__(self, name: Expr, value: Expr) -> None:
        """
        Args:
            name: The key the box was created with. Must evaluate to bytes.
            value: The value to write to the box. Must evaluate to bytes.
        """

        super().__init__()
        require_type(name, TealType.bytes)
        require_type(value, TealType.bytes)
        self.name = name
        self.value = value

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            minVersion=Op.box_put.min_version,
            version=options.version,
            msg=f"{Op.box_put} unavailable",
        )
        return TealBlock.FromOp(
            options, TealOp(self, Op.box_put), self.name, self.value
        )

    def __str__(self):
        return f"(box_put {self.name})"

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


BoxPut.__module__ = "pyteal"
