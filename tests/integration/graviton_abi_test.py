import random

from graviton.blackbox import DryRunInspector

import pyteal as pt
from pyteal.ast.subroutine import ABIReturnSubroutine

from tests.blackbox import (
    Blackbox,
    PyTealDryRunExecutor,
)


# ---- Integers and Complex Integral Numbers (aka Gaussian Integers) ---- #


"""
WARNING: The following ABI types Int65 and Complex130 are ONLY for the purpose of testing/demo'ing 
ABISubroutine and graviton ABI capabilities and are NOT the recommended approach for 
implementing integers and complex integers.
A better approach would likely leverage `Uint64` (if any ABI type at all) and make use of 2's complement arithmetic.

Cf. https://github.com/algorand/pyteal/issues/184
"""

Int65 = pt.abi.Tuple2[pt.abi.Bool, pt.abi.Uint64]
Complex130 = pt.abi.Tuple2[Int65, Int65]


@Blackbox(input_types=[None, None])
@pt.ABIReturnSubroutine
def int65_minus_cond(x: Int65, y: Int65, *, output: Int65):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    x0 = pt.abi.Bool()
    x1 = pt.abi.Uint64()
    y0 = pt.abi.Bool()
    y1 = pt.abi.Uint64()
    z0 = pt.abi.Bool()
    z1 = pt.abi.Uint64()
    return pt.Seq(
        x0.set(x[0]),
        x1.set(x[1]),
        y0.set(y[0]),
        y1.set(y[1]),
        pt.Cond(
            # Case I. x, y positive
            [
                pt.And(x0.get(), y0.get()),
                pt.Seq(
                    z0.set(x1.get() >= y1.get()),
                    z1.set(
                        pt.If(x1.get() <= y1.get())
                        .Then(y1.get() - x1.get())
                        .Else(x1.get() - y1.get())
                    ),
                ),
            ],
            # Case II. x positive, y negative
            [
                pt.And(x0.get(), pt.Not(y0.get())),
                pt.Seq(z0.set(True), z1.set(x1.get() + y1.get())),
            ],
            # Case III. x negative, y positive
            [
                pt.And(pt.Not(x0.get()), y0.get()),
                pt.Seq(z0.set(False), z1.set(x1.get() + y1.get())),
            ],
            # Case IV. x, y negative
            [
                pt.Int(1),
                pt.Seq(
                    z0.set(x1.get() <= y1.get()),
                    z1.set(
                        pt.If(x1.get() <= y1.get())
                        .Then(y1.get() - x1.get())
                        .Else(x1.get() - y1.get())
                    ),
                ),
            ],
        ),
        output.set(z0, z1),
    )


@Blackbox(input_types=[None, None])
@pt.ABIReturnSubroutine
def int65_sub(x: Int65, y: Int65, *, output: Int65):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    x0 = pt.abi.Bool()
    x1 = pt.abi.Uint64()
    y0 = pt.abi.Bool()
    y1 = pt.abi.Uint64()
    z0 = pt.abi.Bool()
    z1 = pt.abi.Uint64()
    return pt.Seq(
        x0.set(x[0]),
        x1.set(x[1]),
        y0.set(y[0]),
        y1.set(y[1]),
        pt.If(x0.get() == y0.get())
        .Then(  # Case I. x, y same signature
            pt.Seq(
                z0.set(pt.Not(x0.get()) ^ (x1.get() >= y1.get())),
                z1.set(
                    pt.If(x1.get() <= y1.get())
                    .Then(y1.get() - x1.get())
                    .Else(x1.get() - y1.get())
                ),
            )
        )
        .Else(  # Case II. x, y opposite signatures
            pt.Seq(
                z0.set(x0.get()),
                z1.set(x1.get() + y1.get()),
            ),
        ),
        output.set(z0, z1),
    )


@Blackbox(input_types=[None, None])
@pt.ABIReturnSubroutine
def int65_mult(x: Int65, y: Int65, *, output: Int65):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    # TODO: can we get something like the following one-liner working?
    # return output.set(pt.Not(x[0].get() ^ y[0].get()), x[1].get() * y[1].get())
    def get(x):
        return x.use(lambda ni: ni.get())

    return pt.Seq(
        (z0 := pt.abi.Bool()).set(pt.Not(get(x[0]) ^ get(y[0]))),
        (z1 := pt.abi.Uint64()).set(get(x[1]) * get(y[1])),
        output.set(z0, z1),
    )


@Blackbox(input_types=[None])
@ABIReturnSubroutine
def int65_negate(x: Int65, *, output: Int65):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    # TODO: can I haz a one-liner pls????
    x0 = pt.abi.Bool()
    x1 = pt.abi.Uint64()
    z0 = pt.abi.Bool()
    z1 = pt.abi.Uint64()
    return pt.Seq(
        x0.set(x[0]),
        x1.set(x[1]),
        z0.set(pt.Not(x0.get())),
        z1.set(x1.get()),
        output.set(z0, z1),
    )


@Blackbox(input_types=[None, None])
@ABIReturnSubroutine
def int65_add(x: Int65, y: Int65, *, output: Int65):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    return pt.Seq(y.set(int65_negate(y)), output.set(int65_sub(x, y)))


@Blackbox(input_types=[None, None])
@ABIReturnSubroutine
def complex130_add(x: Complex130, y: Complex130, *, output: Complex130):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    x0 = pt.abi.make(Int65)
    x1 = pt.abi.make(Int65)
    y0 = pt.abi.make(Int65)
    y1 = pt.abi.make(Int65)
    z0 = pt.abi.make(Int65)
    z1 = pt.abi.make(Int65)
    return pt.Seq(
        x0.set(x[0]),
        x1.set(x[1]),
        y0.set(y[0]),
        y1.set(y[1]),
        z0.set(int65_add(x0, y0)),
        z1.set(int65_add(x1, y1)),
        output.set(z0, z1),
    )


@Blackbox(input_types=[None, None])
@ABIReturnSubroutine
def complex130_mult(x: Complex130, y: Complex130, *, output: Complex130):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    x0 = pt.abi.make(Int65)
    x1 = pt.abi.make(Int65)
    y0 = pt.abi.make(Int65)
    y1 = pt.abi.make(Int65)
    t1 = pt.abi.make(Int65)
    t2 = pt.abi.make(Int65)
    t3 = pt.abi.make(Int65)
    t4 = pt.abi.make(Int65)
    z0 = pt.abi.make(Int65)
    z1 = pt.abi.make(Int65)
    return pt.Seq(
        x0.set(x[0]),
        x1.set(x[1]),
        y0.set(y[0]),
        y1.set(y[1]),
        # TODO: why can't I chain ABI calls?
        # z0.set(int65_sub(int65_mult(x0, y0), int65_mult(x1, y1))),
        # z1.set(int65_add(int65_mult(x0, y1), int65_mult(x1, y0))),
        t1.set(int65_mult(x0, y0)),
        t2.set(int65_mult(x1, y1)),
        t3.set(int65_mult(x0, y1)),
        t4.set(int65_mult(x1, y0)),
        z0.set(int65_sub(t1, t2)),
        z1.set(int65_add(t3, t4)),
        output.set(z0, z1),
    )


@Blackbox(input_types=[None])
@ABIReturnSubroutine
def complex130_real(x: Complex130, *, output: Int65):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    return output.set(x[0])


@Blackbox(input_types=[None])
@ABIReturnSubroutine
def complex130_imag(x: Complex130, *, output: Int65):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    return output.set(x[1])


@Blackbox(input_types=[None])
@ABIReturnSubroutine
def complex130_conjugate(x: Complex130, *, output: Complex130):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    z0 = pt.abi.make(Int65)
    z1 = pt.abi.make(Int65)
    return pt.Seq(
        z0.set(complex130_real(x)),
        z1.set(complex130_imag(x)),
        z1.set(int65_negate(z1)),
        output.set(z0, z1),
    )


@Blackbox(input_types=[None])
@ABIReturnSubroutine
def complex130_norm_squared(x: Complex130, *, output: Int65):
    """
    WARNING: not an ideal implementation. See explanation in first WARNING above.
    """
    t = pt.abi.make(Complex130)
    return pt.Seq(
        t.set(complex130_conjugate(x)),
        t.set(complex130_mult(t, x)),
        output.set(complex130_real(t)),
    )


# ---- additional stand-alone ABIReturnSubroutine's ---- #


@Blackbox(input_types=[None])
@ABIReturnSubroutine
def conditional_factorial(_factor: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    i = pt.ScratchVar(pt.TealType.uint64)

    return pt.Seq(
        output.set(1),
        pt.If(_factor.get() <= pt.Int(1))
        .Then(pt.Return())
        .Else(
            pt.For(
                i.store(_factor.get()),
                i.load() > pt.Int(1),
                i.store(i.load() - pt.Int(1)),
            ).Do(output.set(output.get() * i.load())),
        ),
    )


# ---- integration test functions ---- #


def test_integer65():
    bbpt_subtract_slick = PyTealDryRunExecutor(int65_sub, pt.Mode.Application)

    bbpt_subtract_cond = PyTealDryRunExecutor(int65_minus_cond, pt.Mode.Application)

    bbpt_mult = PyTealDryRunExecutor(int65_mult, pt.Mode.Application)

    bbpt_negate = PyTealDryRunExecutor(int65_negate, pt.Mode.Application)

    bbpt_add = PyTealDryRunExecutor(int65_add, pt.Mode.Application)

    def pynum_to_tuple(n):
        return (n >= 0, abs(n))

    def pytuple_to_num(t):
        s, x = t
        return x if s else -x

    N = 100
    random.seed(42)

    choices = range(-9_999, 10_000)
    unary_inputs = [(pynum_to_tuple(x),) for x in random.sample(choices, N)]

    binary_inputs = [
        (pynum_to_tuple(x), pynum_to_tuple(y))
        for x, y in zip(random.sample(choices, N), random.sample(choices, N))
    ]

    def binary_dryrun(p: PyTealDryRunExecutor) -> list[DryRunInspector]:
        return p.dryrun_on_sequence(binary_inputs)

    # Binary:
    inspectors_subtract_slick = binary_dryrun(bbpt_subtract_slick)

    inspectors_subtract_cond = binary_dryrun(bbpt_subtract_cond)

    inspectors_mult = binary_dryrun(bbpt_mult)

    inspectors_add = binary_dryrun(bbpt_add)

    # Unary:
    inspectors_negate = bbpt_negate.dryrun_on_sequence(unary_inputs)

    for i in range(N):
        binary_args = binary_inputs[i]
        x, y = tuple(map(pytuple_to_num, binary_args))

        unary_args = unary_inputs[i]
        u = pytuple_to_num(unary_args[0])

        inspector_subtract_slick = inspectors_subtract_slick[i]
        inspector_subtract_cond = inspectors_subtract_cond[i]
        inspector_mult = inspectors_mult[i]
        inspector_add = inspectors_add[i]

        inspector_negate = inspectors_negate[i]

        assert x - y == pytuple_to_num(
            inspector_subtract_slick.last_log()
        ), inspector_subtract_slick.report(
            binary_args, f"failed for {binary_args}", row=i
        )

        assert x - y == pytuple_to_num(
            inspector_subtract_cond.last_log()
        ), inspector_subtract_cond.report(
            binary_args, f"failed for {binary_args}", row=i
        )

        assert x * y == pytuple_to_num(
            inspector_mult.last_log()
        ), inspector_mult.report(binary_args, f"failed for {binary_args}", row=i)

        assert x + y == pytuple_to_num(inspector_add.last_log()), inspector_add.report(
            binary_args, f"failed for {binary_args}", row=i
        )

        assert -u == pytuple_to_num(
            inspector_negate.last_log()
        ), inspector_negate.report(unary_args, f"failed for {unary_args}", row=i)


def test_complex130():
    # Binary:

    bbpt_cplx_add = PyTealDryRunExecutor(complex130_add, pt.Mode.Application)

    bbpt_cplx_mult = PyTealDryRunExecutor(complex130_mult, pt.Mode.Application)

    # Unary:

    bbpt_complex_real = PyTealDryRunExecutor(complex130_real, pt.Mode.Application)

    bbpt_complex_imag = PyTealDryRunExecutor(complex130_imag, pt.Mode.Application)

    bbpt_complex_conjugate = PyTealDryRunExecutor(
        complex130_conjugate, pt.Mode.Application
    )

    bbpt_complex_norm_squared = PyTealDryRunExecutor(
        complex130_norm_squared, pt.Mode.Application
    )

    def pyint_to_tuple(n):
        return (n >= 0, abs(n))

    def pycomplex_to_tuple(z):
        return (pyint_to_tuple(int(z.real)), pyint_to_tuple(int(z.imag)))

    def pytuple_to_int(t):
        s, x = t
        return x if s else -x

    def pytuple_to_complex(tt):
        tx, ty = tt
        return complex(pytuple_to_int(tx), pytuple_to_int(ty))

    N = 100
    # just for fun - no random seed - but this shouldn't be flakey

    choices = range(-999_999, 1_000_000)

    unary_inputs = [
        (pycomplex_to_tuple(complex(x, y)),)
        for x, y in zip(random.sample(choices, N), random.sample(choices, N))
    ]

    binary_inputs = [
        (pycomplex_to_tuple(complex(x, y)), pycomplex_to_tuple(complex(z, w)))
        for x, y, z, w in zip(
            random.sample(choices, N),
            random.sample(choices, N),
            random.sample(choices, N),
            random.sample(choices, N),
        )
    ]

    # Binary:
    def binary_dryrun(p: PyTealDryRunExecutor) -> list[DryRunInspector]:
        return p.dryrun_on_sequence(binary_inputs)

    inspectors_cplx_add = binary_dryrun(bbpt_cplx_add)

    inspectors_cplx_mult = binary_dryrun(bbpt_cplx_mult)

    # Unary:
    def unary_dryrun(p: PyTealDryRunExecutor) -> list[DryRunInspector]:
        return p.dryrun_on_sequence(unary_inputs)

    inspectors_cplx_real = unary_dryrun(bbpt_complex_real)

    inspectors_cplx_imag = unary_dryrun(bbpt_complex_imag)

    inspectors_cplx_conjugate = unary_dryrun(bbpt_complex_conjugate)

    inspectors_cplx_norm_squared = unary_dryrun(bbpt_complex_norm_squared)

    for i in range(N):
        binary_args = binary_inputs[i]
        x, y = tuple(map(pytuple_to_complex, binary_args))

        unary_args = unary_inputs[i]
        u = pytuple_to_complex(unary_args[0])

        # Binary:

        inspector_cplx_add = inspectors_cplx_add[i]

        inspector_cplx_mult = inspectors_cplx_mult[i]

        # Unary:

        inspector_cplx_real = inspectors_cplx_real[i]

        inspector_cplx_imag = inspectors_cplx_imag[i]

        inspector_cplx_conjugate = inspectors_cplx_conjugate[i]

        inspector_cplx_norm_squared = inspectors_cplx_norm_squared[i]

        assert x + y == pytuple_to_complex(
            inspector_cplx_add.last_log()
        ), inspector_cplx_add.report(binary_args, f"failed for {binary_args}", row=i)

        assert x * y == pytuple_to_complex(
            inspector_cplx_mult.last_log()
        ), inspector_cplx_mult.report(binary_args, f"failed for {binary_args}", row=i)

        assert u.real == pytuple_to_int(
            inspector_cplx_real.last_log()
        ), inspector_cplx_real.report(unary_args, f"failed for {unary_args}", row=i)

        assert u.imag == pytuple_to_int(
            inspector_cplx_imag.last_log()
        ), inspector_cplx_imag.report(unary_args, f"failed for {unary_args}", row=i)

        assert u.conjugate() == pytuple_to_complex(
            inspector_cplx_conjugate.last_log()
        ), inspector_cplx_conjugate.report(
            unary_args, f"failed for {unary_args}", row=i
        )

        assert u * u.conjugate() == pytuple_to_int(
            inspector_cplx_norm_squared.last_log()
        ), inspector_cplx_norm_squared.report(
            unary_args, f"failed for {unary_args}", row=i
        )


def py_factorial(n):
    return 1 if n <= 1 else n * py_factorial(n - 1)


def test_conditional_factorial():
    ptdre = PyTealDryRunExecutor(conditional_factorial, pt.Mode.Application)
    inputs = [(n,) for n in range(20)]
    inspectors = ptdre.dryrun_on_sequence(inputs)
    for i, args in enumerate(inputs):
        inspector = inspectors[i]
        n = args[0]
        assert inspector.passed(), inspector.report(args, row=i + 1)

        expected = py_factorial(n)
        assert expected == inspector.last_log(), inspector.report(args, row=i + 1)

    n = 21
    args = (n,)
    inspector = ptdre.dryrun(args)
    assert inspector.rejected(), inspector.report(
        args, f"FAILED: should have rejected for {n=}", row=n + 1
    )
    assert inspector.error(), inspector.report(
        args, f"FAILED: should error for {n=}", row=n + 1
    )
