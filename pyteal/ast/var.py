from pyteal import * 


class Var(Expr):
    def __init__(self, val: Expr, type_cast=TealType):

        got = val.type_of()
        match got:
            case TealType.uint64:
                match type_cast:
                    case TealType.bytes:
                        val = Btoi(val)
                    case TealType.uint64 | TealType.anytype:
                        pass
                    case _:
                        raise TealTypeError(type_cast, got)
            case TealType.bytes:
                match type_cast:
                    case TealType.uint64:
                        val = Itob(val)
                    case TealType.bytes | TealType.anytype:
                        pass
                    case _:
                        raise TealTypeError(type_cast, got)
            case TealType.anytype:
                pass
            case _:
                raise TealTypeError(type_cast, got)



        self.val = val
        self.slot = ScratchSlot()
        self.type = val.type_of()
        self.has_stored = False

    def __str__(self):
        if self.has_stored:
            return self.slot.load(self.type).__str__()
        else:
            return self.slot.store(self.val).__str__()

    def __teal__(self, options: CompileOptions):
        if not self.has_stored:
            self.has_stored = True
            return self.slot.store(self.val).__teal__(options)

    def load(self):
        return self.slot.load(self.type)

    def store(self, val: Expr):
        self.val = val
        return self.slot.store(val)

    def has_return(self):
        return False

    def type_of(self):
        if self.has_stored:
            return self.val.type_of()
        else:
            return TealType.none
