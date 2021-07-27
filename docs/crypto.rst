.. _crypto:

Cryptographic Primitives
========================

Algorand Smart Contracts support 4 cryptographic primitives, including 3 cryptographic
hash functions and 1 digital signature verification. Each of these cryptographic
primitives is associated with a cost, which is a number indicating its relative performance
overhead comparing with simple TEAL operations such as addition and substraction.
Simple TEAL opcodes have cost `1`, and more advanced cryptographic operations have a larger
cost. Below is how you express cryptographic primitives in PyTeal:


=============================== ========= ========================================================================================
Operator                        Cost      Description
=============================== ========= ========================================================================================
:code:`Sha256(e)`               `35`      `SHA-256` hash function, produces 32 bytes
:code:`Keccak256(e)`            `130`     `Keccak-256` hash funciton, produces 32 bytes
:code:`Sha512_256(e)`           `45`      `SHA-512/256` hash function, produces 32 bytes
:code:`Ed25519Verify(d, s, p)`  `1900`\*  `1` if :code:`s` is the signature of :code:`d` signed by private key :code:`p`, else `0`
=============================== ========= ========================================================================================

\* :code:`Ed25519Verify` is only available in signature mode.

Note the cost amount is accurate for version 2 of TEAL and higher.

These cryptographic primitives cover the most used ones in blockchains and cryptocurrencies. For example, Bitcoin uses `SHA-256` for creating Bitcoin addresses;
Alogrand uses `ed25519` signature scheme for authorization and uses `SHA-512/256` hash function for
creating contract account addresses from TEAL bytecode.
