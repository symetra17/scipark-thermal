class Opoint:
    def __init__(self, x, y, val):
        self.x = x
        self.y = y
        self.val = val


class Override:

    def __init__(self):
        self._is_enable = False
        self.mlist = []

    def set(self, x, y, value):
        self.mlist.append(Opoint(x, y, value))
        self._is_enable = True

    def is_enable(self):
        return self._is_enable

    def clear(self):
        self.mlist = []
        self._is_enable = False
