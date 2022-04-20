from typing import NamedTuple, List, Literal, Optional, Union, Any, cast
from inspect import isabstract
import pytest

import pyteal as pt
from .util import (
    substringForDecoding,
    int_literal_from_annotation,
    type_spec_from_annotation,
)

options = pt.CompileOptions(version=5)


def test_substringForDecoding():
    class SubstringTest(NamedTuple):
        startIndex: Optional[pt.Expr]
        endIndex: Optional[pt.Expr]
        length: Optional[pt.Expr]
        expected: Union[pt.Expr, Any]

    encoded = pt.Bytes("encoded")

    tests: List[SubstringTest] = [
        SubstringTest(startIndex=None, endIndex=None, length=None, expected=encoded),
        SubstringTest(
            startIndex=None,
            endIndex=None,
            length=pt.Int(4),
            expected=pt.Extract(encoded, pt.Int(0), pt.Int(4)),
        ),
        SubstringTest(
            startIndex=None,
            endIndex=pt.Int(4),
            length=None,
            expected=pt.Substring(encoded, pt.Int(0), pt.Int(4)),
        ),
        SubstringTest(
            startIndex=None,
            endIndex=pt.Int(4),
            length=pt.Int(5),
            expected=pt.TealInputError,
        ),
        SubstringTest(
            startIndex=pt.Int(4),
            endIndex=None,
            length=None,
            expected=pt.Suffix(encoded, pt.Int(4)),
        ),
        SubstringTest(
            startIndex=pt.Int(4),
            endIndex=None,
            length=pt.Int(5),
            expected=pt.Extract(encoded, pt.Int(4), pt.Int(5)),
        ),
        SubstringTest(
            startIndex=pt.Int(4),
            endIndex=pt.Int(5),
            length=None,
            expected=pt.Substring(encoded, pt.Int(4), pt.Int(5)),
        ),
        SubstringTest(
            startIndex=pt.Int(4),
            endIndex=pt.Int(5),
            length=pt.Int(6),
            expected=pt.TealInputError,
        ),
    ]

    for i, test in enumerate(tests):
        if not isinstance(test.expected, pt.Expr):
            with pytest.raises(test.expected):
                substringForDecoding(
                    encoded,
                    startIndex=test.startIndex,
                    endIndex=test.endIndex,
                    length=test.length,
                )
            continue

        expr = substringForDecoding(
            encoded,
            startIndex=test.startIndex,
            endIndex=test.endIndex,
            length=test.length,
        )
        assert expr.type_of() == pt.TealType.bytes
        assert not expr.has_return()

        expected, _ = cast(pt.Expr, test.expected).__teal__(options)
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)


def test_int_literal_from_annotation():
    class IntAnnotationTest(NamedTuple):
        annotation: Any
        expected: Union[int, Any]

    tests: List[IntAnnotationTest] = [
        IntAnnotationTest(annotation=Literal[0], expected=0),
        IntAnnotationTest(annotation=Literal[1], expected=1),
        IntAnnotationTest(annotation=Literal[10], expected=10),
        # In Python 3.8, Literal[True] == Litearl[1], so the below test fails.
        # It's not crucial, so I've commented it out until we no longer support 3.8
        # IntAnnotationTest(annotation=Literal[True], expected=TypeError),
        IntAnnotationTest(annotation=Literal["test"], expected=TypeError),
        IntAnnotationTest(annotation=Literal[b"test"], expected=TypeError),
        IntAnnotationTest(annotation=Literal[None], expected=TypeError),
        IntAnnotationTest(annotation=Literal[0, 1], expected=TypeError),
        IntAnnotationTest(annotation=Literal, expected=TypeError),
    ]

    for i, test in enumerate(tests):
        if type(test.expected) is not int:
            with pytest.raises(test.expected):
                int_literal_from_annotation(test.annotation)
            continue

        actual = int_literal_from_annotation(test.annotation)
        assert actual == test.expected, "Test at index {} failed".format(i)


def test_type_spec_from_annotation():
    class TypeAnnotationTest(NamedTuple):
        annotation: Any
        expected: Union[pt.abi.TypeSpec, Any]

    tests: List[TypeAnnotationTest] = [
        TypeAnnotationTest(annotation=pt.abi.Bool, expected=pt.abi.BoolTypeSpec()),
        TypeAnnotationTest(annotation=pt.abi.Byte, expected=pt.abi.ByteTypeSpec()),
        TypeAnnotationTest(annotation=pt.abi.Uint8, expected=pt.abi.Uint8TypeSpec()),
        TypeAnnotationTest(annotation=pt.abi.Uint16, expected=pt.abi.Uint16TypeSpec()),
        TypeAnnotationTest(annotation=pt.abi.Uint32, expected=pt.abi.Uint32TypeSpec()),
        TypeAnnotationTest(annotation=pt.abi.Uint64, expected=pt.abi.Uint64TypeSpec()),
        TypeAnnotationTest(
            annotation=pt.abi.DynamicArray[pt.abi.Uint32],
            expected=pt.abi.DynamicArrayTypeSpec(pt.abi.Uint32TypeSpec()),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.DynamicArray[pt.abi.Uint64],
            expected=pt.abi.DynamicArrayTypeSpec(pt.abi.Uint64TypeSpec()),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.DynamicArray[pt.abi.DynamicArray[pt.abi.Uint32]],
            expected=pt.abi.DynamicArrayTypeSpec(
                pt.abi.DynamicArrayTypeSpec(pt.abi.Uint32TypeSpec())
            ),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.DynamicArray,
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=pt.abi.StaticArray[pt.abi.Uint32, Literal[0]],
            expected=pt.abi.StaticArrayTypeSpec(pt.abi.Uint32TypeSpec(), 0),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.StaticArray[pt.abi.Uint32, Literal[10]],
            expected=pt.abi.StaticArrayTypeSpec(pt.abi.Uint32TypeSpec(), 10),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.StaticArray[pt.abi.Bool, Literal[500]],
            expected=pt.abi.StaticArrayTypeSpec(pt.abi.BoolTypeSpec(), 500),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.StaticArray[pt.abi.Bool, Literal[-1]],
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=pt.abi.StaticArray[pt.abi.Bool, int],
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=pt.abi.StaticArray,
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=pt.abi.StaticArray[
                pt.abi.StaticArray[pt.abi.Bool, Literal[500]], Literal[5]
            ],
            expected=pt.abi.StaticArrayTypeSpec(
                pt.abi.StaticArrayTypeSpec(pt.abi.BoolTypeSpec(), 500), 5
            ),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.DynamicArray[
                pt.abi.StaticArray[pt.abi.Bool, Literal[500]]
            ],
            expected=pt.abi.DynamicArrayTypeSpec(
                pt.abi.StaticArrayTypeSpec(pt.abi.BoolTypeSpec(), 500)
            ),
        ),
        TypeAnnotationTest(annotation=pt.abi.Tuple, expected=pt.abi.TupleTypeSpec()),
        TypeAnnotationTest(annotation=pt.abi.Tuple0, expected=pt.abi.TupleTypeSpec()),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple1[pt.abi.Uint32],
            expected=pt.abi.TupleTypeSpec(pt.abi.Uint32TypeSpec()),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple1,
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple2[pt.abi.Uint32, pt.abi.Uint16],
            expected=pt.abi.TupleTypeSpec(
                pt.abi.Uint32TypeSpec(), pt.abi.Uint16TypeSpec()
            ),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple2,
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple3[pt.abi.Uint32, pt.abi.Uint16, pt.abi.Byte],
            expected=pt.abi.TupleTypeSpec(
                pt.abi.Uint32TypeSpec(), pt.abi.Uint16TypeSpec(), pt.abi.ByteTypeSpec()
            ),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple3,
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple3[
                pt.abi.Tuple1[pt.abi.Uint32],
                pt.abi.StaticArray[pt.abi.Bool, Literal[55]],
                pt.abi.Tuple2[pt.abi.Uint32, pt.abi.Uint16],
            ],
            expected=pt.abi.TupleTypeSpec(
                pt.abi.TupleTypeSpec(pt.abi.Uint32TypeSpec()),
                pt.abi.StaticArrayTypeSpec(pt.abi.BoolTypeSpec(), 55),
                pt.abi.TupleTypeSpec(pt.abi.Uint32TypeSpec(), pt.abi.Uint16TypeSpec()),
            ),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple4[
                pt.abi.Uint32, pt.abi.Uint16, pt.abi.Byte, pt.abi.Bool
            ],
            expected=pt.abi.TupleTypeSpec(
                pt.abi.Uint32TypeSpec(),
                pt.abi.Uint16TypeSpec(),
                pt.abi.ByteTypeSpec(),
                pt.abi.BoolTypeSpec(),
            ),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple4,
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple5[
                pt.abi.Uint32, pt.abi.Uint16, pt.abi.Byte, pt.abi.Bool, pt.abi.Tuple0
            ],
            expected=pt.abi.TupleTypeSpec(
                pt.abi.Uint32TypeSpec(),
                pt.abi.Uint16TypeSpec(),
                pt.abi.ByteTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.TupleTypeSpec(),
            ),
        ),
        TypeAnnotationTest(
            annotation=pt.abi.Tuple5,
            expected=TypeError,
        ),
        TypeAnnotationTest(
            annotation=List[pt.abi.Uint16],
            expected=TypeError,
        ),
    ]

    for i, test in enumerate(tests):
        if not isinstance(test.expected, pt.abi.TypeSpec):
            with pytest.raises(test.expected):
                type_spec_from_annotation(test.annotation)
            continue

        actual = type_spec_from_annotation(test.annotation)
        assert actual == test.expected, "Test at index {} failed".format(i)


def test_type_spec_from_annotation_is_exhaustive():
    # This test is to make sure there are no new subclasses of BaseType that type_spec_from_annotation
    # is not aware of.

    subclasses = pt.abi.BaseType.__subclasses__()
    while len(subclasses) > 0:
        subclass = subclasses.pop()
        subclasses += subclass.__subclasses__()

        if isabstract(subclass):
            # abstract class type annotations should not be supported
            with pytest.raises(TypeError, match=r"^Unknown annotation origin"):
                type_spec_from_annotation(subclass)
            continue

        try:
            # if subclass is not generic, this will succeed
            type_spec_from_annotation(subclass)
        except TypeError as e:
            # if subclass is generic, we should get an error that is NOT "Unknown annotation origin"
            assert "Unknown annotation origin" not in str(e)
