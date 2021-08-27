from typing import TYPE_CHECKING

from ..types import TealType, require_type, types_match
from ..errors import verifyTealVersion, TealCompileError
from ..ir import TealOp, Op, TealBlock
from .expr import Expr
from .int import Int

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Return(Expr):
    """Return a value from the current execution context."""

    def __init__(self, value: Expr = None) -> None:
        """Create a new Return expression.

        If called from the main program, this will immediately exit the program
        and the value returned will be the program's success value (must be a
        uint64, 0 indicates failure, 1 or greater indicates success).

        If called from within a subroutine, this will return from the current
        subroutine with either no value if the subroutine does not produce a
        return value, or the given return value if it does produce a return value.
        """
        super().__init__()
        if value is not None:
            require_type(value.type_of(), TealType.anytype)
        self.value = value

    def __teal__(self, options: "CompileOptions"):
        if options.currentSubroutine is not None:
            verifyTealVersion(
                Op.retsub.min_version,
                options.version,
                "TEAL version too low to use subroutines",
            )
            returnType = options.currentSubroutine.returnType
            if returnType == TealType.none:
                if self.value is not None:
                    raise TealCompileError(
                        "Cannot return a value from a subroutine with return type TealType.none",
                        self,
                    )
            else:
                if self.value is None:
                    raise TealCompileError(
                        "A subroutine declares it returns a value, but no value is being returned",
                        self,
                    )
                actualType = self.value.type_of()
                if not types_match(actualType, returnType):
                    raise TealCompileError(
                        "Incompatible return type from subroutine, expected {} but got {}".format(
                            returnType, actualType
                        ),
                        self,
                    )
            op = Op.retsub
        else:
            if self.value is None:
                raise TealCompileError(
                    "Return from main program must have an argument", self
                )
            actualType = self.value.type_of()
            if not types_match(actualType, TealType.uint64):
                raise TealCompileError(
                    "Incompatible return type from main program, expected {} but got {}".format(
                        TealType.uint64, actualType
                    ),
                    self,
                )
            op = Op.return_

        args = []
        if self.value is not None:
            args.append(self.value)

        return TealBlock.FromOp(options, TealOp(self, op), *args)

    def __str__(self):
        return "(Return {})".format(self.value)

    def type_of(self):
        return TealType.none

    def has_return(self):
        return True


Return.__module__ = "pyteal"


class ExitProgram(Expr):
    """Immediately exit the program with the indicated success value."""

    def __init__(self, success: Expr) -> None:
        super().__init__()
        require_type(success.type_of(), TealType.uint64)
        self.success = success

    def __teal__(self, options: "CompileOptions"):
        return TealBlock.FromOp(options, TealOp(self, Op.return_), self.success)

    def __str__(self):
        return "(ExitProgram {})".format(self.success)

    def type_of(self):
        return TealType.none

    def has_return(self):
        return True


ExitProgram.__module__ = "pyteal"


def Approve() -> Expr:
    """Immediately exit the program and mark the execution as successful."""
    return ExitProgram(Int(1))


def Reject() -> Expr:
    """Immediately exit the program and mark the execution as unsuccessful."""
    return ExitProgram(Int(0))
