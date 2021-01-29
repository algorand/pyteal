from typing import List, Tuple

from ...ir import Op, TealOp, TealLabel, TealComponent, TealBlock

def detectDuplicatesInBlock(block: TealBlock) -> TealBlock:
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
    complete = Op.dig not in dependencies

    return complete, dependencies[::-1]
