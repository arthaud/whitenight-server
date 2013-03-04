import pygame
from game import Game, Map
import socket
import json

HOST = 'localhost'
PORT = 1234

pygame.init()
screen = pygame.display.set_mode((500,500))
pygame.display.set_caption('Whitenight observer')
pygame.mouse.set_visible(0)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

s.sendall(json.dumps(
    {'type': 'observer'}
) + '\n')

result = json.loads(s.makefile().readline())

players = result['players']
map_size = result['map_size']

game = Game(Map(size=map_size))
