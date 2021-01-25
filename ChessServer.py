# Jack O'Connor
# Pygame Chess Project
# ChessServer.py

import argparse
import os
import pickle
import socket
import threading

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


    def createGame(self, game_id, p1, p2):
        game = {
            'player 1' : p1,
            'player -1' : p2,
            'board' : ChessBoard()
        }
        self.__editGames(game_id, game)



class ClientThread:

    def __init__(self, client_socket, client_address, game_object, game_id, team):
        self.client_socket, self.client_address = client_socket, client_address
        self.game_object, self.game_id, self.team = game_object, game_id, team
        self.game_object.games[game_id][f'player {team}'] = self
        self.active = True
        self.get_board = lambda: game_object.games[game_id]['board']
        self.board = self.get_board()
        
        initial_msg = lambda: self.sendMsg(self.getStrBoard())
        t = threading.Timer(1.0, initial_msg)
        t.start()

        handler_thread = threading.Thread(target=self.handleClient)
        handler_thread.start()

    def handleClient(self):
        while self.active:
            msg = self.client_socket.recv(64).decode()
            print(msg)
            if msg == '!DISCONNECT': break
            
            self.handleMsg(msg)

    def sendMsg(self, data):
        if isinstance(data, dict):
            data = '&'.join(key+':'+val for key, val in data.items())
        self.client_socket.send(data.encode())

    def endConnection(self):
        self.sendMsg('!DISCONNECT')
        self.active = False
        self.client_socket.close()

    def getStrBoard(self):
        board = self.get_board().getBoardValues()
        new_board = []
        for row in board: new_board += [item for item in row]
        return {'BOARD' : ' '.join(str(item) for item in new_board)}

    def handleMsg(self, msg):
        responses = {}
        reqs = msg.split('&')
        for req in reqs:
            sub_reqs = req.split(':')
            if sub_reqs[0] == 'POSSIBLE_MOVES':
                (x, y) = tuple([int(item) for item in sub_reqs[1].split(',')])
                if 0 <= x < 8 and 0 <= y < 8:
                    if self.board.board[y][x] != 0 and self.board.board[y][x].team == self.team and self.team == self.board.turn:
                        pos_moves = self.getPosList(self.board.getPossibleMoves((x, y)), self.team)
                        responses['POS_MOVES_LIST'] = pos_moves
            if sub_reqs[0] == 'MAKE_MOVE':
                moves = self.getPosList(sub_reqs[1], self.team)
                if self.board.turn == self.team and moves[1] in self.board.getPossibleMoves(moves[0]):
                    self.board.movePiece(*moves)
                    str_board = self.getStrBoard()
                    other_player = self.game_object.games[self.game_id][f'player {-self.team}']
                    other_msg = {'MOVE_MADE':self.getPosList(moves, -self.team,), 'BOARD':other_player.getStrBoard()['BOARD']}
                    other_player.sendMsg(other_msg)
                    responses['MSG'] = 'SUCCESS'
                    responses['BOARD'] = str_board['BOARD']
                else:
                    responses['MSG'] = 'FAILURE'

        self.sendMsg(responses)

    def getPosList(self, in_list, team):
        if isinstance(in_list, str):
            tup_list = [tuple(int(i) for i in pos.split(',')) for pos in in_list.split(' ')]
            # if team == -1: tup_list = [(x, 7-y) for (x, y) in tup_list]
            return tup_list
        elif isinstance(in_list, list):
            # if team == -1: in_list = [(x, 7-y) for (x, y) in in_list]
            str_list = ' '.join(','.join(str(i) for i in tup) for tup in in_list)
            return str_list


class ChessServer:

    def __init__(self, host, port, max_conns):
        self.host, self.port, self.max_conns = host, port, max_conns

        games = {}
        with open('saved_chess_games.txt', 'rb') as f:
            games = pickle.load(f)
        print(f'Starting with {len(games)} active sessions')
        self.chess_games = ChessGamesObject(games=games)
        self.clients = []
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
        client_socket.send(b'WAITING')

        if len(self.waiting_room) >= 2:
            game_id = len(self.chess_games.games)
            self.chess_games.createGame(game_id, None, None)
            for team in [1, -1]:
                player = self.waiting_room.pop(0)
                player[0].send(b''); player[0].send(b'ENTERING GAME ' + str(game_id).encode() + b' ' + str(team).encode())
                client_thread = ClientThread(*player, self.chess_games, game_id, team)
                self.clients.append(client_thread)



if __name__ == "__main__":
    args = parseArgs()
    server = ChessServer(host=args.host, port=args.port, max_conns=args.c)
