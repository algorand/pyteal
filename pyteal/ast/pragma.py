from typing import TYPE_CHECKING, Any

from pyteal.ast.expr import Expr
from pyteal.pragma import is_valid_compiler_version, pragma

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Pragma(Expr):
    """A meta expression which defines a pragma for a specific subsection of PyTeal code.

    This expression does not affect the underlying compiled TEAL code in any way."""

    def __init__(self, child: Expr, *, compiler_version: str, **kwargs: Any) -> None:
        """Define a pragma for a specific subsection of PyTeal code.

        The Pragma expression does not affect the underlying compiled TEAL code in any way,
        it merely sets a pragma for the underlying expression.

        Args:
            child: The expression to wrap.
            compiler_version: Acceptable versions of the compiler. Will fail if the current PyTeal version
                is not contained in the range. Follows the npm `semver range scheme <https://github.com/npm/node-semver#ranges>`_
                for specifying compatible versions.

        For example:

        .. code-block:: python

            @Subroutine(TealType.uint64)
            def example() -> Expr:
                # this will fail during compilation if the current PyTeal version does not satisfy
                # the version constraint
                return Pragma(
                    Seq(...),
                    compiler_version="^0.14.0"
                )
        """
        super().__init__()

        self.child = child

        if not is_valid_compiler_version(compiler_version):
            raise ValueError("Invalid compiler version: {}".format(compiler_version))
        self.compiler_version = compiler_version

    def __teal__(self, options: "CompileOptions"):
        pragma(compiler_version=self.compiler_version)

        return self.child.__teal__(options)

    def __str__(self):
        return "(pragma {})".format(self.child)

    def type_of(self):
        return self.child.type_of()

    def has_return(self):
        return self.child.has_return()


Pragma.__module__ = "pyteal"
