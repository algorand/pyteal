import re
from typing import List, Dict, Set, Optional, TypeVar
from collections import OrderedDict

from pyteal.errors import TealInputError
from pyteal.types import TealType
from pyteal.ast import SubroutineDefinition
from pyteal.ir import TealComponent, TealOp, Op

# generic type variable
Node = TypeVar("Node")


def graph_search(graph: Dict[Node, Set[Node]], start: Node, end: Node) -> bool:
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
    """Find all subroutine calls which may result in the current subroutine being called again
    recursively.

    Args:
        subroutineGraph: A graph of subroutines. Each key is a subroutine (the main routine should
            be present), which represents a node in the graph. Each value is a set of all
            subroutines that specific subroutine calls, which represent directional edges in the
            graph.

    Returns:
        A dictionary whose keys are the same as subroutineGraph, and whose values are a subset of
        the key's values from subroutineGraph. Each element in this subset represents a subroutine
        which may reenter the calling subroutine.
    """
    reentryPoints: Dict[SubroutineDefinition, Set[SubroutineDefinition]] = dict()

    for subroutine in subroutineGraph.keys():
        # perform a depth first search to see which callers (if any) have a path to invoke the calling subroutine again
        reentryPoints[subroutine] = set(
            callee
            for callee in subroutineGraph[subroutine]
            if graph_search(subroutineGraph, callee, subroutine)
        )

    return reentryPoints


def find_recursive_path(
    subroutine_graph: Dict[SubroutineDefinition, Set[SubroutineDefinition]],
    subroutine: SubroutineDefinition,
) -> List[SubroutineDefinition]:
    visited = set()
    loop = []

    def dfs(x):
        if x in visited:
            return False

        visited.add(x)
        loop.append(x)
        for y in subroutine_graph[x]:
            if y == subroutine:
                loop.append(y)
                return True
            if dfs(y):
                return True
        loop.pop()
        return False

    found = dfs(subroutine)
    return loop if found else []


def spillLocalSlotsDuringRecursion(
    version: int,
    subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]],
    subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]],
    localSlots: Dict[Optional[SubroutineDefinition], Set[int]],
) -> None:
    """In order to prevent recursion from modifying the local scratch slots a subroutine uses,
    subroutines must "spill" their local slots to the stack before calling any other subroutine
    which may invoke the calling subroutine.

    "Spill to stack" means loading all local slots onto the stack, invoking the subroutine which may
    result in recursion, then restoring all local slots from the stack. This prevents the local
    slots from being modifying by a new recursive invocation of the current subroutine.

    Args:
        version: The current program version being assembled.
        subroutineMapping: A dictionary containing a list of TealComponents for every subroutine in
            a program. The key None is taken to indicate the main program routine. This input may be
            modified by this function in order to spill subroutine slots.
        subroutineGraph: A graph of subroutines. Each key is a subroutine (the main routine should
            not be present), which represents a node in the graph. Each value is a set of all
            subroutines that specific subroutine calls, which represent directional edges in the
            graph.
        localSlots: The output from the function `assignScratchSlotsToSubroutines`, which indicates
            the local slots which must be spilled for each subroutine.
    """
    recursivePoints = findRecursionPoints(subroutineGraph)

    recursive_byref = None
    for k, v in recursivePoints.items():
        if v and k.by_ref_args:
            recursive_byref = k
            break

    if recursive_byref:
        msg = "ScratchVar arguments not allowed in recursive subroutines, but a recursive call-path was detected: {}()"
        raise TealInputError(
            msg.format(
                "()-->".join(
                    f.name()
                    for f in find_recursive_path(subroutineGraph, recursive_byref)
                )
            )
        )

    coverAvailable = version >= Op.cover.min_version

    for subroutine, reentryPoints in recursivePoints.items():
        slots = list(sorted(slot for slot in localSlots[subroutine]))

        if len(reentryPoints) == 0 or len(slots) == 0:
            # no need to spill slots
            continue

        ops = subroutineMapping[subroutine]
        newOps: List[TealComponent] = []

        for stmt in ops:
            before: List[TealComponent] = []
            after: List[TealComponent] = []

            calledSubroutines = stmt.getSubroutines()
            # the only opcode that references subroutines is callsub, and it should only ever
            # reference one subroutine at a time
            assert (
                len(calledSubroutines) <= 1
            ), "Multiple subroutines are called from the same TealComponent"

            reentrySubroutineCalls = list(reentryPoints.intersection(calledSubroutines))
            if len(reentrySubroutineCalls) != 0:
                # A subroutine is being called which may reenter the current subroutine, so insert
                # ops to spill local slots to the stack before calling the subroutine and also to
                # restore the local slots after returning from the subroutine. This prevents a
                # reentry into the current subroutine from modifying variables we are currently
                # using.

                # reentrySubroutineCalls should have a length of 1, since calledSubroutines has a
                # maximum length of 1
                reentrySubroutineCall = reentrySubroutineCalls[0]
                numArgs = reentrySubroutineCall.argument_count()

                digArgs = True
                coverSpilledSlots = False
                uncoverArgs = False
                if coverAvailable:
                    digArgs = False
                    if len(slots) < numArgs:
                        coverSpilledSlots = True
                    else:
                        uncoverArgs = True

                for slot in slots:
                    # spill local slots to the stack
                    before.append(TealOp(None, Op.load, slot))

                    if coverSpilledSlots:
                        # numArgs is guaranteed to be at least 2 here (since numArgs > len(slots)
                        # and len(slots) must be at least 1 for the code to get this far), so no
                        # need to replace this with swap if numArgs is 1
                        before.append(TealOp(None, Op.cover, numArgs))

                for _ in range(numArgs):
                    # pull the subroutine arguments to the top of the stack, above the just spilled
                    # local slots, if needed

                    stackDistance = len(slots) + numArgs - 1

                    if uncoverArgs:
                        if stackDistance == 1:
                            before.append(TealOp(None, Op.swap))
                        else:
                            before.append(TealOp(None, Op.uncover, stackDistance))

                    if digArgs:
                        before.append(
                            TealOp(
                                None,
                                Op.dig,
                                stackDistance,
                            )
                        )
                        # because we are stuck using dig instead of uncover in AVM 4, we'll need to
                        # pop all of the dug up arguments after the function returns

                hideReturnValueInFirstSlot = False

                if subroutine.return_type != TealType.none:
                    # if the subroutine returns a value on the stack, we need to preserve this after
                    # restoring all local slots.

                    if len(slots) == 1:
                        after.append(TealOp(None, Op.swap))
                    elif coverAvailable:
                        after.append(TealOp(None, Op.cover, len(slots)))
                    else:
                        # Store the return value into slots[0] temporarily
                        hideReturnValueInFirstSlot = True
                        after.append(TealOp(None, Op.store, slots[0]))

                for slot in slots[::-1]:
                    # restore slots, iterating in reverse because slots[-1] is at the top of the stack
                    if hideReturnValueInFirstSlot and slot is slots[0]:
                        # time to restore the return value to the top of the stack

                        # slots[0] is being used to store the return value, so load it again
                        after.append(TealOp(None, Op.load, slot))

                        # swap the return value with the actual value of slot[0] on the stack
                        after.append(TealOp(None, Op.swap))

                    after.append(TealOp(None, Op.store, slot))

                if digArgs:
                    for _ in range(numArgs):
                        # clear out the duplicate arguments that were dug up previously, since dig
                        # does not pop the dug values -- once we use cover/uncover to properly set up
                        # the spilled slots, this will no longer be necessary
                        if subroutine.return_type != TealType.none:
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
) -> Dict[SubroutineDefinition, str]:
    """Resolve referenced subroutines for an entire program.

    Args:
        subroutineMapping: A dictionary containing a list of TealComponents for every subroutine in
            a program. The key None is taken to indicate the main program routine. This input will
            be modified by this function in order to assign labels to subroutines.

    Returns:
        An ordered dictionary whose keys are the same as subroutineMapping, minus the None key. The
        values of this dictionary will be the resolved label for each subroutine. The order of this
        dictionary is taken to be the official ordering of the subroutines, which should be used in
        later code generation steps.
    """
    allButMainRoutine = (
        subroutine for subroutine in subroutineMapping.keys() if subroutine is not None
    )

    subroutineOrder = sorted(allButMainRoutine, key=lambda subroutine: subroutine.id)
    subroutineToLabel: Dict[SubroutineDefinition, str] = OrderedDict()
    for index, subroutine in enumerate(subroutineOrder):
        safer_name = re.sub(r"[^A-Za-z0-9]", "", subroutine.name())
        subroutineToLabel[subroutine] = "{}_{}".format(safer_name, index)

    for subroutine, label in subroutineToLabel.items():
        for ops in subroutineMapping.values():
            for stmt in ops:
                stmt.resolveSubroutine(subroutine, label)

    return subroutineToLabel
