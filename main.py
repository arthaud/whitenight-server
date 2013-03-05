#!/usr/bin/env python3
# -*-coding:Utf-8 -*
import argparse
from server import Server

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch a server for the whitenight game.')
    parser.add_argument('host', default='0.0.0.0', nargs='?')
    parser.add_argument('port', type=int)
    parser.add_argument('map_file')
    args = parser.parse_args()
    Server(args.host, args.port, args.map_file).run()
