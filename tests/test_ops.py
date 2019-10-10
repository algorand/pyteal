#!/usr/bin/env python3

import pytest

from pyteal import *

def test_addr():
    Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3THMF")

    with pytest.raises(TealInputError):
        Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3TH")

    with pytest.raises(TealInputError):
        Addr("000000000000000000000000000000000000000000000000000000000")

    with pytest.raises(TealInputError):
        Addr(2)


def test_int():
    Int(232323)

    with pytest.raises(TealInputError):
        Int(6.7)

    with pytest.raises(TealInputError):
        Int(-1)

    with pytest.raises(TealInputError):
        Int(2 ** 64)


def test_arg():
    Arg(0)

    with pytest.raises(TealInputError):
        Arg("k")

    with pytest.raises(TealInputError):
        Arg(-1)

    with pytest.raises(TealInputError):
        Arg(256)


def test_and():
    And(Int(1), Int(1))
    Int(1).And(Int(1))

    with pytest.raises(TealTypeError):
        And(Int(1), Txn.receiver())
