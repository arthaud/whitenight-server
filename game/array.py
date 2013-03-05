from collections import namedtuple

class Point(namedtuple('Point', 'x, y')):
    def __add__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.x + other.x, self.y + other.y)
        if isinstance(other, (tuple,list)):
            assert len(other) == 2
            return self + self.__class__(other[0], other[1])
        raise TypeError


class Array():
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.map = [[None]*height for _ in range(width)]

    def __getitem__(self, key):
        return self.map[key[0]][key[1]]

    def __setitem__(self, key, value):
        self.map[key[0]][key[1]] = value

    def in_bounds(self, key):
        return key[0] in range(self.width) and key[1] in range(self.height)

    def keys(self):
        for x in range(self.width):
            for y in range(self.height):
                yield Point(x, y)

    def items(self):
        for key in self.keys():
            yield (key, self[key])

