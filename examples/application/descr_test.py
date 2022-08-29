from pyteal import *


@ABIReturnSubroutine
def tmp_method(s: abi.String, *, output: abi.String):
    """
    copies input to output

    Args:
        s: The incoming string
        output: The string that gets returned
    """

    return output.set(s)


print(tmp_method.method_spec().dictify())
