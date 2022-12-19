import pytest

import pyteal as pt
from pyteal.ast.acct import AccountParamField
from pyteal.ast.maybe_test import assert_MaybeValue_equality

avm6Options = pt.CompileOptions(version=6)
avm8Options = pt.CompileOptions(version=8)


@pytest.mark.parametrize(
    "method_name,field_name",
    [
        ("balance", "balance"),
        ("minBalance", "min_balance"),
        ("authAddr", "auth_addr"),
        ("totalNumUint", "total_num_uint"),
        ("totalNumByteSlice", "total_num_byte_slice"),
        ("totalExtraAppPages", "total_extra_app_pages"),
        ("totalAppsCreated", "total_apps_created"),
        ("totalAppsOptedIn", "total_apps_opted_in"),
        ("totalAssetsCreated", "total_assets_created"),
        ("totalAssets", "total_assets"),
        ("totalBoxes", "total_boxes"),
        ("totalBoxBytes", "total_box_bytes"),
    ],
)
class TestAcctParam:
    @staticmethod
    def test_acct_param_fields_valid(method_name, field_name):
        arg = pt.Int(1)
        account_param_method = getattr(pt.AccountParam, method_name)
        expr = account_param_method(arg)
        assert expr.type_of() == pt.TealType.none

        account_param_field = AccountParamField[field_name]
        assert expr.value().type_of() == account_param_field.type_of()

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(arg, pt.Op.int, 1),
                pt.TealOp(expr, pt.Op.acct_params_get, account_param_field.arg_name),
                pt.TealOp(None, pt.Op.store, expr.slotOk),
                pt.TealOp(None, pt.Op.store, expr.slotValue),
            ]
        )

        supported_options_version = pt.CompileOptions(
            version=account_param_field.min_version
        )
        actual, _ = expr.__teal__(supported_options_version)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

    @staticmethod
    def test_acct_param_version_checks(method_name, field_name):
        arg = pt.Int(1)
        account_param_method = getattr(pt.AccountParam, method_name)
        expr = account_param_method(arg)

        account_param_field = AccountParamField[field_name]

        def test_unsupported_version(version: int, match: str | None = None):
            with pytest.raises(pt.TealInputError, match=match):
                unsupported_options_version = pt.CompileOptions(version=version)
                expr.__teal__(unsupported_options_version)

        # Test program and field version checks
        program_unsupported_version = pt.ir.Op.acct_params_get.min_version - 1
        program_error_match = "unavailable"
        test_unsupported_version(program_unsupported_version, program_error_match)

        field_unsupported_version = account_param_field.min_version - 1

        # Since program version dominates, we conditionally check field error message or program error message
        # depending on whether the unsupported field version is less than or equal to the program unsupported
        # version.
        field_error_match = (
            "Program version too low to use field"
            if field_unsupported_version > program_unsupported_version
            else program_error_match
        )
        test_unsupported_version(field_unsupported_version, field_error_match)


def test_AccountParamObject():
    for account in (
        pt.Int(7),
        pt.Addr("QSA6K5MNJPEGO5SDSWXBM3K4UEI3Q2NCPS2OUXVJI5QPCHMVI27MFRSHKI"),
    ):
        obj = pt.AccountParamObject(account)

        assert obj._account is account

        assert_MaybeValue_equality(
            obj.balance(), pt.AccountParam.balance(account), avm6Options
        )
        assert_MaybeValue_equality(
            obj.min_balance(), pt.AccountParam.minBalance(account), avm6Options
        )
        assert_MaybeValue_equality(
            obj.auth_address(), pt.AccountParam.authAddr(account), avm6Options
        )

        assert_MaybeValue_equality(
            obj.total_num_uint(), pt.AccountParam.totalNumUint(account), avm8Options
        )
        assert_MaybeValue_equality(
            obj.total_num_byte_slice(),
            pt.AccountParam.totalNumByteSlice(account),
            avm8Options,
        )
        assert_MaybeValue_equality(
            obj.total_extra_app_pages(),
            pt.AccountParam.totalExtraAppPages(account),
            avm8Options,
        )
        assert_MaybeValue_equality(
            obj.total_apps_created(),
            pt.AccountParam.totalAppsCreated(account),
            avm8Options,
        )
        assert_MaybeValue_equality(
            obj.total_apps_opted_in(),
            pt.AccountParam.totalAppsOptedIn(account),
            avm8Options,
        )
        assert_MaybeValue_equality(
            obj.total_assets_created(),
            pt.AccountParam.totalAssetsCreated(account),
            avm8Options,
        )
        assert_MaybeValue_equality(
            obj.total_assets(), pt.AccountParam.totalAssets(account), avm8Options
        )
        assert_MaybeValue_equality(
            obj.total_boxes(), pt.AccountParam.totalBoxes(account), avm8Options
        )
        assert_MaybeValue_equality(
            obj.total_box_bytes(), pt.AccountParam.totalBoxBytes(account), avm8Options
        )
