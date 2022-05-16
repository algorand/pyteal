# import pytest
import pyteal as pt

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


def test_parse_conditions():
    approval_conds, clear_state_conds = pt.Router.parse_conditions(
        concat_strings.method_signature(),
        concat_strings,
        [
            pt.OnComplete.ClearState,
            pt.OnComplete.CloseOut,
            pt.OnComplete.NoOp,
            pt.OnComplete.OptIn,
        ],
        creation=False,
    )
    print()
    print([str(x) for x in approval_conds])
    print([str(x) for x in clear_state_conds])
    pass


def test():
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
