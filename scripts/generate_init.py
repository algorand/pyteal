import argparse, os, sys


from pyteal import __all__ as static_all


pyi_template = """
from .ast import *
from .ir import *

from .compiler import (
    MAX_TEAL_VERSION,
    MIN_TEAL_VERSION,
    DEFAULT_TEAL_VERSION,
    CompileOptions,
    compileTeal,
)

from .types import TealType
from .errors import TealInternalError, TealTypeError, TealInputError, TealCompileError
from .config import MAX_GROUP_SIZE, NUM_SLOTS

__all__ = [
{}
]
"""

pyi_file = "__init__.pyi"
curr_dir = os.path.dirname(os.path.abspath(__file__))
orig_dir = os.path.relpath("../pyteal", curr_dir)


def generate_tmp():

    all_imports = ",\n".join(['"{}"'.format(s) for s in static_all])

    with open(os.path.join(curr_dir, pyi_file), "w") as f:
        f.write(pyi_template.format(all_imports))


def is_different():
    orig_file = os.path.join(orig_dir, pyi_file)

    if not os.path.exists(orig_file):
        return True

    with open(orig_file) as f:
        orig_lines = f.readlines()
    with open(os.path.join(curr_dir, pyi_file)) as f:
        curr_lines = f.readlines()

    if len(orig_lines) != len(curr_lines):
        return True

    for lidx in range(len(orig_lines)):
        if orig_lines[lidx] != curr_lines[lidx]:
            return True

    return False


def overwrite():
    os.rename(os.path.join(curr_dir, pyi_file), os.path.join(orig_dir, pyi_file))


def delete():
    os.remove(os.path.join(curr_dir, pyi_file))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="Check if the program is different only"
    )
    args = parser.parse_args()

    generate_tmp()

    if args.check:
        if is_different():
            print("File changed!")
            sys.exit(1)
        else:
            print("File same, we chillin")
            delete()
            sys.exit(0)

    overwrite()
