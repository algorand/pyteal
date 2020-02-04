.. _arithmetic_expressions:

Arithmetic Expressions
======================

An arithmetic expression is an expression that results in a :code:`TealType.uint64` value.
In PyTeal, arithmetic expressions include integer arithmetics operators and boolean operators.
We overloaded all integer arithmetics operator in Python.

==================== =========== ================================================= =========================
Operator             Overloaded  Semantics                                         Example
==================== =========== ================================================= =========================
:code:`Lt(a, b)`     :code:`<`   `1` if a is less than b, `0` otherwise            :code:`Int(1) < Int(5)`
:code:`Gt(a, b)`     :code:`>`   `1` if a is greater than b, `0` otherwise         :code:`Int(1) > Int(5)`
:code:`Le(a, b)`     :code:`<=`  `1` if a is no greater than b, `0` otherwise      :code:`Int(1) <= Int(5)`
:code:`Ge(a, b)`     :code:`>=`  `1` if a is no less than b, `0` otherwise         :code:`Int(1) >= Int(5)`
:code:`Add(a, b)`    :code:`+`   `a + b`, error (panic) if overflow                :code:`Int(1) + Int(5)`
:code:`Minus(a, b)`  :code:`-`   `a - b`, error if underflow                       :code:`Int(5) - Int(1)`
:code:`Mul(a, b)`    :code:`*`   `a * b`, error if overflow                        :code:`Int(2) * Int(3)`
:code:`Div(a, b)`    :code:`/`   `a / b`, error if devided by zero                 :code:`Int(3) / Int(2)`
:code:`Mod(a, b)`    :code:`%`   `a % b`, modulo operation                         :code:`Int(7) % Int(3)`
:code:`Eq(a, b)`     :code:`==`  `1` if a equals b, `0` otherwise                  :code:`Int(7) == Int(7)`
==================== =========== ================================================= =========================


All these operators takes two :code:`TealType.uint64` values.
In addition, :code:`Eq(a, b)` (:code:`==`)  is polymorphic:
it also takes two `TealType.bytes` values. For example, :code:`Arg(0) == Arg(1)` is a valid PyTeal expression.

While using overloaded Python arithmatic operators, the associativity and precedence is the same as the
`original python operators <https://docs.python.org/3/reference/expressions.html#operator-precedence>`_ . For example:

 * :code:`Int(1) + Int(2) + Int(3)` is equivalent to :code:`Add(Add(Int(1), Int(2)), Int(3))`
 * :code:`Int(1) + Int(2) * Int(3)` is equivalent to :code:`Add(Int(1), Mul(Int(2), Int(3)))` 





