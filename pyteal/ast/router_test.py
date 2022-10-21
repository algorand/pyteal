import pyteal as pt
import secrets
from pyteal.ast.router import ASTBuilder
import pytest
import typing
import algosdk.abi as sdk_abi


options = pt.CompileOptions(version=5)


@pt.ABIReturnSubroutine
def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    """add takes 2 integers a,b and adds them, returning the sum"""
    return output.set(a.get() + b.get())


@pt.ABIReturnSubroutine
def sub(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    """replace me"""
    return output.set(a.get() - b.get())


@pt.ABIReturnSubroutine
def mul(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() * b.get())


@pt.ABIReturnSubroutine
def div(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() / b.get())


@pt.ABIReturnSubroutine
def mod(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() % b.get())


@pt.ABIReturnSubroutine
def qrem(
    a: pt.abi.Uint64,
    b: pt.abi.Uint64,
    *,
    output: pt.abi.Tuple2[pt.abi.Uint64, pt.abi.Uint64],
) -> pt.Expr:
    return pt.Seq(
        (q := pt.abi.Uint64()).set(a.get() / b.get()),
        (rem := pt.abi.Uint64()).set(a.get() % b.get()),
        output.set(q, rem),
    )


@pt.ABIReturnSubroutine
def reverse(a: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:
    idx = pt.ScratchVar()
    buff = pt.ScratchVar()

    init = idx.store(pt.Int(0))
    cond = idx.load() < a.length()
    _iter = idx.store(idx.load() + pt.Int(1))
    return pt.Seq(
        buff.store(pt.Bytes("")),
        pt.For(init, cond, _iter).Do(
            a[idx.load()].use(lambda v: buff.store(pt.Concat(v.encode(), buff.load())))
        ),
        output.set(buff.load()),
    )


@pt.ABIReturnSubroutine
def concat_strings(
    b: pt.abi.DynamicArray[pt.abi.String], *, output: pt.abi.String
) -> pt.Expr:
    idx = pt.ScratchVar()
    buff = pt.ScratchVar()

    init = idx.store(pt.Int(0))
    cond = idx.load() < b.length()
    _iter = idx.store(idx.load() + pt.Int(1))
    return pt.Seq(
        buff.store(pt.Bytes("")),
        pt.For(init, cond, _iter).Do(
            b[idx.load()].use(lambda s: buff.store(pt.Concat(buff.load(), s.get())))
        ),
        output.set(buff.load()),
    )


@pt.ABIReturnSubroutine
def many_args(
    _a: pt.abi.Uint64,
    _b: pt.abi.Uint64,
    _c: pt.abi.Uint64,
    _d: pt.abi.Uint64,
    _e: pt.abi.Uint64,
    _f: pt.abi.Uint64,
    _g: pt.abi.Uint64,
    _h: pt.abi.Uint64,
    _i: pt.abi.Uint64,
    _j: pt.abi.Uint64,
    _k: pt.abi.Uint64,
    _l: pt.abi.Uint64,
    _m: pt.abi.Uint64,
    _n: pt.abi.Uint64,
    _o: pt.abi.Uint64,
    _p: pt.abi.Uint64,
    _q: pt.abi.Uint64,
    _r: pt.abi.Uint64,
    _s: pt.abi.Uint64,
    _t: pt.abi.Uint64,
    *,
    output: pt.abi.Uint64,
) -> pt.Expr:
    return output.set(_t.get())


@pt.ABIReturnSubroutine
def many_args_with_transaction(
    _txn: pt.abi.Transaction,
    _b: pt.abi.Uint64,
    _c: pt.abi.Uint64,
    _d: pt.abi.Uint64,
    _e: pt.abi.Uint64,
    _f: pt.abi.Uint64,
    _g: pt.abi.Uint64,
    _h: pt.abi.Uint64,
    _i: pt.abi.Uint64,
    _j: pt.abi.Uint64,
    _k: pt.abi.Uint64,
    _l: pt.abi.Uint64,
    _m: pt.abi.Uint64,
    _n: pt.abi.Uint64,
    _o: pt.abi.Uint64,
    _p: pt.abi.Uint64,
    _q: pt.abi.Uint64,
    _r: pt.abi.Uint64,
    _s: pt.abi.Uint64,
    _t: pt.abi.Uint64,
    *,
    output: pt.abi.Uint64,
) -> pt.Expr:
    return output.set(_t.get())


@pt.ABIReturnSubroutine
def add_and_store(
    a1: pt.abi.Uint64,
    a2: pt.abi.Uint64,
    a3: pt.abi.Uint64,
    a4: pt.abi.Uint64,
    a5: pt.abi.Uint64,
    a6: pt.abi.Uint64,
    a7: pt.abi.Uint64,
    a8: pt.abi.Uint64,
    a9: pt.abi.Uint64,
    a10: pt.abi.Uint64,
    a11: pt.abi.Uint64,
    a12: pt.abi.Uint64,
    a13: pt.abi.Uint64,
    a14: pt.abi.Uint64,
    a15: pt.abi.Uint64,
    a16: pt.abi.Uint64,
    t1: pt.abi.PaymentTransaction,
    *,
    output: pt.abi.Uint64,
) -> pt.Expr:
    return pt.Seq(
        output.set(a1.get() + a2.get()),
        # store the result in the sender's local state too
        pt.App.localPut(pt.Txn.sender(), pt.Bytes("result"), output.get()),
    )


@pt.Subroutine(pt.TealType.none)
def safe_clear_state_delete():
    return (
        pt.If(pt.Txn.sender() == pt.Global.creator_address())
        .Then(pt.Approve())
        .Else(pt.Reject())
    )


@pt.ABIReturnSubroutine
def dummy_doing_nothing():
    return pt.Seq(pt.Log(pt.Bytes("a message")))


@pt.Subroutine(pt.TealType.uint64)
def returning_u64():
    return pt.Int(1)


@pt.Subroutine(pt.TealType.none)
def mult_over_u64_and_log(a: pt.Expr, b: pt.Expr):
    return pt.Log(pt.Itob(a * b))


@pt.ABIReturnSubroutine
def eine_constant(*, output: pt.abi.Uint64):
    return output.set(1)


@pt.ABIReturnSubroutine
def take_abi_and_log(tb_logged: pt.abi.String):
    return pt.Log(tb_logged.get())


@pt.ABIReturnSubroutine
def not_registrable(lhs: pt.abi.Uint64, rhs: pt.Expr, *, output: pt.abi.Uint64):
    return output.set(lhs.get() * rhs)


@pt.ABIReturnSubroutine
def txn_amount(t: pt.abi.PaymentTransaction, *, output: pt.abi.Uint64):
    return output.set(t.get().amount())


@pt.ABIReturnSubroutine
def multiple_txn(
    appl: pt.abi.ApplicationCallTransaction,
    axfer: pt.abi.AssetTransferTransaction,
    pay: pt.abi.PaymentTransaction,
    any_txn: pt.abi.Transaction,
    *,
    output: pt.abi.Uint64,
):
    return output.set(
        appl.get().fee() + axfer.get().fee() + pay.get().fee() + any_txn.get().fee()
    )


GOOD_SUBROUTINE_CASES: list[pt.ABIReturnSubroutine | pt.SubroutineFnWrapper] = [
    add,
    sub,
    mul,
    div,
    mod,
    qrem,
    reverse,
    concat_strings,
    many_args,
    many_args_with_transaction,
    add_and_store,
    safe_clear_state_delete,
    dummy_doing_nothing,
    eine_constant,
    take_abi_and_log,
    txn_amount,
    multiple_txn,
]

ON_COMPLETE_CASES: list[pt.EnumInt] = [
    pt.OnComplete.NoOp,
    pt.OnComplete.OptIn,
    pt.OnComplete.ClearState,
    pt.OnComplete.CloseOut,
    pt.OnComplete.UpdateApplication,
    pt.OnComplete.DeleteApplication,
]


def power_set(no_dup_list: list, length_override: int = None):
    """
    This function serves as a generator for all possible elements in power_set
    over `non_dup_list`, which is a list of non-duplicated elements (matches property of a set).

    The cardinality of a powerset is 2^|non_dup_list|, so we can iterate from 0 to 2^|non_dup_list| - 1
    to index each element in such power_set.
    By binary representation of each index, we can see it as an allowance over each element in `no_dup_list`,
    and generate a unique subset of `non_dup_list`, which yields as an element of power_set of `no_dup_list`.

    Args:
        no_dup_list: a list of elements with no duplication
        length_override: a number indicating the largest size of super_set element,
            must be in range [1, len(no_dup_list)].
    """
    if length_override is None:
        length_override = len(no_dup_list)
    assert 1 <= length_override <= len(no_dup_list)
    masks = [1 << i for i in range(length_override)]
    for i in range(1 << len(no_dup_list)):
        yield [elem for mask, elem in zip(masks, no_dup_list) if i & mask]


class FullOrderCombinationGen:
    """
    This class serves as a generator for all possible vectors of maximal length `largest_perm_length` (non-negative),
    each of whose entries are one of the elements in `non_dup_list`, namely, a list of non-duplicated elements.
    """

    def __init__(self, non_dup_list: list, largest_perm_length: int) -> None:
        if largest_perm_length < 0:
            raise pt.TealInputError(
                "largest input permutation length must be non-negative"
            )
        elif len(set(non_dup_list)) != len(non_dup_list):
            raise pt.TealInputError(
                f"input non_dup_list {non_dup_list} has duplications"
            )
        elif not len(non_dup_list):
            raise pt.TealInputError("input non_dup_list must be non empty")

        self.__basis_symbol = non_dup_list
        self.__basis_size = len(self.__basis_symbol)
        self.__pre_gen_table: list[list[int]] = [
            [] for _ in range(self.__basis_size**largest_perm_length)
        ]

        # we can index all possible cases of vectors with an index in range
        # [0, |non_dup_list| ^ perm_length - 1]
        # by converting an index into |non_dup_list|-based number,
        # we can get the vector mapped by the index.

        # we iterate through [0, |non_dup_list|^largest_perm_length - 1] to precompute permutation table.
        lhs_scope = 0
        discrete_log = 0
        for expn in range(largest_perm_length + 1):
            for index in range(lhs_scope, self.__basis_size**expn):
                basis_repr = [0 for _ in range(discrete_log)]
                if discrete_log:
                    temp = index
                    for i in range(discrete_log):
                        basis_repr[i] = temp % self.__basis_size
                        temp //= self.__basis_size
                self.__pre_gen_table[index] = basis_repr

            lhs_scope = self.__basis_size**expn
            discrete_log = expn + 1

    def sample_gen(self, perm_length: int, sample_num: int = 10):
        if perm_length < 0:
            raise pt.TealInputError("input permutation length must be non-negative")
        elif perm_length == 0:
            yield []
            return

        # since we are sampling for a permutation with length `perm_length`,
        # this corresponds to sampling a value from [|non_dup_list|^(perm_length - 1), |non_dup_list|^perm_length - 1].
        # if sample number is greater than interval size, by pigeonhole principle there is re-testing
        # reduce back down to interval size
        sample_num = min(sample_num, self.__basis_size ** (perm_length - 1))

        for _ in range(sample_num):
            take = secrets.choice(
                range(
                    self.__basis_size ** (perm_length - 1),
                    self.__basis_size**perm_length,
                )
            )
            yield [self.__basis_symbol[j] for j in self.__pre_gen_table[take]]


def assemble_helper(what: pt.Expr) -> pt.TealBlock:
    assembled, _ = what.__teal__(options)
    assembled.addIncoming()
    assembled = pt.TealBlock.NormalizeBlocks(assembled)
    return assembled


def camel_to_snake(name: str) -> str:
    return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")


def test_call_config():
    for cc in pt.CallConfig:
        approval_cond_on_cc: pt.Expr | int = cc.approval_condition_under_config()
        match approval_cond_on_cc:
            case pt.Expr():
                expected_cc = (
                    (pt.Txn.application_id() == pt.Int(0))
                    if cc == pt.CallConfig.CREATE
                    else (pt.Txn.application_id() != pt.Int(0))
                )
                with pt.TealComponent.Context.ignoreExprEquality():
                    assert assemble_helper(approval_cond_on_cc) == assemble_helper(
                        expected_cc
                    )
            case int():
                assert approval_cond_on_cc == int(cc) & 1
            case _:
                raise pt.TealInternalError(
                    f"unexpected approval_cond_on_cc {approval_cond_on_cc}"
                )

        if cc in (pt.CallConfig.CREATE, pt.CallConfig.ALL):
            with pytest.raises(
                pt.TealInputError,
                match=r"Only CallConfig.CALL or CallConfig.NEVER are valid for a clear state CallConfig, since clear state can never be invoked during creation$",
            ):
                cc.clear_state_condition_under_config()
            continue

        clear_state_cond_on_cc: int = cc.clear_state_condition_under_config()
        match clear_state_cond_on_cc:
            case 0:
                assert cc == pt.CallConfig.NEVER
            case 1:
                assert cc == pt.CallConfig.CALL
            case _:
                raise pt.TealInternalError(
                    f"unexpected clear_state_cond_on_cc {clear_state_cond_on_cc}"
                )


def test_method_config_call_config_never():
    never_mc = pt.MethodConfig(no_op=pt.CallConfig.NEVER)
    assert never_mc.is_never()
    assert never_mc.approval_cond() == 0
    assert never_mc.clear_state_cond() == 0


def _gen_method_configs(sample_count: int = 10):
    on_complete_pow_set = power_set(ON_COMPLETE_CASES)
    focg = FullOrderCombinationGen(list(pt.CallConfig), len(ON_COMPLETE_CASES))

    for on_complete_set in on_complete_pow_set:
        oc_names = [camel_to_snake(oc.name) for oc in on_complete_set]
        for call_configs in focg.sample_gen(len(on_complete_set), sample_count):
            yield pt.MethodConfig(**dict(zip(oc_names, call_configs)))


@pytest.mark.parametrize("mc", _gen_method_configs())
def test_method_config(mc: pt.MethodConfig):
    approval_check_names_n_ocs = [
        (camel_to_snake(oc.name), oc)
        for oc in ON_COMPLETE_CASES
        if str(oc) != str(pt.OnComplete.ClearState)
    ]

    match mc.clear_state:
        case pt.CallConfig.NEVER:
            assert mc.clear_state_cond() == 0
        case pt.CallConfig.CALL:
            assert mc.clear_state_cond() == 1
        case pt.CallConfig.CREATE | pt.CallConfig.ALL:
            with pytest.raises(
                pt.TealInputError,
                match=r"Only CallConfig.CALL or CallConfig.NEVER are valid for a clear state CallConfig, since clear state can never be invoked during creation$",
            ):
                mc.clear_state_cond()
    if mc.is_never() or all(
        getattr(mc, i) == pt.CallConfig.NEVER for i, _ in approval_check_names_n_ocs
    ):
        assert mc.approval_cond() == 0
        return
    elif all(
        getattr(mc, i) == pt.CallConfig.ALL for i, _ in approval_check_names_n_ocs
    ):
        assert mc.approval_cond() == 1
        return
    list_of_cc = [
        (
            typing.cast(
                pt.CallConfig, getattr(mc, i)
            ).approval_condition_under_config(),
            oc,
        )
        for i, oc in approval_check_names_n_ocs
    ]
    list_of_expressions: list[pt.Expr] = []
    for expr_or_int, oc in list_of_cc:
        match expr_or_int:
            case pt.Expr():
                list_of_expressions.append(
                    pt.And(pt.Txn.on_completion() == oc, expr_or_int)
                )
            case 0:
                continue
            case 1:
                list_of_expressions.append(pt.Txn.on_completion() == oc)
    with pt.TealComponent.Context.ignoreExprEquality():
        ac = mc.approval_cond()
        assert isinstance(ac, pt.Expr)
        assert assemble_helper(ac) == assemble_helper(pt.Or(*list_of_expressions))


def test_on_complete_action():
    with pytest.raises(pt.TealInputError) as contradict_err:
        pt.OnCompleteAction(action=pt.Seq(), call_config=pt.CallConfig.NEVER)
    assert "contradicts" in str(contradict_err)
    assert pt.OnCompleteAction.never().is_empty()
    assert pt.OnCompleteAction.call_only(pt.Seq()).call_config == pt.CallConfig.CALL
    assert pt.OnCompleteAction.create_only(pt.Seq()).call_config == pt.CallConfig.CREATE
    assert pt.OnCompleteAction.always(pt.Seq()).call_config == pt.CallConfig.ALL


def test_wrap_handler_bare_call():
    BARE_CALL_CASES = [
        dummy_doing_nothing,
        safe_clear_state_delete,
        pt.Approve(),
        pt.Log(pt.Bytes("message")),
    ]
    for bare_call in BARE_CALL_CASES:
        wrapped: pt.Expr = ASTBuilder.wrap_handler(False, bare_call)
        expected: pt.Expr
        match bare_call:
            case pt.Expr():
                if bare_call.has_return():
                    expected = bare_call
                else:
                    expected = pt.Seq(bare_call, pt.Approve())
            case pt.SubroutineFnWrapper() | pt.ABIReturnSubroutine():
                expected = pt.Seq(bare_call(), pt.Approve())
            case _:
                raise pt.TealInputError("how you got here?")
        wrapped_assemble = assemble_helper(wrapped)
        wrapped_helper = assemble_helper(expected)
        with pt.TealComponent.Context.ignoreExprEquality():
            assert wrapped_assemble == wrapped_helper

    ERROR_CASES = [
        (
            pt.Int(1),
            f"bare appcall handler should be TealType.none not {pt.TealType.uint64}.",
        ),
        (
            returning_u64,
            f"subroutine call should be returning TealType.none not {pt.TealType.uint64}.",
        ),
        (
            mult_over_u64_and_log,
            "subroutine call should take 0 arg for bare-app call. this subroutine takes 2.",
        ),
        (
            eine_constant,
            f"abi-returning subroutine call should be returning void not {pt.abi.Uint64TypeSpec()}.",
        ),
        (
            take_abi_and_log,
            "abi-returning subroutine call should take 0 arg for bare-app call. this abi-returning subroutine takes 1.",
        ),
        (
            1,
            "bare appcall can only accept: none type Expr, or Subroutine/ABIReturnSubroutine with none return and no arg",
        ),
    ]
    for error_case, error_msg in ERROR_CASES:
        with pytest.raises(pt.TealInputError) as bug:
            ASTBuilder.wrap_handler(False, error_case)
        assert error_msg in str(bug)


def test_wrap_handler_method_call():
    with pytest.raises(pt.TealInputError) as bug:
        ASTBuilder.wrap_handler(True, not_registrable)
    assert "method call ABIReturnSubroutine is not routable" in str(bug)

    with pytest.raises(pt.TealInputError) as bug:
        ASTBuilder.wrap_handler(True, safe_clear_state_delete)
    assert "method call should be only registering ABIReturnSubroutine" in str(bug)

    ONLY_ABI_SUBROUTINE_CASES = list(
        filter(lambda x: isinstance(x, pt.ABIReturnSubroutine), GOOD_SUBROUTINE_CASES)
    )

    for abi_subroutine in ONLY_ABI_SUBROUTINE_CASES:
        wrapped: pt.Expr = ASTBuilder.wrap_handler(True, abi_subroutine)
        actual: pt.TealBlock = assemble_helper(wrapped)

        args: list[pt.abi.BaseType] = [
            spec.new_instance()
            for spec in typing.cast(
                list[pt.abi.TypeSpec], abi_subroutine.subroutine.expected_arg_types
            )
        ]

        app_args = [
            arg for arg in args if arg.type_spec() not in pt.abi.TransactionTypeSpecs
        ]

        app_arg_cnt = len(app_args)

        txn_args: list[pt.abi.Transaction] = [
            arg for arg in args if arg.type_spec() in pt.abi.TransactionTypeSpecs
        ]

        loading: list[pt.Expr] = []

        if app_arg_cnt > pt.METHOD_ARG_NUM_CUTOFF:
            sdk_last_arg = pt.abi.TupleTypeSpec(
                *[arg.type_spec() for arg in app_args[pt.METHOD_ARG_NUM_CUTOFF - 1 :]]
            ).new_instance()

            loading = [
                arg.decode(pt.Txn.application_args[index + 1])
                for index, arg in enumerate(app_args[: pt.METHOD_ARG_NUM_CUTOFF - 1])
            ]

            loading.append(
                sdk_last_arg.decode(pt.Txn.application_args[pt.METHOD_ARG_NUM_CUTOFF])
            )
        else:
            loading = [
                arg.decode(pt.Txn.application_args[index + 1])
                for index, arg in enumerate(app_args)
            ]

        if len(txn_args) > 0:
            for idx, txn_arg in enumerate(txn_args):
                loading.append(
                    txn_arg._set_index(
                        pt.Txn.group_index() - pt.Int(len(txn_args) - idx)
                    )
                )
                if str(txn_arg.type_spec()) != "txn":
                    loading.append(
                        pt.Assert(
                            txn_arg.get().type_enum()
                            == txn_arg.type_spec().txn_type_enum()
                        )
                    )

        if app_arg_cnt > pt.METHOD_ARG_NUM_CUTOFF:
            loading.extend(
                [
                    sdk_last_arg[idx].store_into(val)
                    for idx, val in enumerate(app_args[pt.METHOD_ARG_NUM_CUTOFF - 1 :])
                ]
            )

        evaluate: pt.Expr
        if abi_subroutine.type_of() != "void":
            output_temp = abi_subroutine.output_kwarg_info.abi_type.new_instance()
            evaluate = pt.Seq(
                abi_subroutine(*args).store_into(output_temp),
                pt.abi.MethodReturn(output_temp),
            )
        else:
            evaluate = abi_subroutine(*args)

        expected = assemble_helper(pt.Seq(*loading, evaluate, pt.Approve()))
        with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        assert pt.TealBlock.MatchScratchSlotReferences(
            pt.TealBlock.GetReferencedScratchSlots(actual),
            pt.TealBlock.GetReferencedScratchSlots(expected),
        )


def test_wrap_handler_method_txn_types():
    wrapped: pt.Expr = ASTBuilder.wrap_handler(True, multiple_txn)
    actual: pt.TealBlock = assemble_helper(wrapped)

    args: list[pt.abi.Transaction] = [
        pt.abi.ApplicationCallTransaction(),
        pt.abi.AssetTransferTransaction(),
        pt.abi.PaymentTransaction(),
        pt.abi.Transaction(),
    ]
    output_temp = pt.abi.Uint64()
    expected_ast = pt.Seq(
        args[0]._set_index(pt.Txn.group_index() - pt.Int(4)),
        pt.Assert(args[0].get().type_enum() == pt.TxnType.ApplicationCall),
        args[1]._set_index(pt.Txn.group_index() - pt.Int(3)),
        pt.Assert(args[1].get().type_enum() == pt.TxnType.AssetTransfer),
        args[2]._set_index(pt.Txn.group_index() - pt.Int(2)),
        pt.Assert(args[2].get().type_enum() == pt.TxnType.Payment),
        args[3]._set_index(pt.Txn.group_index() - pt.Int(1)),
        multiple_txn(*args).store_into(output_temp),
        pt.abi.MethodReturn(output_temp),
        pt.Approve(),
    )

    expected = assemble_helper(expected_ast)
    with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    assert pt.TealBlock.MatchScratchSlotReferences(
        pt.TealBlock.GetReferencedScratchSlots(actual),
        pt.TealBlock.GetReferencedScratchSlots(expected),
    )


def test_wrap_handler_method_call_many_args():
    wrapped: pt.Expr = ASTBuilder.wrap_handler(True, many_args)
    actual: pt.TealBlock = assemble_helper(wrapped)

    args = [pt.abi.Uint64() for _ in range(20)]
    last_arg = pt.abi.TupleTypeSpec(
        *[pt.abi.Uint64TypeSpec() for _ in range(6)]
    ).new_instance()

    output_temp = pt.abi.Uint64()
    expected_ast = pt.Seq(
        args[0].decode(pt.Txn.application_args[1]),
        args[1].decode(pt.Txn.application_args[2]),
        args[2].decode(pt.Txn.application_args[3]),
        args[3].decode(pt.Txn.application_args[4]),
        args[4].decode(pt.Txn.application_args[5]),
        args[5].decode(pt.Txn.application_args[6]),
        args[6].decode(pt.Txn.application_args[7]),
        args[7].decode(pt.Txn.application_args[8]),
        args[8].decode(pt.Txn.application_args[9]),
        args[9].decode(pt.Txn.application_args[10]),
        args[10].decode(pt.Txn.application_args[11]),
        args[11].decode(pt.Txn.application_args[12]),
        args[12].decode(pt.Txn.application_args[13]),
        args[13].decode(pt.Txn.application_args[14]),
        last_arg.decode(pt.Txn.application_args[15]),
        last_arg[0].store_into(args[14]),
        last_arg[1].store_into(args[15]),
        last_arg[2].store_into(args[16]),
        last_arg[3].store_into(args[17]),
        last_arg[4].store_into(args[18]),
        last_arg[5].store_into(args[19]),
        many_args(*args).store_into(output_temp),
        pt.abi.MethodReturn(output_temp),
        pt.Approve(),
    )
    expected = assemble_helper(expected_ast)
    with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    assert pt.TealBlock.MatchScratchSlotReferences(
        pt.TealBlock.GetReferencedScratchSlots(actual),
        pt.TealBlock.GetReferencedScratchSlots(expected),
    )


def test_contract_json_obj():
    abi_subroutines = list(
        filter(lambda x: isinstance(x, pt.ABIReturnSubroutine), GOOD_SUBROUTINE_CASES)
    )
    contract_name = "contract_name"
    on_complete_actions = pt.BareCallActions(
        clear_state=pt.OnCompleteAction.call_only(safe_clear_state_delete)
    )
    router = pt.Router(contract_name, on_complete_actions)
    method_list: list[sdk_abi.Method] = []
    for subroutine in abi_subroutines:

        doc = subroutine.subroutine.implementation.__doc__
        desc = None
        if doc is not None and doc.strip() == "replace me":
            desc = "dope description"

        router.add_method_handler(subroutine, description=desc)

        ms = subroutine.method_spec()

        # Manually replace it since the override is applied in the method handler
        # not attached to the ABIReturnSubroutine itself
        ms.desc = desc if desc is not None else ms.desc

        sig_method = sdk_abi.Method.from_signature(subroutine.method_signature())

        assert ms.name == sig_method.name

        for idx, arg in enumerate(ms.args):
            assert arg.type == sig_method.args[idx].type

        method_list.append(ms)

    sdk_contract = sdk_abi.Contract(contract_name, method_list)
    contract = router.contract_construct()
    assert contract == sdk_contract


def test_build_program_all_empty():
    router = pt.Router("test")

    approval, clear_state, contract = router.build_program()

    expected_empty_program = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.return_),
        ]
    )

    with pt.TealComponent.Context.ignoreExprEquality():
        assert assemble_helper(approval) == expected_empty_program
        assert assemble_helper(clear_state) == expected_empty_program

    expected_contract = sdk_abi.Contract("test", [])
    assert contract == expected_contract


def test_build_program_approval_empty():
    router = pt.Router(
        "test",
        pt.BareCallActions(clear_state=pt.OnCompleteAction.call_only(pt.Approve())),
    )

    approval, clear_state, contract = router.build_program()

    expected_empty_program = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.return_),
        ]
    )

    with pt.TealComponent.Context.ignoreExprEquality():
        assert assemble_helper(approval) == expected_empty_program
        assert assemble_helper(clear_state) != expected_empty_program

    expected_contract = sdk_abi.Contract("test", [])
    assert contract == expected_contract


def test_build_program_clear_state_empty():
    router = pt.Router(
        "test", pt.BareCallActions(no_op=pt.OnCompleteAction.always(pt.Approve()))
    )

    approval, clear_state, contract = router.build_program()

    expected_empty_program = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.return_),
        ]
    )

    with pt.TealComponent.Context.ignoreExprEquality():
        assert assemble_helper(approval) != expected_empty_program
        assert assemble_helper(clear_state) == expected_empty_program

    expected_contract = sdk_abi.Contract("test", [])
    assert contract == expected_contract


def test_build_program_clear_state_invalid_config():
    for config in (pt.CallConfig.CREATE, pt.CallConfig.ALL):
        bareCalls = pt.BareCallActions(
            clear_state=pt.OnCompleteAction(action=pt.Approve(), call_config=config)
        )
        with pytest.raises(
            pt.TealInputError,
            match=r"Only CallConfig.CALL or CallConfig.NEVER are valid for a clear state CallConfig, since clear state can never be invoked during creation$",
        ):
            pt.Router("test", bareCalls)

        router = pt.Router("test")

        @pt.ABIReturnSubroutine
        def clear_state_method():
            return pt.Approve()

        with pytest.raises(
            pt.TealInputError,
            match=r"Only CallConfig.CALL or CallConfig.NEVER are valid for a clear state CallConfig, since clear state can never be invoked during creation$",
        ):
            router.add_method_handler(
                clear_state_method,
                method_config=pt.MethodConfig(clear_state=config),
            )


def test_build_program_clear_state_valid_config():
    action = pt.If(pt.Txn.fee() == pt.Int(4)).Then(pt.Approve()).Else(pt.Reject())
    config = pt.CallConfig.CALL

    router_with_bare_call = pt.Router(
        "test",
        pt.BareCallActions(
            clear_state=pt.OnCompleteAction(action=action, call_config=config)
        ),
    )
    _, actual_clear_state_with_bare_call, _ = router_with_bare_call.build_program()

    expected_clear_state_with_bare_call = assemble_helper(
        pt.Cond([pt.Txn.application_args.length() == pt.Int(0), action])
    )

    with pt.TealComponent.Context.ignoreExprEquality():
        assert (
            assemble_helper(actual_clear_state_with_bare_call)
            == expected_clear_state_with_bare_call
        )

    router_with_method = pt.Router("test")

    @pt.ABIReturnSubroutine
    def clear_state_method():
        return action

    router_with_method.add_method_handler(
        clear_state_method, method_config=pt.MethodConfig(clear_state=config)
    )

    _, actual_clear_state_with_method, _ = router_with_method.build_program()

    expected_clear_state_with_method = assemble_helper(
        pt.Cond(
            [
                pt.Txn.application_args[0]
                == pt.MethodSignature("clear_state_method()void"),
                pt.Seq(clear_state_method(), pt.Approve()),
            ]
        )
    )

    with pt.TealComponent.Context.ignoreExprEquality():
        assert (
            assemble_helper(actual_clear_state_with_method)
            == expected_clear_state_with_method
        )


def test_override_names():
    r1 = pt.Router("test")

    @r1.method(name="handle")
    def handle_asa(deposit: pt.abi.AssetTransferTransaction):
        """handles the deposit where the input is an asset transfer"""
        return pt.Assert(deposit.get().asset_amount() > pt.Int(0))

    @r1.method(name="handle")
    def handle_algo(deposit: pt.abi.PaymentTransaction):
        """handles the deposit where the input is a payment"""
        return pt.Assert(deposit.get().amount() > pt.Int(0))

    ap1, cs1, c1 = r1.compile_program(version=pt.compiler.MAX_PROGRAM_VERSION)
    assert len(c1.methods) == 2
    for meth in c1.methods:
        dmeth = meth.dictify()
        assert dmeth["name"] == "handle"

    # Confirm an equivalent router definition _without_ `name` overrides produces the same output.
    r2 = pt.Router("test")

    @r2.method()
    def handle(deposit: pt.abi.AssetTransferTransaction):
        """handles the deposit where the input is an asset transfer"""
        return pt.Assert(deposit.get().asset_amount() > pt.Int(0))

    @r2.method()
    def handle(deposit: pt.abi.PaymentTransaction):  # noqa: F811
        """handles the deposit where the input is a payment"""
        return pt.Assert(deposit.get().amount() > pt.Int(0))

    ap2, cs2, c2 = r2.compile_program(version=pt.compiler.MAX_PROGRAM_VERSION)

    assert (ap1, cs1, c1) == (ap2, cs2, c2)
