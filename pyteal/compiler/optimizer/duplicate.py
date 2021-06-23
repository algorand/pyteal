from typing import List, Tuple

from ...ir import Op, TealOp, TealLabel, TealComponent, TealBlock

def detectDuplicatesInBlock(block: TealBlock) -> TealBlock:
    """Detects duplicate opcodes in a block and replaces them with `dup` or `dup2`.

    NOTE: This optimization relies on opcodes being idempotent, meaning regardless of how many times
    an opcode is repeated with the same input (the elements it pops from the stack), it will produce
    the same result (the elements it pushes to the stack, AND all other side effects). Currently
    there are two cases that break this idempotence: the dig opcode, and stateful write opcodes that
    depend on stateful reads. To address this, the dig opcode is excluded from this type of
    optimization, and TODO: ADDRESS STATEFUL CASE

    Args:
        block: The block to optimize. This input will be modified.
    
    Returns:
        The same input block, with its ops modified to reduce duplicate opcodes.
    """
    # this is necessary to compare TealOps without compairing their origin Expr
    with TealComponent.Context.ignoreExprEquality():
        index = len(block.ops) - 1
        while index > 0:
            if block.ops[index].getOp().pushes != 1:
                # TODO: evaluate whether other numbers make sense to analyze
                index -= 1
                continue

            currComplete, currDeps = getDependenciesForOp(block.ops, index)
            
            prevIndex = index - len(currDeps)
            if not currComplete or prevIndex < 0:
                index -= 1
                continue

            prevComplete, prevDeps = getDependenciesForOp(block.ops, prevIndex)
            if not prevComplete:
                index -= 1
                continue

            if currDeps == prevDeps:
                # replace currDeps with dup op
                block.ops = block.ops[:index - len(currDeps) + 1] + [TealOp(None, Op.dup)] + block.ops[index + 1:]
                index -= len(currDeps)
                continue

            prevCurrIndex = index - len(currDeps) - len(prevDeps)
            if prevCurrIndex > 0:
                prevCurrComplete, prevCurrDeps = getDependenciesForOp(block.ops, prevCurrIndex)
                prevPrevIndex = prevCurrIndex - len(prevCurrDeps)

                if prevCurrComplete and prevPrevIndex >= 0 and currDeps == prevCurrDeps:
                    prevPrevComplete, prevPrevDeps = getDependenciesForOp(block.ops, prevPrevIndex)
                    if prevPrevComplete and prevPrevDeps == prevDeps:
                        # replace prevDeps and currDeps with dup2 op
                        block.ops = block.ops[:prevCurrIndex + 1] + [TealOp(None, Op.dup2)] + block.ops[index + 1:]
                        index -= len(currDeps) + len(prevDeps)
                        continue

            index -= 1
        return block

def getDependenciesForOp(ops: List[TealOp], index: int) -> Tuple[bool, List[TealOp]]:
    op = ops[index]
    dependencies = [op]
    pops = op.getOp().pops
    while pops > 0:
        depIndex = index - len(dependencies)
        if depIndex < 0 or depIndex >= len(ops):
            return False, dependencies
        dependency = ops[depIndex]
        dependencies.append(dependency)
        pops += dependency.getOp().pops - dependency.getOp().pushes
    
    # dig can read any value before it in the stack without popping it, so if we
    # depend on dig we can't know what it depends on (at least with this
    # algorithm)
    complete = all(Op.dig != op.getOp() for op in dependencies)

    return complete, dependencies[::-1]
