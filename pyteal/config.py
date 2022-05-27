from algosdk.atomic_transaction_composer import ABI_RETURN_HASH


# Maximum size of an atomic transaction group.
MAX_GROUP_SIZE = 16

# Number of scratch space slots available.
NUM_SLOTS = 256

# Method return selector in base16
RETURN_HASH_PREFIX = ABI_RETURN_HASH

# Method argument number limit
METHOD_ARG_NUM_CUTOFF = 15
