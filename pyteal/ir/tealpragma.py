from pyteal.ir.tealcomponent import TealComponent


class TealPragma(TealComponent):
    _name: str
    _value: str | int

    def __init__(self, version: int | None = None, *, type_track: bool | None = None):
        """Creates an assembler pragma statement.

        Only one of the arguments should be set.

        Args:
            version (optional): Sets the program version.
            type_track (optional): Configures assembler type tracking.
        """
        super().__init__(None)

        if len([x for x in [version, type_track] if x is not None]) != 1:
            raise ValueError("Exactly one of version or type_track must be set")

        if version is not None:
            self._name = "version"
            self._value = version
        elif type_track is not None:
            self._name = "typetrack"
            self._value = "true" if type_track else "false"
        else:
            # Shouldn't happen, just to satisfy type checker
            raise ValueError("Empty pragma statement")

    def assemble(self) -> str:
        return f"#pragma {self._name} {self._value}"

    def __repr__(self) -> str:
        match self._name:
            case "version":
                name = "version"
                value = self._value
            case "typetrack":
                name = "type_track"
                value = self._value == "true"
            case _:
                raise ValueError(f"Unknown pragma name: {self._name}")
        return f"TealPragma({name}={value})"

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealPragma):
            return False
        return self._name == other._name and self._value == other._value


TealPragma.__module__ = "pyteal"
