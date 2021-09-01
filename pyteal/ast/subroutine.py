from typing import Callable, Tuple, List, Optional, cast, TYPE_CHECKING
from inspect import Parameter, signature
from functools import wraps

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from ..errors import TealInputError, verifyTealVersion
from .expr import Expr
from .seq import Seq
from .scratchvar import ScratchVar

if TYPE_CHECKING:
    from ..ir import TealSimpleBlock
    from ..compiler import CompileOptions


class SubroutineDefinition:

    nextSubroutineId = 0

    def __init__(
        self, implementation: Callable[..., Expr], returnType: TealType
    ) -> None:
        super().__init__()
        self.id = SubroutineDefinition.nextSubroutineId
        SubroutineDefinition.nextSubroutineId += 1

        if not callable(implementation):
            raise TealInputError("Input to SubroutineDefinition is not callable")

        sig = signature(implementation)

        for name, param in sig.parameters.items():
            if param.kind not in (
                Parameter.POSITIONAL_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            ):
                raise TealInputError(
                    "Function has a parameter type that is not allowed in a subroutine: parameter {} with type {}".format(
                        name, param.kind
                    )
                )

            if param.default != Parameter.empty:
                raise TealInputError(
                    "Function has a parameter with a default value, which is not allowed in a subroutine: {}".format(
                        name
                    )
                )

        self.implementation = implementation
        self.implementationParams = sig.parameters
        self.returnType = returnType

        self.declaration: Optional["SubroutineDeclaration"] = None

    def getDeclaration(self) -> "SubroutineDeclaration":
        if self.declaration is None:
            # lazy evaluate subroutine
            self.declaration = evaluateSubroutine(self)
        return self.declaration

    def name(self) -> str:
        return self.implementation.__name__

    def argumentCount(self) -> int:
        return len(self.implementationParams)

    def invoke(self, args: List[Expr]) -> "SubroutineCall":
        if len(args) != self.argumentCount():
            raise TealInputError(
                "Incorrect number of arguments for subroutine call. Expected {} arguments, got {}".format(
                    self.argumentCount(), len(args)
                )
            )

        for i, arg in enumerate(args):
            if not isinstance(arg, Expr):
                raise TealInputError(
                    "Argument at index {} of subroutine call is not a PyTeal expression: {}".format(
                        i, arg
                    )
                )

        return SubroutineCall(self, args)

    def __str__(self):
        return "subroutine#{}".format(self.id)

    def __eq__(self, other):
        if isinstance(other, SubroutineDefinition):
            return self.id == other.id and self.implementation == other.implementation
        return False

    def __hash__(self):
        return hash(self.id)


SubroutineDefinition.__module__ = "pyteal"


class SubroutineDeclaration(Expr):
    def __init__(self, subroutine: SubroutineDefinition, body: Expr) -> None:
        super().__init__()
        self.subroutine = subroutine
        self.body = body

    def __teal__(self, options: "CompileOptions"):
        return self.body.__teal__(options)

    def __str__(self):
        return '(SubroutineDeclaration "{}" {})'.format(
            self.subroutine.name(), self.body
        )

    def type_of(self):
        return self.body.type_of()

    def has_return(self):
        return self.body.has_return()


SubroutineDeclaration.__module__ = "pyteal"


class SubroutineCall(Expr):
    def __init__(self, subroutine: SubroutineDefinition, args: List[Expr]) -> None:
        super().__init__()
        self.subroutine = subroutine
        self.args = args

        for i, arg in enumerate(args):
            if arg.type_of() == TealType.none:
                raise TealInputError(
                    "Subroutine argument at index {} evaluates to TealType.none".format(
                        i
                    )
                )

    def __teal__(self, options: "CompileOptions"):
        verifyTealVersion(
            Op.callsub.min_version,
            options.version,
            "TEAL version too low to use SubroutineCall expression",
        )

        op = TealOp(self, Op.callsub, self.subroutine)
        return TealBlock.FromOp(options, op, *self.args)

    def __str__(self):
        ret_str = '(SubroutineCall "' + self.subroutine.name() + '" ('
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += "))"
        return ret_str

    def type_of(self):
        return self.subroutine.returnType

    def has_return(self):
        return False


SubroutineCall.__module__ = "pyteal"


class Subroutine:
    """Used to create a PyTeal subroutine from a Python function.

    This class is meant to be used as a function decorator. For example:

        .. code-block:: python

            @Subroutine(TealType.uint64)
            def mySubroutine(a: Expr, b: Expr) -> Expr:
                return a + b

            program = Seq([
                App.globalPut(Bytes("key"), mySubroutine(Int(1), Int(2))),
                Approve(),
            ])
    """

    def __init__(self, returnType: TealType) -> None:
        """Define a new subroutine with the given return type.

        Args:
            returnType: The type that the return value of this subroutine must conform to.
                TealType.none indicates that this subroutine does not return any value.
        """
        self.returnType = returnType

    def __call__(self, fnImplementation: Callable[..., Expr]) -> Callable[..., Expr]:
        subroutine = SubroutineDefinition(fnImplementation, self.returnType)

        @wraps(fnImplementation)
        def subroutineCall(*args: Expr, **kwargs) -> Expr:
            if len(kwargs) != 0:
                raise TealInputError(
                    "Subroutine cannot be called with keyword arguments. Received keyword arguments: {}".format(
                        ",".join(kwargs.keys())
                    )
                )
            return subroutine.invoke(list(args))

        return subroutineCall


Subroutine.__module__ = "pyteal"


def evaluateSubroutine(subroutine: SubroutineDefinition) -> SubroutineDeclaration:
    argumentVars = [ScratchVar() for _ in range(subroutine.argumentCount())]
    loadedArgs = [var.load() for var in argumentVars]

    subroutineBody = subroutine.implementation(*loadedArgs)

    if not isinstance(subroutineBody, Expr):
        raise TealInputError(
            "Subroutine function does not return a PyTeal expression. Got type {}".format(
                type(subroutineBody)
            )
        )

    # need to reverse order of argumentVars because the last argument will be on top of the stack
    bodyOps = [var.slot.store() for var in argumentVars[::-1]]
    bodyOps.append(subroutineBody)

    return SubroutineDeclaration(subroutine, Seq(bodyOps))
