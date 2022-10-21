# Unreleased

## Added
* Added option to `OpUp` utility to allow specification of source for fees ([566](https://github.com/algorand/pyteal/pull/566))

## Fixed
* Erroring on constructing an odd length hex string. ([#539](https://github.com/algorand/pyteal/pull/539))
* Incorrect behavior when overriding a method name ([#550](https://github.com/algorand/pyteal/pull/550))
* Add missing `abi.NamedTupleTypeSpec` equality override, such that equality holds only when `instance_class` and `value_type_specs` match. ([#540](https://github.com/algorand/pyteal/pull/540))
* Prohibited instantiating `abi.NamedTuple` from inheriting subclasses of `abi.NamedTuple`, for fields in subclasses are not inherited. ([#540](https://github.com/algorand/pyteal/pull/540))
* Fixed bug in app arg tupling and detupling when a Txn argument is present ([#577](https://github.com/algorand/pyteal/pull/577))

## Changed
* Subroutines that take ABI type of Transaction now allow any Transaction type to be passed. ([#531](https://github.com/algorand/pyteal/pull/531))
* Relaxing exact type check in `InnerTxnFieldExpr.MethodCall` by applying `abi.type_spec_is_assignable_to`. ([#561](https://github.com/algorand/pyteal/pull/561))

# 0.18.1

## Fixed
* ABI methods without a docstring now have their arguments in the output Contract object. ([#524](https://github.com/algorand/pyteal/pull/524))

# 0.18.0

## Added

* ABI Methods will now parse the docstring for the method and set the description for any parameters that are described. ([#518](https://github.com/algorand/pyteal/pull/518))
  * Note: the docstring must adhere to one of google, rst, numpy , or epy formatting styles.

## Fixed
* Subroutines annotated with a `TupleX` class are now invoked with an instance of that exact class, instead of the more general `Tuple` class ([#519](https://github.com/algorand/pyteal/pull/519))

# 0.17.0

## Added
* Static and Dynamic Byte Array convenience classes ([#500](https://github.com/algorand/pyteal/pull/500), [#514](https://github.com/algorand/pyteal/pull/514))
* Add the ability to insert comments in TEAL source file with the `Comment` method ([#410](https://github.com/algorand/pyteal/pull/410))
* Add a `comment` keyword argument to the Assert expression that will place the comment immediately above the `assert` op in the resulting TEAL ([#510](https://github.com/algorand/pyteal/pull/510))

## Fixed
* Fix AST duplication bug in `String.set` when called with an `Expr` argument ([#508](https://github.com/algorand/pyteal/pull/508))

# 0.16.0

## Added
* Add the ability to pass foreign reference arrays directly into inner transactions ([#384](https://github.com/algorand/pyteal/pull/384))

* NamedTuple Implementation ([#473](https://github.com/algorand/pyteal/pull/473))

* ExecuteMethodCall helper ([#501](https://github.com/algorand/pyteal/pull/501))

## Fixed

* CI: Fail readthedocs build on warning ([#478](https://github.com/algorand/pyteal/pull/478))

* Windows Compatibility ([#499](https://github.com/algorand/pyteal/pull/499))

## Changed
* Update `Block` docs to match spec change ([#503](https://github.com/algorand/pyteal/pull/503))

# 0.15.0

## Added
* Support AVM 7 updates:
  * New opcodes:
    * `base64_decode` ([#418](https://github.com/algorand/pyteal/pull/418))
    * `block` ([#415](https://github.com/algorand/pyteal/pull/415))
    * `ed25519verify_bare` ([#426](https://github.com/algorand/pyteal/pull/426))
    * `json_ref` ([#417](https://github.com/algorand/pyteal/pull/417))
    * `replace2`, `replace3` ([#413](https://github.com/algorand/pyteal/pull/413))
    * `sha3_256` ([#425](https://github.com/algorand/pyteal/pull/425))
    * `vrf_verify` ([#419](https://github.com/algorand/pyteal/pull/419))
  * `Secp256r1` curve for ECDSA opcodes ([#423](https://github.com/algorand/pyteal/pull/423))
  * Program page transaction field access ([#412](https://github.com/algorand/pyteal/pull/412))

# 0.14.0

## Added
* Add [ARC-0004](https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0004.md) support for building and calling Apps.  See user guide for a walkthrough of capabilities and limitations ([#264](https://github.com/algorand/pyteal/pull/264)).
* Introduce ABI Router to simplify ARC-0004 App construction and JSON descriptor generation.  See user guide for a walkthrough ([#170](https://github.com/algorand/pyteal/pull/170)).
* Support declaring PyTeal version compatibility with a new pragma directive ([#429](https://github.com/algorand/pyteal/pull/429)).
* Add `Execute` method to simplify inner transaction creation and submission ([#444](https://github.com/algorand/pyteal/pull/444)).
* Add `py.typed` marker to allow downstream use of mypy with PyTeal ([#465](https://github.com/algorand/pyteal/pull/465)).

## Fixed
* Fix misspelled function names (`localNumUint`, `globalNumUint`) and corresponding internal field references ([#431](https://github.com/algorand/pyteal/pull/431)).
* Fix stale user guide references ([#359](https://github.com/algorand/pyteal/pull/359)).

## Changed
* Make PyTeal stack traces easier to debug ([#371](https://github.com/algorand/pyteal/pull/371)).
* Streamline multi-expression clause construction ([#442](https://github.com/algorand/pyteal/pull/442)).

# 0.13.0

## Added
* Add opcode support for ECDSA verify, decompress, and recover ([#307](https://github.com/algorand/pyteal/pull/307)).

## Fixed
* Fix bug where `Continue` skips `While` condition check ([#332](https://github.com/algorand/pyteal/pull/332)).
* Fix `If` construction using builder syntax ([#329](https://github.com/algorand/pyteal/pull/329)).

## Changed
* Correct multiple doc typos ([#324](https://github.com/algorand/pyteal/pull/324), [#330](https://github.com/algorand/pyteal/pull/330)).

# 0.12.1

## Fixed
* Resolve PyPi upload issue introduced in v0.12.0 ([#317](https://github.com/algorand/pyteal/pull/317)).

# 0.12.0

## Added
* Introduce a utility for increasing opcode budget referred to as OpUp ([#274](https://github.com/algorand/pyteal/pull/274)).
* Introduce dryrun testing facilities referred to as blackbox testing ([#249](https://github.com/algorand/pyteal/pull/249)). 

## Changed
* Make various user guide updates/corrections ([#291](https://github.com/algorand/pyteal/pull/291), [#295](https://github.com/algorand/pyteal/pull/295), [#301](https://github.com/algorand/pyteal/pull/301)).
* Install flake8 linter ([#273](https://github.com/algorand/pyteal/pull/273), [#283](https://github.com/algorand/pyteal/pull/283)).

# 0.11.1

## Fixed
* Fix readthedocs build issue introduced in v0.11.0 ([#276](https://github.com/algorand/pyteal/pull/276), [#279](https://github.com/algorand/pyteal/pull/279)).

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
