class LabelReference:
    def __init__(self, label: str) -> None:
        self.label = label

    def addPrefix(self, prefix: str) -> None:
        self.label = prefix + self.label

    def getLabel(self) -> str:
        return self.label

    def __repr__(self) -> str:
        return repr(self.label)

    def __hash__(self) -> int:
        return hash(self.label)

    def __eq__(self, other) -> bool:
        if not isinstance(other, LabelReference):
            return False
        return self.label == other.label
