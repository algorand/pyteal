from inspect import Parameter, get_annotations, isclass, signature
from types import MappingProxyType
from typing import Callable, List, Optional, Type, Union, TYPE_CHECKING

from pyteal.errors import TealInputError, verifyTealVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.types import TealType

from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq
from pyteal.ast.scratchvar import DynamicScratchVar, ScratchVar

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class SubroutineDefinition:
    """
    Class that leverages TEAL's `callsub` and `retsub` opcode-pair for subroutines
    """

    nextSubroutineId = 0

    def __init__(
        self,
        implementation: Callable[..., Expr],
        returnType: TealType,
        nameStr: str = None,
    ) -> None:
        """
        Args:
            implementation: The python function defining the subroutine
            returnType: the TealType to be returned by the subroutine
            nameStr (optional): the name that is used to identify the subroutine.
                If omitted, the name defaults to the implementation's __name__ attribute
        """
        super().__init__()
        self.id = SubroutineDefinition.nextSubroutineId
        SubroutineDefinition.nextSubroutineId += 1

        self.returnType = returnType
        self.declaration: Optional["SubroutineDeclaration"] = None

        self.implementation: Callable = implementation

        impl_params, anns, arg_types, byrefs = self._validate()
        self.implementationParams: MappingProxyType[str, Parameter] = impl_params
        self.annotations: dict[str, Expr | ScratchVar] = anns
        self.expected_arg_types: list[type[Expr | ScratchVar]] = arg_types
        self.by_ref_args: set[str] = byrefs

        self.__name: str = nameStr if nameStr else self.implementation.__name__

    def _validate(
        self, input_types: list[TealType] = None
    ) -> tuple[
        MappingProxyType[str, Parameter],
        dict[str, Expr | ScratchVar],
        list[type[Expr | ScratchVar]],
        set[str],
    ]:
        implementation = self.implementation
        if not callable(implementation):
            raise TealInputError("Input to SubroutineDefinition is not callable")

        impl_params: MappingProxyType[str, Parameter] = signature(
            implementation
        ).parameters
        anns: dict[str, Expr | ScratchVar] = get_annotations(implementation)
        arg_types: list[type[Expr | ScratchVar]] = []
        byrefs: set[str] = set()

        sig_params = impl_params
        if input_types is not None and len(input_types) != len(sig_params):
            raise TealInputError(
                "Provided number of input_types ({}) does not match detected number of parameters ({})".format(
                    len(input_types), len(sig_params)
                )
            )

        if "return" in anns and anns["return"] is not Expr:
            raise TealInputError(
                "Function has return of disallowed type {}. Only Expr is allowed".format(
                    anns["return"]
                )
            )

        for i, (name, param) in enumerate(impl_params.items()):
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

            if input_types:
                intype = input_types[i]
                if not isinstance(intype, TealType):
                    raise TealInputError(
                        "Function has input type {} for parameter {} which is not a TealType".format(
                            intype, name
                        )
                    )

            expected_arg_type = self._validate_parameter_type(anns, name)

            arg_types.append(expected_arg_type)
            if expected_arg_type is ScratchVar:
                byrefs.add(name)
        return impl_params, anns, arg_types, byrefs

    @staticmethod
    def _validate_parameter_type(
        user_defined_annotations: dict, parameter_name: str
    ) -> Type[Union[Expr, ScratchVar]]:
        ptype = user_defined_annotations.get(parameter_name, None)
        if ptype is None:
            # Without a type annotation, `SubroutineDefinition` presumes an implicit `Expr` declaration rather than these alternatives:
            # * Throw error requiring type annotation.
            # * Defer parameter type checks until arguments provided during invocation.
            #
            # * Rationale:
            #   * Provide an upfront, best-effort type check before invocation.
            #   * Preserve backwards compatibility with TEAL programs written when `Expr` is the only supported annotation type.
            # * `invoke` type checks provided arguments against parameter types to catch mismatches.
            return Expr
        else:
            if not isclass(ptype):
                raise TealInputError(
                    "Function has parameter {} of declared type {} which is not a class".format(
                        parameter_name, ptype
                    )
                )

            if ptype not in (Expr, ScratchVar):
                raise TealInputError(
                    "Function has parameter {} of disallowed type {}. Only the types {} are allowed".format(
                        parameter_name, ptype, (Expr, ScratchVar)
                    )
                )

            return ptype

    def getDeclaration(self) -> "SubroutineDeclaration":
        if self.declaration is None:
            # lazy evaluate subroutine
            self.declaration = evaluateSubroutine(self)
        return self.declaration

    def name(self) -> str:
        return self.__name

    def argumentCount(self) -> int:
        return len(self.implementationParams)

    def arguments(self) -> List[str]:
        return list(self.implementationParams.keys())

    def invoke(self, args: List[Union[Expr, ScratchVar]]) -> "SubroutineCall":
        if len(args) != self.argumentCount():
            raise TealInputError(
                "Incorrect number of arguments for subroutine call. Expected {} arguments, got {}".format(
                    self.argumentCount(), len(args)
                )
            )

        for i, arg in enumerate(args):
            atype = self.expected_arg_types[i]
            if not isinstance(arg, atype):
                raise TealInputError(
                    "supplied argument {} at index {} had type {} but was expecting type {}".format(
                        arg, i, type(arg), atype
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
    def __init__(
        self, subroutine: SubroutineDefinition, args: List[Union[Expr, ScratchVar]]
    ) -> None:
        super().__init__()
        self.subroutine = subroutine
        self.args = args

        for i, arg in enumerate(args):
            arg_type = None

            if not isinstance(arg, (Expr, ScratchVar)):
                raise TealInputError(
                    "Subroutine argument {} at index {} was of unexpected Python type {}".format(
                        arg, i, type(arg)
                    )
                )

            arg_type = arg.type_of() if isinstance(arg, Expr) else arg.type

            if arg_type == TealType.none:
                raise TealInputError(
                    "Subroutine argument {} at index {} evaluates to TealType.none".format(
                        arg, i
                    )
                )

    def __teal__(self, options: "CompileOptions"):
        """
        Generate the subroutine's start and end teal blocks.
        The subroutine's arguments are pushed on the stack to be picked up into local scratch variables.
        There are 2 cases to consider for the pushed arg expression:

        1. (by-value) In the case of typical arguments of type Expr, the expression ITSELF is evaluated for the stack
            and will be stored in a local ScratchVar for subroutine evaluation

        2. (by-reference) In the case of a by-reference argument of type ScratchVar, its SLOT INDEX is put on the stack
            and will be stored in a local DynamicScratchVar for subroutine evaluation
        """
        verifyTealVersion(
            Op.callsub.min_version,
            options.version,
            "TEAL version too low to use SubroutineCall expression",
        )

        def handle_arg(arg):
            return arg.index() if isinstance(arg, ScratchVar) else arg

        op = TealOp(self, Op.callsub, self.subroutine)
        return TealBlock.FromOp(options, op, *(handle_arg(x) for x in self.args))

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


class SubroutineFnWrapper:
    def __init__(
        self,
        fnImplementation: Callable[..., Expr],
        returnType: TealType,
        name: str = None,
    ) -> None:
        self.subroutine = SubroutineDefinition(
            fnImplementation, returnType=returnType, nameStr=name
        )

    def __call__(self, *args: Expr | ScratchVar, **kwargs) -> Expr:
        if len(kwargs) != 0:
            raise TealInputError(
                "Subroutine cannot be called with keyword arguments. Received keyword arguments: {}".format(
                    ",".join(kwargs.keys())
                )
            )
        return self.subroutine.invoke(list(args))

    def name(self) -> str:
        return self.subroutine.name()

    def type_of(self):
        return self.subroutine.getDeclaration().type_of()

    def has_return(self):
        return self.subroutine.getDeclaration().has_return()


SubroutineFnWrapper.__module__ = "pyteal"


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

    def __init__(self, returnType: TealType, name: str = None) -> None:
        """Define a new subroutine with the given return type.

        Args:
            returnType: The type that the return value of this subroutine must conform to.
                TealType.none indicates that this subroutine does not return any value.
        """
        self.returnType = returnType
        self.name = name

    def __call__(self, fnImplementation: Callable[..., Expr]) -> SubroutineFnWrapper:
        return SubroutineFnWrapper(
            fnImplementation=fnImplementation,
            returnType=self.returnType,
            name=self.name,
        )


Subroutine.__module__ = "pyteal"


def evaluateSubroutine(subroutine: SubroutineDefinition) -> SubroutineDeclaration:
    """
    Puts together the data necessary to define the code for a subroutine.
    "evaluate" is used here to connote evaluating the PyTEAL AST into a SubroutineDeclaration,
    but not actually placing it at call locations. The trickiest part here is managing the subroutine's arguments.
    The arguments are needed for two different code-paths, and there are 2 different argument types to consider
    for each of the code-paths:

    2 Argument Usages / Code-Paths
    - -------- ------   ----------
    Usage (A) for run-time: "argumentVars" --reverse--> "bodyOps"
        These are "store" expressions that pick up parameters that have been pre-placed on the stack prior to subroutine invocation.
        The argumentVars are stored into local scratch space to be used by the TEAL subroutine.

    Usage (B) for compile-time: "loadedArgs"
        These are expressions supplied to the user-defined PyTEAL function.
        The loadedArgs are invoked to by the subroutine to create a self-contained AST which will translate into a TEAL subroutine.

    In both usage cases, we need to handle

    2 Argument Types
    - -------- -----
    Type 1 (by-value): these have python type Expr
    Type 2 (by-reference): these have python type ScratchVar

    Usage (A) "argumentVars" - Storing pre-placed stack variables into local scratch space:
        Type 1. (by-value) use ScratchVar.store() to pick the actual value into a local scratch space
        Type 2. (by-reference) ALSO use ScratchVar.store() to pick up from the stack
            NOTE: SubroutineCall.__teal__() has placed the _SLOT INDEX_ on the stack so this is stored into the local scratch space

    Usage (B) "loadedArgs" - Passing through to an invoked PyTEAL subroutine AST:
        Type 1. (by-value) use ScratchVar.load() to have an Expr that can be compiled in python by the PyTEAL subroutine
        Type 2. (by-reference) use a DynamicScratchVar as the user will have written the PyTEAL in a way that satisfies
            the ScratchVar API. I.e., the user will write `x.load()` and `x.store(val)` as opposed to just `x`.
    """

    def var_n_loaded(param):
        if param in subroutine.by_ref_args:
            argVar = DynamicScratchVar(TealType.anytype)
            loaded = argVar
        else:
            argVar = ScratchVar(TealType.anytype)
            loaded = argVar.load()

        return argVar, loaded

    args = subroutine.arguments()
    argumentVars, loadedArgs = zip(*map(var_n_loaded, args)) if args else ([], [])

    # Arg usage "B" supplied to build an AST from the user-defined PyTEAL function:
    subroutineBody = subroutine.implementation(*loadedArgs)

    if not isinstance(subroutineBody, Expr):
        raise TealInputError(
            "Subroutine function does not return a PyTeal expression. Got type {}".format(
                type(subroutineBody)
            )
        )

    # Arg usage "A" to be pick up and store in scratch parameters that have been placed on the stack
    # need to reverse order of argumentVars because the last argument will be on top of the stack
    bodyOps = [var.slot.store() for var in argumentVars[::-1]]
    bodyOps.append(subroutineBody)

    return SubroutineDeclaration(subroutine, Seq(bodyOps))
