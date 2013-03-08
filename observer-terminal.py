#!/usr/bin/env python3
import curses
import socket
import argparse
from game import Game, Map
from game.map import Base, Mine
from server import send_json, recv_json

class Observer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.teams_color = (curses.COLOR_RED, curses.COLOR_BLUE, curses.COLOR_GREEN, curses.COLOR_MAGENTA, curses.COLOR_CYAN)
        self.mine_color = curses.COLOR_YELLOW # background color of mines
        self.default_color = -1 # foreground color of units on their base

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

        send_json(self.socket, { 'type': 'observer' })

        assert recv_json(self.socket) == True

    def run(self):
        curses.wrapper(self._run)
        print('Victoire de %s' % self.players[str(self.game.winner())])

    def _run(self, screen):
        self.screen = screen
        curses.curs_set(0)
        curses.use_default_colors()
        self.init_pairs()

        # waiting for players
        screen.addstr('Connected to %s:%s\nWaiting for players...' % (self.host, self.port))
        screen.refresh()

        result = recv_json(self.socket)
        self.players = result['players']
        map_size = result['map_size']
        self.game = Game(Map(size=map_size))

        screen.erase()
        self.status_pad = curses.newpad(1, 100)
        self.map_pad = curses.newpad(map_size[1], map_size[0])

        while not self.game.winner():
            # waiting for player
            self.set_status('Waiting...')
            self.refresh()

            result = recv_json(self.socket)
            if result:
                self.game.set_state(result)

            # display
            self.set_status('Type enter to continue')
            self.draw_map()
            self.refresh()

            curses.flushinp()
            screen.getch()
            send_json(self.socket, True)

    def init_pairs(self):
        ''' store all colors in curses '''
        nb_colors = len(self.teams_color)

        for i, fg_color in enumerate(self.teams_color):
            curses.init_pair(i * (nb_colors + 2) + 1, fg_color, -1)
            curses.init_pair(i * (nb_colors + 2) + 2, fg_color, self.mine_color)
            for j, bg_color in enumerate(self.teams_color):
                curses.init_pair(i * (nb_colors + 2) + j + 3, fg_color, bg_color)

        for i, bg_color in enumerate(self.teams_color):
            curses.init_pair(nb_colors * (nb_colors + 2) + i + 1, self.default_color, bg_color)

    def get_color_number(self, unit, building):
        nb_colors = len(self.teams_color)

        if unit:
            unit_color = (unit.team - 1) % nb_colors
            if building:
                if isinstance(building, Base):
                    if unit.team == building.team:
                        return nb_colors * (nb_colors + 2) + unit_color + 1
                    else:
                        building_color = (building.team - 1) % nb_colors
                        return unit_color * (nb_colors + 2) + building_color + 3
                elif isinstance(building, Mine):
                    return unit_color * (nb_colors + 2) + 2
            else:
                return unit_color * (nb_colors + 2) + 1
        elif building:
            if isinstance(building, Base):
                building_color = (building.team - 1) % nb_colors
                return building_color + 3
            elif isinstance(building, Mine):
                return 2
        return -1

    def set_status(self, status):
        self.status_pad.erase()
        self.status_pad.addstr(status)

    def draw_map(self):
        self.map_pad.erase()

        for pos, building in self.game.map.iter_buildings():
            attr = curses.color_pair(self.get_color_number(None, building))
            self.map_pad.addch(pos.y, pos.x, ' ', attr)

        for pos, unit in self.game.map.iter_units():
            building = self.game.map.ground[pos]
            attr = curses.color_pair(self.get_color_number(unit, building))
            if unit.gold > 0:
                attr = attr | curses.A_UNDERLINE
            self.map_pad.addch(pos.y, pos.x, str(unit.team), attr)

    def refresh(self):
        y, x = self.screen.getmaxyx()

        self.screen.refresh()
        self.status_pad.refresh(0, 0, 0, 0, 1, x-1)
        self.map_pad.refresh(0, 0, 1, 0, y-1, x-1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A terminal observer for the whitnight game.')
    parser.add_argument('host')
    parser.add_argument('-p', '--port', default=4321, type=int)
    args = parser.parse_args()
    Observer(args.host, args.port).run()

