from typing import Iterable
from build.lib.pyteal.ast.txn import TxnExprBuilder
from pyteal import *


class SerializedExpr:
    def __init__(self, name: str, args: list["SerializedExpr"]):
        self.name = name
        self.args = args

    @staticmethod
    def from_expr(e: Expr) -> "SerializedExpr":
        nested_args: list[SerializedExpr] = []
        name: str = ""

        match e:
            case Seq() | Cond() | NaryExpr():
                for arg in e.args:
                    if isinstance(arg, Iterable):
                        for x in arg:
                            nested_args.append(SerializedExpr.from_expr(x))
                    else:
                        nested_args.append(SerializedExpr.from_expr(arg))
            case BinaryExpr():
                nested_args.append(SerializedExpr.from_expr(e.argLeft))
                nested_args.append(SerializedExpr.from_expr(e.argRight))
            case Assert():
                for cond in e.cond:
                    nested_args.append(SerializedExpr.from_expr(cond))
            case App():
                field = str(e.field).split(".")[1]
                name = "App." + field
                for arg in e.args:
                    nested_args.append(SerializedExpr.from_expr(arg))
            case Int():
                nested_args.append(SerializedExpr.from_expr(e.value))
            case Bytes():
                nested_args.append(
                    SerializedExpr.from_expr(e.byte_str.replace('"', ""))
                )
            case TxnExpr():
                field = str(e.field).split(".")[1]
                name = "Txn." + field
            case UnaryExpr():
                nested_args.append(SerializedExpr.from_expr(e.arg))
            case TxnaExpr():
                field = str(e.field).split(".")[1]
                name = f"Txna.{field}"
                nested_args.append(SerializedExpr.from_expr(Int(e.index)))
            case Return():
                nested_args.append(SerializedExpr.from_expr(e.value))
            case If():
                nested_args.append(SerializedExpr.from_expr(e.cond))
                nested_args.append(SerializedExpr.from_expr(e.thenBranch))
                if e.elseBranch is not None:
                    nested_args.append(SerializedExpr.from_expr(e.elseBranch))
            case Global():
                field = str(e.field).split(".")[1]
                name = "Global." + field
            case MaybeValue():
                if len(e.immediate_args) > 0:
                    nested_args.append(SerializedExpr.from_expr(e.immediate_args))

                for arg in e.args:
                    nested_args.append(SerializedExpr.from_expr(arg))

                if e.op.name == "app_local_get_ex":
                    name = "App.localGetEx"
                elif e.op.name == "app_global_get_ex":
                    name = "App.globalGetEx"
            case ScratchSlot():
                name = "ScratchSlot"
            case ScratchStackStore():
                name = "ScratchStackStore"
                if e.slot is not None:
                    nested_args.append(SerializedExpr.from_expr(e.slot))
            case ScratchLoad():
                name = "ScratchLoad"
                if e.slot is not None:
                    nested_args.append(SerializedExpr.from_expr(e.slot))
            case EnumInt():
                name = "OnComplete." + e.name
            case _:
                # print(f"unhandled: {e.__class__}")
                pass

        if name == "":
            if hasattr(e, "op"):
                name = e.op.name.title().replace("_", "")
                if name == "LogicAnd":
                    name = "And"
            elif len(nested_args) == 0:
                name = e[1] if type(e) is tuple else str(e)
            else:
                name = e.__class__.__name__

        return SerializedExpr(name, nested_args)

    @staticmethod
    def undictify(d: dict) -> "SerializedExpr":
        return SerializedExpr(
            d["name"], [SerializedExpr.undictify(arg) for arg in d["args"]]
        )

    def to_expr(self) -> Expr:
        if self.name == "Int":
            return Int(int(self.args[0].name))
        elif self.name == "Bytes":
            return Bytes(str(self.args[0].name))
        elif self.name == "Cond":
            args = [arg.to_expr() for arg in self.args]
            return Cond(*[[args[idx], args[idx + 1]] for idx in range(0, len(args), 2)])
        elif self.name == "Txn":
            field_name = self.args[0].name.split(".")[1]
            return getattr(Txn, field_name)()
        elif self.name.startswith("Txna"):
            field_name = self.name.split(".")[1]
            return getattr(Txn, field_name)[self.args[0].to_expr()]
        elif self.name.startswith("OnComplete"):
            return eval(self.name)

        return eval(self.name)(*[arg.to_expr() for arg in self.args])

    def dictify(self) -> dict:
        return {"name": self.name, "args": [a.dictify() for a in self.args]}


if __name__ == "__main__":
    import json
    from application.vote import approval_program

    se = SerializedExpr.from_expr(approval_program())
    print(json.dumps(se.dictify()))
    print(se.to_expr())
