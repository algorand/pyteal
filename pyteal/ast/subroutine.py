from collections import OrderedDict
from dataclasses import dataclass
from inspect import isclass, Parameter, signature, Signature
from typing import (
    Callable,
    Optional,
    Type,
    TYPE_CHECKING,
    cast,
    Any,
)

from pyteal.ast.abi.type import ReturnedValue

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
        name_str: Optional[str] = None,
        abi_output_arg_name: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.id = SubroutineDefinition.nextSubroutineId
        SubroutineDefinition.nextSubroutineId += 1

        if not callable(implementation):
            raise TealInputError("Input to SubroutineDefinition is not callable")

        sig = signature(implementation)

        annotations = getattr(implementation, "__annotations__", OrderedDict())

        if "return" in annotations and annotations["return"] is not Expr:
            raise TealInputError(
                f"Function has return of disallowed type {annotations['return']}. Only Expr is allowed"
            )

        # validate full signature takes following two arguments:
        # - `signature`, which contains the signature of the python function.
        #    NOTE: it contains all the arguments, we get type annotations from `annotations`.
        # - `annotations`, which contains all available argument type annotations and return type annotation.
        #    NOTE: `annotations` does not contain all the arguments,
        #          an argument is not included in `annotations` if its type
        # annotation is not available.
        (
            expected_arg_types,
            by_ref_args,
            abi_args,
            abi_output_kwarg,
        ) = SubroutineDefinition._arg_types_and_by_refs(
            sig, annotations, abi_output_arg_name
        )
        self.expected_arg_types: list[
            Type[Expr] | Type[ScratchVar] | abi.TypeSpec
        ] = expected_arg_types
        self.by_ref_args: set[str] = by_ref_args
        self.abi_args: dict[str, abi.TypeSpec] = abi_args
        self.abi_output_kwarg: dict[str, abi.TypeSpec] = abi_output_kwarg

        self.implementation = implementation
        self.implementation_params = sig.parameters
        self.return_type = return_type

        self.declaration: Optional["SubroutineDeclaration"] = None
        self.__name = self.implementation.__name__ if name_str is None else name_str

    @staticmethod
    def is_abi_annotation(obj: Any) -> bool:
        try:
            abi.type_spec_from_annotation(obj)
            return True
        except TypeError:
            return False

    @staticmethod
    def _validate_parameter_type(
        user_defined_annotations: dict[str, Any], parameter_name: str
    ) -> Type[Expr] | Type[ScratchVar] | abi.TypeSpec:
        ptype = user_defined_annotations.get(parameter_name, None)

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
                    f"Function has parameter {parameter_name} of declared type {ptype} which is not a class"
                )

            if ptype in (Expr, ScratchVar):
                return ptype
            elif SubroutineDefinition.is_abi_annotation(ptype):
                return abi.type_spec_from_annotation(ptype)
            else:
                raise TealInputError(
                    f"Function has parameter {parameter_name} of disallowed type {ptype}. "
                    f"Only the types {(Expr, ScratchVar, 'ABI')} are allowed"
                )

    @staticmethod
    def _arg_types_and_by_refs(
        sig: Signature,
        annotations: dict[str, type],
        abi_output_arg_name: Optional[str] = None,
    ) -> tuple[
        list[Type[Expr] | Type[ScratchVar] | abi.TypeSpec],
        set[str],
        dict[str, abi.TypeSpec],
        dict[str, abi.TypeSpec],
    ]:
        """Validate the full function signature and annotations for subroutine definition.

        This function iterates through `sig.parameters.items()`, and checks each of subroutine arguments.
        On each of the subroutine arguments, the following checks are performed:
        - If argument is not POSITION_ONLY or not POSITIONAL_OR_KEYWORD, error
        - If argument has default value, error

        After the previous checks, the function signature is correct in structure,
        but we still need to check the argument types are matching requirements
        (i.e., in {Expr, ScratchVar, inheritances of abi.BaseType}).

        Finally, this function outputs `expected_arg_types` for type-checking, `by_ref_args` for compilation,
        and `abi_args` for compilation.
        - `expected_arg_types` is an array of elements of Type[Expr], Type[ScratchVar] or abi.TypeSpec instances.
          It helps type-checking on SubroutineCall from `invoke` method.
        - `by_ref_args` is a set of argument names, which are type annotated by ScratchVar.
          We put the scratch slot id on stack, rather than value itself.
        - `abi_args` is a set of argument names, which are type annotated by ABI types.
          We load the ABI scratch space stored value to stack, and store them later in subroutine's local ABI values.

        Args:
            sig: containing the signature of the python function for subroutine definition.
                NOTE: it contains all the arguments, we obtain type annotations from `annotations`.
            annotations: all available argument type annotations and return type annotation.
                NOTE: `annotations` does not contain all the arguments,
                an argument is not included in `annotations` if its type annotation is not available.
        """
        expected_arg_types = []
        by_ref_args: set[str] = set()
        abi_args: dict[str, abi.TypeSpec] = {}
        abi_output_kwarg: dict[str, abi.TypeSpec] = {}
        for name, param in sig.parameters.items():
            if param.kind not in (
                Parameter.POSITIONAL_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            ) and not (
                param.kind is Parameter.KEYWORD_ONLY
                and abi_output_arg_name is not None
                and name == abi_output_arg_name
            ):
                raise TealInputError(
                    f"Function has a parameter type that is not allowed in a subroutine: "
                    f"parameter {name} with type {param.kind}"
                )

            if param.default != Parameter.empty:
                raise TealInputError(
                    f"Function has a parameter with a default value, which is not allowed in a subroutine: {name}"
                )

            expected_arg_type = SubroutineDefinition._validate_parameter_type(
                annotations, name
            )

            if param.kind is Parameter.KEYWORD_ONLY:
                if not isinstance(expected_arg_type, abi.TypeSpec):
                    raise TealInputError(
                        f"Function keyword parameter {name} has type {expected_arg_type}"
                    )
                # TODO not sure if I should put this in by_ref_args, since compiler will use this to disallow recursion
                abi_output_kwarg[name] = expected_arg_type
                continue
            else:
                expected_arg_types.append(expected_arg_type)

            if expected_arg_type is ScratchVar:
                by_ref_args.add(name)
            if isinstance(expected_arg_type, abi.TypeSpec):
                abi_args[name] = expected_arg_type

        return expected_arg_types, by_ref_args, abi_args, abi_output_kwarg

    def getDeclaration(self) -> "SubroutineDeclaration":
        if self.declaration is None:
            # lazy evaluate subroutine
            self.declaration = evaluateSubroutine(self)
        return self.declaration

    def name(self) -> str:
        return self.__name

    def argumentCount(self) -> int:
        return len(self.implementation_params)

    def arguments(self) -> list[str]:
        return list(self.implementation_params.keys())

    # TODO need to support keyword invoke
    def invoke(
        self,
        args: list[Expr | ScratchVar | abi.BaseType],
        *,
        output_kwargs: Optional[dict[str, abi.BaseType]] = None,
    ) -> "SubroutineCall":
        if len(args) != self.argumentCount():
            raise TealInputError(
                f"Incorrect number of arguments for subroutine call. "
                f"Expected {self.argumentCount()} arguments, got {len(args)}"
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
        return f"subroutine#{self.id}"

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
        return f'(SubroutineDeclaration "{self.subroutine.name()}" {self.body})'

    def type_of(self):
        return self.body.type_of()

    def has_return(self):
        return self.body.has_return()


SubroutineDeclaration.__module__ = "pyteal"


# TODO support keyword argument
class SubroutineCall(Expr):
    def __init__(
        self,
        subroutine: SubroutineDefinition,
        args: list[Expr | ScratchVar | abi.BaseType],
    ) -> None:
        super().__init__()
        self.subroutine = subroutine
        self.args = args

        for i, arg in enumerate(args):
            if isinstance(arg, Expr):
                arg_type = arg.type_of()
            elif isinstance(arg, ScratchVar):
                arg_type = arg.type
            elif isinstance(arg, abi.BaseType):
                arg_type = cast(abi.BaseType, arg).stored_value.type
            else:
                raise TealInputError(
                    f"Subroutine argument {arg} at index {i} was of unexpected Python type {type(arg)}"
                )

            if arg_type == TealType.none:
                raise TealInputError(
                    f"Subroutine argument {arg} at index {i} evaluates to TealType.none"
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

        3. (ABI, or a special case in by-value) In this case, the storage of an ABI value are loaded
            to the stack and will be stored in a local ABI value for subroutine evaluation
        """
        verifyTealVersion(
            Op.callsub.min_version,
            options.version,
            "TEAL version too low to use SubroutineCall expression",
        )

        def handle_arg(arg: Expr | ScratchVar | abi.BaseType) -> Expr:
            if isinstance(arg, ScratchVar):
                return arg.index()
            elif isinstance(arg, Expr):
                return arg
            elif isinstance(arg, abi.BaseType):
                return arg.stored_value.load()
            else:
                raise TealInputError(
                    f"cannot handle current arg: {arg} to put it on stack"
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
        fn_implementation: Callable[..., Expr],
        return_type: TealType,
        name: Optional[str] = None,
    ) -> None:
        self.subroutine = SubroutineDefinition(
            fn_implementation,
            return_type=return_type,
            name_str=name,
        )

    def __call__(self, *args: Expr | ScratchVar | abi.BaseType, **kwargs) -> Expr:
        if len(kwargs) != 0:
            raise TealInputError(
                f"Subroutine cannot be called with keyword arguments. "
                f"Received keyword arguments: {','.join(kwargs.keys())}"
            )
        return self.subroutine.invoke(list(args))

    def name(self) -> str:
        return self.subroutine.name()

    def type_of(self):
        return self.subroutine.getDeclaration().type_of()

    def has_return(self):
        return self.subroutine.getDeclaration().has_return()


SubroutineFnWrapper.__module__ = "pyteal"


@dataclass
class _OutputKwArgInfo:
    name: str
    abi_type: abi.TypeSpec
    abi_instance: abi.BaseType


class ABIReturnSubroutineFnWrapper:
    def __init__(
        self,
        fn_implementation: Callable[..., Expr],
    ) -> None:
        self.output_kwarg_info: None | _OutputKwArgInfo = (
            self._output_name_type_from_fn(fn_implementation)
        )
        output_kwarg_name = (
            None if self.output_kwarg_info is None else self.output_kwarg_info.name
        )

        # no matter what, output is void or abiType, stack type is TealType.none
        self.subroutine = SubroutineDefinition(
            fn_implementation,
            return_type=TealType.none,
            abi_output_arg_name=output_kwarg_name,
        )

    @staticmethod
    def _output_name_type_from_fn(
        fn_implementation: Callable[..., Expr]
    ) -> None | _OutputKwArgInfo:
        sig = signature(fn_implementation)
        fn_annotations = getattr(fn_implementation, "__annotations__", OrderedDict())

        potential_abi_arg_names = list(
            filter(
                lambda key: sig.parameters[key].kind == Parameter.KEYWORD_ONLY,
                sig.parameters.keys(),
            )
        )
        if len(potential_abi_arg_names) == 0:
            return None
        elif len(potential_abi_arg_names) == 1:
            name = potential_abi_arg_names[0]
            annotation = fn_annotations.get(name, None)
            if annotation is None:
                raise TealInputError(
                    f"ABI subroutine output-kwarg {name} must specify ABI type"
                )
            type_spec = abi.type_spec_from_annotation(annotation)
            type_instance = type_spec.new_instance()
            return _OutputKwArgInfo(name, type_spec, type_instance)
        else:
            raise TealInputError(
                f"multiple output arguments with type annotations {potential_abi_arg_names}"
            )

    def __call__(
        self, *args: Expr | ScratchVar | abi.BaseType, **kwargs: abi.BaseType
    ) -> abi.ReturnedValue | Expr:
        if self.output_kwarg_info is None:
            if len(kwargs) != 0:
                raise TealInputError(
                    f"Subroutine cannot be called with keyword arguments. "
                    f"Received keyword arguments: {','.join(kwargs.keys())}"
                )
            return self.subroutine.invoke(list(args))

        if len(kwargs) != 1:
            raise TealInputError(
                f"Subroutine should have provided output keyword argument with name {self.output_kwarg_info.name}, "
                f"while the kwargs are {kwargs}."
            )
        if self.output_kwarg_info.name not in kwargs:
            raise TealInputError(
                f"Subroutine should have provided output keyword argument with name {self.output_kwarg_info.name}, "
                f"while provided kwarg is {list(kwargs.keys())}"
            )
        invoked = self.subroutine.invoke(
            list(args),
            output_kwargs={
                self.output_kwarg_info.name: self.output_kwarg_info.abi_instance
            },
        )
        return ReturnedValue(self.output_kwarg_info.abi_instance, invoked)

    def name(self) -> str:
        return self.subroutine.name()

    def type_of(self) -> str | abi.TypeSpec:
        return (
            "void"
            if self.output_kwarg_info is None
            else self.output_kwarg_info.abi_type
        )

    def is_registrable(self) -> bool:
        # return len(self.subroutine.abi_args) == self.subroutine.argumentCount()
        # TODO
        return False


ABIReturnSubroutineFnWrapper.__module__ = "pyteal"


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

    def __init__(self, return_type: TealType, name: Optional[str] = None) -> None:
        """Define a new subroutine with the given return type.

        Args:
            return_type: The type that the return value of this subroutine must conform to.
                TealType.none indicates that this subroutine does not return any value.
        """
        self.return_type = return_type
        self.name = name

    def __call__(self, fn_implementation: Callable[..., Expr]) -> SubroutineFnWrapper:
        return SubroutineFnWrapper(
            fn_implementation=fn_implementation,
            return_type=self.return_type,
            name=self.name,
        )


Subroutine.__module__ = "pyteal"


def abi_return_subroutine(
    fn_implementation: Callable[..., Expr]
) -> ABIReturnSubroutineFnWrapper:
    return ABIReturnSubroutineFnWrapper(fn_implementation=fn_implementation)


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
    Type 3 (ABI): these are ABI typed variables with scratch space storage, and still pass by value
    Type 4 (ABI-output-arg): ABI typed variables with scractch space, but pass by ref to allow for changes

    Usage (A) "argumentVars" - Storing pre-placed stack variables into local scratch space:
        Type 1. (by-value) use ScratchVar.store() to pick the actual value into a local scratch space
        Type 2. (by-reference) ALSO use ScratchVar.store() to pick up from the stack
            NOTE: SubroutineCall.__teal__() has placed the _SLOT INDEX_ on the stack so this is stored into the local scratch space
        Type 3. (ABI) abi_value.stored_value.store() to pick from the stack
        Type 4. (ABI-output-arg) use ScratchVar.store() to pick up from the stack
            NOTE: SubroutineCall.__teal__() has placed the ABI value's _SLOT INDEX_ on the stack, pass-by-ref is similarly achieved

    Usage (B) "loadedArgs" - Passing through to an invoked PyTEAL subroutine AST:
        Type 1. (by-value) use ScratchVar.load() to have an Expr that can be compiled in python by the PyTEAL subroutine
        Type 2. (by-reference) use a DynamicScratchVar as the user will have written the PyTEAL in a way that satisfies
            the ScratchVar API. I.e., the user will write `x.load()` and `x.store(val)` as opposed to just `x`.
        Type 3. (ABI) use abi_value itself after storing stack value into scratch space.
        Type 4. (ABI-output-arg) use a DynamicScratchVar to "point to" the output ABI value's scratch variable
            all the ABI operations are passed through DynamicScratchVar to original ScratchVar, which is pass-by-ref behavior
    """

    def var_n_loaded(
        param: str,
    ) -> tuple[ScratchVar, ScratchVar | abi.BaseType | Expr]:
        loaded: ScratchVar | abi.BaseType | Expr
        arg_var: ScratchVar

        if param in subroutine.by_ref_args:
            arg_var = DynamicScratchVar(TealType.anytype)
            loaded = arg_var
        elif param in subroutine.abi_output_kwarg:
            arg_var = DynamicScratchVar(TealType.anytype)
            internal_abi_var = subroutine.abi_output_kwarg[param].new_instance()
            internal_abi_var.stored_value = arg_var
            loaded = internal_abi_var
        elif param in subroutine.abi_args:
            internal_abi_var = subroutine.abi_args[param].new_instance()
            arg_var = internal_abi_var.stored_value
            loaded = internal_abi_var
        else:
            arg_var = ScratchVar(TealType.anytype)
            loaded = arg_var.load()

        return arg_var, loaded

    args = subroutine.arguments()
    args = [arg for arg in args if arg not in subroutine.abi_output_kwarg]

    argument_vars, loaded_args = (
        cast(
            tuple[list[ScratchVar], list[ScratchVar | Expr | abi.BaseType]],
            zip(*map(var_n_loaded, args)),
        )
        if args
        else ([], [])
    )

    abi_output_kwargs = {}
    assert len(subroutine.abi_output_kwarg) <= 1, "exceeding "
    if len(subroutine.abi_output_kwarg) > 1:
        raise TealInputError(
            f"ABI keyword argument num: {len(subroutine.abi_output_kwarg)}. "
            f"Exceeding abi output keyword argument max number 1."
        )
    for name in subroutine.abi_output_kwarg:
        arg_var, loaded = var_n_loaded(name)
        abi_output_kwargs[name] = loaded
        argument_vars.append(arg_var)

    # Arg usage "B" supplied to build an AST from the user-defined PyTEAL function:
    subroutineBody = subroutine.implementation(*loaded_args, **abi_output_kwargs)

    if not isinstance(subroutineBody, Expr):
        raise TealInputError(
            f"Subroutine function does not return a PyTeal expression. Got type {type(subroutineBody)}"
        )

    # Arg usage "A" to be pick up and store in scratch parameters that have been placed on the stack
    # need to reverse order of argumentVars because the last argument will be on top of the stack
    bodyOps = [var.slot.store() for var in argument_vars[::-1]]
    bodyOps.append(subroutineBody)

    return SubroutineDeclaration(subroutine, Seq(bodyOps))
