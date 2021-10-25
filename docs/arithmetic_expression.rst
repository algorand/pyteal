.. _arithmetic_expressions:

Arithmetic Operations
=====================

An arithmetic expression is an expression that results in a :code:`TealType.uint64` value.
In PyTeal, arithmetic expressions include integer and boolean operators (booleans are the integers
`0` or `1`). The table below summarized all arithmetic expressions in PyTeal.

=================================== ============== ================================================= ===========================
Operator                            Overloaded     Semantics                                         Example
=================================== ============== ================================================= ===========================
:any:`Lt(a, b) <Lt>`                :code:`a < b`  `1` if `a` is less than `b`, `0` otherwise        :code:`Int(1) < Int(5)`
:any:`Gt(a, b) <Gt>`                :code:`a > b`  `1` if `a` is greater than `b`, `0` otherwise     :code:`Int(1) > Int(5)`
:any:`Le(a, b) <Le>`                :code:`a <= b` `1` if `a` is no greater than `b`, `0` otherwise  :code:`Int(1) <= Int(5)`
:any:`Ge(a, b) <Ge>`                :code:`a >= b` `1` if `a` is no less than `b`, `0` otherwise     :code:`Int(1) >= Int(5)`
:any:`Add(a, b) <Add>`              :code:`a + b`  `a + b`, error (panic) if overflow                :code:`Int(1) + Int(5)`
:any:`Minus(a, b) <Minus>`          :code:`a - b`  `a - b`, error if underflow                       :code:`Int(5) - Int(1)`
:any:`Mul(a, b) <Mul>`              :code:`a * b`  `a * b`, error if overflow                        :code:`Int(2) * Int(3)`
:any:`Div(a, b) <Div>`              :code:`a / b`  `a / b`, error if divided by zero                 :code:`Int(3) / Int(2)`
:any:`Mod(a, b) <Mod>`              :code:`a % b`  `a % b`, modulo operation                         :code:`Int(7) % Int(3)`
:any:`Exp(a, b) <Exp>`              :code:`a ** b` `a ** b`, exponent operation                      :code:`Int(7) ** Int(3)`
:any:`Eq(a, b) <Eq>`                :code:`a == b` `1` if `a` equals `b`, `0` otherwise              :code:`Int(7) == Int(7)`
:any:`Neq(a, b) <Neq>`              :code:`a != b` `0` if `a` equals `b`, `1` otherwise              :code:`Int(7) != Int(7)`
:any:`And(a, b) <pyteal.And>`                      `1` if `a > 0 && b > 0`, `0` otherwise            :code:`And(Int(1), Int(1))`
:any:`Or(a, b) <pyteal.Or>`                        `1` if `a > 0 || b > 0`, `0` otherwise            :code:`Or(Int(1), Int(0))`
:any:`Not(a) <pyteal.Not>`                         `1` if `a` equals `0`, `0` otherwise              :code:`Not(Int(0))`
:any:`BitwiseAnd(a,b) <BitwiseAnd>` :code:`a & b`  `a & b`, bitwise and operation                    :code:`Int(1) & Int(3)`
:any:`BitwiseOr(a,b) <BitwiseOr>`   :code:`a | b`  `a | b`, bitwise or operation                     :code:`Int(2) | Int(5)`
:any:`BitwiseXor(a,b) <BitwiseXor>` :code:`a ^ b`  `a ^ b`, bitwise xor operation                    :code:`Int(3) ^ Int(7)`
:any:`BitwiseNot(a) <BitwiseNot>`   :code:`~a`     `~a`, bitwise complement operation                :code:`~Int(1)`
=================================== ============== ================================================= ===========================

Most of the above operations take two :code:`TealType.uint64` values as inputs.
In addition, :code:`Eq(a, b)` (:code:`==`) and :code:`Neq(a, b)` (:code:`!=`) also work for byte slices.
For example, :code:`Arg(0) == Arg(1)` and :code:`Arg(0) != Arg(1)` are valid PyTeal expressions.

Both :code:`And` and :code:`Or` also support more than 2 arguments when called as functions:

 * :code:`And(a, b, ...)`
 * :code:`Or(a, b, ...)`

The associativity and precedence of the overloaded Python arithmetic operators are the same as the
`original python operators <https://docs.python.org/3/reference/expressions.html#operator-precedence>`_ . For example:

 * :code:`Int(1) + Int(2) + Int(3)` is equivalent to :code:`Add(Add(Int(1), Int(2)), Int(3))`
 * :code:`Int(1) + Int(2) * Int(3)` is equivalent to :code:`Add(Int(1), Mul(Int(2), Int(3)))` 

Byteslice Arithmetic
--------------------

Byteslice arithemetic is available for Teal V4 and above. 
Byteslice arithmetic operators allow up to 512-bit arithmetic.
In PyTeal, byteslice arithmetic expressions include 
:code:`TealType.Bytes` values as arguments (with the exception of :code:`BytesZero`)
and must be 64 bytes or less.
The table below summarizes the byteslize arithmetic operations in PyTeal.

======================================= ======================= ====================================================================== ==================
Operator                                Return Type             Example                                                                Example Result
======================================= ======================= ====================================================================== ==================
:any:`BytesLt(a, b) <BytesLt>`          :code:`TealType.uint64` :code:`BytesLt(Bytes("base16", "0xFF"), Bytes("base16", "0xFE"))`      :code:`0`
:any:`BytesGt(a, b) <BytesGt>`          :code:`TealType.uint64` :code:`BytesGt(Bytes("base16", "0xFF"), Bytes("base16", "0xFE"))`      :code:`1`
:any:`BytesLe(a, b) <BytesLe>`          :code:`TealType.uint64` :code:`BytesLe(Bytes("base16", "0xFF"), Bytes("base16", "0xFE"))`      :code:`0`
:any:`BytesGe(a, b) <BytesGe>`          :code:`TealType.uint64` :code:`BytesGe(Bytes("base16", "0xFF"), Bytes("base16", "0xFE"))`      :code:`1`
:any:`BytesEq(a, b) <BytesEq>`          :code:`TealType.uint64` :code:`BytesEq(Bytes("base16", "0xFF"), Bytes("base16", "0xFF"))`      :code:`1`
:any:`BytesNeq(a, b) <BytesNeq>`        :code:`TealType.uint64` :code:`BytesNeq(Bytes("base16", "0xFF"), Bytes("base16", "0xFF"))`     :code:`0`
:any:`BytesAdd(a, b) <BytesAdd>`        :code:`TealType.Bytes`  :code:`BytesAdd(Bytes("base16", "0xFF"), Bytes("base16", "0xFE"))`     :code:`0x01FD`
:any:`BytesMinus(a, b) <BytesMinus>`    :code:`TealType.Bytes`  :code:`BytesMinus(Bytes("base16", "0xFF"), Bytes("base16", "0xFE"))`   :code:`0x01`
:any:`BytesMul(a, b) <BytesMul>`        :code:`TealType.Bytes`  :code:`BytesMul(Bytes("base16", "0xFF"), Bytes("base16", "0xFE"))`     :code:`0xFD02`
:any:`BytesDiv(a, b) <BytesDiv>`        :code:`TealType.Bytes`  :code:`BytesDiv(Bytes("base16", "0xFF"), Bytes("base16", "0x11"))`     :code:`0x0F`
:any:`BytesMod(a, b) <BytesMod>`        :code:`TealType.Bytes`  :code:`BytesMod(Bytes("base16", "0xFF"), Bytes("base16", "0x12"))`     :code:`0x03`
:any:`BytesAnd(a, b) <pyteal.BytesAnd>` :code:`TealType.Bytes`  :code:`BytesAnd(Bytes("base16", "0xBEEF"), Bytes("base16", "0x1337"))` :code:`0x1227`
:any:`BytesOr(a, b) <pyteal.BytesOr>`   :code:`TealType.Bytes`  :code:`BytesOr(Bytes("base16", "0xBEEF"), Bytes("base16", "0x1337"))`  :code:`0xBFFF`
:any:`BytesXor(a, b) <pyteal.BytesXor>` :code:`TealType.Bytes`  :code:`BytesXor(Bytes("base16", "0xBEEF"), Bytes("base16", "0x1337"))` :code:`0xADD8`
:any:`BytesNot(a) <pyteal.BytesNot>`    :code:`TealType.Bytes`  :code:`BytesNot(Bytes("base16", "0xFF00"))`                            :code:`0x00FF`
:any:`BytesZero(a) <pyteal.BytesZero>`  :code:`TealType.Bytes`  :code:`BytesZero(Int(4))`                                              :code:`0x00000000`
======================================= ======================= ====================================================================== ==================

Currently, byteslice arithmetic operations are not overloaded, and must be explicitly called.

.. _bit_and_byte_manipulation:

Bit and Byte Operations
-----------------------

In addition to the standard arithmetic operators above, PyTeal also supports operations that
manipulate the individual bits and bytes of PyTeal values.

To use these operations, you'll need to provide an index specifying which bit or byte to access.
These indexes have different meanings depending on whether you are manipulating integers or byte slices:

* For integers, bit indexing begins with low-order bits. For example, the bit at index 4 of the integer
  16 (:code:`000...0001000` in binary) is 1. Every other index has a bit value of 0. Any index less
  than 64 is valid, regardless of the integer's value.

  Byte indexing is not supported for integers.

* For byte strings, bit indexing begins at the first bit. For example, the bit at index 0 of the base16
  byte string :code:`0xf0` (:code:`11110000` in binary) is 1. Any index less than 4 has a bit
  value of 1, and any index 4 or greater has a bit value of 0. Any index less than 8 times the length
  of the byte string is valid.
  
  Likewise, byte indexing begins at the first byte of the string. For example, the byte at index 0 of
  that the base16 string :code:`0xff00` (:code:`1111111100000000` in binary) is 255 (:code:`111111111` in binary),
  and the byte at index 1 is 0. Any index less than the length of the byte string is valid.

Bit Manipulation
~~~~~~~~~~~~~~~~

The :any:`GetBit` expression can extract individual bit values from integers and byte strings. For example,

.. code-block:: python

    GetBit(Int(16), Int(0)) # get the 0th bit of 16, produces 0
    GetBit(Int(16), Int(4)) # get the 4th bit of 16, produces 1
    GetBit(Int(16), Int(63)) # get the 63rd bit of 16, produces 0
    GetBit(Int(16), Int(64)) # get the 64th bit of 16, invalid index

    GetBit(Bytes("base16", "0xf0"), Int(0)) # get the 0th bit of 0xf0, produces 1
    GetBit(Bytes("base16", "0xf0"), Int(7)) # get the 7th bit of 0xf0, produces 0
    GetBit(Bytes("base16", "0xf0"), Int(8)) # get the 8th bit of 0xf0, invalid index

Additionally, the :any:`SetBit` expression can modify individual bit values from integers and byte strings. For example,

.. code-block:: python

    SetBit(Int(0), Int(4), Int(1)) # set the 4th bit of 0 to 1, produces 16
    SetBit(Int(4), Int(0), Int(1)) # set the 0th bit of 4 to 1, produces 5
    SetBit(Int(4), Int(0), Int(0)) # set the 0th bit of 4 to 0, produces 4
    
    SetBit(Bytes("base16", "0x00"), Int(0), Int(1)) # set the 0th bit of 0x00 to 1, produces 0x80
    SetBit(Bytes("base16", "0x00"), Int(3), Int(1)) # set the 3rd bit of 0x00 to 1, produces 0x10
    SetBit(Bytes("base16", "0x00"), Int(7), Int(1)) # set the 7th bit of 0x00 to 1, produces 0x01

Byte Manipulation
~~~~~~~~~~~~~~~~~

In addition to manipulating bits, individual bytes in byte strings can be manipulated.

The :any:`GetByte` expression can extract individual bytes from byte strings. For example,

.. code-block:: python

    GetByte(Bytes("base16", "0xff00"), Int(0)) # get the 0th byte of 0xff00, produces 255
    GetByte(Bytes("base16", "0xff00"), Int(1)) # get the 1st byte of 0xff00, produces 0
    GetByte(Bytes("base16", "0xff00"), Int(2)) # get the 2nd byte of 0xff00, invalid index
    
    GetByte(Bytes("abc"), Int(0)) # get the 0th byte of "abc", produces 97 (ASCII 'a')
    GetByte(Bytes("abc"), Int(1)) # get the 1st byte of "abc", produces 98 (ASCII 'b')
    GetByte(Bytes("abc"), Int(2)) # get the 2nd byte of "abc", produces 99 (ASCII 'c')

Additionally, the :any:`SetByte` expression can modify individual bytes in byte strings. For example,

.. code-block:: python

    SetByte(Bytes("base16", "0xff00"), Int(0), Int(0)) # set the 0th byte of 0xff00 to 0, produces 0x0000
    SetByte(Bytes("base16", "0xff00"), Int(0), Int(128)) # set the 0th byte of 0xff00 to 128, produces 0x8000

    SetByte(Bytes("abc"), Int(0), Int(98)) # set the 0th byte of "abc" to 98 (ASCII 'b'), produces "bbc"
    SetByte(Bytes("abc"), Int(1), Int(66)) # set the 1st byte of "abc" to 66 (ASCII 'B'), produces "aBc"
