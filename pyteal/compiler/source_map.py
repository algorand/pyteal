from pathlib import Path
from pathlib import Path
from tabulate import tabulate
from typing import Dict, List, NamedTuple, Optional, Tuple
from pyteal.ir.tealop import TealOp


def tabulateSourceMap(
    lines: List[str],
    sourceMap: Dict[int, Tuple[TealOp, Optional[NamedTuple], Optional[str]]],
    shorten_filename: bool = True,
) -> str:
    """
    # TL - Teal Line
    # PTL - PyTeal Line
    """
    start_index = len(str(Path.cwd())) + 1 if shorten_filename else 0

    def _row(t):
        if not t:
            return None, None, None, None, None
        if not t[1]:
            return None, None, t[0], None, t[2]

        # TODO: THIS CANNOT GO INTO PROD:
        assert len(t[1].code_context) == 1
        return [
            t[1].lineno,
            t[1].code_context[0],
            t[0],
            t[1].filename[start_index:],
            t[2],
        ]

    def row(t):
        r = _row(t)
        return {
            "PTL": r[0],
            "PyTeal": r[1],
            "Op": r[2],
            "file": r[3],
            "note": r[4],
        }

    ORDER = [
        "TL",
        "TEAL",
        "PTL",
        "PyTeal",
        "note",
        "file",
        # "Op",
    ]

    records = [
        {"TL": n, "TEAL": lines[n - 1], **row(sourceMap[n] if n in sourceMap else None)}
        for n in range(1, len(lines) + 1)
    ]

    # table = [
    #     [n, lines[n - 1], *row(sourceMap[n] if n in sourceMap else None)]
    #     for n in range(1, len(lines) + 1)
    # ]

    table = [[r.get(k) for k in ORDER] for r in records]

    return tabulate(table, headers=ORDER, tablefmt="presto")
