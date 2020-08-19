
class TealInternalError(Exception):

    def __init__(self, message:str) -> None:
        self.message = "Internal Error: {}".format(message)

    def __str__(self):
        return self.message

TealInternalError.__module__ = "pyteal"

class TealTypeError(Exception):

    def __init__(self, actual, expected):
        self.message = "Type error: {} while expected {} ".format(actual, expected)

    def __str__(self):
        return self.message

TealTypeError.__module__ = "pyteal"

class TealInputError(Exception):

    def __init__(self, msg):
        self.message = "Input error: {}".format(msg)

    def __str__(self):
        return self.message

TealInputError.__module__ = "pyteal"
