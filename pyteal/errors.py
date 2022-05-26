from typing import Any, Optional, TYPE_CHECKING
import inspect

if TYPE_CHECKING:
    from pyteal.ast import Expr


class TealInternalError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self):
        return self.message


TealInternalError.__module__ = "pyteal"


class TealTypeError(Exception):
    def __init__(self, actual, expected) -> None:
        self.message = "{} while expected {} ".format(actual, expected)

    def __str__(self) -> str:
        return self.message


TealTypeError.__module__ = "pyteal"


class TealInputError(Exception):
    def __init__(self, msg: str) -> None:
        self.message = msg

    def __str__(self) -> str:
        return self.message

    def __eq__(self, other: Any) -> bool:
        return type(other) is TealInputError and self.message == other.message


TealInputError.__module__ = "pyteal"


class TealCompileError(Exception):
    def __init__(self, msg: str, sourceExpr: Optional["Expr"]) -> None:
        self.msg = msg
        self.sourceExpr = sourceExpr

    def __str__(self) -> str:
        if self.sourceExpr is None:
            return self.msg

        trace = getSourceTrace(self.sourceExpr)

        return self.msg + trace

    def __eq__(self, other) -> bool:
        if not isinstance(other, TealCompileError):
            return False
        return self.msg == other.msg and self.sourceExpr is other.sourceExpr


TealCompileError.__module__ = "pyteal"


def getSourceTrace(py_obj):
    trace = "\nTraceback of origin expression (most recent call last):\n" + "".join(
        py_obj.getDefinitionTrace()
    )

    if hasattr(py_obj, "value") and py_obj.value is not None:
        val = py_obj.value
        # TODO: when are these things None?
        if hasattr(val, "subroutine") and val.subroutine is not None:
            impl = val.subroutine.implementation
            source_file = inspect.getabsfile(impl)
            _, source_line = inspect.getsourcelines(impl)
            trace = f": File {source_file}, line {source_line}"

    return trace


def verifyTealVersion(minVersion: int, version: int, msg: str):
    if minVersion > version:
        msg = "{}. Minimum version needed is {}, but current version being compiled is {}".format(
            msg, minVersion, version
        )
        raise TealInputError(msg)


def verifyFieldVersion(fieldName: str, fieldMinVersion: int, version: int):
    verifyTealVersion(
        fieldMinVersion,
        version,
        "TEAL version too low to use field {}".format(fieldName),
    )
