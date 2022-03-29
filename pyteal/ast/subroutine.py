from collections import OrderedDict
from inspect import isclass, Parameter, signature, Signature
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
    Union,
    TYPE_CHECKING,
    Tuple,
    cast,
    Any,
)

from ..errors import TealInputError, verifyTealVersion
from ..ir import TealOp, Op, TealBlock
from ..types import TealType

from .expr import Expr
from .seq import Seq
from .scratchvar import DynamicScratchVar, ScratchVar
from . import abi

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class SubroutineDefinition:
    nextSubroutineId = 0

    def __init__(
        self,
        implementation: Callable[..., Expr],
        return_type: TealType,
        nameStr: Optional[str] = None,
        router_registrable: bool = False,
    ) -> None:
        super().__init__()
        self.id = SubroutineDefinition.nextSubroutineId
        SubroutineDefinition.nextSubroutineId += 1
        self.__routerRegistrable = router_registrable

        if not callable(implementation):
            raise TealInputError("Input to SubroutineDefinition is not callable")

        sig = signature(implementation)

        annotations = getattr(implementation, "__annotations__", OrderedDict())

        if "return" in annotations and annotations["return"] is not Expr:
            raise TealInputError(
                f"Function has return of disallowed type {annotations['return']}. Only Expr is allowed"
            )

        # validate full signature takes following four arguments:
        # - `can_accept_abi_outputs`, which is decided by the `returnType`: if `returnType` is `TealType.none`,
        #    then we are able to return an ABI value, which eventually evaluates to `TealType.none` on stack.
        # - `signature`, which contains the signature of the python function.
        #    NOTE: it contains all the arguments, we get type annotations from `annotations`.
        # - `annotations`, which contains all available argument type annotations and return type annotation.
        #    NOTE: `annotations` does not contain all the arguments,
        #          an argument is not included in `annotations` if its type annotation is not available.
        # - `routerRegistrable`, which enforces every argument are ABI typed.
        (
            expected_arg_types,
            by_ref_args,
            abi_args,
        ) = SubroutineDefinition._arg_types_and_by_refs(
            return_type == TealType.none, sig, annotations, self.__routerRegistrable
        )
        self.expected_arg_types: List[
            Union[Type[Expr], Type[ScratchVar], abi.TypeSpec]
        ] = expected_arg_types
        self.by_ref_args: Set[str] = by_ref_args
        self.abi_args: Dict[str, abi.TypeSpec] = abi_args

        self.implementation = implementation
        self.implementation_params = sig.parameters
        self.return_type = return_type

        self.declaration: Optional["SubroutineDeclaration"] = None
        self.__name = self.implementation.__name__ if nameStr is None else nameStr

    @staticmethod
    def is_abi_class(arg_type: Type) -> bool:
        return (
            isclass(arg_type)
            and arg_type is not abi.BaseType
            and issubclass(arg_type, abi.BaseType)
        )

    @staticmethod
    def is_abi_annotation(obj: Any) -> bool:
        try:
            abi.type_spec_from_annotation(obj)
            return True
        except TypeError:
            return False

    @staticmethod
    def _check_abi_output(annotations: Dict[str, type], sig: Signature) -> None:
        """Checks the `output` keyword argument in subroutine, specialized for outputting ABI value case.

        Assuming that `output` keyword argument is available in `annotations`, which satisfying:
        - it is a KEYWORD_ONLY argument
        - it has no default value
        - it is annotated with ABI type

        Args:
            annotations: annotations obtained from the subroutine definition python implementation
            sig: function signature obtained from the subroutine definition python implementation
        """
        outputParams = sig.parameters["output"]
        if outputParams.kind != Parameter.KEYWORD_ONLY:
            raise TealInputError(
                "output is a reserved name in subroutine for ABI type annotation"
            )
        if outputParams.default != Parameter.empty:
            raise TealInputError(
                "reserved name output in subroutine for ABI type annotation is not allowed to have default value"
            )
        outputPType = annotations.get("output", None)
        if not outputPType:
            raise TealInputError(
                "ABI type annotation for subroutine argument output is required"
            )
        if not SubroutineDefinition.is_abi_annotation(outputPType):
            raise TealInputError(
                "ABI type annotation for subroutine argument output get unexpected: {}".format(
                    outputPType
                )
            )

    @staticmethod
    def _validate_parameter_type(
        user_defined_annotations: dict, parameter_name: str, enforce_abi: bool
    ) -> Union[Type[Union[Expr, ScratchVar]], abi.TypeSpec]:
        ptype = user_defined_annotations.get(parameter_name, None)

        if enforce_abi and not SubroutineDefinition.is_abi_annotation(ptype):
            raise TealInputError(
                f"Function has parameter {parameter_name} of not ABI type: {ptype}"
            )

        if ptype is None:
            # Without a type annotation, `SubroutineDefinition` presumes an implicit `Expr` declaration
            # rather than these alternatives:
            # * Throw error requiring type annotation.
            # * Defer parameter type checks until arguments provided during invocation.
            #
            # * Rationale:
            #   * Provide an upfront, best-effort type check before invocation.
            #   * Preserve backwards compatibility with TEAL programs written
            #     when `Expr` is the only supported annotation type.
            # * `invoke` type checks provided arguments against parameter types to catch mismatches.
            return Expr
        else:
            if not isclass(ptype) and not SubroutineDefinition.is_abi_annotation(ptype):
                raise TealInputError(
                    "Function has parameter {} of declared type {} which is not a class".format(
                        parameter_name, ptype
                    )
                )

            if ptype in (Expr, ScratchVar):
                return ptype
            elif SubroutineDefinition.is_abi_annotation(ptype):
                return abi.type_spec_from_annotation(ptype)
            else:
                raise TealInputError(
                    "Function has parameter {} of disallowed type {}. Only the types {} are allowed".format(
                        parameter_name, ptype, (Expr, ScratchVar, "ABI")
                    )
                )

    @staticmethod
    def _arg_types_and_by_refs(
        can_have_abi_output: bool,
        sig: Signature,
        annotations: Dict[str, type],
        enforce_all_abi: bool,
    ) -> Tuple[
        List[Union[Type[Union[Expr, ScratchVar]], abi.TypeSpec]],
        Set[str],
        Dict[str, abi.TypeSpec],
    ]:
        """Validate the full function signature and annotations for subroutine definition.

        This function iterates through `sig.parameters.items()`, and checks each of subroutine arguments.
        On each of the subroutine arguments, the following checks are performed:
        - If argument is not POSITION_ONLY or not POSITIONAL_OR_KEYWORD
          - if we can_have_abi_output, and the argument name is not `output`, error.
          - if we cannot have abi output (i.e., subroutine return is not `TealType.none`), then error.
        - If argument has default value, error
        - If `output` is available in function signature, then perform `_check_abi_output` on `output` argument.

        After the previous three checks, the function signature is correct in structure,
        but we still need to check the argument types are matching requirements
        (i.e., in {Expr, ScratchVar, inheritances of abi.BaseType} or {inheritances of abi.BaseTypes}).

        Finally, this function outputs `expected_arg_types` for type-checking, and `by_ref_args` for compilation.
        - `expected_arg_types` is an array of elements of Type[Expr], Type[ScratchVar] or abi.TypeSpec instances.
          It helps type-checking on SubroutineCall from `invoke` method.
        - `by_ref_args` is a set of argument names, which are type annotated by ScratchVar or ABI types
          We put the scratch slot id on stack, rather than value itself.

        Args:
            can_have_abi_output: decided by the subroutine's `returnType`, if `returnType` is `TealType.none`,
                then we are able to return an ABI value, which eventually evaluates to `TealType.none` on stack.
            sig: containing the signature of the python function for subroutine definition.
                NOTE: it contains all the arguments, we obtain type annotations from `annotations`.
            annotations: all available argument type annotations and return type annotation.
                NOTE: `annotations` does not contain all the arguments,
                an argument is not included in `annotations` if its type annotation is not available.
            enforce_all_abi: decides whether we enforce each subroutine argument is only ABI typed
        """
        expected_arg_types = []
        by_ref_args: Set[str] = set()
        abi_args: Dict[str, abi.TypeSpec] = {}
        for name, param in sig.parameters.items():
            if param.kind not in (
                Parameter.POSITIONAL_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            ) and (not can_have_abi_output or name != "output"):
                raise TealInputError(
                    "Function has a parameter type that is not allowed in a subroutine: "
                    "parameter {} with type {}".format(name, param.kind)
                )
            if param.default != Parameter.empty:
                raise TealInputError(
                    f"Function has a parameter with a default value, which is not allowed in a subroutine: {name}"
                )

            # if an argument with name `output` reach here, and it's kind is `KEYWORD_ONLY`,
            # then we are only under `enforce_all_abi == True` case.
            # otherwise (`enforce_all_abi == False`), it is eliminated in previous argument kind check.
            if name == "output" and param.kind == Parameter.KEYWORD_ONLY:
                SubroutineDefinition._check_abi_output(annotations, sig)

            expected_arg_type = SubroutineDefinition._validate_parameter_type(
                annotations, name, enforce_all_abi
            )
            expected_arg_types.append(expected_arg_type)
            if expected_arg_type is ScratchVar:
                by_ref_args.add(name)
            if isinstance(expected_arg_type, abi.TypeSpec):
                abi_args[name] = expected_arg_type

        return expected_arg_types, by_ref_args, abi_args

    def routerRegistrable(self) -> bool:
        return self.__routerRegistrable

    def getDeclaration(self) -> "SubroutineDeclaration":
        if self.declaration is None:
            # lazy evaluate subroutine
            self.declaration = evaluateSubroutine(self)
        return self.declaration

    def name(self) -> str:
        return self.__name

    def argumentCount(self) -> int:
        return len(self.implementation_params)

    def arguments(self) -> List[str]:
        return list(self.implementation_params.keys())

    def invoke(
        self, args: List[Union[Expr, ScratchVar, abi.BaseType]]
    ) -> "SubroutineCall":
        if len(args) != self.argumentCount():
            raise TealInputError(
                "Incorrect number of arguments for subroutine call. Expected {} arguments, got {}".format(
                    self.argumentCount(), len(args)
                )
            )

        for i, arg in enumerate(args):
            arg_type = self.expected_arg_types[i]
            if arg_type is Expr and not isinstance(arg, Expr):
                raise TealInputError(
                    f"supplied argument {arg} at index {i} had type {type(arg)} but was expecting type {arg_type}"
                )
            elif arg_type is ScratchVar and not isinstance(arg, ScratchVar):
                raise TealInputError(
                    f"supplied argument {arg} at index {i} had type {type(arg)} but was expecting type {arg_type}"
                )
            elif isinstance(arg_type, abi.TypeSpec):
                if not isinstance(arg, abi.BaseType):
                    raise TealInputError(
                        f"supplied argument at index {i} should be an ABI type but got {arg}"
                    )
                if arg.type_spec() != arg_type:
                    raise TealInputError(
                        f"supplied argument {arg} at index {i} "
                        f"should have ABI typespec {arg_type} but got {arg.type_spec()}"
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
        self,
        subroutine: SubroutineDefinition,
        args: List[Union[Expr, ScratchVar, abi.BaseType]],
    ) -> None:
        super().__init__()
        self.subroutine = subroutine
        self.args = args

        for i, arg in enumerate(args):
            if isinstance(arg, Expr):
                arg_type = arg.type_of()
            elif isinstance(arg, ScratchVar):
                arg_type = arg.type
            elif SubroutineDefinition.is_abi_class(type(arg)):
                arg_type = cast(abi.BaseType, arg).stored_value.type
            else:
                raise TealInputError(
                    "Subroutine argument {} at index {} was of unexpected Python type {}".format(
                        arg, i, type(arg)
                    )
                )

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

        def handle_arg(arg: Union[Expr, ScratchVar, abi.BaseType]) -> Expr:
            if isinstance(arg, ScratchVar):
                return arg.index()
            elif isinstance(arg, Expr):
                return arg
            elif isinstance(arg, abi.BaseType):
                return arg.stored_value.load()
            else:
                raise TealInputError(
                    "cannot handle current arg: {} to put it on stack".format(arg)
                )

        op = TealOp(self, Op.callsub, self.subroutine)
        return TealBlock.FromOp(options, op, *(handle_arg(x) for x in self.args))

    def __str__(self):
        ret_str = '(SubroutineCall "' + self.subroutine.name() + '" ('
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += "))"
        return ret_str

    def type_of(self):
        return self.subroutine.return_type

    def has_return(self):
        return False


SubroutineCall.__module__ = "pyteal"


class SubroutineFnWrapper:
    def __init__(
        self,
        fnImplementation: Callable[..., Expr],
        returnType: TealType,
        name: Optional[str] = None,
        routerRegistrable: bool = False,
    ) -> None:
        self.subroutine = SubroutineDefinition(
            fnImplementation,
            return_type=returnType,
            nameStr=name,
            router_registrable=routerRegistrable,
        )

    def __call__(self, *args: Union[Expr, ScratchVar, abi.BaseType], **kwargs) -> Expr:
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

    def __init__(self, returnType: TealType, name: Optional[str] = None) -> None:
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


def abi_return_subroutine(fnImplementation: Callable[..., Expr]) -> SubroutineFnWrapper:
    return SubroutineFnWrapper(
        fnImplementation, returnType=TealType.none, routerRegistrable=True
    )


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
        Type 3. ABI ...

    Usage (B) "loadedArgs" - Passing through to an invoked PyTEAL subroutine AST:
        Type 1. (by-value) use ScratchVar.load() to have an Expr that can be compiled in python by the PyTEAL subroutine
        Type 2. (by-reference) use a DynamicScratchVar as the user will have written the PyTEAL in a way that satisfies
            the ScratchVar API. I.e., the user will write `x.load()` and `x.store(val)` as opposed to just `x`.
        Type 3. ABI ...
    """

    def var_n_loaded(param):
        # the question is that, abi args are indices laied on the stack, then how to pass by ref with write protection for args?
        # - if we know they are arguments (not output), we can loads from index, and store into arg
        # - if we know it is an output, then how to create an arg that has same index as output one.
        if param in subroutine.abi_args:
            internal_abi_var = subroutine.abi_args[param].new_instance()
            argVar = internal_abi_var.stored_value
            loaded = internal_abi_var
        elif param in subroutine.by_ref_args:
            argVar = DynamicScratchVar(TealType.anytype)
            loaded = argVar
        else:
            argVar = ScratchVar(TealType.anytype)
            loaded = argVar.load()

        return argVar, loaded

    args = subroutine.arguments()
    argumentVars, loadedArgs = zip(*map(var_n_loaded, args)) if args else ([], [])

    argumentVars = cast(List[Union[ScratchVar, DynamicScratchVar]], argumentVars)

    # Arg usage "B" supplied to build an AST from the user-defined PyTEAL function:
    subroutineBody = subroutine.implementation(*loadedArgs)

    if not isinstance(subroutineBody, Expr):
        raise TealInputError(
            f"Subroutine function does not return a PyTeal expression. Got type {type(subroutineBody)}"
        )

    # Arg usage "A" to be pick up and store in scratch parameters that have been placed on the stack
    # need to reverse order of argumentVars because the last argument will be on top of the stack
    bodyOps = [var.slot.store() for var in argumentVars[::-1]]
    bodyOps.append(subroutineBody)

    return SubroutineDeclaration(subroutine, Seq(bodyOps))
