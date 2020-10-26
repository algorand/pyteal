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
