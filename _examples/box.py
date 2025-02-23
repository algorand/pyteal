from pyteal import App, Assert, Bytes, Int, Itob, ScratchVar, Seq, TealType


def box_create():
    return Seq(
        # example: BOX_CREATE
        # ...
        # box created with box_create, size 100 bytes
        App.box_create(Bytes("MyKey"), Int(100)),
        # OR box created with box_put, size is implicitly the
        # length of bytes written
        App.box_put(Bytes("MyKey"), Bytes("My data values"))
        # ...
        # example: BOX_CREATE
    )


def box_get():
    return Seq(
        App.box_put(Bytes("MyKey"), Itob(Int(123))),
        # example: BOX_GET
        boxval := App.box_get(Bytes("MyKey")),
        Assert(boxval.hasValue()),
        # do something with boxval.value()
        # ...
        # example: BOX_GET
    )


def box_extract():
    return Seq(
        (scratchVar := ScratchVar(TealType.bytes)).store(Bytes("")),
        # example: BOX_EXTRACT
        # ...
        App.box_put(
            Bytes("BoxA"), Bytes("this is a test of a very very very very long string")
        ),
        scratchVar.store(App.box_extract(Bytes("BoxA"), Int(5), Int(9))),
        Assert(scratchVar.load() == Bytes("is a test"))
        # ...
        # example: BOX_EXTRACT
    )


def box_len():
    return Seq(
        # example: BOX_LEN
        App.box_put(
            Bytes("BoxA"), Bytes("this is a test of a very very very very long string")
        ),
        # box length is equal to the size of the box created
        # not a measure of how many bytes have been _written_
        # by the smart contract
        bt := App.box_length(Bytes("BoxA")),
        Assert(bt.hasValue()),
        Assert(bt.value() == 51),
        # example: BOX_LEN
    )


def box_delete():
    return Seq(
        # example: BOX_DELETE
        App.box_put(
            Bytes("BoxA"), Bytes("this is a test of a very very very very long string")
        ),
        # Box delete returns a 1/0 on the stack
        # depending on if it was successful
        Assert(App.box_delete(Bytes("BoxA"))),
        # example: BOX_DELETE
    )
