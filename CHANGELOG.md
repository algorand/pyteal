# 0.11.0

## Added
* Introduce optional compiler optimization to remove redundant sequential `ScratchSlot` store/load invocations ([#247](https://github.com/algorand/pyteal/pull/247)).  The optimization is disabled by default.
* Expose `DynamicScratchVar` to reference arbitrary `ScratchVar` instances ([#198](https://github.com/algorand/pyteal/pull/198)). 

## Changed
* Bump minimum supported Python version to v3.10 ([#269](https://github.com/algorand/pyteal/pull/269)).
* Add `@Subroutine` support for `ScratchVar` parameters ([#198](https://github.com/algorand/pyteal/pull/198)).
* Make minor doc updates ([#248](https://github.com/algorand/pyteal/pull/248)) and ([#265](https://github.com/algorand/pyteal/pull/265)).
* Remove outdated Jupyter notebook demo ([#268](https://github.com/algorand/pyteal/pull/268)).
* Fix docs warning about multiple OptimizeOptions targets ([#271](https://github.com/algorand/pyteal/pull/271)).

# 0.10.1

## Fixed
* Fixed a bug which caused incorrect TEAL code to be produced for mutually recursive subroutines
  with different argument counts ([#234](https://github.com/algorand/pyteal/pull/234))
* Minor docs updates ([#211](https://github.com/algorand/pyteal/pull/211), [#210](https://github.com/algorand/pyteal/pull/210), [#229](https://github.com/algorand/pyteal/pull/229))

# 0.10.0

## Added
* Support for new TEAL 6 features:
  * Increase maximum TEAL version ([#146](https://github.com/algorand/pyteal/pull/146))
  * New `Gitxn` expression, inner transaction group creation with `InnerTxnBuilder.Next()`, inner
    transaction array field setting, and allow using dynamic slot IDs with `ImportScratchValue` ([#149](https://github.com/algorand/pyteal/pull/149))
  * New `BytesSqrt` expression ([#163](https://github.com/algorand/pyteal/pull/163))
  * New `Global` fields `opcode_budget`, `caller_app_id`, and `caller_app_address` ([#168](https://github.com/algorand/pyteal/pull/168))
  * New `AccountParam` expressions for getting information about accounts ([#165](https://github.com/algorand/pyteal/pull/165))
  * New `Divw` expression, new transaction fields `last_log` and `state_proof_pk`, and dynamic index
    support for `InnerTxn` array fields ([#174](https://github.com/algorand/pyteal/pull/174))
* Added a new `MethodSignature` expression ([#153](https://github.com/algorand/pyteal/pull/153))
* Added a new `Suffix` expression and optimized existing `Substring` and `Extract` expressions ([#126](https://github.com/algorand/pyteal/pull/126))
* Added the `MultiValue` class as an alternative to `MaybeValue` ([#196](https://github.com/algorand/pyteal/pull/196))

## Fixed
* Various documentation fixes ([#140](https://github.com/algorand/pyteal/pull/140), [#142](https://github.com/algorand/pyteal/pull/142), [#191](https://github.com/algorand/pyteal/pull/191), [#202](https://github.com/algorand/pyteal/pull/202), [#207](https://github.com/algorand/pyteal/pull/207))
* Clearer error messages when non-PyTeal expressions are present ([#151](https://github.com/algorand/pyteal/pull/151))

## Changed
* **WARNING**: Due to code generation improvements, programs compiled with this version will likely
  produce different TEAL code than previous versions, but their functionality will be the same. Be
  aware that even small differences in generated TEAL code will change the address associated with
  escrow LogicSig contracts.
* Optimized constant assembly for small integers ([#128](https://github.com/algorand/pyteal/pull/128))
* Generated TEAL code for subroutines is more human-readable ([#148](https://github.com/algorand/pyteal/pull/148))
* Subroutine argument and return type annotations, if present, **MUST** be `Expr` ([#182](https://github.com/algorand/pyteal/pull/182))
* Transaction field documentation now separates fields by transaction type ([#204](https://github.com/algorand/pyteal/pull/204))
* Added documentation about how to generate the documentation ([#205](https://github.com/algorand/pyteal/pull/205))

# 0.9.1

## Added
* Documentation for exponent operator ([#134](https://github.com/algorand/pyteal/pull/134))
* Documentation for using `Seq` with lists ([#135](https://github.com/algorand/pyteal/pull/135))

## Fixed
* Fixed use of wildcard import in Pylance ([#133](https://github.com/algorand/pyteal/pull/133))

# 0.9.0

## Added
* Support for new TEAL 5 features:
  * `AppParam` expressions ([#107](https://github.com/algorand/pyteal/pull/107), [#123](https://github.com/algorand/pyteal/pull/123))
  * New `nonparticipation` transaction field ([#106](https://github.com/algorand/pyteal/pull/106))
  * Inner transactions, zero-element `Seq` expressions, dynamic transaction array access ([#115](https://github.com/algorand/pyteal/pull/115))
  * Logs, dynamic LogicSig argument indexes, single-element `NaryExpr`s, and creating `Bytes` from `bytes` and `bytearray` ([#117](https://github.com/algorand/pyteal/pull/117))
  * Extract expressions ([#118](https://github.com/algorand/pyteal/pull/118))
  * More efficient implementation of recursive subroutines in TEAL 5+ ([#114](https://github.com/algorand/pyteal/pull/114))
* Add `WideRatio`, an expression which exposes `mulw` and `divmodw` ([#121](https://github.com/algorand/pyteal/pull/121), [#122](https://github.com/algorand/pyteal/pull/122))

## Changed
* **WARNING**: Due to code generation improvements, programs compiled with this version will likely
  produce different TEAL code than previous versions, but their functionality will be the same. Be
  aware that even small differences in generated TEAL code will change the address associated with
  escrow LogicSig contracts.
* Some unnecessary branch conditions have been removed ([#120](https://github.com/algorand/pyteal/pull/120))

# 0.8.0

## Added
* Support for new TEAL 4 features:
  * Basic ops ([#67](https://github.com/algorand/pyteal/pull/67))
  * Byteslice arithmetic ([#75](https://github.com/algorand/pyteal/pull/75))
  * Importing scratch slot values from previous app calls ([#79](https://github.com/algorand/pyteal/pull/79), [#83](https://github.com/algorand/pyteal/pull/83))
  * Direct reference support for applications/accounts/assets ([#90](https://github.com/algorand/pyteal/pull/90))
  * `While` and `For` loops ([#95](https://github.com/algorand/pyteal/pull/95))
  * Subroutines ([#99](https://github.com/algorand/pyteal/pull/99))
* New logo ([#88](https://github.com/algorand/pyteal/pull/88), [#91](https://github.com/algorand/pyteal/pull/91))
* Added the `assembleConstants` option to `compileTeal`. When enabled, the compiler will assemble
int and byte constants in the most efficient way to reduce program size ([#57](https://github.com/algorand/pyteal/pull/57), [#61](https://github.com/algorand/pyteal/pull/61), [#66](https://github.com/algorand/pyteal/pull/66)).
* Added an alternative syntax for constructing `If` statements ([#77](https://github.com/algorand/pyteal/pull/77), [#82](https://github.com/algorand/pyteal/pull/82)).
* Align `Seq` with the rest of the API ([#96](https://github.com/algorand/pyteal/pull/96)).

## Fixed
* Fixed `NaryExpr.__str__` method ([#102](https://github.com/algorand/pyteal/pull/102)).

## Changed
* **WARNING**: Due to code generation changes required to support TEAL 4 loops and subroutines,
  programs compiled with this version will likely produce different TEAL code than previous
  versions, but their functionality will be the same. Be aware that even small differences in
  generated TEAL code will change the address associated with escrow LogicSig contracts.
* Improved crypto cost docs ([#81](https://github.com/algorand/pyteal/pull/81)).
* Applied code formatter ([#100](https://github.com/algorand/pyteal/pull/100)).

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
