from .local_optimization import LocalOptimization, applyLocalOptimizationToList
from .duplicate import detectDuplicatesInBlock

class OptimizeOptions:
    """An object which specifies optimizations to be performed."""

    useDup: bool

    def __init__(self, *, useDup: bool = False):
        """Create a new OptimizeOptions object.

        Args:
            useDup (optional): When True, the `dup` and `dup2` opcodes will be used when possible to
                reduce program size. Defaults to False.
        """
        self.useDup = useDup
