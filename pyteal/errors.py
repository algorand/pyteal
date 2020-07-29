
class TealInternalError(Exception):

    def __init__(self, message:str) -> None:
        self.message = "Internal Error: {}".format(message)

    def __str__(self):
        return self.message

class TealTypeError(Exception):

    def __init__(self, actual, expected):
        self.message = "Type error: {} while expected {} ".format(actual, expected)

    def __str__(self):
        return self.message

class TealTypeMismatchError(Exception):

    def __init__(self, t1, t2):
        self.message = "Type mismatch error: {} cannot be resolved to {}".format(t1, t2)

    def __str__(self):
        return self.message

class TealInputError(Exception):

    def __init__(self, msg):
        self.message = "Input error: {}".format(msg)

    def __str__(self):
        return self.message
