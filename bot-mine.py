#!/usr/bin/env python3
# -*-coding:Utf-8 -*
import socket
import argparse
from game import Game, Map, UNIT_RANGE
from game.map import Base, Mine
from server import send_json, recv_json
from math import sqrt

def distance(p1, p2):
    return sqrt((p1.x - p2.x)*(p1.x - p2.x) + (p1.y - p2.y)*(p1.y - p2.y))

class Bot:
    def __init__(self, host, port, username):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

        send_json(self.socket, {
            'type': 'player',
            'name': username,
        })

        assert recv_json(self.socket) == True

    def run(self):
        result = recv_json(self.socket)
        self.team_id = int(result['id'])
        self.game = Game(Map(size=result['map_size']))

        while not self.game.winner():
            # waiting
            result = recv_json(self.socket)
            self.game.set_state(result)

            # computing turn
            self.init_turn()

            # kill ennemies
            for from_, unit in self.game.map.iter_units():
                if unit.team == self.team_id: # for each unit of my team
                    for to in self.game.map.range(from_, UNIT_RANGE):
                        unit_to = self.game.map.units[to]

                        if unit_to and unit_to.team != self.team_id: # ennemy
                            self.move_unit(from_, to)
                            break

            # move units
            for from_, unit in self.game.map.iter_units():
                if unit.team == self.team_id and unit not in self.units_moved: # for each unit of my team
                    destinations = list(self.game.map.range(from_, UNIT_RANGE))

                    if unit.gold > 0: 
                        # return to base
                        def key(to):
                            return distance(to, self.base_pos)
                    else:
                        # go to the nearest mine
                        def key(to):
                            return min([distance(to, mine_pos) for mine_pos in self.mines_pos])

                    destinations = sorted(destinations, key=key)
                    for to in destinations:
                        if not self.game.map.units[to] and not(to == self.base_pos and self.base_gold() > 0):
                            self.move_unit(from_, to)
                            break

            # create units
            if self.base_gold() > 0 and not self.game.map.units[self.base_pos]:
                self.create_unit()

            self.end_turn()

        if self.game.winner() == self.team_id:
            print('You win !')
        else:
            print('You lost.')

    def init_turn(self):
        self.commands = []
        self.units_moved = set()

        # computed only the first time
        if not hasattr(self, 'base_pos'):
            for pos, building in self.game.map.iter_buildings():
                if isinstance(building, Base) and building.team == self.team_id:
                    self.base_pos = pos

        if not hasattr(self, 'mines_pos'):
            self.mines_pos = []

            for pos, building in self.game.map.iter_buildings():
                if isinstance(building, Mine):
                    self.mines_pos.append(pos)

    def end_turn(self):
        send_json(self.socket, self.commands)

    def move_unit(self, from_, to):
        unit = self.game.map.units[from_]
        assert unit
        assert unit.team == self.team_id
        assert unit not in self.units_moved

        command = {
            'type': 'move',
            'from': from_,
            'to': to,
        }
        self.game.play_turn(self.team_id, [command])
        self.commands.append(command)
        self.units_moved.add(unit)

    def create_unit(self):
        assert self.base_gold() > 0
        assert not self.game.map.units[self.base_pos]

        command = {
            'type': 'create',
            'pos': self.base_pos,
        }
        self.game.play_turn(self.team_id, [command])
        self.commands.append(command)
        self.units_moved.add(self.game.map.units[self.base_pos])

    def base_gold(self):
        return self.game.map.ground[self.base_pos].gold

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A simple bot that only goes to the mines.')
    parser.add_argument('host')
    parser.add_argument('-p', '--port', default=4321, type=int)
    parser.add_argument('username')
    args = parser.parse_args()
    Bot(args.host, args.port, args.username).run()
