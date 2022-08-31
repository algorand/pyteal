from typing import Callable, NamedTuple, Literal, Optional, Any, get_origin
from inspect import isabstract
import pytest

import algosdk.abi

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.util import (
    substring_for_decoding,
    int_literal_from_annotation,
    type_spec_from_algosdk,
)

options = pt.CompileOptions(version=5)


class SubstringTest(NamedTuple):
    start_index: Optional[pt.Expr]
    end_index: Optional[pt.Expr]
    length: Optional[pt.Expr]
    expected: Callable[[pt.Expr], pt.Expr | type[Exception]]


SUBSTRING_TEST_CASES: list[SubstringTest] = [
    SubstringTest(
        start_index=None, end_index=None, length=None, expected=lambda encoded: encoded
    ),
    SubstringTest(
        start_index=None,
        end_index=None,
        length=pt.Int(4),
        expected=lambda encoded: pt.Extract(encoded, pt.Int(0), pt.Int(4)),
    ),
    SubstringTest(
        start_index=None,
        end_index=pt.Int(4),
        length=None,
        expected=lambda encoded: pt.Substring(encoded, pt.Int(0), pt.Int(4)),
    ),
    SubstringTest(
        start_index=None,
        end_index=pt.Int(4),
        length=pt.Int(5),
        expected=lambda _: pt.TealInputError,
    ),
    SubstringTest(
        start_index=pt.Int(4),
        end_index=None,
        length=None,
        expected=lambda encoded: pt.Suffix(encoded, pt.Int(4)),
    ),
    SubstringTest(
        start_index=pt.Int(4),
        end_index=None,
        length=pt.Int(5),
        expected=lambda encoded: pt.Extract(encoded, pt.Int(4), pt.Int(5)),
    ),
    SubstringTest(
        start_index=pt.Int(4),
        end_index=pt.Int(5),
        length=None,
        expected=lambda encoded: pt.Substring(encoded, pt.Int(4), pt.Int(5)),
    ),
    SubstringTest(
        start_index=pt.Int(4),
        end_index=pt.Int(5),
        length=pt.Int(6),
        expected=lambda _: pt.TealInputError,
    ),
]


@pytest.mark.parametrize(
    "start_index, end_index, length, expected", SUBSTRING_TEST_CASES
)
def test_substringForDecoding(
    start_index: Optional[pt.Expr],
    end_index: Optional[pt.Expr],
    length: Optional[pt.Expr],
    expected: Callable[[pt.Expr], pt.Expr | type[Exception]],
):
    encoded = pt.Bytes("encoded")

    expected_expr = expected(encoded)

    if not isinstance(expected_expr, pt.Expr):
        with pytest.raises(expected_expr):
            substring_for_decoding(
                encoded,
                start_index=start_index,
                end_index=end_index,
                length=length,
            )
        return

    expr = substring_for_decoding(
        encoded,
        start_index=start_index,
        end_index=end_index,
        length=length,
    )
    assert expr.type_of() == pt.TealType.bytes
    assert not expr.has_return()

    expected_blocks, _ = expected_expr.__teal__(options)
    expected_blocks.addIncoming()
    expected_blocks = pt.TealBlock.NormalizeBlocks(expected_blocks)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected_blocks


class IntAnnotationTest(NamedTuple):
    annotation: Any
    expected: int | type[Exception]


IN_ANNOTATION_TEST_CASES: list[IntAnnotationTest] = [
    IntAnnotationTest(annotation=Literal[0], expected=0),
    IntAnnotationTest(annotation=Literal[1], expected=1),
    IntAnnotationTest(annotation=Literal[10], expected=10),
    IntAnnotationTest(annotation=Literal[True], expected=TypeError),
    IntAnnotationTest(annotation=Literal["test"], expected=TypeError),
    IntAnnotationTest(annotation=Literal[b"test"], expected=TypeError),
    IntAnnotationTest(annotation=Literal[None], expected=TypeError),
    IntAnnotationTest(annotation=Literal[0, 1], expected=TypeError),
    IntAnnotationTest(annotation=Literal, expected=TypeError),
]


@pytest.mark.parametrize("annotation, expected", IN_ANNOTATION_TEST_CASES)
def test_int_literal_from_annotation(annotation: Any, expected: int | type[Exception]):
    if not isinstance(expected, int):
        with pytest.raises(expected):
            int_literal_from_annotation(annotation)
        return

    actual = int_literal_from_annotation(annotation)
    assert actual == expected


class TypeAnnotationTest(NamedTuple):
    annotation: Any
    expected: abi.TypeSpec | type[Exception]


class ExampleNamedTuple(abi.NamedTuple):
    a: abi.Field[abi.Uint16]
    b: abi.Field[abi.DynamicArray[abi.Byte]]
    c: abi.Field[abi.Address]


TYPE_ANNOTATION_TEST_CASES: list[TypeAnnotationTest] = [
    TypeAnnotationTest(annotation=abi.Bool, expected=abi.BoolTypeSpec()),
    TypeAnnotationTest(annotation=abi.Byte, expected=abi.ByteTypeSpec()),
    TypeAnnotationTest(annotation=abi.Uint8, expected=abi.Uint8TypeSpec()),
    TypeAnnotationTest(annotation=abi.Uint16, expected=abi.Uint16TypeSpec()),
    TypeAnnotationTest(annotation=abi.Uint32, expected=abi.Uint32TypeSpec()),
    TypeAnnotationTest(annotation=abi.Uint64, expected=abi.Uint64TypeSpec()),
    TypeAnnotationTest(
        annotation=abi.DynamicArray[abi.Uint32],
        expected=abi.DynamicArrayTypeSpec(abi.Uint32TypeSpec()),
    ),
    TypeAnnotationTest(
        annotation=abi.DynamicArray[abi.Uint64],
        expected=abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec()),
    ),
    TypeAnnotationTest(
        annotation=abi.DynamicArray[abi.DynamicArray[abi.Uint32]],
        expected=abi.DynamicArrayTypeSpec(
            abi.DynamicArrayTypeSpec(abi.Uint32TypeSpec())
        ),
    ),
    TypeAnnotationTest(
        annotation=abi.DynamicArray,
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=abi.StaticArray[abi.Uint32, Literal[0]],
        expected=abi.StaticArrayTypeSpec(abi.Uint32TypeSpec(), 0),
    ),
    TypeAnnotationTest(
        annotation=abi.StaticArray[abi.Uint32, Literal[10]],
        expected=abi.StaticArrayTypeSpec(abi.Uint32TypeSpec(), 10),
    ),
    TypeAnnotationTest(
        annotation=abi.StaticArray[abi.Bool, Literal[500]],
        expected=abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 500),
    ),
    TypeAnnotationTest(
        annotation=abi.StaticArray[abi.Bool, Literal[-1]],
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=abi.StaticArray[abi.Bool, int],
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=abi.StaticArray,
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=abi.StaticArray[abi.StaticArray[abi.Bool, Literal[500]], Literal[5]],
        expected=abi.StaticArrayTypeSpec(
            abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 500), 5
        ),
    ),
    TypeAnnotationTest(annotation=abi.Address, expected=abi.AddressTypeSpec()),
    TypeAnnotationTest(
        annotation=abi.StaticBytes[Literal[10]],
        expected=abi.StaticBytesTypeSpec(10),
    ),
    TypeAnnotationTest(
        annotation=abi.DynamicArray[abi.StaticArray[abi.Bool, Literal[500]]],
        expected=abi.DynamicArrayTypeSpec(
            abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 500)
        ),
    ),
    TypeAnnotationTest(annotation=abi.String, expected=abi.StringTypeSpec()),
    TypeAnnotationTest(
        annotation=abi.DynamicBytes,
        expected=abi.DynamicBytesTypeSpec(),
    ),
    TypeAnnotationTest(annotation=abi.Tuple, expected=abi.TupleTypeSpec()),
    TypeAnnotationTest(annotation=abi.Tuple0, expected=abi.TupleTypeSpec()),
    TypeAnnotationTest(
        annotation=abi.Tuple1[abi.Uint32],
        expected=abi.TupleTypeSpec(abi.Uint32TypeSpec()),
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple1,
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple2[abi.Uint32, abi.Uint16],
        expected=abi.TupleTypeSpec(abi.Uint32TypeSpec(), abi.Uint16TypeSpec()),
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple2,
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple3[abi.Uint32, abi.Uint16, abi.Byte],
        expected=abi.TupleTypeSpec(
            abi.Uint32TypeSpec(), abi.Uint16TypeSpec(), abi.ByteTypeSpec()
        ),
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple3,
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple3[
            abi.Tuple1[abi.Uint32],
            abi.StaticArray[abi.Bool, Literal[55]],
            abi.Tuple2[abi.Uint32, abi.Uint16],
        ],
        expected=abi.TupleTypeSpec(
            abi.TupleTypeSpec(abi.Uint32TypeSpec()),
            abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 55),
            abi.TupleTypeSpec(abi.Uint32TypeSpec(), abi.Uint16TypeSpec()),
        ),
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple4[abi.Uint32, abi.Uint16, abi.Byte, abi.Bool],
        expected=abi.TupleTypeSpec(
            abi.Uint32TypeSpec(),
            abi.Uint16TypeSpec(),
            abi.ByteTypeSpec(),
            abi.BoolTypeSpec(),
        ),
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple4,
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple5[abi.Uint32, abi.Uint16, abi.Byte, abi.Bool, abi.Tuple0],
        expected=abi.TupleTypeSpec(
            abi.Uint32TypeSpec(),
            abi.Uint16TypeSpec(),
            abi.ByteTypeSpec(),
            abi.BoolTypeSpec(),
            abi.TupleTypeSpec(),
        ),
    ),
    TypeAnnotationTest(
        annotation=abi.Tuple5,
        expected=TypeError,
    ),
    TypeAnnotationTest(
        annotation=ExampleNamedTuple, expected=ExampleNamedTuple().type_spec()
    ),
    TypeAnnotationTest(
        annotation=list[abi.Uint16],
        expected=TypeError,
    ),
    TypeAnnotationTest(annotation=abi.Transaction, expected=abi.TransactionTypeSpec()),
    TypeAnnotationTest(
        annotation=abi.PaymentTransaction, expected=abi.PaymentTransactionTypeSpec()
    ),
    TypeAnnotationTest(
        annotation=abi.KeyRegisterTransaction,
        expected=abi.KeyRegisterTransactionTypeSpec(),
    ),
    TypeAnnotationTest(
        annotation=abi.AssetConfigTransaction,
        expected=abi.AssetConfigTransactionTypeSpec(),
    ),
    TypeAnnotationTest(
        annotation=abi.AssetFreezeTransaction,
        expected=abi.AssetFreezeTransactionTypeSpec(),
    ),
    TypeAnnotationTest(
        annotation=abi.AssetTransferTransaction,
        expected=abi.AssetTransferTransactionTypeSpec(),
    ),
    TypeAnnotationTest(
        annotation=abi.ApplicationCallTransaction,
        expected=abi.ApplicationCallTransactionTypeSpec(),
    ),
    TypeAnnotationTest(annotation=abi.Account, expected=abi.AccountTypeSpec()),
    TypeAnnotationTest(annotation=abi.Asset, expected=abi.AssetTypeSpec()),
    TypeAnnotationTest(annotation=abi.Application, expected=abi.ApplicationTypeSpec()),
]


@pytest.mark.parametrize("annotation, expected", TYPE_ANNOTATION_TEST_CASES)
def test_type_spec_from_annotation(
    annotation: Any, expected: abi.TypeSpec | type[Exception]
):
    if not isinstance(expected, abi.TypeSpec):
        with pytest.raises(expected):
            abi.type_spec_from_annotation(annotation)
        return

    actual = abi.type_spec_from_annotation(annotation)
    assert actual == expected

    new_instance = actual.new_instance()

    annotation_origin = get_origin(annotation)
    if annotation_origin is None:
        # get_origin will return None for annotations without generic args, e.g. `Byte`
        annotation_origin = annotation

    assert isinstance(
        new_instance, annotation_origin
    ), "TypeSpec.new_instance() returns a value that does not match the annotation type"

    assert (
        actual == new_instance.type_spec()
    ), "TypeSpec.new_instance().type_spec() does not match original TypeSpec"


def test_type_spec_from_annotation_is_exhaustive():
    # This test is to make sure there are no new subclasses of BaseType that type_spec_from_annotation
    # is not aware of.

    subclasses = abi.BaseType.__subclasses__()
    while len(subclasses) > 0:
        subclass = subclasses.pop()
        subclasses += subclass.__subclasses__()

        if isabstract(subclass):
            # abstract class type annotations should not be supported
            with pytest.raises(TypeError, match=r"^Unknown annotation origin"):
                abi.type_spec_from_annotation(subclass)
            continue

        if subclass is pt.abi.NamedTuple:
            with pytest.raises(
                pt.TealInputError, match=r"^NamedTuple must be subclassed$"
            ):
                abi.type_spec_from_annotation(subclass)
            continue

        try:
            # if subclass is not generic, this will succeed
            abi.type_spec_from_annotation(subclass)
        except TypeError as e:
            # if subclass is generic, we should get an error that is NOT "Unknown annotation origin"
            assert "Unknown annotation origin" not in str(e)

        if issubclass(subclass, pt.abi.NamedTuple):
            # ignore NamedTuple subclasses for the following check
            continue

        # make sure there is a testcase for this subclass in test_type_spec_from_annotation
        found = False
        for testcase in TYPE_ANNOTATION_TEST_CASES:
            if subclass is testcase.annotation or subclass is get_origin(
                testcase.annotation
            ):
                found = True
                break
        assert (
            found
        ), f"Test case for subclass {subclass} is not present in TYPE_ANNOTATION_TEST_CASES"


def test_make():
    actual = abi.make(abi.Tuple2[abi.Uint64, abi.StaticArray[abi.Bool, Literal[8]]])
    expected_type_spec = abi.TupleTypeSpec(
        abi.Uint64TypeSpec(), abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 8)
    )

    assert actual.type_spec() == expected_type_spec
    assert type(actual) is abi.Tuple2


def test_size_of():
    values = [
        (abi.Uint8, 1),
        (abi.Address, 32),
        (abi.StaticArray[abi.Uint16, Literal[10]], 2 * 10),
        (abi.StaticBytes[Literal[36]], 36),
    ]

    for (t, s) in values:
        assert abi.size_of(t) == s

    with pytest.raises(pt.TealInputError):
        abi.size_of(abi.String)

    with pytest.raises(pt.TealInputError):
        abi.size_of(abi.DynamicBytes)


ABI_TRANSLATION_TEST_CASES = [
    # Test for byte/bool/address/strings
    (algosdk.abi.ByteType(), "byte", abi.ByteTypeSpec(), abi.Byte),
    (algosdk.abi.BoolType(), "bool", abi.BoolTypeSpec(), abi.Bool),
    (
        algosdk.abi.AddressType(),
        "address",
        abi.AddressTypeSpec(),
        abi.Address,
    ),
    (algosdk.abi.StringType(), "string", abi.StringTypeSpec(), abi.String),
    # Test for dynamic array type
    (
        algosdk.abi.ArrayDynamicType(algosdk.abi.UintType(32)),
        "uint32[]",
        abi.DynamicArrayTypeSpec(abi.Uint32TypeSpec()),
        abi.DynamicArray[abi.Uint32],
    ),
    (
        algosdk.abi.ArrayDynamicType(
            algosdk.abi.ArrayDynamicType(algosdk.abi.ByteType())
        ),
        "byte[][]",
        abi.DynamicArrayTypeSpec(abi.DynamicArrayTypeSpec(abi.ByteTypeSpec())),
        abi.DynamicArray[abi.DynamicArray[abi.Byte]],
    ),
    # TODO: Turn these tests on when PyTeal supports ufixed<N>x<M>
    # cf https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0004.md#types
    # (
    #     algosdk.abi.ArrayDynamicType(algosdk.abi.UfixedType(256, 64)),
    #     "ufixed256x64[]",
    #     abi.DynamicArrayTypeSpec(abi.UfixedTypeSpec(256, 64)),
    # ),
    # # Test for static array type
    # (
    #     algosdk.abi.ArrayStaticType(algosdk.abi.UfixedType(128, 10), 100),
    #     "ufixed128x10[100]",
    #     abi.ArrayStaticTypeSpec(abi.UfixedTypeSpec(128, 10), 100),
    # ),
    (
        algosdk.abi.ArrayStaticType(
            algosdk.abi.ArrayStaticType(algosdk.abi.BoolType(), 256),
            100,
        ),
        "bool[256][100]",
        abi.StaticArrayTypeSpec(
            abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 256),
            100,
        ),
        abi.StaticArray[abi.StaticArray[abi.Bool, Literal[256]], Literal[100]],
    ),
    # Test for tuple
    (algosdk.abi.TupleType([]), "()", abi.TupleTypeSpec(), abi.Tuple0),
    (
        algosdk.abi.TupleType(
            [
                algosdk.abi.UintType(16),
                algosdk.abi.TupleType(
                    [
                        algosdk.abi.ByteType(),
                        algosdk.abi.ArrayStaticType(algosdk.abi.AddressType(), 10),
                    ]
                ),
            ]
        ),
        "(uint16,(byte,address[10]))",
        abi.TupleTypeSpec(
            abi.Uint16TypeSpec(),
            abi.TupleTypeSpec(
                abi.ByteTypeSpec(),
                abi.StaticArrayTypeSpec(abi.AddressTypeSpec(), 10),
            ),
        ),
        abi.Tuple2[
            abi.Uint16,
            abi.Tuple2[
                abi.Byte,
                abi.StaticArray[abi.Address, Literal[10]],
            ],
        ],
    ),
    (
        algosdk.abi.TupleType(
            [
                algosdk.abi.UintType(64),
                algosdk.abi.TupleType(
                    [
                        algosdk.abi.ByteType(),
                        algosdk.abi.ArrayStaticType(algosdk.abi.AddressType(), 10),
                    ]
                ),
                algosdk.abi.TupleType([]),
                algosdk.abi.BoolType(),
            ]
        ),
        "(uint64,(byte,address[10]),(),bool)",
        abi.TupleTypeSpec(
            abi.Uint64TypeSpec(),
            abi.TupleTypeSpec(
                abi.ByteTypeSpec(),
                abi.StaticArrayTypeSpec(abi.AddressTypeSpec(), 10),
            ),
            abi.TupleTypeSpec(),
            abi.BoolTypeSpec(),
        ),
        abi.Tuple4[
            abi.Uint64,
            abi.Tuple2[
                abi.Byte,
                abi.StaticArray[abi.Address, Literal[10]],
            ],
            abi.Tuple,
            abi.Bool,
        ],
    ),
    # TODO: Turn the following test on when PyTeal supports ufixed<N>x<M>
    # cf https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0004.md#types
    # (
    #     algosdk.abi.TupleType(
    #         [
    #             algosdk.abi.UfixedType(256, 16),
    #             algosdk.abi.TupleType(
    #                 [
    #                     algosdk.abi.TupleType(
    #                         [
    #                             algosdk.abi.StringType(),
    #                         ]
    #                     ),
    #                     algosdk.abi.BoolType(),
    #                     algosdk.abi.TupleType(
    #                         [
    #                             algosdk.abi.AddressType(),
    #                             algosdk.abi.UintType(8),
    #                         ]
    #                     ),
    #                 ]
    #             ),
    #         ]
    #     ),
    #     "(ufixed256x16,((string),bool,(address,uint8)))",
    #     abi.TupleType(
    #         [
    #             abi.UfixedType(256, 16),
    #             abi.TupleType(
    #                 [
    #                     abi.TupleType(
    #                         [
    #                             abi.StringType(),
    #                         ]
    #                     ),
    #                     abi.BoolType(),
    #                     abi.TupleType(
    #                         [
    #                             abi.AddressType(),
    #                             abi.UintType(8),
    #                         ]
    #                     ),
    #                 ]
    #             ),
    #         ]
    #     ),
    # ),
    (
        "cannot map ABI transaction type spec <pyteal.abi.TransactionTypeSpec",
        "txn",
        abi.TransactionTypeSpec(),
        abi.Transaction,
    ),
    (
        "cannot map ABI transaction type spec <pyteal.abi.PaymentTransactionTypeSpec",
        "pay",
        abi.PaymentTransactionTypeSpec(),
        abi.PaymentTransaction,
    ),
    (
        "cannot map ABI transaction type spec <pyteal.abi.KeyRegisterTransactionTypeSpec",
        "keyreg",
        abi.KeyRegisterTransactionTypeSpec(),
        abi.KeyRegisterTransaction,
    ),
    (
        "cannot map ABI transaction type spec <pyteal.abi.AssetConfigTransactionTypeSpec",
        "acfg",
        abi.AssetConfigTransactionTypeSpec(),
        abi.AssetConfigTransaction,
    ),
    (
        "cannot map ABI transaction type spec <pyteal.abi.AssetTransferTransactionTypeSpec",
        "axfer",
        abi.AssetTransferTransactionTypeSpec(),
        abi.AssetTransferTransaction,
    ),
    (
        "cannot map ABI transaction type spec <pyteal.abi.AssetFreezeTransactionTypeSpec",
        "afrz",
        abi.AssetFreezeTransactionTypeSpec(),
        abi.AssetFreezeTransaction,
    ),
    (
        "cannot map ABI transaction type spec <pyteal.abi.ApplicationCallTransactionTypeSpec",
        "appl",
        abi.ApplicationCallTransactionTypeSpec(),
        abi.ApplicationCallTransaction,
    ),
    (
        "cannot map ABI reference type spec <pyteal.abi.AccountTypeSpec",
        "account",
        abi.AccountTypeSpec(),
        abi.Account,
    ),
    (
        "cannot map ABI reference type spec <pyteal.abi.ApplicationTypeSpec",
        "application",
        abi.ApplicationTypeSpec(),
        abi.Application,
    ),
    (
        "cannot map ABI reference type spec <pyteal.abi.AssetTypeSpec",
        "asset",
        abi.AssetTypeSpec(),
        abi.Asset,
    ),
]

ABI_SIGNATURE_TYPESPEC_CASES = [
    (
        "check(uint64,uint64)uint64",
        [abi.Uint64TypeSpec(), abi.Uint64TypeSpec()],
        abi.Uint64TypeSpec(),
    ),
    (
        "check(uint64[],uint64)uint64",
        [abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec()), abi.Uint64TypeSpec()],
        abi.Uint64TypeSpec(),
    ),
    (
        "check(uint64[5],uint64)uint64",
        [abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 5), abi.Uint64TypeSpec()],
        abi.Uint64TypeSpec(),
    ),
    (
        "check(uint64,uint64)uint64[]",
        [abi.Uint64TypeSpec(), abi.Uint64TypeSpec()],
        abi.DynamicArrayTypeSpec(abi.Uint64TypeSpec()),
    ),
    (
        "check(uint64,uint64)uint64[5]",
        [abi.Uint64TypeSpec(), abi.Uint64TypeSpec()],
        abi.StaticArrayTypeSpec(abi.Uint64TypeSpec(), 5),
    ),
    (
        "check((uint64,uint64),asset)string",
        [
            abi.TupleTypeSpec(abi.Uint64TypeSpec(), abi.Uint64TypeSpec()),
            abi.AssetTypeSpec(),
        ],
        abi.StringTypeSpec(),
    ),
    (
        "check(string,asset)(uint64,uint64)",
        [abi.StringTypeSpec(), abi.AssetTypeSpec()],
        abi.TupleTypeSpec(abi.Uint64TypeSpec(), abi.Uint64TypeSpec()),
    ),
    (
        "check(account,asset,application)string",
        [abi.AccountTypeSpec(), abi.AssetTypeSpec(), abi.ApplicationTypeSpec()],
        abi.StringTypeSpec(),
    ),
    (
        "check(pay,txn,appl)string",
        [
            abi.PaymentTransactionTypeSpec(),
            abi.TransactionTypeSpec(),
            abi.ApplicationCallTransactionTypeSpec(),
        ],
        abi.StringTypeSpec(),
    ),
    ("check(uint64,uint64)void", [abi.Uint64TypeSpec(), abi.Uint64TypeSpec()], None),
]


@pytest.mark.parametrize(
    "algosdk_abi, abi_string, pyteal_abi_ts, pyteal_abi",
    ABI_TRANSLATION_TEST_CASES,
)
def test_abi_type_translation(algosdk_abi, abi_string, pyteal_abi_ts, pyteal_abi):
    print(f"({algosdk_abi}, {abi_string}, {pyteal_abi_ts}),")

    assert pyteal_abi_ts == abi.type_spec_from_annotation(pyteal_abi)

    assert str(pyteal_abi_ts.new_instance()) == abi_string

    if abi_string in (
        "account",
        "application",
        "asset",
        "txn",
        "pay",
        "keyreg",
        "acfg",
        "axfer",
        "afrz",
        "appl",
    ):
        assert str(pyteal_abi_ts) == abi_string

        with pytest.raises(pt.TealInputError) as tie:
            abi.algosdk_from_type_spec(pyteal_abi_ts)
        assert str(tie.value).startswith(algosdk_abi)

        with pytest.raises(pt.TealInputError) as tie:
            abi.algosdk_from_annotation(pyteal_abi)
        assert str(tie.value).startswith(algosdk_abi)

        return

    assert str(algosdk_abi) == abi_string == str(pyteal_abi_ts)
    assert (
        algosdk_abi
        == algosdk.abi.ABIType.from_string(abi_string)
        == algosdk.abi.ABIType.from_string(str(pyteal_abi_ts))
    )
    assert algosdk_abi == abi.algosdk_from_type_spec(pyteal_abi_ts)
    assert algosdk_abi == abi.algosdk_from_annotation(pyteal_abi)


@pytest.mark.parametrize("case", ABI_TRANSLATION_TEST_CASES)
def test_sdk_abi_translation(case):
    # Errors are strings in the 0th element
    if type(case[0]) is str:
        return
    assert type_spec_from_algosdk(case[0]) == case[2]


@pytest.mark.parametrize("sig_str, sig_args, sig_rets", ABI_SIGNATURE_TYPESPEC_CASES)
def test_sdk_type_specs_from_signature(sig_str, sig_args, sig_rets):
    args, ret = abi.type_specs_from_signature(sig_str)
    assert args == sig_args
    assert ret == sig_rets
