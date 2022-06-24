from typing import TYPE_CHECKING
from enum import Enum

from pyteal.types import TealType, require_type
from pyteal.errors import TealTypeError, verifyFieldVersion, verifyTealVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr
from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class JsonRefType(Enum):
    # fmt: off
    #              id |    name   |      type      | min version
    json_string = (0, "JSONString", TealType.bytes,  7)
    json_uint64 = (1, "JSONUint64", TealType.uint64, 7)
    json_object = (2, "JSONObject", TealType.bytes,  7)
    # fmt: on

    def __init__(self, id: int, name: str, type: TealType, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.ret_type = type
        self.min_version = min_version

    def type_of(self) -> TealType:
        return self.ret_type


JsonRefType.__module__ = "pyteal"


class JsonRef(LeafExpr):
    """An expression that accesses a key from a supported utf-8 encoded json object.

    The json object must satisfy a [particular specification](https://github.com/algorand/go-algorand/blob/master/data/transactions/logic/jsonspec.md).
    """

    json_string = JsonRefType.json_string
    json_uint64 = JsonRefType.json_uint64
    json_object = JsonRefType.json_object

    def __init__(self, type: JsonRefType, json_obj: Expr, key: Expr) -> None:
        super().__init__()

        if not isinstance(type, JsonRefType):
            raise TealTypeError(type, JsonRefType)
        self.type = type

        require_type(json_obj, TealType.bytes)
        self.json_obj = json_obj

        require_type(key, TealType.bytes)
        self.key = key

    def __teal__(self, options: "CompileOptions"):
        verifyTealVersion(
            Op.json_ref.min_version,
            options.version,
            "TEAL version too low to use op json_ref",
        )

        verifyFieldVersion(self.type.arg_name, self.type.min_version, options.version)

        op = TealOp(self, Op.json_ref, self.type.arg_name)
        return TealBlock.FromOp(options, op, self.json_obj, self.key)

    def __str__(self):
        return "(JsonRef {})".format(self.type.arg_name)

    def type_of(self):
        return self.type.type_of()


JsonRef.__module__ = "pyteal"
