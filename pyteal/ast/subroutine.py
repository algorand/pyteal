from contextlib import contextmanager
import algosdk.abi as sdk_abi
import warnings

from dataclasses import dataclass
from docstring_parser import parse as parse_docstring
from inspect import isclass, Parameter, signature, get_annotations
from types import MappingProxyType, NoneType
from typing import Any, Callable, Final, TYPE_CHECKING, cast, ClassVar

from pyteal.ast import abi
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq
from pyteal.ast.scratchvar import DynamicScratchVar, ScratchVar, ScratchSlot
from pyteal.ast.frame import FrameBury, Proto, FrameVar, ProtoStackLayout
from pyteal.errors import TealInputError, TealInternalError, verifyProgramVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.stack_frame import NatalStackFrame
from pyteal.types import TealType

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class _SubroutineDeclByOption:
    def __init__(self, subroutine_def: "SubroutineDefinition") -> None:
        self.subroutine: SubroutineDefinition = subroutine_def
        self.option_map: dict[bool, SubroutineDeclaration | None] = {
            True: None,
            False: None,
        }
        self.option_method: dict[bool, SubroutineEval] = {
            True: SubroutineEval.fp_evaluator(),
            False: SubroutineEval.normal_evaluator(),
        }
        self.has_return: bool | None = None
        self.type_of: TealType | None = None

    def get_declaration(self) -> "SubroutineDeclaration":
        warnings.warn(
            "`get_declaration` is being deprecated: Please use `get_declaration_by_option` instead.",
            DeprecationWarning,
        )
        return self.get_declaration_by_option(False)

    def get_declaration_by_option(
        self,
        fp_option: bool = True,
    ) -> "SubroutineDeclaration":
        decl = self.option_map[fp_option]
        if decl is not None:
            return decl
        self.option_map[fp_option] = self.option_method[fp_option].evaluate(
            self.subroutine
        )
        return cast(SubroutineDeclaration, self.option_map[fp_option])

    def __probe_info(self, fp_option: bool) -> tuple[bool, TealType]:
        starting_slot_id = ScratchSlot.nextSlotId
        is_pre_existing = self.option_map[fp_option] is not None
        decl = self.get_declaration_by_option(fp_option)
        has_return, type_of = decl.has_return(), decl.type_of()
        if not is_pre_existing:
            self.option_map[fp_option] = None
        ScratchSlot.reset_slot_numbering(starting_slot_id)
        return has_return, type_of

    def __info_prepare(self) -> None:
        if self.has_return is not None and self.type_of is not None:
            return
        ss_ret, ss_type = self.__probe_info(False)
        fp_ret, fp_type = self.__probe_info(True)
        assert ss_ret == fp_ret
        assert ss_type == fp_type
        self.has_return = ss_ret
        self.type_of = ss_type

    def versions_type_of(self) -> TealType:
        self.__info_prepare()
        return cast(TealType, self.type_of)

    def versions_has_return(self) -> bool:
        self.__info_prepare()
        return cast(bool, self.has_return)

    def get_declarations(self) -> None:
        self.option_map[False] = self.get_declaration_by_option(False)
        self.option_map[True] = self.get_declaration_by_option(True)


_SubroutineDeclByOption.__module__ = "pyteal"


class SubroutineDefinition:
    """
    Class that leverages TEAL's `callsub` and `retsub` opcode-pair for subroutines
    """

    nextSubroutineId = 0

    def __init__(
        self,
        implementation: Callable[..., Expr],
        return_type: TealType,
        name_str: str | None = None,
        has_abi_output: bool = False,
    ) -> None:
        """
        Args:
            implementation: The python function defining the subroutine
            return_type: the TealType to be returned by the subroutine
            name_str (optional): the name that is used to identify the subroutine.
                If omitted, the name defaults to the implementation's __name__ attribute
            has_abi_output (optional): the boolean that tells if ABI output kwarg for subroutine is used.
        """
        super().__init__()
        self.id = SubroutineDefinition.nextSubroutineId
        SubroutineDefinition.nextSubroutineId += 1

        self.return_type = return_type
        self.declaration: "SubroutineDeclaration | None" = None
        self.declarations: _SubroutineDeclByOption = _SubroutineDeclByOption(self)

        self.implementation: Callable = implementation
        self.has_abi_output: bool = has_abi_output

        self.implementation_params: MappingProxyType[str, Parameter]
        self.annotations: dict[str, type]
        self.expected_arg_types: list[type[Expr] | type[ScratchVar] | abi.TypeSpec]
        self.by_ref_args: set[str]
        self.abi_args: dict[str, abi.TypeSpec]
        self.output_kwarg: dict[str, abi.TypeSpec]

        (
            self.implementation_params,
            self.annotations,
            self.expected_arg_types,
            self.by_ref_args,
            self.abi_args,
            self.output_kwarg,
        ) = self._validate()

        self.__name: str = name_str if name_str else self.implementation.__name__

        self.stack_frames: NatalStackFrame = NatalStackFrame()

    def _validate(
        self, input_types: list[TealType | None] | None = None
    ) -> tuple[
        MappingProxyType[str, Parameter],
        dict[str, type],
        list[type[Expr] | type[ScratchVar] | abi.TypeSpec],
        set[str],
        dict[str, abi.TypeSpec],
        dict[str, abi.TypeSpec],
    ]:
        """Validate the full function signature and annotations for subroutine definition.

        NOTE: `self.implementation` should be set before calling `_validate()`

        This function iterates through `sig.parameters.items()`, and checks each of subroutine arguments.
        On each of the subroutine arguments, the following checks are performed:
        - If argument is not POSITION_ONLY or not POSITIONAL_OR_KEYWORD, error
        - If argument has default value, error

        After the previous checks, the function signature is correct in structure,
        but we still need to check the argument types are matching requirements
        (i.e., in {Expr, ScratchVar, inheritances of abi.BaseType}).

        Finally, this function outputs:
        - `implementation_params` - ordered map from parameter name to inspect.Parameter
        - `annotations` - map from parameter name to annotation (if available)
        - `expected_arg_types` - an array of elements of Type[Expr], Type[ScratchVar] or abi.TypeSpec instances
          It helps type-checking on SubroutineCall from `invoke` method.
        - `by_ref_args` - a set of argument names, which are type annotated by ScratchVar.
        We put the scratch slot id on the stack, rather than the value itself.
        - `abi_args` - a set of argument names, which are type annotated by ABI types.
        We load the ABI scratch space stored value to stack, and store them later in subroutine's local ABI values.
        - `abi_output_kwarg` - a possibly empty dict which when non-empty contains exactly one key
            `ABIReturnSubroutine.OUTPUT_ARG_NAME` with a value that gives abi-tye information about the output

        Args:
            input_types (optional): for testing purposes - expected `TealType`s of each parameter

        Returns:
            impl_params: a map from python function implementation's argument name, to argument's parameter.
            annotations: a dict whose keys are names of type-annotated arguments,
                and values are appearing type-annotations.
            arg_types: a list of argument type inferred from python function implementation,
                containing [type[Expr]| type[ScratchVar] | abi.TypeSpec].
            by_ref_args: a list of argument names that are passed in Subroutine with by-reference mechanism.
            abi_args: a dict whose keys are names of ABI arguments, and values are their ABI type-specs.
            abi_output_kwarg (might be empty): a dict whose key is the name of ABI output keyword argument,
                and the value is the corresponding ABI type-spec.
                NOTE: this dict might be empty, when we are defining a normal subroutine,
                    but it has at most one element when we define an ABI-returning subroutine.
        """

        if not callable(self.implementation):
            raise TealInputError("Input to SubroutineDefinition is not callable")

        impl_params: MappingProxyType[str, Parameter] = signature(
            self.implementation
        ).parameters
        annotations: dict[str, type] = get_annotations(self.implementation)
        arg_types: list[type[Expr] | type[ScratchVar] | abi.TypeSpec] = []
        by_ref_args: set[str] = set()
        abi_args: dict[str, abi.TypeSpec] = {}
        abi_output_kwarg: dict[str, abi.TypeSpec] = {}

        if "return" in annotations and annotations["return"] is not Expr:
            raise TealInputError(
                f"Function has return of disallowed type {annotations['return']}. Only Expr is allowed"
            )

        for name, param in impl_params.items():
            if param.kind not in (
                Parameter.POSITIONAL_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            ) and not (
                param.kind is Parameter.KEYWORD_ONLY
                and self.has_abi_output
                and name == ABIReturnSubroutine.OUTPUT_ARG_NAME
            ):
                raise TealInputError(
                    f"Function has a parameter type that is not allowed in a subroutine: parameter {name} with type {param.kind}"
                )

            if param.default != Parameter.empty:
                raise TealInputError(
                    f"Function has a parameter with a default value, which is not allowed in a subroutine: {name}"
                )

            expected_arg_type = self._validate_annotation(annotations, name)

            if param.kind is Parameter.KEYWORD_ONLY:
                # this case is only entered when
                # - `self.has_abi_output is True`
                # - `name == ABIReturnSubroutine.OUTPUT_ARG_NAME`
                if not isinstance(expected_arg_type, abi.TypeSpec):
                    raise TealInputError(
                        f"Function keyword parameter {name} has type {expected_arg_type}"
                    )
                abi_output_kwarg[name] = expected_arg_type
                continue

            arg_types.append(expected_arg_type)
            if expected_arg_type is ScratchVar:
                by_ref_args.add(name)
            if isinstance(expected_arg_type, abi.TypeSpec):
                abi_args[name] = expected_arg_type

        if input_types is not None:
            input_arg_count = len(impl_params) - len(abi_output_kwarg)
            if len(input_types) != input_arg_count:
                raise TealInputError(
                    f"Provided number of input_types ({len(input_types)}) "
                    f"does not match detected number of input parameters ({input_arg_count})"
                )
            for in_type, name in zip(input_types, impl_params):
                if not isinstance(in_type, (TealType, NoneType)):
                    raise TealInputError(
                        f"Function has input type {in_type} for parameter {name} which is not a TealType"
                    )
                if in_type is None and name not in abi_args:
                    raise TealInputError(
                        f"input_type for {name} is unspecified i.e. None "
                        f"but this is only allowed for ABI arguments"
                    )

        return (
            impl_params,
            annotations,
            arg_types,
            by_ref_args,
            abi_args,
            abi_output_kwarg,
        )

    @staticmethod
    def _is_abi_annotation(obj: Any) -> bool:
        try:
            abi.type_spec_from_annotation(obj)
            return True
        except TypeError:
            return False

    @staticmethod
    def _validate_annotation(
        user_defined_annotations: dict[str, Any], parameter_name: str
    ) -> type[Expr] | type[ScratchVar] | abi.TypeSpec:
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
        if ptype in (Expr, ScratchVar):
            return ptype
        if SubroutineDefinition._is_abi_annotation(ptype):
            return abi.type_spec_from_annotation(ptype)
        if not isclass(ptype):
            raise TealInputError(
                f"Function has parameter {parameter_name} of declared type {ptype} which is not a class"
            )
        raise TealInputError(
            f"Function has parameter {parameter_name} of disallowed type {ptype}. "
            f"Only the types {(Expr, ScratchVar, 'ABI')} are allowed"
        )

    def get_declaration(self) -> "SubroutineDeclaration":
        warnings.warn(
            "`get_declaration` is being deprecated: Please use `get_declaration_by_option` instead.",
            DeprecationWarning,
        )
        return self.declarations.get_declaration_by_option(False)

    def get_declaration_by_option(
        self,
        fp_option: bool = True,
    ) -> "SubroutineDeclaration":
        return self.declarations.get_declaration_by_option(fp_option)

    def name(self) -> str:
        return self.__name

    def argument_count(self) -> int:
        return len(self.arguments())

    def arguments(self) -> list[str]:
        syntax_args = list(self.implementation_params.keys())
        syntax_args = [
            arg_name for arg_name in syntax_args if arg_name not in self.output_kwarg
        ]
        return syntax_args

    def invoke(
        self,
        args: list[Expr | ScratchVar | abi.BaseType],
    ) -> "SubroutineCall":
        from pyteal.ast.abi.util import type_spec_is_assignable_to

        if len(args) != self.argument_count():
            raise TealInputError(
                f"Incorrect number of arguments for subroutine call. "
                f"Expected {self.arguments()} arguments, got {len(args)} arguments"
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

                if not type_spec_is_assignable_to(arg.type_spec(), arg_type):
                    raise TealInputError(
                        f"supplied argument {arg} at index {i} "
                        f"should have ABI typespec {arg_type} but got {arg.type_spec()}"
                    )

        return SubroutineCall(
            self, args, output_kwarg=OutputKwArgInfo.from_dict(self.output_kwarg)
        )

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
    def __init__(
        self,
        subroutine: SubroutineDefinition,
        body: Expr,
        deferred_expr: Expr | None = None,
    ) -> None:
        super().__init__()
        self.subroutine = subroutine
        self.body = body
        self.deferred_expr = deferred_expr
        self._sframes_container: SubroutineDefinition = subroutine

    def __teal__(self, options: "CompileOptions"):
        return self.body.__teal__(options)

    def __str__(self):
        return f'(SubroutineDeclaration "{self.subroutine.name()}" {self.body})'

    def type_of(self):
        return self.body.type_of()

    def has_return(self):
        return self.body.has_return()


SubroutineDeclaration.__module__ = "pyteal"


@dataclass
class OutputKwArgInfo:
    name: str
    abi_type: abi.TypeSpec

    @staticmethod
    def from_dict(kwarg_info: dict[str, abi.TypeSpec]) -> "OutputKwArgInfo | None":
        match list(kwarg_info.keys()):
            case []:
                return None
            case [k]:
                return OutputKwArgInfo(k, kwarg_info[k])
            case _:
                raise TealInputError(
                    f"illegal conversion kwarg_info length {len(kwarg_info)}."
                )


OutputKwArgInfo.__module__ = "pyteal"


class SubroutineCall(Expr):
    def __init__(
        self,
        subroutine: SubroutineDefinition,
        args: list[Expr | ScratchVar | abi.BaseType],
        *,
        output_kwarg: OutputKwArgInfo | None = None,
    ) -> None:
        super().__init__()
        self.subroutine = subroutine
        self.args = args
        self.output_kwarg = output_kwarg

        for i, arg in enumerate(args):
            if isinstance(arg, Expr):
                arg_type = arg.type_of()
            elif isinstance(arg, ScratchVar):
                arg_type = arg.type
            elif isinstance(arg, abi.BaseType):
                arg_type = cast(abi.BaseType, arg)._stored_value.storage_type()
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
        There are 4 cases to consider for the pushed arg expression:

        1. (by-value) In the case of typical arguments of type Expr, the expression ITSELF is evaluated for the stack
            and will be stored in a local ScratchVar for subroutine evaluation

        2. (by-reference) In the case of a by-reference argument of type ScratchVar, its SLOT INDEX is put on the stack
            and will be stored in a local DynamicScratchVar for subroutine evaluation

        3. (ABI, or a special case in by-value) In this case, the storage of an ABI value are loaded
            to the stack and will be stored in a local ABI value for subroutine evaluation

        4. (ABI output keyword argument) In this case, we do not place ABI values (encoding) on the stack.
            This is an *output-only* argument: in `evaluate_subroutine` an ABI typed instance for subroutine evaluation
            will be generated, and gets in to construct the subroutine implementation.
        """
        verifyProgramVersion(
            Op.callsub.min_version,
            options.version,
            "Program version too low to use SubroutineCall expression",
        )

        def handle_arg(arg: Expr | ScratchVar | abi.BaseType) -> Expr:
            ret_expr: Expr
            if isinstance(arg, ScratchVar):
                ret_expr = arg.index()
                ret_expr.stack_frames = self.subroutine.stack_frames
            elif isinstance(arg, Expr):
                ret_expr = arg
            elif isinstance(arg, abi.BaseType):
                ret_expr = arg._stored_value.load()
                ret_expr.stack_frames = self.subroutine.stack_frames
            else:
                raise TealInputError(
                    f"cannot handle current arg: {arg} to put it on stack"
                )

            return ret_expr

        op = TealOp(self, Op.callsub, self.subroutine)
        return TealBlock.FromOp(options, op, *[handle_arg(x) for x in self.args])

    def __str__(self):
        arg_str_list = list(map(str, self.args))
        if self.output_kwarg:
            arg_str_list.append(
                f"{self.output_kwarg.name}={str(self.output_kwarg.abi_type)}"
            )
        return f'(SubroutineCall {self.subroutine.name()} ({" ".join(arg_str_list)}))'

    def type_of(self):
        output_info = OutputKwArgInfo.from_dict(self.subroutine.output_kwarg)
        if output_info:
            return output_info.abi_type.storage_type()
        return self.subroutine.return_type

    def has_return(self):
        return False


SubroutineCall.__module__ = "pyteal"


class SubroutineFnWrapper:
    def __init__(
        self,
        fn_implementation: Callable[..., Expr],
        return_type: TealType,
        name: str | None = None,
    ) -> None:
        self.subroutine = SubroutineDefinition(
            fn_implementation,
            return_type=return_type,
            name_str=name,
        )

    def __call__(
        self, *args: Expr | ScratchVar | abi.BaseType, **kwargs: Any
    ) -> SubroutineCall:
        if len(kwargs) != 0:
            raise TealInputError(
                f"Subroutine cannot be called with keyword arguments. "
                f"Received keyword arguments: {','.join(kwargs.keys())}"
            )
        return self.subroutine.invoke(list(args))

    def name(self) -> str:
        return self.subroutine.name()

    def type_of(self):
        return self.subroutine.declarations.versions_type_of()

    def has_return(self):
        return self.subroutine.declarations.versions_has_return()


SubroutineFnWrapper.__module__ = "pyteal"


class ABIReturnSubroutine:
    """Used to create a PyTeal Subroutine (returning an ABI value) from a python function.  It's primarily intended to define ARC-4 Application entry points though it can also be used more generally.

    *Disclaimer*:  ABIReturnSubroutine is still taking shape and is subject to backwards incompatible changes.

    * For ARC-4 Application entry point definition, feel encouraged to use ABIReturnSubroutine.  Expect a best-effort attempt to minimize backwards incompatible changes along with a migration path.
    * For general purpose subroutine definition usage, use at your own risk.  Based on feedback, the API and usage patterns will change more freely and with less effort to provide migration paths.

    This class is meant to be used as a function decorator. For example:

        .. code-block:: python

            @ABIReturnSubroutine
            def abi_sum(toSum: abi.DynamicArray[abi.Uint64], *, output: abi.Uint64) -> Expr:
                i = ScratchVar(TealType.uint64)
                valueAtIndex = abi.Uint64()
                return Seq(
                    output.set(0),
                    For(i.store(Int(0)), i.load() < toSum.length(), i.store(i.load() + Int(1))).Do(
                        Seq(
                            toSum[i.load()].store_into(valueAtIndex),
                            output.set(output.get() + valueAtIndex.get()),
                        )
                    ),
                )

            program = Seq(
                (to_sum_arr := abi.make(abi.DynamicArray[abi.Uint64])).decode(
                    Txn.application_args[1]
                ),
                (res := abi.Uint64()).set(abi_sum(to_sum_arr)),
                abi.MethodReturn(res),
                Int(1),
            )
    """

    OUTPUT_ARG_NAME: Final[str] = "output"

    def __init__(
        self,
        fn_implementation: Callable[..., Expr],
        /,
        *,
        overriding_name: str | None = None,
    ) -> None:
        self.output_kwarg_info: OutputKwArgInfo | None = self._get_output_kwarg_info(
            fn_implementation
        )
        self.subroutine = SubroutineDefinition(
            fn_implementation,
            return_type=TealType.none,
            name_str=overriding_name,
            has_abi_output=self.output_kwarg_info is not None,
        )

    @staticmethod
    def name_override(name: str) -> Callable[..., "ABIReturnSubroutine"]:
        def wrapper(fn_impl: Callable[..., Expr]) -> ABIReturnSubroutine:
            return ABIReturnSubroutine(fn_impl, overriding_name=name)

        return wrapper

    @classmethod
    def _get_output_kwarg_info(
        cls, fn_implementation: Callable[..., Expr]
    ) -> OutputKwArgInfo | None:
        if not callable(fn_implementation):
            raise TealInputError("Input to ABIReturnSubroutine is not callable")
        sig = signature(fn_implementation)
        fn_annotations = get_annotations(fn_implementation)

        potential_abi_arg_names = [
            k for k, v in sig.parameters.items() if v.kind == Parameter.KEYWORD_ONLY
        ]

        match potential_abi_arg_names:
            case []:
                return None
            case [name]:
                if name != cls.OUTPUT_ARG_NAME:
                    raise TealInputError(
                        f"ABI return subroutine output-kwarg name must be `output` at this moment, "
                        f"while {name} is the keyword."
                    )
                annotation = fn_annotations.get(name, None)
                if annotation is None:
                    raise TealInputError(
                        f"ABI return subroutine output-kwarg {name} must specify ABI type"
                    )
                type_spec = abi.type_spec_from_annotation(annotation)
                return OutputKwArgInfo(name, type_spec)
            case _:
                raise TealInputError(
                    f"multiple output arguments ({len(potential_abi_arg_names)}) "
                    f"with type annotations {potential_abi_arg_names}"
                )

    def __call__(
        self, *args: Expr | ScratchVar | abi.BaseType, **kwargs
    ) -> abi.ReturnedValue | SubroutineCall:
        if len(kwargs) != 0:
            raise TealInputError(
                f"Subroutine cannot be called with keyword arguments. "
                f"Received keyword arguments: {', '.join(kwargs.keys())}"
            )

        invoked = self.subroutine.invoke(list(args))
        if self.output_kwarg_info is None:
            if invoked.type_of() != TealType.none:
                raise TealInputError(
                    "ABI subroutine with void type should be evaluated to TealType.none"
                )
            return invoked

        return abi.ReturnedValue(
            self.output_kwarg_info.abi_type,
            invoked,
        )

    def name(self) -> str:
        return self.subroutine.name()

    def method_signature(self, overriding_name: str | None = None) -> str:
        if not self.is_abi_routable():
            raise TealInputError(
                "Only registrable methods may return a method signature"
            )

        ret_type = self.type_of()
        if isinstance(ret_type, abi.TypeSpec) and abi.contains_type_spec(
            ret_type, abi.TransactionTypeSpecs + abi.ReferenceTypeSpecs
        ):
            raise TealInputError(
                f"Reference and Transaction types may not be used as return values, got {ret_type}"
            )

        args = [str(v) for v in self.subroutine.abi_args.values()]
        if overriding_name is None:
            overriding_name = self.name()
        return f"{overriding_name}({','.join(args)}){self.type_of()}"

    def method_spec(self) -> sdk_abi.Method:
        desc: str = ""
        arg_descs: dict[str, str] = {}
        return_desc: str = ""
        args: list[dict[str, str]] = []

        if self.subroutine.implementation.__doc__:
            docstring = parse_docstring(self.subroutine.implementation.__doc__)

            # Combine short and long descriptions with newline
            method_descriptions: list[str] = []
            if docstring.short_description:
                method_descriptions.append(docstring.short_description)
            if docstring.long_description:
                method_descriptions.append(docstring.long_description)

            method_desc = "\n\n".join(method_descriptions)

            # Turn double new line into single, replacing single newline with space
            desc = "\n".join(
                [
                    i.replace("\n", " ").strip()
                    for i in method_desc.split("\n\n")
                    if i.strip()
                ]
            )

            # Get the descriptions for any documented arguments
            arg_descs = {
                arg.arg_name: arg.description.replace("\n", " ").strip()
                for arg in docstring.params
                if arg.arg_name != self.OUTPUT_ARG_NAME and arg.description is not None
            }

            # Get the special return description
            return_desc = (
                ""
                if not docstring.returns or not docstring.returns.description
                else docstring.returns.description.replace("\n", " ").strip()
            )

        # Generate the ABI method object given the subroutine args
        # Add in description if one is set
        for name, val in self.subroutine.annotations.items():
            # Skip annotations for `return` and `output` in the args list
            if name in ["return", self.OUTPUT_ARG_NAME]:
                continue

            arg_obj = {
                "type": str(abi.type_spec_from_annotation(val)),
                "name": name,
            }

            if name in arg_descs:
                arg_obj["desc"] = arg_descs[name]

            args.append(arg_obj)

        # Create the return obj for the method, adding description if set
        return_obj = {"type": str(self.type_of())}
        if return_desc and return_obj["type"] != "void":
            return_obj["desc"] = return_desc

        # Create the method spec, adding description if set
        spec = {"name": self.name(), "args": args, "returns": return_obj}
        if desc:
            spec["desc"] = desc

        return sdk_abi.Method.undictify(spec)

    def type_of(self) -> str | abi.TypeSpec:
        return (
            "void"
            if self.output_kwarg_info is None
            else self.output_kwarg_info.abi_type
        )

    def is_abi_routable(self) -> bool:
        return len(self.subroutine.abi_args) == self.subroutine.argument_count()


ABIReturnSubroutine.__module__ = "pyteal"


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

    def __init__(self, return_type: TealType, name: str | None = None) -> None:
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


@contextmanager
def _frame_pointer_context(proto: Proto | None):
    tmp, SubroutineEval._current_proto = SubroutineEval._current_proto, proto
    yield proto
    SubroutineEval._current_proto = tmp


@dataclass
class SubroutineEval:
    """
    Puts together the data necessary to define the code for a subroutine.
    "evaluate" is used here to connote evaluating the PyTEAL AST into a SubroutineDeclaration,
    but not actually placing it at call locations. The trickiest part here is managing the subroutine's arguments.
    The arguments are needed for two different code-paths, and there are 2 different argument types to consider
    for each of the code-paths.

    2 Argument Usages / Code-Paths
    - -------- ------   ----------
    Usage (A) for run-time: "argumentVars" --reverse--> "body_ops"
        These are "store" expressions that pick up parameters that have been pre-placed on the stack prior to subroutine invocation.
        The argumentVars are stored into local scratch space to be used by the TEAL subroutine.

    Usage (B) for compile-time: "loadedArgs"
        These are expressions supplied to the user-defined PyTEAL function.
        The loadedArgs are invoked to by the subroutine to create a self-contained AST which will translate into a TEAL subroutine.

    In both usage cases, we need to handle

    4 Argument Types
    - -------- -----
    Type 1 (by-value): these have python type Expr
    Type 2 (by-reference): these have python type ScratchVar
    Type 3 (ABI): these are ABI typed variables with scratch space storage, and still pass by value
    Type 4 (ABI-output-arg): ABI typed variables with scratch space, a new ABI instance is generated inside function body,
        not one of the cases in the previous three options

    Because of the introduction of frame pointer, the "argumentVars" and "loadedArgs" are different before and after program version 8.

    "argumentVars" and "loadedArgs" before version 8 (frame pointer version)
    -------------- --- ------------ ------ ------- - -----------------------

    Usage (A) "argumentVars" - Storing pre-placed stack variables into local scratch space:
        Type 1. (by-value) use ScratchVar.store() to pick the actual value into a local scratch space
        Type 2. (by-reference) ALSO use ScratchVar.store() to pick up from the stack
            NOTE: SubroutineCall.__teal__() has placed the _SLOT INDEX_ on the stack so this is stored into the local scratch space
        Type 3. (ABI) abi_value.stored_value.store() to pick from the stack
        Type 4. (ABI-output-arg) it is not really used here, since it is only generated internal of the subroutine

    Usage (B) "loadedArgs" - Passing through to an invoked PyTEAL subroutine AST:
        Type 1. (by-value) use ScratchVar.load() to have an Expr that can be compiled in python by the PyTEAL subroutine
        Type 2. (by-reference) use a DynamicScratchVar as the user will have written the PyTEAL in a way that satisfies
            the ScratchVar API. I.e., the user will write `x.load()` and `x.store(val)` as opposed to just `x`.
        Type 3. (ABI) use abi_value itself after storing stack value into scratch space.
        Type 4. (ABI-output-arg) generates a new instance of the ABI value,
            and appends a return expression of stored value of the ABI keyword value.

    "argumentVars" and "loadedArgs" after version 8 (frame pointer version)
    -------------- --- ------------ ----- ------- - -----------------------

    Usage (A) "argumentVars" - Storing pre-placed stack variables with frame pointer:
        Type 1. (by-value) use None for we can load from stack with FrameDig() from FrameVar abstraction
        Type 2. (by-reference) use FrameDig() from FrameVar abstraction to pick up from the stack
            NOTE: SubroutineCall.__teal__() has placed the _SLOT INDEX_ on the stack so this is stored into the local scratch space
        Type 3. (ABI) use None for we can load from stack with FrameDig() from FrameVar abstraction
            NOTE: SubroutineCall.__teal__() has placed the ABI encoding on the stack, so ABI set and get methods are working over stack
        Type 4. (ABI-output-arg) it is not really used here, but we use FrameDig/Bury to interact with it

    Usage (B) "loadedArgs" - Passing through to an invoked PyTEAL subroutine AST:
        Type 1. (by-value) use FrameDig() from FrameVar abstraction, to have an Expr that can be compiled in python by the PyTEAL subroutine.
        Type 2. (by-reference) use a DynamicScratchVar as the user will have written the PyTEAL in a way that satisfies
            the ScratchVar API. I.e., the user will write `x.load()` and `x.store(val)` as opposed to just `x`.
        Type 3. (ABI) use abi_value that interface with stack data through FrameVar abstraction.
        Type 4. (ABI-output-arg) Prepare a FrameVar over the stack with frame-index 0 against current frame pointer,
            and set the ABI value's _stored_value to be using FrameVar.
    """

    var_n_loaded_method: Callable[
        [SubroutineDefinition, str, Proto | None],
        tuple[ScratchVar | None, ScratchVar | abi.BaseType | Expr],
    ]
    use_frame_pt: bool = False
    _current_proto: ClassVar[Proto | None] = None

    @staticmethod
    def _new_abi_instance_from_storage(
        spec: abi.TypeSpec, storage: FrameVar
    ) -> abi.BaseType:
        """
        This hidden method generates new ABI instance that is tied to the storage: FrameVar as follows:
        - generates new instance that is based on scratch vars
        - rewind the new instance to be using storage: FrameVar
        - rewind the state changed by scratch slot allocation
        """
        current_scratch_id = ScratchSlot.nextSlotId
        with _frame_pointer_context(None):
            instance = spec.new_instance()
        instance._stored_value = storage
        ScratchSlot.reset_slot_numbering(current_scratch_id)
        return instance

    @staticmethod
    def var_n_loaded_scratch(
        subroutine: SubroutineDefinition,
        param: str,
        _: Proto | None = None,
    ) -> tuple[ScratchVar, ScratchVar | abi.BaseType | Expr]:
        loaded_var: ScratchVar | abi.BaseType | Expr
        argument_var: ScratchVar

        if param in subroutine.by_ref_args:
            argument_var = DynamicScratchVar(TealType.anytype)
            loaded_var = argument_var
        elif param in subroutine.abi_args:
            with _frame_pointer_context(None):
                internal_abi_var = subroutine.abi_args[param].new_instance()
            argument_var = cast(ScratchVar, internal_abi_var._stored_value)
            loaded_var = internal_abi_var
        else:
            argument_var = ScratchVar(TealType.anytype)
            loaded_var = argument_var.load()

        return argument_var, loaded_var

    @staticmethod
    def var_n_loaded_fp(
        subroutine: SubroutineDefinition,
        param: str,
        proto: Proto | None,
    ) -> tuple[ScratchVar | None, ScratchVar | abi.BaseType | Expr]:
        if not proto:
            raise TealInternalError(
                "proto should be available for frame pointer based subroutine."
            )

        loaded_var: ScratchVar | abi.BaseType | Expr
        argument_var: ScratchVar | None

        if param in subroutine.by_ref_args:
            argument_var = DynamicScratchVar(TealType.anytype)
            loaded_var = argument_var
        elif param in subroutine.abi_args:
            dig_index = (
                subroutine.arguments().index(param) - subroutine.argument_count()
            )
            internal_abi_var = SubroutineEval._new_abi_instance_from_storage(
                subroutine.abi_args[param], FrameVar(proto, dig_index)
            )
            argument_var = None
            loaded_var = internal_abi_var
        else:
            dig_index = (
                subroutine.arguments().index(param) - subroutine.argument_count()
            )
            argument_var = None
            loaded_var = FrameVar(proto, dig_index).load()

        return argument_var, loaded_var

    @staticmethod
    def __proto(subroutine: SubroutineDefinition) -> Proto:
        arg_stack_types: list[TealType] = []
        for t in subroutine.expected_arg_types:
            if t is Expr:
                arg_stack_types.append(TealType.anytype)
            elif t is ScratchVar:
                arg_stack_types.append(TealType.uint64)
            else:
                arg_stack_types.append(cast(abi.TypeSpec, t).storage_type())

        num_return_allocs: int = int(subroutine.has_abi_output)

        local_stack_types: list[TealType] = []
        if subroutine.has_abi_output:
            output_info = cast(
                OutputKwArgInfo, OutputKwArgInfo.from_dict(subroutine.output_kwarg)
            )
            local_stack_types = [output_info.abi_type.storage_type()]

        layout: ProtoStackLayout = ProtoStackLayout(
            arg_stack_types, local_stack_types, num_return_allocs
        )

        # if subroutine do not have abi output, then only two cases happen:
        # - subroutine is a normal subroutine, then check subroutine body evaluates to something, rather than none
        # - subroutine is an ABIReturnSubroutine, the type is void, and its subroutine body type of is always none
        num_stack_outputs: int = (
            1
            if subroutine.has_abi_output
            else int(subroutine.return_type != TealType.none)
        )

        return Proto(subroutine.argument_count(), num_stack_outputs, mem_layout=layout)

    def evaluate(self, subroutine: SubroutineDefinition) -> SubroutineDeclaration:
        proto = self.__proto(subroutine)

        args = subroutine.arguments()
        arg_var_n_frame_index_pairs: list[tuple[ScratchVar, int]] = []
        loaded_args: list[ScratchVar | Expr | abi.BaseType] = []
        for index, arg in enumerate(args):
            arg_var, loaded_arg = self.var_n_loaded_method(subroutine, arg, proto)
            if arg_var:
                arg_var_n_frame_index_pairs.append(
                    (arg_var, index - subroutine.argument_count())
                )
            loaded_args.append(loaded_arg)

        abi_output_kwargs: dict[str, abi.BaseType] = {}
        output_kwarg_info = OutputKwArgInfo.from_dict(subroutine.output_kwarg)
        output_carrying_abi: abi.BaseType | None = None

        if output_kwarg_info:
            if not self.use_frame_pt:
                with _frame_pointer_context(None):
                    output_carrying_abi = output_kwarg_info.abi_type.new_instance()
            else:
                output_carrying_abi = SubroutineEval._new_abi_instance_from_storage(
                    output_kwarg_info.abi_type, FrameVar(proto, 0)
                )

            abi_output_kwargs[output_kwarg_info.name] = output_carrying_abi

        # Arg usage "B" supplied to build an AST from the user-defined PyTEAL function:
        subroutine_body: Expr

        with _frame_pointer_context(proto if self.use_frame_pt else None):
            subroutine_body = subroutine.implementation(
                *loaded_args, **abi_output_kwargs
            )

        if not isinstance(subroutine_body, Expr):
            raise TealInputError(
                f"Subroutine function does not return a PyTeal expression. Got type {type(subroutine_body)}."
            )

        deferred_expr: Expr | None = None

        # if there is an output keyword argument for ABI
        # place the storing on the stack with deferred expr only when compile to scratch var
        if output_carrying_abi:
            if subroutine_body.type_of() != TealType.none:
                raise TealInputError(
                    f"ABI returning subroutine definition should evaluate to TealType.none, "
                    f"while evaluate to {subroutine_body.type_of()}."
                )
            if not self.use_frame_pt:
                deferred_expr = output_carrying_abi._stored_value.load()

        if self.use_frame_pt:
            local_size = len(proto.mem_layout.local_stack_types)
            # only when we have 1 return, and with other local variables
            # we use bury to bury the result to 0 index against frame pointer
            if not abi_output_kwargs and proto.num_returns > 0 and local_size > 0:
                deferred_expr = FrameBury(Seq(), 0, inferred_type=TealType.none)

        # Arg usage "A" to be pick up and store in scratch parameters that have been placed on the stack
        # need to reverse order of argumentVars because the last argument will be on top of the stack

        body_ops: list[Expr]
        if not self.use_frame_pt:
            body_ops = [
                var.slot.store() for var, _ in arg_var_n_frame_index_pairs[::-1]
            ]
        else:
            body_ops = [proto]
            body_ops += [
                var.slot.store(FrameVar(proto, index).load())
                for var, index in arg_var_n_frame_index_pairs[::-1]
            ]

        # don't reframe the subroutine body
        subroutine.stack_frames.reframe(*body_ops)
        body_ops.append(subroutine_body)
        sd = SubroutineDeclaration(subroutine, Seq(body_ops), deferred_expr)
        sd.trace = subroutine_body.trace
        return sd

    @classmethod
    def normal_evaluator(cls) -> "SubroutineEval":
        return cls(SubroutineEval.var_n_loaded_scratch, False)

    @classmethod
    def fp_evaluator(cls) -> "SubroutineEval":
        return cls(SubroutineEval.var_n_loaded_fp, True)


SubroutineEval.__module__ = "pyteal"
