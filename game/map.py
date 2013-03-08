from .array import Array, Point

class Building():
    pass


class Unit():
    def __init__(self, team, gold=0):
        self.team = team
        self.gold = gold

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__, self.team, self.gold)


class Base(Building):
    def __init__(self, team, gold=0):
        self.team = team
        self.gold = gold

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__, self.team, self.gold)


class Mine(Building):
    def __repr__(self):
        return "%s()" % (self.__class__.__name__,)


class Map():
    def __init__(self, map_file=None, size=None):
        if map_file:
            lines = [line.strip() for line in open(map_file).readlines()]
            map_width = len(lines[0])
            assert all(len(line) == map_width for line in lines)
            map_height = len(lines)

            self.units = Array(map_width, map_height)
            self.ground = Array(map_width, map_height)

            for y, line in enumerate(lines):
                for x, char in enumerate(line):
                    if char in "123456789":
                        self.ground[x,y] = Base(team=int(char))
                    elif char == "M":
                        self.ground[x,y] = Mine()
        else:
            assert size
            self.units = Array(size[0], size[1])
            self.ground = Array(size[0], size[1])


    def iter_units(self):
        for key, item in self.units.items():
            if item is not None:
                yield (key, item)


    def iter_buildings(self):
        for key, item in self.ground.items():
            if item is not None:
                yield (key, item)


    def keys(self):
        return self.ground.keys()


    @property
    def width(self):
        return self.ground.width

    @property
    def height(self):
        return self.ground.height


    def range(self, point, moves):
        """ Return a list of points from which we can go from the given point, in the given number of moves """
        r = set()
        for y in range(point[1] - moves, point[1] + moves + 1):
            d = moves - abs(point[1] - y)
            r.update(Point(x, y) for x in range(point[0] - d, point[0] + d + 1) if self.ground.in_bounds((x,y)))
        return r

    
