from collections import defaultdict

from pyteal.ast import Expr, SubroutineDefinition
from pyteal.compiler.options import CompileOptions
from pyteal.errors import TealInternalError, TealInputError
from pyteal.ir import (
    Op,
    TealOp,
    TealLabel,
    TealComponent,
    TealBlock,
    TealSimpleBlock,
    TealConditionalBlock,
    LabelReference,
)


def flattenBlocks(blocks: list[TealBlock]) -> list[TealComponent]:
    """Lowers a list of TealBlocks into a list of TealComponents.

    Args:
        blocks: The blocks to lower.
    """
    codeblocks: list[list[TealOp]] = []
    references: defaultdict[int, int] = defaultdict(int)
    referer: dict[int, int] = {}

    def add_if_new(nextIndex, i):
        if nextIndex not in referer:
            referer[nextIndex] = i

    labelRefs: dict[int, LabelReference] = dict()

    def indexToLabel(index: int) -> LabelReference:
        if index not in labelRefs:
            labelRefs[index] = LabelReference("l{}".format(index))
        return labelRefs[index]

    def blockIndexByReference(block: TealBlock) -> int:
        for i, b in enumerate(blocks):
            if block is b:
                return i
        raise ValueError("Block not present in list: {}".format(block))

    root_expr: Expr | None = None
    for i, block in enumerate(blocks):
        code = list(block.ops)
        codeblocks.append(code)
        if block.isTerminal():
            continue

        root_expr = block._root_expr

        if type(block) is TealSimpleBlock:
            assert block.nextBlock is not None

            nextIndex = blockIndexByReference(block.nextBlock)

            if nextIndex != i + 1:
                references[nextIndex] += 1
                add_if_new(nextIndex, i)
                code.append(TealOp(root_expr, Op.b, indexToLabel(nextIndex)))

        elif type(block) is TealConditionalBlock:
            assert block.trueBlock is not None
            assert block.falseBlock is not None

            trueIndex = blockIndexByReference(block.trueBlock)
            falseIndex = blockIndexByReference(block.falseBlock)

            if falseIndex == i + 1:
                references[trueIndex] += 1
                add_if_new(trueIndex, i)
                code.append(TealOp(root_expr, Op.bnz, indexToLabel(trueIndex)))
                continue

            if trueIndex == i + 1:
                references[falseIndex] += 1
                add_if_new(falseIndex, i)
                code.append(TealOp(root_expr, Op.bz, indexToLabel(falseIndex)))
                continue

            references[trueIndex] += 1
            add_if_new(trueIndex, i)
            code.append(TealOp(root_expr, Op.bnz, indexToLabel(trueIndex)))

            references[falseIndex] += 1
            add_if_new(falseIndex, i)
            code.append(TealOp(root_expr, Op.b, indexToLabel(falseIndex)))
        else:
            raise TealInternalError("Unrecognized block type: {}".format(type(block)))

    teal: list[TealComponent] = []
    root_expr = None
    for i, code in enumerate(codeblocks):
        if references[i] != 0:
            root_expr = (
                blocks[i]._root_expr or blocks[referer[i]]._root_expr or root_expr
            )
            teal.append(TealLabel(root_expr, indexToLabel(i)))
        teal += code

    return teal


def flattenSubroutines(
    subroutineMapping: dict[SubroutineDefinition | None, list[TealComponent]],
    subroutineToLabel: dict[SubroutineDefinition, str],
    options: CompileOptions,
) -> list[TealComponent]:
    """Combines each subroutine's list of TealComponents into a single list of TealComponents that
    represents the entire program.

    Args:
        subroutineMapping: A dictionary containing a list of TealComponents for every subroutine in
            a program. The key None is taken to indicate the main program routine.
        subroutineToLabel: An ordered dictionary which resolves each subroutine to a string label.

    Returns:
        A single list of TealComponents representing the entire program.
    """
    from pyteal.ast import Expr

    combinedOps: list[TealComponent] = []

    # By default all branch labels in each subroutine will start from "l0". To
    # make each subroutine have unique labels, we prefix "main_" to the ones
    # from the main routine, and "subX_" (the subroutine label) to the
    # ones from each subroutine

    mainRoutine = subroutineMapping[None]
    for stmt in mainRoutine:
        if isinstance(stmt, TealLabel):
            stmt.getLabelRef().addPrefix("main_")
    combinedOps += mainRoutine

    for subroutine, label in subroutineToLabel.items():
        comment = subroutine.name()
        labelPrefix = label + "_"

        subroutineOps = subroutineMapping[subroutine]
        for stmt in subroutineOps:
            if isinstance(stmt, TealLabel):
                stmt.getLabelRef().addPrefix(labelPrefix)

        # TODO: As this is only used by source mapper consider
        # adding sourcemaps options to `options`` and only call when sourcemaps is on
        # dexpr: Expr | None = subroutine.declarations.get_declaration_by_option(
        #     options.use_frame_pointers
        # )
        dexpr_good = subroutine.declarations.get_declaration()

        # dexpr_bad = subroutine.declarations.get_declaration_by_option(
        #     options.use_frame_pointers
        # )

        # # dexpr = dexpr_good

        # fs_bad = dexpr_bad.body.stack_frames[0].full_stack
        # fs_good = dexpr_good.body.stack_frames[0].full_stack
        # assert fs_bad and fs_good

        # comps = [
        #     {"good": g, "bad": fs_bad[i]} if i < len(fs_bad) else None
        #     for i, g in enumerate(fs_good)
        # ]

        # def vprop(d, prop):
        #     return d and {k: getattr(v, prop) for k, v in d.items()}

        # comps_cc = [vprop(c, "code_context") for c in comps]
        # core = comps_cc[:10]

        combinedOps.append(
            TealLabel(dexpr_good, LabelReference(label), comment)
        )  # T2PT1
        combinedOps += subroutineOps

    return combinedOps
