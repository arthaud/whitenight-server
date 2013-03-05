from __future__ import division
import pygame
from game import Game, Map
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
    'name': sys.argv[0],
}) + '\n')

assert json.loads(s.makefile().readline()) == True
result = json.loads(s.makefile().readline())

players = result['players']
map_size = result['map_size']

game = Game(Map(size=map_size))

def loop():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

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

                text = repr(game.map.units[pos]) + repr(game.map.ground[pos])
                
                t = pygame.font.SysFont('nonexistent', 16).render(text, True, pygame.Color(0,0,0,0))
                screen.blit(t, ((left + right) / 2, (top + bottom) / 2))

            pygame.display.flip()

            result = json.loads(s.makefile().readline())
            if result:
                game.set_state(result)


loop()