from pathlib import Path
import pytest
from typing import Literal

import algosdk.abi

from pyteal import abi
import pyteal as pt

from tests.compile_asserts import assert_teal_as_expected

from tests.abi_roundtrip import ABIRoundtrip

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
    abi.Tuple3[abi.Bool, abi.Uint64, abi.Uint32],
    abi.Tuple3[abi.Byte, abi.Bool, abi.Uint64],
    abi.Tuple3[abi.Uint8, abi.Byte, abi.Bool],
    abi.Tuple3[abi.Uint16, abi.Uint8, abi.Byte],
    abi.Tuple3[abi.Uint32, abi.Uint16, abi.Uint8],
    abi.Tuple3[abi.Uint64, abi.Uint32, abi.Uint16],
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
    (abi.DynamicArray[abi.Address], 11),
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
        13,
    ),
]


@pytest.mark.parametrize("abi_type", ABI_TYPES)
def test_pure_compilation(abi_type):
    print(f"Testing {abi_type=}")

    dynamic_length = None
    if isinstance(abi_type, tuple):
        abi_type, dynamic_length = abi_type

    sdk_abi_type = abi.algosdk_from_annotation(abi_type)

    roundtripper = ABIRoundtrip(abi_type, dynamic_length).pytealer()

    abi_arg_types = roundtripper.abi_argument_types()
    assert [sdk_abi_type] == abi_arg_types

    abi_ret_type = roundtripper.abi_return_type()
    assert algosdk.abi.TupleType([sdk_abi_type] * 3) == abi_ret_type

    program = roundtripper.program()
    teal = pt.compileTeal(program, pt.Mode.Application, version=6)

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
