from abc import abstractmethod
from typing import cast
from pyteal.ast.abi.uint import Uint, UintTypeSpec


class ReferenceTypeSpec(UintTypeSpec):
    @abstractmethod
    def __init__(self) -> None:
        return super().__init__(8)

    @abstractmethod
    def new_instance(self) -> "ReferenceType":
        pass


ReferenceTypeSpec.__module__ = "pyteal"


class ReferenceType(Uint):
    @abstractmethod
    def __init__(self, spec: ReferenceTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> ReferenceTypeSpec:
        return cast(ReferenceTypeSpec, super().type_spec())


ReferenceType.__module__ = "pyteal"


class AccountTypeSpec(ReferenceTypeSpec):
    def __init__(self):
        super().__init__()

    def new_instance(self) -> "Account":
        return Account()

    def __str__(self) -> str:
        return "account"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AccountTypeSpec)


AccountTypeSpec.__module__ = "pyteal"


class Account(ReferenceType):
    def __init__(self) -> None:
        super().__init__(AccountTypeSpec())


Account.__module__ = "pyteal"


class AssetTypeSpec(ReferenceTypeSpec):
    def __init__(self):
        super().__init__()

    def new_instance(self) -> "Asset":
        return Asset()

    def __str__(self) -> str:
        return "asset"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AssetTypeSpec)


AssetTypeSpec.__module__ = "pyteal"


class Asset(ReferenceType):
    def __init__(self) -> None:
        super().__init__(AssetTypeSpec())


Asset.__module__ = "pyteal"


class ApplicationTypeSpec(ReferenceTypeSpec):
    def __init__(self):
        super().__init__()

    def new_instance(self) -> "Application":
        return Application()

    def __str__(self) -> str:
        return "application"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ApplicationTypeSpec)


ApplicationTypeSpec.__module__ = "pyteal"


class Application(ReferenceType):
    def __init__(self) -> None:
        super().__init__(ApplicationTypeSpec())


Application.__module__ = "pyteal"
