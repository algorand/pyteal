====================
Source Mapping HowTo
====================

Below, we illustrate how to enable source mapping and print out an *annotated* teal version of the program which includes the original PyTeal in the comments.

Executive Summary
-----------------

0. Author your PyTeal script as usual and make other preparations.
1. Enable the source mapper by turning on its feature gate.
2. Use a source-mappable compile instruction.
3. Grab the annotated teal out of the compile's result.
4. Run the script as before.

0. Preparation
--------------

Go ahead and author your PyTeal dapp as you normally would. No modifications to PyTeal expressions are necessary to make your program source-mappable.

Consider the `AlgoBank example <https://github.com/algorand/pyteal/blob/67089381fcd9bf096c0b9118244709d145e90646/examples/application/abi/algobank.py>`_.
It was authored long before the source mapper became available, but below we'll see how to tweak it to be source-mappable.

You may need to upgrade your pyteal dependency to a version that includes source mapping as well as feature gating.
In particular, :code:`pip install pyteal` will install the :code:`feature_gates` package alongside :code:`pyteal`.

(Optional)  **AlgodClient**
------------------------------

If you intend to add the bytecode's program counters to the source map, you'll need to ensure that an :code:`AlgodClient` is available.
If it's running on port 4001 (the default Sandbox port for Algod) then everything should just work automatically. 
However, if Algod is running on a different port, you'll need to create a separate :code:`AlgodClient` in your script which you will then supply 
as an argument to the compile instruction.

NOTE: In this example *we're going to assume* that an :code:`AlgodClient` is running on port 4001.


1. Enable the source map feature gate
-------------------------------------

This is as simple as adding the two lines to the top of `algobank.py`:

.. code-block:: python

    from feature_gates import FeatureGates
    FeatureGates.set_sourcemap_enabled(True)

    # previously-existing imports:
    from pyteal import *  # noqa: E402
    import json # noqa: E402

    # rest of the file
    ...

The code importing :code:`FeatureGates` and enabling the feature **must come before** any pyteal imports.
That's because as a side effect, pyteal imports actually create expressions that can end up in the PyTeal program, and we want these to be properly source mapped.

In this example, we also added **flake8** lint ignore comments :code:`# noqa: E402` because in python 
it's preferred to conclude all imports before running any code.

2. Modify the compile instruction
---------------------------------

In the :code:`algobank.py` example, the compile instruction looks like :code:`router.compile_program(...)`. 
This traditional expression, along with its analog for non-ABI programs, :code:`compileTeal(...)`,
*don't support* source mapping. However, the newer :code:`compile(...)` methods do suport it:

- Compiler: :any:`Compilation.compile`. Source map specific parameters:

  * :code:`with_sourcemap`
  * :code:`teal_filename`
  * :code:`pcs_in_sourcemap`
  * :code:`algod_client`
  * :code:`annotate_teal`
  * :code:`annotate_teal_headers`
  * :code:`annotate_teal_concise`

- ABI Router: :any:`Router.compile`. Source map specific parameters:

  * :code:`with_sourcemaps`
  * :code:`approval_filename`
  * :code:`clear_filename`
  * :code:`pcs_in_sourcemap`
  * :code:`algod_client`
  * :code:`annotate_teal`
  * :code:`annotate_teal_headers`
  * :code:`annotate_teal_concise`


Please follow the links above to the :code:`compile(...)` methods
for the details of each parameter.

For our purposes, let's get a *full* source map annotation
while letting PyTeal bootstrap its own Algod. Modify the 
`snippet between lines 116 and 118 <https://github.com/algorand/pyteal/blob/67089381fcd9bf096c0b9118244709d145e90646/examples/application/abi/algobank.py#L116-L127>`_
to look like:

.. code-block:: python

    # Compile the program
    results = router.compile(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        with_sourcemaps=True,
        annotate_teal=True,
        pcs_in_sourcemap=True,
        annotate_teal_headers=True,
        annotate_teal_concise=False,
    )

Here we are enabling the source map and requesting annotated teal by
setting :code:`with_sourcemaps=True` and :code:`annotate_teal=True`.
:code:`pcs_in_sourcemap=True` will add the program counters to the source map.
Finally, we customize the annotated teal to have a header row with column names,
and get as many columns as available by specifying :code:`annotate_teal_headers=True`
and :code:`annotate_teal_concise=False`.

3. Grab annotated teal from result
----------------------------------

The newer :code:`compile(...)` methods return objects that contain source map information:

- Compiler: :any:`Compilation.compile`. Returns a :any:`CompileResults` object which has a :code:`sourcemap` field of type :any:`PyTealSourceMap`.
- ABI Router: :any:`Router.compile`. Returns a :any:`RouterResults` object which has :code:`approval_sourcemap` and :code:`clear_sourcemap` fields of type :any:`PyTealSourceMap`.

We modified ``algobank.py`` to call :any:`Router.compile` and
received a ``results`` object of type :any:`RouterResults`. 
Let's simply print out the resulting annotated approval program:

.. code-block:: python

    # Print the results
    print(results.approval_sourcemap.annotated_teal)

4. Run the script
-----------------

.. code-block:: none
  
    ❯ python examples/application/abi/algobank.py
    // GENERATED TEAL                      //    PC     PYTEAL PATH                           LINE    PYTEAL
    #pragma version 6                      //    (0)    examples/application/abi/algobank.py  137     router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), with_sourcemaps=True, annotate_teal=True, pcs_in_sourcemap=True, annotate_teal_headers=True, annotate_teal_concise=False)
    txn NumAppArgs                         //    (20)                                         27      BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL))
    int 0                                  //    (22)
    ... continues ...

About the Output
----------------

The resulting annotated teal assembles down to the same bytecode
as the unadorned program in :code:`results.approval_program`.

Each line's comments also provide:

- (``PC``) - the program counter of the assembled bytecode for the TEAL instruction
- (``PYTEAL PATH``) - the PyTeal file which generated the TEAL instruction
- (``LINE``) - the line *number* of the PyTeal source
- (``PYTEAL``) - the PyTeal code that generated the TEAL instruction

When a value -such as a line number- is omitted, it means that it is the same as the previous.

Typically, the PyTeal compiler adds expressions to a user's program to make various
constructs work. Consequently, not every TEAL instruction will have a corresponding
PyTeal expression that was explicity written by the program author. 
In such cases, the source mapper will attempt to find a reasonable user-attributable substitute.
For example, if a program includes a :any:`Subroutine` definition, the compiler will add
boiler plate for adding arguments to the stack before the subroutine is called, and then
more boiler plate to read the arguments from the stack at the beginning of the subroutine's
execution. The source mapper will attribute these boiler plate expressions to the subroutine's
python definition.

Sometimes, the source mapper doesn't succeed to find a user attribution
and resorts to a attributing to the entry point into pyteal - the line
that called the compiler. In the example above, the first line of the
annotated teal is attributed to the line that called the compiler:

.. code-block:: none

  examples/application/abi/algobank.py  137     router.compile(version=6, ...)
  
This is the line that would get mapped to in the case of such source map "misses".
