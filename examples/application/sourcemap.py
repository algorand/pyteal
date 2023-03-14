"""
This example shows how to use the source map feature to for a PyTeal program.

For this example, no `pyteal.ini` file is assumed and to enable the feature
one must import `FeatureGate` from `feature_gates` and set `FeatureGate.sourcemap_enabled` to `True`.
This import must occur before any object from PyTeal is imported, as PyTeal will
default to its own sourcemap configuration if not set before hand.
"""

from feature_gates import FeatureGates


def program():
    # we defer importing pyteal until after we set sourcemap feature
    import pyteal as pt

    @pt.Subroutine(pt.TealType.uint64)
    def is_even(i):
        return (
            pt.If(i == pt.Int(0))
            .Then(pt.Int(1))
            .ElseIf(i == pt.Int(1))
            .Then(pt.Int(0))
            .Else(is_even(i - pt.Int(2)))
        )

    n = pt.Btoi(arg0 := pt.Txn.application_args[0])

    return pt.Seq(
        pt.Log(pt.Bytes("n:")),
        pt.Log(arg0),
        pt.Log(pt.Bytes("is_even(n):")),
        pt.Log(pt.Itob(is_even(n))),
        pt.Int(1),
    )


if __name__ == "__main__":
    # This assumes running as follows:
    # cd examples/application
    # python sourcemap.py

    # print out debugging details about FeatureGates:
    FeatureGates.verbose = True

    FeatureGates.set_sourcemap_enabled(True)

    from pyteal import Compilation, Mode

    approval_program = program()

    results = Compilation(approval_program, mode=Mode.Application, version=8).compile(
        with_sourcemap=True, annotate_teal=True, annotate_teal_headers=True
    )

    teal = "teal/sourcemap.teal"
    annotated = "teal/sourcemap_annotated.teal"

    with open(teal, "w") as f:
        f.write(results.teal)

    with open(annotated, "w") as f:
        f.write(results.sourcemap.annotated_teal)

    print(f"SUCCESS!!! Please check out {teal} and {annotated}")
