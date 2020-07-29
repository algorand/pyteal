from .ast import Expr

def compileTeal(ast: Expr) -> str:
    """Compile a PyTeal expression into TEAL assembly.

    Args:
        ast: The PyTeal expression to assemble.

    Returns:
        str: A TEAL assembly program compiled from the input expression.
    """
    teal = ast.__teal__()

    lines = ["#pragma version 1"]
    lines += [" ".join(i) for i in teal]
    return "\n".join(lines)
