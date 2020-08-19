from .tealcomponent import TealComponent

class TealLabel(TealComponent):

    def __init__(self, label: str) -> None:
        self.label = label
    
    def assemble(self) -> str:
        return self.label + ":"
    
    def __repr__(self) -> str:
        return "TealLabel({})".format(self.label.__repr__())
    
    def __hash__(self) -> int:
        return self.label.__hash__()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealLabel):
            return False
        return self.label == other.label

TealLabel.__module__ = "pyteal"
