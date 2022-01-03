import base64

from typing import Union, List, Dict, cast
from collections import OrderedDict
from algosdk import encoding

from ..ir import (
    Op,
    TealOp,
    TealComponent,
)
from ..util import unescapeStr, correctBase32Padding
from ..errors import TealInternalError

intEnumValues = {
    # OnComplete values
    "NoOp": 0,
    "OptIn": 1,
    "CloseOut": 2,
    "ClearState": 3,
    "UpdateApplication": 4,
    "DeleteApplication": 5,
    # TxnType values
    "unknown": 0,
    "pay": 1,
    "keyreg": 2,
    "acfg": 3,
    "axfer": 4,
    "afrz": 5,
    "appl": 6,
}


def extractIntValue(op: TealOp) -> Union[str, int]:
    """Extract the constant value being loaded by a TealOp whose op is Op.int.

    Returns:
        If the op is loading a template variable, returns the name of the variable as a string.
        Otherwise, returns the integer that the op is loading.
    """
    if len(op.args) != 1 or type(op.args[0]) not in (int, str):
        raise TealInternalError("Unexpected args in int opcode: {}".format(op.args))

    value = cast(Union[str, int], op.args[0])
    if type(value) is int or cast(str, value).startswith("TMPL_"):
        return value
    if value not in intEnumValues:
        raise TealInternalError("Int constant not recognized: {}".format(value))
    return intEnumValues[cast(str, value)]


def extractBytesValue(op: TealOp) -> Union[str, bytes]:
    """Extract the constant value being loaded by a TealOp whose op is Op.byte.

    Returns:
        If the op is loading a template variable, returns the name of the variable as a string.
        Otherwise, returns the byte string that the op is loading.
    """
    if len(op.args) != 1 or type(op.args[0]) is not str:
        raise TealInternalError("Unexpected args in byte opcode: {}".format(op.args))

    value = op.args[0]
    if value.startswith("TMPL_"):
        return value
    if value.startswith('"') and value.endswith('"'):
        return unescapeStr(value).encode("utf-8")
    if value.startswith("0x"):
        return bytes.fromhex(value[2:])
    if value.startswith("base32(") and value.endswith(")"):
        return base64.b32decode(correctBase32Padding(value[len("base32(") : -1]))
    if value.startswith("base64(") and value.endswith(")"):
        return base64.b64decode(value[len("base64(") : -1])

    raise TealInternalError("Unexpected format for byte value: {}".format(value))


def extractAddrValue(op: TealOp) -> Union[str, bytes]:
    """Extract the constant value being loaded by a TealOp whose op is Op.addr.

    Returns:
        If the op is loading a template variable, returns the name of the variable as a string.
        Otherwise, returns the bytes of the public key of the address that the op is loading.
    """
    if len(op.args) != 1 or type(op.args[0]) != str:
        raise TealInternalError("Unexpected args in addr opcode: {}".format(op.args))

    value = cast(str, op.args[0])
    if not value.startswith("TMPL_"):
        value = encoding.decode_address(value)
    return value


def extractMethodSigValue(op: TealOp) -> bytes:
    """Extract the constant value being loaded by a TealOp whose op is Op.method.

    Returns:
        The bytes of method selector computed from the method signature that the op is loading.
    """
    if len(op.args) != 1 or type(op.args[0]) != str:
        raise TealInternalError("Unexpected args in method opcode: {}".format(op.args))

    methodSignature = cast(str, op.args[0])
    if methodSignature[0] == methodSignature[-1] and methodSignature.startswith('"'):
        methodSignature = methodSignature[1:-1]
    else:
        raise TealInternalError(
            "Method signature opcode error: signatue {} not wrapped with double-quotes".format(
                methodSignature
            )
        )
    methodSelector = encoding.checksum(bytes(methodSignature, "utf-8"))[:4]
    return methodSelector


def createConstantBlocks(ops: List[TealComponent]) -> List[TealComponent]:
    """Convert TEAL code from using pseudo-ops for constants to using assembled constant blocks.

    This conversion will assemble constants to be as space-efficient as possible.

    Args:
        ops: A list of TealComponents to convert.

    Returns:
        A list of TealComponent that are functionally the same as the input, but with all constants
        loaded either through blocks or the `pushint`/`pushbytes` single-use ops.
    """
    intFreqs: Dict[Union[str, int], int] = OrderedDict()
    byteFreqs: Dict[Union[str, bytes], int] = OrderedDict()

    for op in ops:
        if not isinstance(op, TealOp):
            continue

        basicOp = op.getOp()

        if basicOp == Op.int:
            intValue = extractIntValue(op)
            intFreqs[intValue] = intFreqs.get(intValue, 0) + 1
        elif basicOp == Op.byte:
            byteValue = extractBytesValue(op)
            byteFreqs[byteValue] = byteFreqs.get(byteValue, 0) + 1
        elif basicOp == Op.addr:
            addrValue = extractAddrValue(op)
            byteFreqs[addrValue] = byteFreqs.get(addrValue, 0) + 1
        elif basicOp == Op.method_signature:
            methodValue = extractMethodSigValue(op)
            byteFreqs[methodValue] = byteFreqs.get(methodValue, 0) + 1

    assembled: List[TealComponent] = []

    # because we used OrderedDicts and python sorting is stable, constants with the same frequency
    # will remain in the same order, i.e. first defined, first in block
    sortedInts = sorted(intFreqs, key=lambda x: intFreqs[x], reverse=True)
    sortedBytes = sorted(byteFreqs, key=lambda x: byteFreqs[x], reverse=True)

    # Use Op.pushint if the constant does not occur in the top 4 most frequent and is smaller than
    # 2 ** 7 to improve performance and save block space.
    intBlock = [
        val
        for i, val in enumerate(sortedInts)
        if intFreqs[val] > 1 and (i < 4 or isinstance(val, str) or val >= 2 ** 7)
    ]

    byteBlock = [
        ("0x" + b.hex()) if type(b) is bytes else cast(str, b)
        for b in sortedBytes
        if byteFreqs[b] > 1
    ]

    if len(intBlock) != 0:
        assembled.append(TealOp(None, Op.intcblock, *intBlock))

    if len(byteBlock) != 0:
        assembled.append(TealOp(None, Op.bytecblock, *byteBlock))

    for op in ops:
        if isinstance(op, TealOp):
            basicOp = op.getOp()

            if basicOp == Op.int:
                intValue = extractIntValue(op)
                if intValue not in intBlock:
                    assembled.append(
                        TealOp(op.expr, Op.pushint, intValue, "//", *op.args)
                    )
                    continue

                index = intBlock.index(intValue)
                if index == 0:
                    assembled.append(TealOp(op.expr, Op.intc_0, "//", *op.args))
                elif index == 1:
                    assembled.append(TealOp(op.expr, Op.intc_1, "//", *op.args))
                elif index == 2:
                    assembled.append(TealOp(op.expr, Op.intc_2, "//", *op.args))
                elif index == 3:
                    assembled.append(TealOp(op.expr, Op.intc_3, "//", *op.args))
                else:
                    assembled.append(TealOp(op.expr, Op.intc, index, "//", *op.args))
                continue

            if (
                basicOp == Op.byte
                or basicOp == Op.addr
                or basicOp == Op.method_signature
            ):
                if basicOp == Op.byte:
                    byteValue = extractBytesValue(op)
                elif basicOp == Op.addr:
                    byteValue = extractAddrValue(op)
                elif basicOp == Op.method_signature:
                    byteValue = extractMethodSigValue(op)
                else:
                    raise TealInternalError(
                        "Expect a byte-like constant opcode, get {}".format(op)
                    )

                if byteFreqs[byteValue] == 1:
                    encodedValue = (
                        ("0x" + byteValue.hex())
                        if type(byteValue) is bytes
                        else cast(str, byteValue)
                    )
                    assembled.append(
                        TealOp(op.expr, Op.pushbytes, encodedValue, "//", *op.args)
                    )
                    continue

                index = sortedBytes.index(byteValue)
                if index == 0:
                    assembled.append(TealOp(op.expr, Op.bytec_0, "//", *op.args))
                elif index == 1:
                    assembled.append(TealOp(op.expr, Op.bytec_1, "//", *op.args))
                elif index == 2:
                    assembled.append(TealOp(op.expr, Op.bytec_2, "//", *op.args))
                elif index == 3:
                    assembled.append(TealOp(op.expr, Op.bytec_3, "//", *op.args))
                else:
                    assembled.append(TealOp(op.expr, Op.bytec, index, "//", *op.args))
                continue

        assembled.append(op)

    return assembled
