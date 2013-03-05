from __future__ import division
import pygame
from game import Game, Map
from game.map import Base
import socket
import json
import sys

HOST = 'localhost'
PORT = 1234
SIZE = (1200,800)

pygame.init()
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption('Whitenight observer')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

s.sendall(json.dumps({
    'type': 'player',
    'name': sys.argv[1],
}) + '\n')

assert json.loads(s.makefile().readline()) == True
result = json.loads(s.makefile().readline())

players = result['players']
map_size = result['map_size']
print(players)

game = Game(Map(size=map_size))

def loop():
    socketWait = True
    clickedPos = None
    commands = []

    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and pygame.key.get_pressed()[pygame.K_SPACE]:
                s.send(json.dumps(commands) + '\n')
                socketWait = True
                commands = []
            elif event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                x = int(pygame.mouse.get_pos()[0] * game.map.width / SIZE[0])
                y = int(pygame.mouse.get_pos()[1] * game.map.height / SIZE[1])
                if clickedPos:
                    if game.map.units[x, y] is None:
                        commands.append({'type': 'move', 'from': clickedPos, 'to': (x,y)})
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

        pygame.display.flip()


        if socketWait:
            socketWait = False
            result = json.loads(s.makefile().readline())
            if result:
                game.set_state(result)


loop()
