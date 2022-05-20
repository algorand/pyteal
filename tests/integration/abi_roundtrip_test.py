from pathlib import Path
import pytest
from typing import Literal

import algosdk.abi

from graviton.abi_strategy import ABIStrategy

from pyteal import abi

from tests.abi_roundtrip import ABIRoundtrip
from tests.compile_asserts import assert_teal_as_expected

PATH = Path.cwd() / "tests" / "integration"
FIXTURES = PATH / "teal"
GENERATED = PATH / "generated"
ABI_TYPES = [
    abi.Address,
    abi.Bool,
    abi.Byte,
    (abi.String, 0),
    (abi.String, 1),
    (abi.String, 13),
    abi.Uint8,
    abi.Uint16,
    abi.Uint32,
    abi.Uint64,
    abi.Tuple0,
    abi.Tuple1[abi.Bool],
    abi.Tuple1[abi.Byte],
    abi.Tuple1[abi.Uint8],
    abi.Tuple1[abi.Uint16],
    abi.Tuple1[abi.Uint32],
    abi.Tuple1[abi.Uint64],
    abi.Tuple2[abi.Bool, abi.Byte],
    abi.Tuple3[abi.Bool, abi.Uint64, abi.Uint32],
    abi.Tuple3[abi.Byte, abi.Bool, abi.Uint64],
    abi.Tuple3[abi.Uint8, abi.Byte, abi.Bool],
    abi.Tuple3[abi.Uint16, abi.Uint8, abi.Byte],
    abi.Tuple3[abi.Uint32, abi.Uint16, abi.Uint8],
    abi.Tuple3[abi.Uint64, abi.Uint32, abi.Uint16],
    abi.Tuple4[abi.Bool, abi.Byte, abi.Address, abi.String],
    abi.Tuple5[abi.Bool, abi.Byte, abi.Address, abi.String, abi.Uint64],
    abi.StaticArray[abi.Bool, Literal[1]],
    abi.StaticArray[abi.Bool, Literal[42]],
    abi.StaticArray[abi.Uint64, Literal[1]],
    abi.StaticArray[abi.Uint64, Literal[42]],
    (abi.DynamicArray[abi.Bool], 0),
    (abi.DynamicArray[abi.Bool], 1),
    (abi.DynamicArray[abi.Bool], 42),
    (abi.DynamicArray[abi.Uint64], 0),
    (abi.DynamicArray[abi.Uint64], 1),
    (abi.DynamicArray[abi.Uint64], 42),
    (abi.DynamicArray[abi.Address], 10),
    (abi.DynamicArray[abi.StaticArray[abi.Bool, Literal[3]]], 11),
    abi.StaticArray[abi.Tuple1[abi.Bool], Literal[10]],
    (
        abi.DynamicArray[
            abi.Tuple4[
                abi.StaticArray[abi.Byte, Literal[4]],
                abi.Tuple2[abi.Bool, abi.Bool],
                abi.Uint64,
                abi.Address,
            ]
        ],
        7,
    ),
    (
        abi.DynamicArray[
            abi.Tuple5[
                abi.Bool,
                abi.Byte,
                abi.Address,
                abi.String,
                abi.Tuple4[
                    abi.Address,
                    abi.StaticArray[
                        abi.Tuple5[
                            abi.Uint32,
                            abi.DynamicArray[abi.String],
                            abi.StaticArray[abi.Bool, Literal[2]],
                            abi.Tuple1[abi.Byte],
                            abi.Uint8,
                        ],
                        Literal[2],
                    ],
                    abi.String,
                    abi.DynamicArray[abi.Bool],
                ],
            ]
        ],
        2,
    ),
]


def roundtrip_setup(abi_type):
    dynamic_length = None
    if isinstance(abi_type, tuple):
        abi_type, dynamic_length = abi_type

    return (
        abi_type,
        dynamic_length,
        ABIRoundtrip(abi.make(abi_type), length=dynamic_length).pytealer(),
    )


def test_abi_types_comprehensive():
    top_level_names = {
        tli.split("[")[0] if tli.startswith("pyteal") else tli.split("'")[1]
        for tli in (
            str(x) for x in (at[0] if isinstance(at, tuple) else at for at in ABI_TYPES)
        )
    }

    def get_subclasses(cls):
        for subclass in cls.__subclasses__():
            yield from get_subclasses(subclass)
            yield subclass

    all_abi_names = {
        str(at).split("'")[1]
        for at in (
            cls
            for cls in abi.__dict__.values()
            if isinstance(cls, type)
            and issubclass(cls, abi.BaseType)
            and not cls.__abstractmethods__
            and cls is not abi.Tuple
        )
    }

    missing_cases = all_abi_names - top_level_names
    assert not missing_cases, f"missing round trip tests for {missing_cases}"


@pytest.mark.parametrize("abi_type", ABI_TYPES)
def test_pure_compilation(abi_type):
    print(f"Pure Compilation Test for {abi_type=}")
    abi_type, dynamic_length, roundtripper = roundtrip_setup(abi_type)

    sdk_abi_type = abi.algosdk_from_annotation(abi_type)

    abi_arg_types = roundtripper.abi_argument_types()
    abi_ret_type = roundtripper.abi_return_type()
    assert [sdk_abi_type] == abi_arg_types
    assert algosdk.abi.TupleType([sdk_abi_type] * 3) == abi_ret_type

    teal = roundtripper.compile(version=6)

    filename = (
        f"app_roundtrip_{sdk_abi_type}"
        + ("" if dynamic_length is None else f"_<{dynamic_length}>")
        + ".teal"
    )
    tealdir = GENERATED / "roundtrip"
    tealdir.mkdir(parents=True, exist_ok=True)

    save_to = tealdir / filename
    with open(save_to, "w") as f:
        f.write(teal)

    assert_teal_as_expected(save_to, FIXTURES / "roundtrip" / filename)


GAI_ISSUE_2050 = "https://github.com/algorand/go-algorand-internal/issues/2050"

BAD_TEALS = {
    "()": GAI_ISSUE_2050,
}


@pytest.mark.parametrize("abi_type", ABI_TYPES)
def test_roundtrip(abi_type):
    print(f"Round Trip Test for {abi_type=}")

    _, dynamic_length, roundtripper = roundtrip_setup(abi_type)

    sdk_abi_types = roundtripper.abi_argument_types()
    sdk_ret_type = roundtripper.abi_return_type()

    sdk_abi_str = str(sdk_abi_types[0])
    if sdk_abi_str in BAD_TEALS:
        print(
            f"Skipping encoding roundtrip test of '{sdk_abi_str}' because of {BAD_TEALS[sdk_abi_str]}"
        )
        return

    abi_strat = ABIStrategy(sdk_abi_types[0], dynamic_length=dynamic_length)
    rand_abi_instance = abi_strat.get_random()
    args = (rand_abi_instance,)
    inspector = roundtripper.dryrun(args)

    cost = inspector.cost()
    passed = inspector.passed()
    original, mut, mut_mut = inspector.last_log()

    print(
        f"""
{abi_type=}
{sdk_abi_str=}
{dynamic_length=}
{sdk_abi_types=}
{sdk_ret_type=}
{rand_abi_instance=}
{cost=}
{original=}
{mut=}
{mut_mut=}
"""
    )

    last_rows = 2

    assert passed == (cost <= 700), inspector.report(
        args, f"passed={passed} contradicted cost={cost}", last_rows=last_rows
    )
    assert rand_abi_instance == original, inspector.report(
        args, "rand_abi_instance v. original", last_rows=last_rows
    )
    assert original == mut_mut, inspector.report(
        args, "orginal v. mut_mut", last_rows=last_rows
    )

    expected_mut = abi_strat.mutate_for_roundtrip(rand_abi_instance)
    assert expected_mut == mut, inspector.report(
        args, "expected_mut v. mut", last_rows=last_rows
    )