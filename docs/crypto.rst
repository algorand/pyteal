.. _crypto:

Cryptographic Primitives
========================

Algorand Smart Contracts support 4 cryptographic primitives, including 3 cryptographic
hash functions and 1 digital signature verification. Each of these cryptographic
primitives is associated with a cost, which is a number indicating its relative performance
overhead comparing with simple teal operations such as addition and substraction.
All TEAL opcodes except crypto primitives have cost `1`.
Below is how you express cryptographic primitives in PyTeal:


=============================== ========= ================================================================================ 
Operator                        Cost      Description
=============================== ========= ================================================================================
:code:`Sha256(e)`               `35`      `SHA-256` hash function, produces 32 bytes
:code:`Keccak256(e)`            `130`     `Keccak-256` hash funciton, produces 32 bytes
:code:`Sha512_256(e)`           `45`      `SHA512-256` hash function, produces 32 bytes
:code:`Ed25519Verify(d, s, p)`  `1900`\*   `1` if :code:`s` is the signature of :code:`d` signed by :code:`p` (PK), else `0`
=============================== ========= ================================================================================

\* :code:`Ed25519Verify` is only available in signature mode.

These cryptographic primitives cover the most used ones in blockchains and cryptocurrencies. For example, Bitcoin uses `SHA-256` for creating Bitcoin addresses;
Alogrand uses `ed25519` signature scheme for authorization and uses `SHA512-256` hash function for
creating contract account addresses from TEAL bytecode.
