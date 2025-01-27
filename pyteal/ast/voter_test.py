import pytest

import pyteal as pt
from pyteal.ast.voter import VoterParamField
from pyteal.ast.maybe_test import assert_MaybeValue_equality

avm10Options = pt.CompileOptions(version=10)
avm11Options = pt.CompileOptions(version=11)


@pytest.mark.parametrize(
    "method_name,field_name",
    [
        ("balance", "balance"),
        ("incentiveEligible", "incentive_eligible"),
    ],
)
class TestVoterParam:
    @staticmethod
    def test_voter_param_fields_valid(method_name, field_name):
        arg = pt.Int(1)
        voter_param_method = getattr(pt.VoterParam, method_name)
        expr = voter_param_method(arg)
        assert expr.type_of() == pt.TealType.none

        voter_param_field = VoterParamField[field_name]
        assert expr.value().type_of() == voter_param_field.type_of()

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(arg, pt.Op.int, 1),
                pt.TealOp(expr, pt.Op.voter_params_get, voter_param_field.arg_name),
                pt.TealOp(None, pt.Op.store, expr.slotOk),
                pt.TealOp(None, pt.Op.store, expr.slotValue),
            ]
        )

        supported_options_version = pt.CompileOptions(
            version=voter_param_field.min_version
        )
        actual, _ = expr.__teal__(supported_options_version)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

    @staticmethod
    def test_voter_param_version_checks(method_name, field_name):
        arg = pt.Int(1)
        voter_param_method = getattr(pt.VoterParam, method_name)
        expr = voter_param_method(arg)

        voter_param_field = VoterParamField[field_name]

        def test_unsupported_version(version: int, match: str | None = None):
            with pytest.raises(pt.TealInputError, match=match):
                unsupported_options_version = pt.CompileOptions(version=version)
                expr.__teal__(unsupported_options_version)

        # Test program and field version checks
        program_unsupported_version = pt.ir.Op.voter_params_get.min_version - 1
        program_error_match = "unavailable"
        test_unsupported_version(program_unsupported_version, program_error_match)

        field_unsupported_version = voter_param_field.min_version - 1

        # Since program version dominates, we conditionally check field error message or program error message
        # depending on whether the unsupported field version is less than or equal to the program unsupported
        # version.
        field_error_match = (
            "Program version too low to use field"
            if field_unsupported_version > program_unsupported_version
            else program_error_match
        )
        test_unsupported_version(field_unsupported_version, field_error_match)


def test_VoterParamObject():
    for account in (
        pt.Int(7),
        pt.Addr("QSA6K5MNJPEGO5SDSWXBM3K4UEI3Q2NCPS2OUXVJI5QPCHMVI27MFRSHKI"),
    ):
        obj = pt.VoterParamObject(account)

        assert obj._account is account

        assert_MaybeValue_equality(
            obj.balance(), pt.VoterParam.balance(account), avm11Options
        )
        assert_MaybeValue_equality(
            obj.incentive_eligible(),
            pt.VoterParam.incentiveEligible(account),
            avm11Options,
        )
