# This example is provided for informational purposes only and has not been audited for security.
from pyteal import *
import json

router = Router(name="Vote")

approval_program, clear_state_program, contract = router.compile_program(
    version=8, optimize=OptimizeOptions(scratch_slots=True)
)

if __name__ == "__main__":
    with open("approval.teal", "w") as f:
        f.write(approval_program)

    with open("clear_state.teal", "w") as f:
        f.write(clear_state_program)

    with open("contract.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))
