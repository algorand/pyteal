from .ast.bytes import Bytes


# Maximum size of an atomic transaction group.
MAX_GROUP_SIZE = 16

# Number of scratch space slots available.
NUM_SLOTS = 256

# Bytes to prepend in log for ABI method return
RETURN_EVENT_SELECTOR = Bytes("base16", "151f7c75")
