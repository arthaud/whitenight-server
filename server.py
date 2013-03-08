#!/usr/bin/env python3
# -*-coding:Utf-8 -*
import socket
from collections import namedtuple
from game import Game, Map
import json

class Player(namedtuple('Player', 'socket, name')):
    pass

def send_json(socket, obj):
    socket.sendall(bytes(json.dumps(obj) + '\n', 'UTF-8'))

def recv_json(socket):
    if not hasattr(recv_json, 'files'):
        recv_json.files = {} # static variable

    if not socket in recv_json.files:
        recv_json.files[socket] = socket.makefile()

    data = recv_json.files[socket].readline()
    return json.loads(data.strip())

class Server():
    def __init__(self, host, port, map_file):
        self.game = Game(Map(map_file))

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        print('server started on %s:%s' % (host, port))

    def run(self):
        # connection of players
        print('waiting for players...')
        unconnected_players = self.game.get_teams()
        self.players = {}
        self.observers = []

        while unconnected_players:
            client, address = self.server.accept()
            try:
                conn_message = recv_json(client)
                if conn_message['type'] == 'player':
                    assert 'name' in conn_message, 'undefined key : name'

                    pid = unconnected_players.pop()
                    self.players[pid] = Player(client, conn_message['name'])

                    print('Client connected : %s' % conn_message['name'])

                elif conn_message['type'] == 'observer':
                    self.observers.append(client)
                    print('Observer connected')

                send_json(client, True)
            except Exception as ex:
                print(repr(ex))
                send_json(client, { 'error': repr(ex), })
                client.close()

        # initialize 
        print('playing...')
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
                socket = self.players[pid].socket

                send_json(socket, self.game.get_state())
                try:
                    play_message = recv_json(socket)
                    self.game.play_turn(pid, play_message)
                except Exception as ex:
                    print(repr(ex))
                    send_json(socket, { 'error': repr(ex), })

                # send turn to observers
                for socket in self.observers:
                    send_json(socket, self.game.get_state())
                # wait for observers
                for socket in self.observers:
                    assert recv_json(socket) == True

        # end of game
        for socket, _ in self.players.values():
            socket.close()
        for socket in self.observers:
            socket.close()
        self.server.close()

