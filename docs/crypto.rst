.. _crypto:

Cryptographic Primitives
========================

Algorand Smart Contracts support the set of cryptographic primitives described in the table below.
Each of these cryptographic primitives is associated with a cost, which is a number indicating its
relative performance overhead compared with simple TEAL operations such as addition and substraction.
Simple TEAL opcodes have cost `1`, and more advanced cryptographic operations have a larger cost.
Below is how you express cryptographic primitives in PyTeal:


==================================== ========= ==================================================================================================================
Operator                             Cost      Description
==================================== ========= ==================================================================================================================
:code:`Sha256(e)`                    `35`      `SHA-256` hash function, produces 32 bytes
:code:`Sha3_256(e)`                  `130`     `SHA3-256` hash function, produces 32 bytes
:code:`Keccak256(e)`                 `130`     `Keccak-256` hash funciton, produces 32 bytes
:code:`Sha512_256(e)`                `45`      `SHA-512/256` hash function, produces 32 bytes
:code:`Ed25519Verify(d, s, p)`       `1900`\*  `1` if :code:`s` is the signature of the concatenation :code:`("ProgData" + hash_of_current_program + d)` signed by the private key corresponding to the public key :code:`p`, else `0`
:code:`Ed25519Verify_Bare(d, s, p)`  `1900`    `1` if :code:`s` is the signature of :code:`d` signed by the private key corresponding to the public key :code:`p`, else `0`
:code:`EcdsaVerify(c, d, r, s, pk)`  `1700`    `1` if :code:`(r, s)` is the signature of :code:`d` by private key corresponding to public key :code:`pk`, else 0
:code:`EcdsaDecompress(c, short_pk)` `650`     produces the decompressed public key associated with the compressed public key :code:`short_pk`
:code:`EcdsaRecover(c, d, id, r, s)` `2000`    produces the public key associated with the signature :code:`(r, s)` and recovery id :code:`id`
==================================== ========= ==================================================================================================================

\* :code:`Ed25519Verify` is only available in signature mode up to version 4 of AVM. From version 5 upwards, `Ed25519Verify` can be used in any mode.

Note the cost amount is accurate for version 2 of AVM and higher. The parameter :code:`c` in the ECDSA expressions defined above represents the elliptic curve
specification to be used (for example, :code:`Secp256k1`).

These cryptographic primitives cover the most used ones in blockchains and cryptocurrencies. For example, Bitcoin uses `SHA-256` for creating Bitcoin addresses;
Algorand uses `ed25519` signature scheme for authorization and uses `SHA-512/256` hash function for
creating contract account addresses from TEAL bytecode.
