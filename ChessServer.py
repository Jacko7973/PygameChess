# Jack O'Connor
# Pygame Chess Project
# ChessServer.py

import argparse
import os
import pickle
import socket
import threading
import json

import numpy as np

from ChessBoard import ChessBoard


def parseArgs():
    parser = argparse.ArgumentParser(description="Starts a chess server")
    parser.add_argument('--host', default='127.0.0.1', type=str, help='host ip of your server (default: localhost)')
    parser.add_argument('--port', default=8080, type=int, help='port to host listen on (default: 8080)')
    parser.add_argument('-c', required=False, default=20, type=int, help='max number of concurrent connections (default: 20)')

    return parser.parse_args()


class ChessGamesObject:

    def __init__(self, games={}):
        self.lock = threading.Lock()
        self.__games = games

    @property
    def games(self): return self.__games

    @games.getter
    def games(self): return self.__games

    def __editGames(self, game_id, new_data=None, delete=False):
        with self.lock:
            if delete:
                del self.games[game_id]
                return
            self.games[game_id] = new_data


    def createGame(self, p1, p2):
        game_id = len(self.games)
        game = {
            'players' : (p1, p2),
            'board' : ChessBoard()
        }
        self.__editGames(game_id, game)

        return game_id



class ClientThread:

    def __init__(self, client_socket, client_address, game_object, game_id):
        self.client_socket, self.client_address = client_socket, client_address
        self.game_object, self.game_id = game_object, game_id
        self.active = True
        self.get_board = lambda: game_object.games[game_id]['board']
        self.sendBoard()

        self.handleClient()

    def handleClient(self):
        while self.active:
            msg = self.client_socket.recv(64).decode()
            if msg == '!DISCONNECT': break
            self.handleMsg(msg)

        self.client_socket.close()

    def sendMsg(self, data):
        if isinstance(data, dict):
            data = '&'.join(key+':'+val for key, val in data.items())
        self.client_socket.send(data.encode() + b'\n')

    def endConnection(self):
        self.sendMsg('!DISCONNECT')
        self.active = False

    def sendBoard(self):
        board = self.get_board().getBoardValues()
        new_board = []
        for row in board: new_board += [item for item in row]
        self.sendMsg({'BOARD' : ' '.join(str(item) for item in new_board)})

    def handleMsg(self, msg):
        
        if msg == 




class ChessServer:

    def __init__(self, host, port, max_conns):
        self.host, self.port, self.max_conns = host, port, max_conns

        games = {}
        with open('saved_chess_games.txt', 'rb') as f:
            games = pickle.load(f)
        print(f'Starting with {len(games)} active sessions')
        self.chess_games = ChessGamesObject(games=games)
        self.waiting_room = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.listenForClients()


    def listenForClients(self):
        self.server.listen(self.max_conns)
        print(f'Accepting clients on {self.host} at port {self.port}')
        while True:
            try:
                client_socket, client_address = self.server.accept()
            except KeyboardInterrupt:
                print('\nExiting...')
                self.server.close()
                return

            print(f'[CONNECTION] New connection to {client_address[0]}')
            self.handleClient(client_socket, client_address)

    def handleClient(self, client_socket, client_address):
        self.waiting_room.append((client_socket, client_address))
        client_socket.send(b'WAITING\n')

        if len(self.waiting_room) >= 2:
            p1, p2 = self.waiting_room.pop(0), self.waiting_room.pop(0)
            game_id = self.chess_games.createGame(p1, p2)
            print(f'Starting game {game_id} with players: {p1[1][0]} and {p2[1][0]}')
            for (sock, addr) in [p1, p2]:
                sock.send(b''); sock.send(b'ENTERING GAME ' + str(game_id).encode() + b'\n');

                client_thread = threading.Thread(target=ClientThread, args=(sock, addr, self.chess_games, game_id))
                client_thread.start()
                # sock.close(); print(f'Connection closed to {addr}')



if __name__ == "__main__":
    args = parseArgs()
    server = ChessServer(host=args.host, port=args.port, max_conns=args.c)
