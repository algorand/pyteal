from pyteal.ir.tealcomponent import TealComponent


class TealPragma(TealComponent):
    def __init__(self, version: int):
        super().__init__(None)
        self.version = version

    def assemble(self) -> str:
        return f"#pragma version {self.version}"

    def __repr__(self) -> str:
        return f"TealPragma({self.version})"

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealPragma):
            return False
        return self.version == other.version


TealPragma.__module__ = "pyteal"
