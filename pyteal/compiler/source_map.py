from pathlib import Path
from pathlib import Path
from tabulate import tabulate
from typing import Dict, List, NamedTuple, Optional, Tuple
from pyteal.ir.tealop import TealOp


def tabulateSourceMap(
    lines: List[str],
    sourceMap: Dict[int, Tuple[TealOp, Optional[NamedTuple]]],
    shorten_filename: bool = True,
) -> str:
    if shorten_filename:
        start_index = len(str(Path.cwd())) + 1

    def row(t):
        if not t:
            return None, None, None, None
        if not t[1]:
            return None, None, t[0], None

        # TODO: (ZEPH) THIS CANNOT GO INTO PROD:
        assert len(t[1].code_context) == 1
        return t[1].lineno, t[1].code_context[0], t[0], t[1].filename[start_index:]

    table = [
        [n, lines[n - 1], *row(sourceMap[n] if n in sourceMap else None)]
        for n in range(1, len(lines) + 1)
    ]
    # TL - Teal Line
    # PTL - PyTeal Line
    return tabulate(table, headers=["TL", "TEAL", "PTL", "PyTeal", "Op", "file"])


# d = [["Mark", 12, 95], ["Jay", 11, 88], ["Jack", 14, 90]]

# print(tabulate(d, headers=["Name", "Age", "Percent"]))
