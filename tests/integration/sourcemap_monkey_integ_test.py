"""
This file monkey-patches ConfigParser in order to enable source mapping
and test the results of source mapping various PyTeal apps.
"""

from configparser import ConfigParser
from unittest import mock


@mock.patch.object(ConfigParser, "getboolean", return_value=True)
def test_sourcemap_annotate(_):
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    COMPILATION = "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), assemble_constants=False, with_sourcemaps=True, approval_filename=a_fname, clear_filename=c_fname, pcs_in_sourcemap=True, annotate_teal=True, annotate_teal_headers=True, annotate_teal_concise=False)"
    L = 250  # COMPILATION LINE
    ROUTER = "Router(name='AlgoBank', bare_calls=BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), clear_state=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL)))"
    INNERTXN = "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})"
    expected = f"""
// GENERATED TEAL                      //    PC           PYTEAL PATH                                       LINE    PYTEAL
#pragma version 6                      //    PC[0-19]     tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
txn NumAppArgs                         //    PC[20-21]    examples/application/abi/algobank.py              17      {ROUTER}
int 0                                  //    PC[22]
==                                     //    PC[23]
bnz main_l8                            //    PC[24-26]    tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
txna ApplicationArgs 0                 //    PC[27-29]    examples/application/abi/algobank.py              43      def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:
method "deposit(pay,account)void"      //    PC[30-35]
==                                     //    PC[36]
bnz main_l7                            //    PC[37-39]    tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
txna ApplicationArgs 0                 //    PC[40-42]    examples/application/abi/algobank.py              67      def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:
method "getBalance(account)uint64"     //    PC[43-48]
==                                     //    PC[49]
bnz main_l6                            //    PC[50-52]    tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
txna ApplicationArgs 0                 //    PC[53-55]    examples/application/abi/algobank.py              80      def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:
method "withdraw(uint64,account)void"  //    PC[56-61]
==                                     //    PC[62]
bnz main_l5                            //    PC[63-65]    tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
err                                    //    PC[66]
main_l5:                               //    PC[]
txn OnCompletion                       //    PC[67-68]    examples/application/abi/algobank.py              80      def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:
int NoOp                               //    PC[69]
==                                     //    PC[70]
txn ApplicationID                      //    PC[71-72]
int 0                                  //    PC[73]
!=                                     //    PC[74]
&&                                     //    PC[75]
assert                                 //    PC[76]
txna ApplicationArgs 1                 //    PC[77-79]
btoi                                   //    PC[80]
store 3                                //    PC[81-82]
txna ApplicationArgs 2                 //    PC[83-85]
int 0                                  //    PC[86]
getbyte                                //    PC[87]
store 4                                //    PC[88-89]
load 3                                 //    PC[90-91]    tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
load 4                                 //    PC[92-93]
callsub withdraw_3                     //    PC[94-96]    examples/application/abi/algobank.py              80      def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:
int 1                                  //    PC[97]
return                                 //    PC[98]
main_l6:                               //    PC[]         tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
txn OnCompletion                       //    PC[99-100]   examples/application/abi/algobank.py              67      def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:
int NoOp                               //    PC[101]
==                                     //    PC[102]
txn ApplicationID                      //    PC[103-104]
int 0                                  //    PC[105]
!=                                     //    PC[106]
&&                                     //    PC[107]
assert                                 //    PC[108]
txna ApplicationArgs 1                 //    PC[109-111]
int 0                                  //    PC[112]
getbyte                                //    PC[113]
callsub getBalance_2                   //    PC[114-116]
store 2                                //    PC[117-118]
byte 0x151f7c75                        //    PC[119-124]  tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
load 2                                 //    PC[125-126]
itob                                   //    PC[127]
concat                                 //    PC[128]
log                                    //    PC[129]
int 1                                  //    PC[130]      examples/application/abi/algobank.py              67      def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:
return                                 //    PC[131]
main_l7:                               //    PC[]         tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
txn OnCompletion                       //    PC[132-133]  examples/application/abi/algobank.py              43      def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:
int NoOp                               //    PC[134]
==                                     //    PC[135]
txn ApplicationID                      //    PC[136-137]
int 0                                  //    PC[138]
!=                                     //    PC[139]
&&                                     //    PC[140]
txn OnCompletion                       //    PC[141-142]
int OptIn                              //    PC[143]
==                                     //    PC[144]
txn ApplicationID                      //    PC[145-146]
int 0                                  //    PC[147]
!=                                     //    PC[148]
&&                                     //    PC[149]
||                                     //    PC[150]
assert                                 //    PC[151]
txna ApplicationArgs 1                 //    PC[152-154]
int 0                                  //    PC[155]
getbyte                                //    PC[156]
store 1                                //    PC[157-158]
txn GroupIndex                         //    PC[159-160]
int 1                                  //    PC[161]
-                                      //    PC[162]
store 0                                //    PC[163-164]
load 0                                 //    PC[165-166]
gtxns TypeEnum                         //    PC[167-168]
int pay                                //    PC[169]
==                                     //    PC[170]
assert                                 //    PC[171]
load 0                                 //    PC[172-173]  tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
load 1                                 //    PC[174-175]
callsub deposit_1                      //    PC[176-178]  examples/application/abi/algobank.py              43      def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:
int 1                                  //    PC[179]
return                                 //    PC[180]
main_l8:                               //    PC[]                                                           17      {ROUTER}
txn OnCompletion                       //    PC[181-182]
int NoOp                               //    PC[183]
==                                     //    PC[184]
bnz main_l18                           //    PC[185-187]
txn OnCompletion                       //    PC[188-189]
int OptIn                              //    PC[190]
==                                     //    PC[191]
bnz main_l17                           //    PC[192-194]
txn OnCompletion                       //    PC[195-196]
int CloseOut                           //    PC[197-198]
==                                     //    PC[199]
bnz main_l16                           //    PC[200-202]
txn OnCompletion                       //    PC[203-204]
int UpdateApplication                  //    PC[205-206]
==                                     //    PC[207]
bnz main_l15                           //    PC[208-210]
txn OnCompletion                       //    PC[211-212]
int DeleteApplication                  //    PC[213-214]
==                                     //    PC[215]
bnz main_l14                           //    PC[216-218]
err                                    //    PC[219]
main_l14:                              //    PC[]
txn ApplicationID                      //    PC[220-221]
int 0                                  //    PC[222]
!=                                     //    PC[223]
assert                                 //    PC[224]
callsub assertsenderiscreator_0        //    PC[225-227]
int 1                                  //    PC[228]
return                                 //    PC[229]
main_l15:                              //    PC[]
txn ApplicationID                      //    PC[230-231]
int 0                                  //    PC[232]
!=                                     //    PC[233]
assert                                 //    PC[234]
callsub assertsenderiscreator_0        //    PC[235-237]
int 1                                  //    PC[238]
return                                 //    PC[239]
main_l16:                              //    PC[]
txn ApplicationID                      //    PC[240-241]
int 0                                  //    PC[242]
!=                                     //    PC[243]
assert                                 //    PC[244]
byte "lost"                            //    PC[245]                                                        13      Bytes('lost')
byte "lost"                            //    PC[246]                                                        14
app_global_get                         //    PC[247]                                                                App.globalGet(Bytes('lost'))
txn Sender                             //    PC[248-249]                                                            Txn.sender()
byte "balance"                         //    PC[250]                                                                Bytes('balance')
app_local_get                          //    PC[251]                                                                App.localGet(Txn.sender(), Bytes('balance'))
+                                      //    PC[252]                                                                App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance'))
app_global_put                         //    PC[253]                                                        12      App.globalPut(Bytes('lost'), App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance')))
int 1                                  //    PC[254]                                                        17      {ROUTER}
return                                 //    PC[255]
main_l17:                              //    PC[]
int 1                                  //    PC[256]                                                        23      Approve()
return                                 //    PC[257]
main_l18:                              //    PC[]                                                           17      {ROUTER}
txn ApplicationID                      //    PC[258-259]
int 0                                  //    PC[260]
==                                     //    PC[261]
assert                                 //    PC[262]
int 1                                  //    PC[263]                                                        21      Approve()
return                                 //    PC[264]
                                       //    PC[]                                                           17      {ROUTER}
// assert_sender_is_creator            //
assertsenderiscreator_0:               //
txn Sender                             //    PC[265-266]                                                    8       Txn.sender()
global CreatorAddress                  //    PC[267-268]                                                            Global.creator_address()
==                                     //    PC[269]                                                                Txn.sender() == Global.creator_address()
assert                                 //    PC[270]                                                                Assert(Txn.sender() == Global.creator_address())
retsub                                 //    PC[271]      tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
                                       //    PC[]
// deposit                             //
deposit_1:                             //
store 6                                //    PC[272-273]
store 5                                //    PC[274-275]
load 5                                 //    PC[276-277]  examples/application/abi/algobank.py              56      payment.get()
gtxns Sender                           //    PC[278-279]                                                            payment.get().sender()
load 6                                 //    PC[280-281]                                                            sender.address()
txnas Accounts                         //    PC[282-283]
==                                     //    PC[284]                                                                payment.get().sender() == sender.address()
assert                                 //    PC[285]                                                                Assert(payment.get().sender() == sender.address())
load 5                                 //    PC[286-287]                                                    57      payment.get()
gtxns Receiver                         //    PC[288-289]                                                            payment.get().receiver()
global CurrentApplicationAddress       //    PC[290-291]                                                            Global.current_application_address()
==                                     //    PC[292]                                                                payment.get().receiver() == Global.current_application_address()
assert                                 //    PC[293]                                                                Assert(payment.get().receiver() == Global.current_application_address())
load 6                                 //    PC[294-295]                                                    59      sender.address()
txnas Accounts                         //    PC[296-297]
byte "balance"                         //    PC[298]                                                        60      Bytes('balance')
load 6                                 //    PC[299-300]                                                    61      sender.address()
txnas Accounts                         //    PC[301-302]
byte "balance"                         //    PC[303]                                                                Bytes('balance')
app_local_get                          //    PC[304]                                                                App.localGet(sender.address(), Bytes('balance'))
load 5                                 //    PC[305-306]                                                            payment.get()
gtxns Amount                           //    PC[307-308]                                                            payment.get().amount()
+                                      //    PC[309]                                                                App.localGet(sender.address(), Bytes('balance')) + payment.get().amount()
app_local_put                          //    PC[310]                                                        58      App.localPut(sender.address(), Bytes('balance'), App.localGet(sender.address(), Bytes('balance')) + payment.get().amount())
retsub                                 //    PC[311]      tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
                                       //    PC[]         examples/application/abi/algobank.py              67      def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:
// getBalance                          //
getBalance_2:                          //
txnas Accounts                         //    PC[312-313]                                                    76      user.address()
byte "balance"                         //    PC[314]                                                                Bytes('balance')
app_local_get                          //    PC[315]                                                                App.localGet(user.address(), Bytes('balance'))
retsub                                 //    PC[316]      tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
                                       //    PC[]
// withdraw                            //
withdraw_3:                            //
store 8                                //    PC[317-318]
store 7                                //    PC[319-320]
txn Sender                             //    PC[321-322]  examples/application/abi/algobank.py              100     Txn.sender()
byte "balance"                         //    PC[323]                                                        101     Bytes('balance')
txn Sender                             //    PC[324-325]                                                    102     Txn.sender()
byte "balance"                         //    PC[326]                                                                Bytes('balance')
app_local_get                          //    PC[327]                                                                App.localGet(Txn.sender(), Bytes('balance'))
load 7                                 //    PC[328-329]                                                            amount.get()
-                                      //    PC[330]                                                                App.localGet(Txn.sender(), Bytes('balance')) - amount.get()
app_local_put                          //    PC[331]                                                        99      App.localPut(Txn.sender(), Bytes('balance'), App.localGet(Txn.sender(), Bytes('balance')) - amount.get())
itxn_begin                             //    PC[332]                                                        104     InnerTxnBuilder.Begin()
int pay                                //    PC[333]                                                        105     {INNERTXN}
itxn_field TypeEnum                    //    PC[334-335]
load 8                                 //    PC[336-337]                                                    108     recipient.address()
txnas Accounts                         //    PC[338-339]
itxn_field Receiver                    //    PC[340-341]                                                    105     {INNERTXN}
load 7                                 //    PC[342-343]                                                    109     amount.get()
itxn_field Amount                      //    PC[344-345]                                                    105     {INNERTXN}
int 0                                  //    PC[346]                                                        110     Int(0)
itxn_field Fee                         //    PC[347-348]                                                    105     {INNERTXN}
itxn_submit                            //    PC[349]                                                        113     InnerTxnBuilder.Submit()
retsub                                 //    PC[350]      tests/integration/sourcemap_monkey_integ_test.py  {L}     {COMPILATION}
""".strip()

    a_fname, c_fname = "A.teal", "C.teal"
    compile_bundle = router.compile(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        assemble_constants=False,
        with_sourcemaps=True,
        approval_filename=a_fname,
        clear_filename=c_fname,
        pcs_in_sourcemap=True,
        annotate_teal=True,
        annotate_teal_headers=True,
        annotate_teal_concise=False,
    )
    ptsm = compile_bundle.approval_sourcemap
    assert ptsm
    actual = ptsm.annotated_teal(omit_headers=False, concise=False)
    assert expected == actual, first_diff(expected, actual)

    assert expected == compile_bundle.approval_teal


def first_diff(expected, actual):
    alines = actual.splitlines()
    elines = expected.splitlines()
    for i, e in enumerate(elines):
        if i >= len(alines):
            return f"""LINE[{i+1}] missing from actual:
{e}"""
        if e != (a := alines[i]):
            return f"""LINE[{i+1}]
{e}
VS.
{a}
"""
    if len(alines) > len(elines):
        return f"""LINE[{len(elines) + 1}] missing from expected:
{alines[len(elines)]}"""

    return ""
