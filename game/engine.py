from map import *

UNIT_RANGE = 3

class Game():
    def __init__(self, map_file, players):
        """ Start a game, using the map file passed as a parameter, and a list of player ID """
        self.map = Map(map_file)

        teams = {}
        for pos, building in self.map.iter_buildings():
            if hasattr(building, 'team'):
                teams.add(building.team)
        assert teams == set(players)


    def get_state(self):
        """ Returns a python object with the state of the map (to be JSON-encoded) """
        mines = []
        bases = []
        units = []

        for pos, building in self.map.iter_buildings():
            if isinstance(building, Base):
                bases.append({'pos': (pos.x, pos.y), 'team': building.team, 'gold': building.gold})
            elif isinstance(building, Mine):
                mines.append({'pos': (pos.x, pos.y)})

        for pos, unit in self.map.iter_units():
            units.append({'pos': (pos.x, pos.y), 'team': unit.team, 'gold': unit.gold})

        return {
                'bases': bases,
                'mines': mines,
                'units': units,
               }

    def play_turn(self, player, actions):
        """ 
            Change the state of the game for a player.
            Player is a player ID.
            Actions is a python object containing the actions.
            Can raise an exception if something is wrong.
        """
        units_moved = {}

        for action in actions:
            if action['type'] == 'move':
                square_from = self.map.units[action['from']]

                assert square_from.team == player
                assert Point(action['to'][0], action['to'][1]) in self.map.range(action['from'], UNIT_RANGE)
                assert square_from not in units_moved

                units_moved.add(square_from)
                self.map.units[action['to']] = square_from
                self.map.units[action['from']] = None

            elif action['type'] == 'create':
                base = self.map.ground[action['pos']]
                assert base.team == player
                assert base.gold > 0

                base.gold -= 1
                self.map.units[action['pos']] = Unit(player)

        self._transfer_gold()

    
    def winner(self):
        """ Return the ID of the winner, or None if the game is not finished """
        players_still_alive = {}
        for pos, unit in self.map.iter_units():
            players_still_alive.add(unit.team)

        if len(players_still_alive) == 0:
            return 0
        elif len(players_still_alive) == 1:
            return list(players_still_alive)[0]
        else:
            return None

    
    def _transfer_gold(self):
        for pos in self.map.units.keys():
            ground = self.map.ground[pos]
            unit = self.map.units[pos]
            if isinstance(ground, Mine) and isinstance(unit, Unit):
                unit.gold = 1
            elif isinstance(ground, Base) and isinstance(unit, Unit) and unit.team == ground.team and unit.gold > 0:
                ground.gold += unit.gold
                unit.gold = 0

