from typing import List, Dict, Set, Optional, TypeVar
from collections import OrderedDict
from itertools import chain

from ..types import TealType
from ..ast import SubroutineDefinition
from ..ir import TealComponent, TealOp, Op

# generic type variable
Node = TypeVar("Node")


def depthFirstSearch(graph: Dict[Node, Set[Node]], start: Node, end: Node) -> bool:
    """Check whether a path between start and end exists in the graph.

    This works even if start == end, in which case True is only returned if the
    node belongs to a cycle.
    """
    visited: Set[Node] = set()
    stack: List[Node] = list(graph[start])

    while len(stack) != 0:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        if end == current:
            return True
        stack += list(graph[current])

    return False


def findRecursionPoints(
    subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]]
) -> Dict[SubroutineDefinition, Set[SubroutineDefinition]]:
    reentryPoints: Dict[SubroutineDefinition, Set[SubroutineDefinition]] = dict()

    for subroutine in subroutineGraph.keys():
        # perform a depth first search to see which callers (if any) have a path to invoke the calling subroutine again
        reentryPoints[subroutine] = set(
            callee
            for callee in subroutineGraph[subroutine]
            if depthFirstSearch(subroutineGraph, callee, subroutine)
        )

    return reentryPoints


def spillLocalSlotsDuringRecursion(
    subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]],
    recursivePoints: Dict[SubroutineDefinition, Set[SubroutineDefinition]],
    localSlots: Dict[Optional[SubroutineDefinition], Set[int]],
) -> None:
    for subroutine, reentryPoints in recursivePoints.items():
        slots = list(sorted(slot for slot in localSlots[subroutine]))
        numArgs = subroutine.argumentCount()

        if len(reentryPoints) == 0 or len(slots) == 0:
            continue

        ops = subroutineMapping[subroutine]
        newOps: List[TealComponent] = []

        for stmt in ops:
            before: List[TealComponent] = []
            after: List[TealComponent] = []

            if len(reentryPoints.intersection(stmt.getSubroutines())) != 0:
                # A subroutine is being called which may reenter the current subroutine, so insert
                # ops to spill local slots to the stack before calling the subroutine and also to
                # restore the local slots after returning from the subroutine. This prevents a
                # reentry into the current subroutine from modifying variables we are currently
                # using.
                for slot in slots:
                    # spill local slots to the stack
                    before.append(TealOp(None, Op.load, slot))

                if numArgs != 0:
                    for _ in range(numArgs):
                        # pull the subroutine arguments to the top of the stack, above the just spilled
                        # local slots

                        # TODO: TEAL 5+, do this instead:
                        # before.append(TealOp(None, Op.uncover, len(slots)))
                        # or just do cover during the previous loop where slots are loaded, whichever
                        # is more efficient I suppose
                        before.append(
                            TealOp(
                                None,
                                Op.dig,
                                len(slots) + subroutine.argumentCount() - 1,
                            )
                        )
                        # because we are stuck using dig instead of uncover in TEAL 4, we'll need to
                        # pop all of the dug up arguments after the function returns

                putReturnValueInLastSlot = False

                if subroutine.returnType != TealType.none:
                    # if the subroutine returns a value on the stack, we need to preserve this after
                    # restoring all local slots.
                    putReturnValueInLastSlot = True
                    if len(slots) > 1:
                        # Store the return value into slots[0] temporarily. As an optimization, if
                        # len(slots) == 1 we can just do a single swap instead
                        after.append(TealOp(None, Op.store, slots[0]))

                    # TODO: TEAL 5+, just do cover len(slots), so after restoring all slots the
                    # return value is on top of the stack

                for slot in slots[::-1]:
                    # restore slots, iterating in reverse because slots[-1] is at the top of the stack
                    if putReturnValueInLastSlot and slot == slots[0]:
                        # time to restore the return value to the top of the stack
                        if len(slots) > 1:
                            # slots[0] is being used to store the return value, so load it again
                            after.append(TealOp(None, Op.load, slot))
                        # swap the return value with the actual value of slot[0] on the stack
                        after.append(TealOp(None, Op.swap))
                    after.append(TealOp(None, Op.store, slot))

                if numArgs != 0:
                    for _ in range(numArgs):
                        # clear out the duplicate arguments that were dug up previously, since dig
                        # does not pop the dug values
                        if subroutine.returnType != TealType.none:
                            # if there is a return value on top of the stack, we need to preserve
                            # it, so swap it with the subroutine argument that's below it on the
                            # stack
                            after.append(TealOp(None, Op.swap))
                        after.append(TealOp(None, Op.pop))

            newOps += before
            newOps.append(stmt)
            newOps += after

        subroutineMapping[subroutine] = newOps


def resolveSubroutines(
    subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]]
) -> OrderedDict[SubroutineDefinition, str]:
    """Resolve referenced subroutines for an entire program.

    Args:
        TODO

    Raises:
        TODO

    Returns:
        TODO
    """
    allButMainRoutine = (
        subroutine for subroutine in subroutineMapping.keys() if subroutine is not None
    )

    subroutineOrder = sorted(allButMainRoutine, key=lambda subroutine: subroutine.id)
    subroutineToLabel: OrderedDict[SubroutineDefinition, str] = OrderedDict()
    for index, subroutine in enumerate(subroutineOrder):
        subroutineToLabel[subroutine] = "sub{}".format(index)

    for subroutine, label in subroutineToLabel.items():
        for ops in subroutineMapping.values():
            for stmt in ops:
                stmt.resolveSubroutine(subroutine, label)

    return subroutineToLabel
