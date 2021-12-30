from .bytes import Bytes
from .int import Int


def get_teal_type(obj):
    if isinstance(obj, str):
        return Bytes(obj)
    elif isinstance(obj, int):
        return Int(obj)
    else:
        return obj
