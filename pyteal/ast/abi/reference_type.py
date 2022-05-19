from pyteal.ast.abi.uint import Uint, UintTypeSpec


class AccountTypeSpec(UintTypeSpec):
    def __init__(self):
        super().__init__(8)

    def new_instance(self) -> "Account":
        return Account()

    def __str__(self) -> str:
        return "account"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AccountTypeSpec)


AccountTypeSpec.__module__ = "pyteal"


class Account(Uint):
    def __init__(self) -> None:
        super().__init__(AccountTypeSpec())


Account.__module__ = "pyteal"


class AssetTypeSpec(UintTypeSpec):
    def __init__(self):
        super().__init__(8)

    def new_instance(self) -> "Asset":
        return Asset()

    def __str__(self) -> str:
        return "asset"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AssetTypeSpec)


AssetTypeSpec.__module__ = "pyteal"


class Asset(Uint):
    def __init__(self) -> None:
        super().__init__(AssetTypeSpec())


Asset.__module__ = "pyteal"


class ApplicationTypeSpec(UintTypeSpec):
    def __init__(self):
        super().__init__(8)

    def new_instance(self) -> "Application":
        return Application()

    def __str__(self) -> str:
        return "application"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ApplicationTypeSpec)


ApplicationTypeSpec.__module__ = "pyteal"


class Application(Uint):
    def __init__(self) -> None:
        super().__init__(ApplicationTypeSpec())


Application.__module__ = "pyteal"
