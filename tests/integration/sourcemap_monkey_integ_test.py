from configparser import ConfigParser
from unittest import mock

import pytest

"""
This file monkey-patches ConfigParser in order to enable source mapping
and test the results of source mapping various PyTeal apps.
"""


@pytest.fixture
def mock_ConfigParser():
    patcher = mock.patch.object(ConfigParser, "getboolean", return_value=True)
    patcher.start()
    yield
    patcher.stop()


# TODO: this gotta be cleaned up before merging

"""
Q: Why is this an integration test? 
A: Because we are using an algod here. In particular:
BTW: I don't think the algod logic needs to be THIS COMPLICATED!!!
1. setting router.compile(..., pcs_in_source=True, ...)
2. is passed to instance `input` = _RouterCompileInput which       
    on __post_init__ bootstraps an algod
3. `input` is then passed to router._build_impl()
4. inside _build_impl(), a Compilation instance is obtained via `input.get_compilation(each program)`
5. the compilation instance's `compile()` is called with param algod_client
    receiving `input.algod_client`
6. inside Compilation.compile() algod_client is enhanced with a liveness assertion
7. still inside compile(), algod_client is passed to PyTealSourceMap()'s init via algod
8. inside PTSM's __init__(), ONCE AGAIN, algod is enhanced with a liveness assertion
9. inside PTSM's _build(), ONCE AGAIN, algod is enhanced with a liveness assertion
10. FINALLY, we call algod.compile() and get the "sourcemap" value from the result
11. and supply it to a PCSourcemap() init
12. and set the rstuls to the _cached_pc_sourcemap property
"""


@pytest.mark.serial
def test_sourcemap_annotate(mock_ConfigParser):
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions

    a_fname, c_fname = "A.teal", "C.teal"
    annotate_teal_headers, annotate_teal_concise = True, False
    compile_bundle = router.compile(
        version=6,
        optimize=OptimizeOptions(scratch_slots=True),
        assemble_constants=False,
        with_sourcemaps=True,
        approval_filename=a_fname,
        clear_filename=c_fname,
        pcs_in_sourcemap=True,
        annotate_teal=True,
        annotate_teal_headers=annotate_teal_headers,
        annotate_teal_concise=annotate_teal_concise,
    )

    CL = 50  # COMPILATION LINE
    BCAs = "BareCallActions(no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE), opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL), close_out=OnCompleteAction(action=transfer_balance_to_lost, call_config=CallConfig.CALL), update_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL), delete_application=OnCompleteAction(action=assert_sender_is_creator, call_config=CallConfig.CALL))"
    ROUTER = f"Router(name='AlgoBank', bare_calls={BCAs}, clear_state=transfer_balance_to_lost)"
    COMPILATION = "router.compile(version=6, optimize=OptimizeOptions(scratch_slots=True), assemble_constants=False, with_sourcemaps=True, approval_filename=a_fname, clear_filename=c_fname, pcs_in_sourcemap=True, annotate_teal=True, annotate_teal_headers=annotate_teal_headers, annotate_teal_concise=annotate_teal_concise)"
    INNERTXN = "InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment, TxnField.receiver: recipient.address(), TxnField.amount: amount.get(), TxnField.fee: Int(0)})"
    EXPECTED_ANNOTATED_TEAL_311 = f"""
// GENERATED TEAL                      //    PC     PYTEAL PATH                                       LINE    PYTEAL
#pragma version 6                      //    (0)    tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
txn NumAppArgs                         //    (20)   examples/application/abi/algobank.py              19      {BCAs}
int 0                                  //    (22)
==                                     //    (23)
bnz main_l8                            //    (24)
txna ApplicationArgs 0                 //    (27)   tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
method "deposit(pay,account)void"      //    (30)
==                                     //    (36)
bnz main_l7                            //    (37)
txna ApplicationArgs 0                 //    (40)
method "getBalance(account)uint64"     //    (43)
==                                     //    (49)
bnz main_l6                            //    (50)
txna ApplicationArgs 0                 //    (53)
method "withdraw(uint64,account)void"  //    (56)
==                                     //    (62)
bnz main_l5                            //    (63)
err                                    //    (66)
main_l5:                               //
txn OnCompletion                       //    (67)   examples/application/abi/algobank.py              78      def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:
int NoOp                               //    (69)
==                                     //    (70)
txn ApplicationID                      //    (71)
int 0                                  //    (73)
!=                                     //    (74)
&&                                     //    (75)
assert                                 //    (76)   tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
txna ApplicationArgs 1                 //    (77)
btoi                                   //    (80)
store 3                                //    (81)
txna ApplicationArgs 2                 //    (83)
int 0                                  //    (86)
getbyte                                //    (87)
store 4                                //    (88)
load 3                                 //    (90)
load 4                                 //    (92)
callsub withdraw_3                     //    (94)
int 1                                  //    (97)
return                                 //    (98)
main_l6:                               //
txn OnCompletion                       //    (99)   examples/application/abi/algobank.py              65      def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:
int NoOp                               //    (101)
==                                     //    (102)
txn ApplicationID                      //    (103)
int 0                                  //    (105)
!=                                     //    (106)
&&                                     //    (107)
assert                                 //    (108)  tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
txna ApplicationArgs 1                 //    (109)
int 0                                  //    (112)
getbyte                                //    (113)
callsub getBalance_2                   //    (114)
store 2                                //    (117)
byte 0x151f7c75                        //    (119)
load 2                                 //    (125)
itob                                   //    (127)
concat                                 //    (128)
log                                    //    (129)
int 1                                  //    (130)
return                                 //    (131)
main_l7:                               //
txn OnCompletion                       //    (132)  examples/application/abi/algobank.py              41      def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:
int NoOp                               //    (134)
==                                     //    (135)
txn ApplicationID                      //    (136)
int 0                                  //    (138)
!=                                     //    (139)
&&                                     //    (140)
txn OnCompletion                       //    (141)
int OptIn                              //    (143)
==                                     //    (144)
txn ApplicationID                      //    (145)
int 0                                  //    (147)
!=                                     //    (148)
&&                                     //    (149)
||                                     //    (150)
assert                                 //    (151)  tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
txna ApplicationArgs 1                 //    (152)
int 0                                  //    (155)
getbyte                                //    (156)
store 1                                //    (157)
txn GroupIndex                         //    (159)
int 1                                  //    (161)
-                                      //    (162)
store 0                                //    (163)
load 0                                 //    (165)
gtxns TypeEnum                         //    (167)
int pay                                //    (169)
==                                     //    (170)
assert                                 //    (171)
load 0                                 //    (172)
load 1                                 //    (174)
callsub deposit_1                      //    (176)
int 1                                  //    (179)
return                                 //    (180)
main_l8:                               //           examples/application/abi/algobank.py              17      {ROUTER}
txn OnCompletion                       //    (181)
int NoOp                               //    (183)
==                                     //    (184)
bnz main_l18                           //    (185)
txn OnCompletion                       //    (188)
int OptIn                              //    (190)
==                                     //    (191)
bnz main_l17                           //    (192)
txn OnCompletion                       //    (195)
int CloseOut                           //    (197)
==                                     //    (199)
bnz main_l16                           //    (200)
txn OnCompletion                       //    (203)
int UpdateApplication                  //    (205)
==                                     //    (207)
bnz main_l15                           //    (208)
txn OnCompletion                       //    (211)
int DeleteApplication                  //    (213)
==                                     //    (215)
bnz main_l14                           //    (216)
err                                    //    (219)                                                    19      {BCAs}
main_l14:                              //                                                             17      {ROUTER}
txn ApplicationID                      //    (220)
int 0                                  //    (222)
!=                                     //    (223)
assert                                 //    (224)
callsub assertsenderiscreator_0        //    (225)
int 1                                  //    (228)
return                                 //    (229)
main_l15:                              //
txn ApplicationID                      //    (230)
int 0                                  //    (232)
!=                                     //    (233)
assert                                 //    (234)
callsub assertsenderiscreator_0        //    (235)
int 1                                  //    (238)
return                                 //    (239)
main_l16:                              //
txn ApplicationID                      //    (240)
int 0                                  //    (242)
!=                                     //    (243)
assert                                 //    (244)
byte \"lost\"                            //    (245)                                                    13      Bytes('lost')
byte \"lost\"                            //    (246)                                                    14      Bytes('lost')
app_global_get                         //    (247)                                                            App.globalGet(Bytes('lost'))
txn Sender                             //    (248)                                                            Txn.sender()
byte \"balance\"                         //    (250)                                                            Bytes('balance')
app_local_get                          //    (251)                                                            App.localGet(Txn.sender(), Bytes('balance'))
+                                      //    (252)                                                            App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance'))
app_global_put                         //    (253)                                                    12      App.globalPut(Bytes('lost'), App.globalGet(Bytes('lost')) + App.localGet(Txn.sender(), Bytes('balance')))
int 1                                  //    (254)                                                    17      {ROUTER}
return                                 //    (255)
main_l17:                              //
int 1                                  //    (256)                                                    23      Approve()
return                                 //    (257)
main_l18:                              //                                                             17      {ROUTER}
txn ApplicationID                      //    (258)
int 0                                  //    (260)
==                                     //    (261)
assert                                 //    (262)
int 1                                  //    (263)                                                    21      Approve()
return                                 //    (264)
                                       //           tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
// assert_sender_is_creator            //
assertsenderiscreator_0:               //
txn Sender                             //    (265)  examples/application/abi/algobank.py              8       Txn.sender()
global CreatorAddress                  //    (267)                                                            Global.creator_address()
==                                     //    (269)                                                            Txn.sender() == Global.creator_address()
assert                                 //    (270)                                                            Assert(Txn.sender() == Global.creator_address())
retsub                                 //    (271)  tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
                                       //
// deposit                             //
deposit_1:                             //
store 6                                //    (272)
store 5                                //    (274)
load 5                                 //    (276)  examples/application/abi/algobank.py              54      payment.get()
gtxns Sender                           //    (278)                                                            payment.get().sender()
load 6                                 //    (280)                                                            sender.address()
txnas Accounts                         //    (282)
==                                     //    (284)                                                            payment.get().sender() == sender.address()
assert                                 //    (285)                                                            Assert(payment.get().sender() == sender.address())
load 5                                 //    (286)                                                    55      payment.get()
gtxns Receiver                         //    (288)                                                            payment.get().receiver()
global CurrentApplicationAddress       //    (290)                                                            Global.current_application_address()
==                                     //    (292)                                                            payment.get().receiver() == Global.current_application_address()
assert                                 //    (293)                                                            Assert(payment.get().receiver() == Global.current_application_address())
load 6                                 //    (294)                                                    57      sender.address()
txnas Accounts                         //    (296)
byte \"balance\"                         //    (298)                                                    58      Bytes('balance')
load 6                                 //    (299)                                                    59      sender.address()
txnas Accounts                         //    (301)
byte \"balance\"                         //    (303)                                                            Bytes('balance')
app_local_get                          //    (304)                                                            App.localGet(sender.address(), Bytes('balance'))
load 5                                 //    (305)                                                            payment.get()
gtxns Amount                           //    (307)                                                            payment.get().amount()
+                                      //    (309)                                                            App.localGet(sender.address(), Bytes('balance')) + payment.get().amount()
app_local_put                          //    (310)                                                    56      App.localPut(sender.address(), Bytes('balance'), App.localGet(sender.address(), Bytes('balance')) + payment.get().amount())
retsub                                 //    (311)  tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
                                       //
// getBalance                          //
getBalance_2:                          //
txnas Accounts                         //    (312)  examples/application/abi/algobank.py              74      user.address()
byte \"balance\"                         //    (314)                                                            Bytes('balance')
app_local_get                          //    (315)                                                            App.localGet(user.address(), Bytes('balance'))
retsub                                 //    (316)  tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
                                       //
// withdraw                            //
withdraw_3:                            //
store 8                                //    (317)
store 7                                //    (319)
txn Sender                             //    (321)  examples/application/abi/algobank.py              98      Txn.sender()
byte \"balance\"                         //    (323)                                                    99      Bytes('balance')
txn Sender                             //    (324)                                                    100     Txn.sender()
byte \"balance\"                         //    (326)                                                            Bytes('balance')
app_local_get                          //    (327)                                                            App.localGet(Txn.sender(), Bytes('balance'))
load 7                                 //    (328)                                                            amount.get()
-                                      //    (330)                                                            App.localGet(Txn.sender(), Bytes('balance')) - amount.get()
app_local_put                          //    (331)                                                    97      App.localPut(Txn.sender(), Bytes('balance'), App.localGet(Txn.sender(), Bytes('balance')) - amount.get())
itxn_begin                             //    (332)                                                    102     InnerTxnBuilder.Begin()
int pay                                //    (333)                                                    103     {INNERTXN}
itxn_field TypeEnum                    //    (334)
load 8                                 //    (336)                                                    106     recipient.address()
txnas Accounts                         //    (338)
itxn_field Receiver                    //    (340)                                                    103     {INNERTXN}
load 7                                 //    (342)                                                    107     amount.get()
itxn_field Amount                      //    (344)                                                    103     {INNERTXN}
int 0                                  //    (346)                                                    108     Int(0)
itxn_field Fee                         //    (347)                                                    103     {INNERTXN}
itxn_submit                            //    (349)                                                    111     InnerTxnBuilder.Submit()
retsub                                 //    (350)  tests/integration/sourcemap_monkey_integ_test.py  {CL}      {COMPILATION}
""".strip()
    annotated_approval, annotated_clear = (
        compile_bundle.approval_annotated_teal,
        compile_bundle.clear_annotated_teal,
    )
    assert annotated_approval
    assert annotated_clear

    approval_ptsm, clear_ptsm = (
        compile_bundle.approval_sourcemap,
        compile_bundle.clear_sourcemap,
    )
    assert approval_ptsm
    assert clear_ptsm

    kwargs = dict(omit_headers=not annotate_teal_headers, concise=annotate_teal_concise)
    annotated_approval2, annotated_clear2 = approval_ptsm.annotated_teal(
        **kwargs
    ), clear_ptsm.annotated_teal(**kwargs)
    assert annotated_approval == annotated_approval2
    assert annotated_clear == annotated_clear2

    # FINALLY: compare to the actual expected
    # expected_annotated_teal = (
    #     EXPECTED_ANNOTATED_TEAL_310
    #     if sys.version_info < (3, 11)
    #     else EXPECTED_ANNOTATED_TEAL_311
    # )

    the_same = EXPECTED_ANNOTATED_TEAL_311 == annotated_approval
    print(f"{annotated_approval.splitlines()=}")
    assert the_same, first_diff(EXPECTED_ANNOTATED_TEAL_311, annotated_approval)

    raw_approval_lines, raw_clear_lines = (
        compile_bundle.approval_teal.splitlines(),
        compile_bundle.clear_teal.splitlines(),
    )

    ann_approval_lines, ann_clear_lines = (
        annotated_approval.splitlines(),
        annotated_clear.splitlines(),
    )

    assert len(raw_approval_lines) + 1 == len(ann_approval_lines)
    assert len(raw_clear_lines) + 1 == len(ann_clear_lines)

    for i, raw_line in enumerate(raw_approval_lines):
        assert ann_approval_lines[i + 1].startswith(raw_line)

    for i, raw_line in enumerate(raw_clear_lines):
        assert ann_clear_lines[i + 1].startswith(raw_line)


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
