from typing import Literal as L
from pyteal import *


# @Subroutine(TealType.none)
# def myFunction(
#     a: abi.Uint64,
#     b: abi.StaticArray[abi.Uint8, L[10]],
#     c: abi.Tuple2[abi.Uint8, abi.Bool],
# ):
#     pass


# def approval_program():
#     a = abi.Uint64()
#     b = abi.StaticArrayTypeSpec(abi.Uint8TypeSpec, 10).new_instance()
#     c = abi.TupleTypeSpec(abi.Uint8TypeSpec(), abi.BoolTypeSpec()).new_instance()

#     return Seq(myFunction(a, b, c), Approve())


# print(compileTeal(approval_program(), Mode.Application, version=6))
