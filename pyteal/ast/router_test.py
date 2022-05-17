import pyteal as pt
import itertools
import pytest
import random
import typing
import algosdk.abi as sdk_abi

options = pt.CompileOptions(version=5)


@pt.ABIReturnSubroutine
def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a.get() + b.get())


@pt.ABIReturnSubroutine
def sub(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
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
    safe_clear_state_delete,
    dummy_doing_nothing,
]

ON_COMPLETE_CASES: list[pt.EnumInt] = [
    pt.OnComplete.NoOp,
    pt.OnComplete.OptIn,
    pt.OnComplete.ClearState,
    pt.OnComplete.CloseOut,
    pt.OnComplete.UpdateApplication,
    pt.OnComplete.DeleteApplication,
]


def non_empty_power_set(no_dup_list: list):
    masks = [1 << i for i in range(len(no_dup_list))]
    for i in range(1, 1 << len(no_dup_list)):
        yield [elem for mask, elem in zip(masks, no_dup_list) if i & mask]


def is_sth_in_oc_list(sth: pt.EnumInt, oc_list: list[pt.EnumInt]):
    return any(map(lambda x: str(x) == str(sth), oc_list))


def test_parse_conditions():
    ON_COMPLETE_COMBINED_CASES = non_empty_power_set(ON_COMPLETE_CASES)

    for subroutine, on_completes, is_creation in itertools.product(
        GOOD_SUBROUTINE_CASES, ON_COMPLETE_COMBINED_CASES, [False, True]
    ):
        if not isinstance(subroutine, pt.ABIReturnSubroutine):
            subroutine = None

        method_sig = subroutine.method_signature() if subroutine else None

        if is_creation and (
            is_sth_in_oc_list(pt.OnComplete.CloseOut, on_completes)
            or is_sth_in_oc_list(pt.OnComplete.ClearState, on_completes)
        ):
            with pytest.raises(pt.TealInputError) as err_conflict_conditions:
                pt.Router.parse_conditions(
                    method_sig, subroutine, on_completes, is_creation
                )
            assert (
                "OnComplete ClearState/CloseOut may be ill-formed with app creation"
                in str(err_conflict_conditions)
            )
            continue

        mutated_on_completes = on_completes + [random.choice(on_completes)]
        with pytest.raises(pt.TealInputError) as err_dup_oc:
            pt.Router.parse_conditions(
                method_sig, subroutine, mutated_on_completes, is_creation
            )
        assert "has duplicated on_complete(s)" in str(err_dup_oc)

        if subroutine is not None:
            with pytest.raises(pt.TealInputError) as err_wrong_override:
                pt.Router.parse_conditions(None, subroutine, on_completes, is_creation)
            assert (
                "A method_signature must be provided if method_to_register is not None"
                in str(err_wrong_override)
            )

        (
            approval_condition_list,
            clear_state_condition_list,
        ) = pt.Router.parse_conditions(
            method_sig, subroutine, on_completes, is_creation
        )

        if not is_sth_in_oc_list(pt.OnComplete.ClearState, on_completes):
            assert len(clear_state_condition_list) == 0

        def assemble_helper(what: pt.Expr) -> pt.TealBlock:
            assembled, _ = what.__teal__(options)
            assembled.addIncoming()
            assembled = pt.TealBlock.NormalizeBlocks(assembled)
            return assembled

        assembled_ap_condition_list: list[pt.TealBlock] = [
            assemble_helper(expr) for expr in approval_condition_list
        ]
        assembled_csp_condition_list: list[pt.TealBlock] = [
            assemble_helper(expr) for expr in clear_state_condition_list
        ]
        if is_creation:
            creation_condition: pt.Expr = pt.Txn.application_id() == pt.Int(0)
            assembled_condition = assemble_helper(creation_condition)
            with pt.TealComponent.Context.ignoreExprEquality():
                assert assembled_condition in assembled_ap_condition_list

        subroutine_arg_cond: pt.Expr
        if subroutine:
            max_subroutine_arg_allowed = 1 + min(
                pt.METHOD_ARG_NUM_LIMIT, subroutine.subroutine.argument_count()
            )
            subroutine_arg_cond = pt.And(
                pt.Txn.application_args[0]
                == pt.MethodSignature(typing.cast(str, method_sig)),
                pt.Txn.application_args.length() == pt.Int(max_subroutine_arg_allowed),
            )
        else:
            subroutine_arg_cond = pt.Txn.application_args.length() == pt.Int(0)

        assembled_condition = assemble_helper(subroutine_arg_cond)
        with pt.TealComponent.Context.ignoreExprEquality():
            assert assembled_condition in assembled_ap_condition_list

        if is_sth_in_oc_list(pt.OnComplete.ClearState, on_completes):
            with pt.TealComponent.Context.ignoreExprEquality():
                assert assembled_condition in assembled_csp_condition_list

        if len(on_completes) == 1 and is_sth_in_oc_list(
            pt.OnComplete.ClearState, on_completes
        ):
            continue

        on_completes_cond: pt.Expr = pt.Or(
            *[
                pt.Txn.on_completion() == oc
                for oc in on_completes
                if str(oc) != str(pt.OnComplete.ClearState)
            ]
        )
        on_completes_cond_assembled = assemble_helper(on_completes_cond)
        with pt.TealComponent.Context.ignoreExprEquality():
            assert on_completes_cond_assembled in assembled_ap_condition_list


# TODO test wrap_handler
def test_wrap_handler_not_bare_call():
    router = pt.Router()
    router.add_method_handler(many_args)
    router.add_bare_call(
        pt.Approve(), [pt.OnComplete.ClearState, pt.OnComplete.DeleteApplication]
    )
    ap, _, _ = router.build_program()
    print(
        pt.compileTeal(
            ap,
            version=6,
            mode=pt.Mode.Application,
            # optimize=pt.OptimizeOptions(scratch_slots=True),
        )
    )


def test_wrap_handler_method_call():
    pass


def test_contract_json_obj():
    ONLY_ABI_SUBROUTINE_CASES = list(
        filter(lambda x: isinstance(x, pt.ABIReturnSubroutine), GOOD_SUBROUTINE_CASES)
    )
    ONLY_ABI_SUBROUTINE_CASES = random.choices(ONLY_ABI_SUBROUTINE_CASES, k=6)
    for index, case in enumerate(non_empty_power_set(ONLY_ABI_SUBROUTINE_CASES)):
        contract_name = f"contract_{index}"
        router = pt.Router(contract_name)
        method_list: list[sdk_abi.contract.Method] = []
        for subroutine in case:
            router.add_method_handler(subroutine)
            method_list.append(
                sdk_abi.Method.from_signature(subroutine.method_signature())
            )
        router.add_bare_call(safe_clear_state_delete, pt.OnComplete.ClearState)
        sdk_contract = sdk_abi.contract.Contract(contract_name, method_list)
        contract = router.contract_construct()
        assert sdk_contract.dictify() == contract
