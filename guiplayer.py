#!/usr/bin/env python2
# -*-coding:Utf-8 -*
from __future__ import division
import pygame
from game import Game, Map
from game.map import Base, Mine
import socket
import json
import argparse
from copy import deepcopy

SIZE = (1200,800)
WINDOW_TITLE = 'Whitenight gui player'

def send_json(socket, obj):
    socket.sendall(json.dumps(obj) + '\n')

def recv_json(socket):
    if not hasattr(recv_json, 'files'):
        recv_json.files = {} # static variable

    if not socket in recv_json.files:
        recv_json.files[socket] = socket.makefile()

    data = recv_json.files[socket].readline()
    return json.loads(data.strip())

def run(host, port, username):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    pygame.init()
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption(WINDOW_TITLE)

    teams_color = (
        pygame.Color(255, 0, 0, 0),
        pygame.Color(0, 0, 255, 0),
        pygame.Color(0, 255, 0, 0),
        pygame.Color(249, 132, 229, 0),
        pygame.Color(0, 255, 255, 0),
    )
    mine_color = pygame.Color(255, 255, 0, 0)
    font = pygame.font.SysFont('arial', 16, True)

    send_json(s, {
        'type': 'player',
        'name': username,
    })

    assert recv_json(s) == True
    print('Connected to %s:%s as %s' % (host, port, username))

    result = recv_json(s)
    team = int(result['id'])
    players = result['players']
    map_size = result['map_size']

    game = Game(Map(size=map_size))

    socketWait = True
    clickedPos = None
    commands = []

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and pygame.key.get_pressed()[pygame.K_ESCAPE]:
                commands = []
            elif event.type == pygame.KEYDOWN and (pygame.key.get_pressed()[pygame.K_SPACE] or pygame.key.get_pressed()[pygame.K_RETURN]):
                old_game = deepcopy(game)
                try:
                    game.play_turn(team, commands)
                except Exception as e:
                    print('Invalid command : %s' % repr(e))
                    game = old_game
                else:
                    send_json(s, commands)
                    socketWait = True
                commands = []
            elif event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                x = int(pygame.mouse.get_pos()[0] * game.map.width / SIZE[0])
                y = int(pygame.mouse.get_pos()[1] * game.map.height / SIZE[1])
                if clickedPos:
                    commands.append({'type': 'move', 'from': clickedPos, 'to': (x,y)})
                    clickedPos = None
                else:
                    if game.map.units[x, y] is not None:
                        clickedPos = (x, y)
                    elif isinstance(game.map.ground[x, y], Base):
                        commands.append({'type': 'create', 'pos': (x,y)})

        
        screen.fill(pygame.Color(255,255,255,0))

        for pos in game.map.keys():
            left = pos.x * SIZE[0] / game.map.width
            right = (pos.x + 1) * SIZE[0] / game.map.width
            top = pos.y * SIZE[1] / game.map.height
            bottom = (pos.y + 1) * SIZE[1] / game.map.height

            pygame.draw.line(screen, pygame.Color(0,0,0,0), (left, top), (right, top))
            pygame.draw.line(screen, pygame.Color(0,0,0,0), (left, bottom), (right, bottom))
            pygame.draw.line(screen, pygame.Color(0,0,0,0), (left, top), (left, bottom))
            pygame.draw.line(screen, pygame.Color(0,0,0,0), (right, top), (right, bottom))

            building = game.map.ground[pos]
            unit = game.map.units[pos]
            rect = pygame.Rect(left + 1, top + 1, right - left, bottom - top)

            if building:
                if isinstance(building, Base):
                    color = teams_color[(building.team - 1) % len(teams_color)]
                    pygame.draw.rect(screen, color, rect)
                elif isinstance(building, Mine):
                    pygame.draw.rect(screen, mine_color, rect)

            if unit:
                if building and isinstance(building, Base) and unit.team == building.team:
                    color = pygame.Color(255, 255, 255, 0)
                else:
                    color = teams_color[(unit.team - 1) % len(teams_color)]

                text = str(unit.team)
                if unit.gold > 0:
                    text = text + '*'
                surface = font.render(text, True, color)
                screen.blit(surface, (rect.centerx - surface.get_width() / 2, rect.centery - surface.get_height() / 2))

        headerText = '[waiting for your turn]' if socketWait else '[your turn]'
        headerText += ' ' + repr(commands)
        surface = font.render(headerText, True, pygame.Color(0,0,0,0))
        screen.blit(surface, (5, 5))


        pygame.display.flip()


        if socketWait:
            socketWait = False
            result = recv_json(s)
            if result:
                game.set_state(result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A gui player for the whitnight game.')
    parser.add_argument('host')
    parser.add_argument('-p', '--port', default=4321, type=int)
    parser.add_argument('username')
    args = parser.parse_args()
    run(args.host, args.port, args.username)
