from pyteal import AssetHolding, AssetParam, If, Int, Mode, Return, Seq, compileTeal


def asset_balance():
    # example: APPL_ASSET_BALANCE
    asset_balance = AssetHolding.balance(Int(0), Int(2))
    program = Seq(
        asset_balance, If(asset_balance.hasValue(), Return(Int(1)), Return(Int(0)))
    )
    print(compileTeal(program, Mode.Application))
    # example: APPL_ASSET_BALANCE


def asset_param():
    # example: APPL_ASSET_PARAM
    program = AssetParam.total(Int(0))
    print(compileTeal(program, Mode.Application))
    # example: APPL_ASSET_PARAM
