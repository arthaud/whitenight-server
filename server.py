#!/usr/bin/env python3
# -*-coding:Utf-8 -*
import socket
from collections import namedtuple
from game import Game, Map
import json

class Player(namedtuple('Player', 'socket, name')):
    pass

def send_json(socket, obj):
    socket.send(bytes(json.dumps(obj) + '\n', 'utf-8'))

class Server():
    def __init__(self, host, port, map_file):
        self.game = Game(Map(map_file))

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)

    def run(self):
        # connection of players
        unconnected_players = self.game.get_teams()
        self.players = {}
        self.observers = []

        while unconnected_players:
            client, address = self.server.accept()
            data = client.makefile().readline()
            if data:
                conn_message = json.loads(str(data))

                if conn_message['type'] == 'player':
                    pid = unconnected_players.pop()
                    self.players[pid] = Player(client, conn_message['name'])

                elif conn_message['type'] == 'observer':
                    self.observers.append(client)

                send_json(client, True)

            else:
                client.close()

        # initialize 
        for pid, (socket, _) in self.players.items():
            send_json(socket, {
                'id': pid,
                'players': { id: name for id, (_, name) in self.players.items() },
                'map_size': (self.game.map.width, self.game.map.height),
            })
        for socket in self.observers:
            send_json(socket, {
                'players': { id: name for id, (_, name) in self.players.items() },
                'map_size': (self.game.map.width, self.game.map.height),
            })

        # play
        while not self.game.winner():
            teams = list(self.players.keys())
            while teams and not self.game.winner():
                pid = teams.pop()
                send_json(self.players[pid].socket, self.game.get_state())
                data = self.players[pid].socket.makefile().readline()

                if data:
                    try:
                        play_message = json.loads(data.strip())
                        self.game.play_turn(pid, play_message)
                    except KeyError as key:
                        send_json(self.players[pid].socket, {
                            'error': 'undefined key %s' % key,
                        })
                    except AssertionError as message:
                        send_json(self.players[pid].socket, {
                            'error': message,
                        })
                    except:
                        send_json(self.players[pid].socket, {
                            'error': 'unknow error',
                        })


                for socket in self.observers:
                    send_json(socket, self.game.get_state())
                    data = self.server.makefile().readline()
                    assert data.strip() == json.dumps(True)

        for socket, _, _ in self.players:
            socket.close()
        for socket in self.observers:
            socket.close()
        self.server.close()
