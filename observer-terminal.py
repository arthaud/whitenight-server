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

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

        send_json(self.socket, { 'type': 'observer' })

        assert recv_json(self.socket) == True

    def run(self):
        curses.wrapper(self._run)

    def _run(self, screen):
        self.screen = screen
        curses.use_default_colors()

        # waiting for players
        screen.addstr('Connected to %s:%s\nWaiting for players...' % (self.host, self.port))
        screen.refresh()

        result = recv_json(self.socket)
        players = result['players']
        map_size = result['map_size']
        self.game = Game(Map(size=map_size))

        screen.erase()
        self.status_pad = curses.newpad(1, 100)
        self.map_pad = curses.newpad(map_size[1], map_size[0])

        while True:
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

    def set_status(self, status):
        self.status_pad.erase()
        self.status_pad.addstr(status)

    def draw_map(self):
        self.map_pad.erase()
        for pos, building in self.game.map.iter_buildings():
            if isinstance(building, Base):
                self.map_pad.addch(pos.y, pos.x, 'B')
            elif isinstance(building, Mine):
                self.map_pad.addch(pos.y, pos.x, 'M')

        for pos, unit in self.game.map.iter_units():
            self.map_pad.addch(pos.y, pos.x, str(unit.team))

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

