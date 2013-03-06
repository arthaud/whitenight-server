from __future__ import division
import pygame
from game import Game, Map
from game.map import Base
import socket
import json
import sys
from copy import deepcopy

HOST = 'palkeo.com'
PORT = 4321
SIZE = (1200,800)
USERNAME = sys.argv[1]

pygame.init()
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption('Whitenight observer')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

s.sendall(json.dumps({
    'type': 'player',
    'name': USERNAME,
}) + '\n')

assert json.loads(s.makefile().readline()) == True
result = json.loads(s.makefile().readline())

players = result['players']
map_size = result['map_size']
print(players)

team = None
for t, username in players.items():
    if username == USERNAME:
        team = int(t)
assert team

game = Game(Map(size=map_size))

def loop():
    global game, team

    socketWait = True
    clickedPos = None
    commands = []

    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and pygame.key.get_pressed()[pygame.K_SPACE]:
                old_game = deepcopy(game)
                try:
                    game.play_turn(team, commands)
                except:
                    print('Error : invalid commands')
                    game = old_game
                else:
                    s.send(json.dumps(commands) + '\n')
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

            text = ''

            if game.map.units[pos] is not None:
                text += repr(game.map.units[pos]) + ' '
            if game.map.ground[pos] is not None:
                text += repr(game.map.ground[pos])
            
            t = pygame.font.SysFont('nonexistent', 16).render(text, True, pygame.Color(0,0,0,0))
            screen.blit(t, (left + 2, (top + bottom) / 2))


        headerText = '[waiting for your turn]' if socketWait else '[your turn]'
        headerText += ' ' + repr(commands)
        t = pygame.font.SysFont('nonexistent', 18).render(headerText, True, pygame.Color(0,0,0,0))
        screen.blit(t, (0,0))


        pygame.display.flip()


        if socketWait:
            socketWait = False
            result = json.loads(s.makefile().readline())
            if result:
                game.set_state(result)


loop()
