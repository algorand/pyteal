from typing import List

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealLabel
from ..errors import TealInputError
from ..util import new_label
from .expr import Expr
from .err import Err
from .if_ import If

class Cond(Expr):
    """A chainable branching expression that supports an arbitrary number of conditions."""

    def __init__(self, *argv: List[Expr]):
        """Create a new Cond expression.
        
        At least one argument must be provided, and each argument must be a list with two elements.
        The first element is a condition which evalutes to uint64, and the second is the body of the
        condition, which will execute if that condition is true. All condition bodies must have the
        same return type. During execution, each condition is tested in order, and the first
        condition to evaluate to a true value will cause its associated body to execute and become
        the value for this Cond expression. If no condition evalutes to a true value, the Cond
        expression produces an error and the TEAL program terminates.
        
        Example:
            .. code-block:: python

                Cond([Global.group_size() == Int(5), bid],
                    [Global.group_size() == Int(4), redeem],
                    [Global.group_size() == Int(1), wrapup])
        """

        if len(argv) < 1:
            raise TealInputError("Cond requires at least one [condition, value]")

        value_type = None

        for arg in argv:
            msg = "Cond should be in the form of Cond([cond1, value1], [cond2, value2], ...), error in {}"
            if not isinstance(arg, list):
                raise TealInputError(msg.format(arg))
            if len(arg) != 2:
                raise TealInputError(msg.format(arg))
            
            require_type(arg[0].type_of(), TealType.uint64) # cond_n should be int

            if value_type is None: # the types of all branches should be the same
                value_type = arg[1].type_of()
            else:
                require_type(arg[1].type_of(), value_type)

        self.value_type = value_type        
        self.args = argv        

    def __teal__(self):
        teal = []

        labels = []
        for arg in self.args:
            l = new_label()
            cond = arg[0]

            teal += cond.__teal__()
            teal.append(TealOp(Op.bnz, l))

            labels.append(l)

        # err if no conditions are met
        teal.append(TealOp(Op.err))

        # end label
        labels.append(new_label())
        
        for i, arg in enumerate(self.args):
            label = TealLabel(labels[i])
            branch = arg[1]

            teal.append(label)
            teal += branch.__teal__()
            if i + 1 != len(self.args):
                teal.append(TealOp(Op.b, labels[-1]))

        teal.append(TealLabel(labels[-1]))

        return teal

    def __str__(self):
        ret_str = "(Cond"
        for a in self.args:
            ret_str += " [" + a[0].__str__() + ", " + a[1].__str__() + "]"
        ret_str += ")"
        return ret_str
        
    def type_of(self):
        return self.value_type

Cond.__module__ = "pyteal"
