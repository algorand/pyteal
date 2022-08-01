from typing import TYPE_CHECKING
from enum import Enum

from pyteal.types import TealType, require_type
from pyteal.errors import verifyFieldVersion, verifyProgramVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class JsonRefType(Enum):
    # fmt: off
    #              id |    name   |      type      | min version
    string = (0, "JSONString", TealType.bytes,  7)
    uint64 = (1, "JSONUint64", TealType.uint64, 7)
    object = (2, "JSONObject", TealType.bytes,  7)
    # fmt: on

    def __init__(self, id: int, name: str, type: TealType, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.ret_type = type
        self.min_version = min_version

    def type_of(self) -> TealType:
        return self.ret_type


JsonRefType.__module__ = "pyteal"


class JsonRef(Expr):
    """An expression that accesses the value associated with a given key from a supported utf-8 encoded json object.

    The json object must satisfy a `particular specification <https://github.com/algorand/go-algorand/blob/master/data/transactions/logic/jsonspec.md>`_.
    """

    def __init__(self, type: JsonRefType, json_obj: Expr, key: Expr) -> None:
        super().__init__()

        self.type = type

        require_type(json_obj, TealType.bytes)
        self.json_obj = json_obj

        require_type(key, TealType.bytes)
        self.key = key

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            Op.json_ref.min_version,
            options.version,
            "Program version too low to use op json_ref",
        )

        verifyFieldVersion(self.type.arg_name, self.type.min_version, options.version)

        op = TealOp(self, Op.json_ref, self.type.arg_name)
        return TealBlock.FromOp(options, op, self.json_obj, self.key)

    def __str__(self):
        return "(JsonRef {} {} {})".format(self.type.arg_name, self.json_obj, self.key)

    def type_of(self):
        return self.type.type_of()

    def has_return(self):
        return False

    @classmethod
    def as_string(cls, json_obj: Expr, key: Expr) -> Expr:
        """Access the value of a given key as a string.

        Refer to the `JsonRef` class documentation for valid json specification.

        Args:
            json_obj: The utf-8 encoded json object.
            key: The key to access in the json object.
        """
        return cls(JsonRefType.string, json_obj, key)

    @classmethod
    def as_uint64(cls, json_obj: Expr, key: Expr) -> Expr:
        """Access the value of a given key as a uint64.

        Refer to the `JsonRef` class documentation for valid json specification.

        Args:
            json_obj: The utf-8 encoded json object.
            key: The key to access in the json object.
        """
        return cls(JsonRefType.uint64, json_obj, key)

    @classmethod
    def as_object(cls, json_obj: Expr, key: Expr) -> "JsonRef":
        """Access the value of a given key as a json object.

        Refer to the `JsonRef` class documentation for valid json specification.

        Args:
            json_obj: The utf-8 encoded json object.
            key: The key to access in the json object.
        """
        return cls(JsonRefType.object, json_obj, key)


JsonRef.__module__ = "pyteal"
