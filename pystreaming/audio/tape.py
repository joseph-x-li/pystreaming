class Tape:
    def __init__(self, length):
        self.length = length
        self.shape = self.dtype = None
        self.buffer = {}
        self.frames = set()

    def write(self, data):
        ...

    def read(self, left, right):
        ...
