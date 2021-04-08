# 0.7.0

## Added
* Support for new TEAL 3 features:
  * Bit/byte manipulation and new transaction and global fields ([#50](https://github.com/algorand/pyteal/pull/50)).
  * Dynamic `Gtxn` indexes ([#53](https://github.com/algorand/pyteal/pull/53)).
  * `MinBalance` expression ([#54](https://github.com/algorand/pyteal/pull/54)).
  * Documentation for new features ([#55](https://github.com/algorand/pyteal/pull/55)).
* Added the ability to specify the TEAL version target when using `compileTeal` ([#45](https://github.com/algorand/pyteal/pull/45)).
* Added `ScratchVar`, an interface for storing and loading values from scratch space ([#33](https://github.com/algorand/pyteal/pull/33)).
* Added a warning when scratch slots are loaded before anything has been stored ([#47](https://github.com/algorand/pyteal/pull/47)).

## Changed
* Rewrote internal code generation to produce smaller programs and make future optimization easier
([#26](https://github.com/algorand/pyteal/pull/26)). Programs compiled with this version will likely
produce different TEAL code than previous versions, but their functionality will be the same.

# 0.6.2

## Fixed
* Corrected documentation and examples that incorrectly used the `Txn.accounts` array ([#42](https://github.com/algorand/pyteal/pull/42)).
* Fixed improper base32 validation and allow the use of padding ([#34](https://github.com/algorand/pyteal/pull/34)
and [#37](https://github.com/algorand/pyteal/pull/37)).

# 0.6.1

## Added
* An application deployment example, `vote_deploy.py`.

## Fixed
* Internal modules no longer pollute the global namespace when importing with `from pyteal import *`
([#29](https://github.com/algorand/pyteal/pull/29)).
* Fixed several documentation typos.

## Changed
* Moved signature and application mode examples into separate folders.

# 0.6.0

## Added
* TEAL v2 `Txn` and `Gtxn` fields
* TEAL v2 `Global` fields
* `TxnType` enum
* `Pop` expression
* `Not` expression
* `BitwiseNot` expression
* `BitwiseAnd` expression
* `BitwiseOr` expression
* `BitwiseXor` expression
* `Neq` (not equal) expression
* `Assert` expression
* `AssetHolding` expressions
* `AssetParam` expressions
* State manipulation with `App` expressions
* `Concat` expression
* `Substring` expression
* `Bytes` constructor now accepts UTF-8 strings
* `If` expression now allows single branches

## Changed
* Compiling a PyTeal program must now be done with the `compileTeal(program, mode)` function. The `.teal()` method no longer exists.
* The API for group transactions has changed from `Gtxn.field(transaction_index)` to `Gtxn[transaction_index].field()`.
* `Tmpl` syntax has changed from `Type(Tmpl("TMPL_NAME"))` to `Tmpl.Type("TMPL_NAME")`.
