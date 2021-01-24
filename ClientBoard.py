# Jack O'Connor
# Pygame Chess Project
# ClientBoard.py

import sys
import socket
import threading
import argparse

import pygame
from pygame.locals import *
import numpy as np


def parseArgs():
    parser = argparse.ArgumentParser(description="Client instance of Chess")
    parser.add_argument('host', default='127.0.0.1', type=str, help='Server host ip (default: localhost)')
    parser.add_argument('port', default=8080, type=int, help='Server port (default: 8080)')

    return parser.parse_args()


class ClientPygameRenderer():

    def __init__(self, host, port):
        self.host, self.port = host, port
        pygame.init()
        pygame.font.init()

        self.board_size = (400, 400)
        self.canvas = pygame.display.set_mode((self.board_size[0]+100, self.board_size[1]+100))
        pygame.display.set_caption('Pygame Chess')
        icon_surface = pygame.image.load('images/Chess_-6.png')
        pygame.display.set_icon(icon_surface)

        self.clock = pygame.time.Clock()

        self.setupGame()

        while True:
            self.update()
            pygame.display.update()
            self.clock.tick(60)

    def update(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                self.board_object.disconnect()
                sys.exit()
            elif event.type == MOUSEBUTTONUP:
                (x, y) = event.pos
                if 50 <= x < 450 and 50 <= y < 450:
                    self.board_object.handleClick((x-50, y-50))

        self.canvas.fill((230, 230, 230))
        self.canvas.blit(self.board_object.render(), (50, 50))

    
    def setupGame(self):
        self.board_object = ClientBoard(self.host, self.port)




class ClientBoard():

    def __init__(self, host, port):

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.is_active = True
        self.game_is_active = False
        self.images = self.createImages()
        self.setupGame()
        self.size = 400
        self.square_size = self.size // 8

        self.team = None
        self.turn = 1


        handler_thread = threading.Thread(target=self.handleConnection)
        handler_thread.start()

    def handleConnection(self):
        while self.is_active:
            msg = self.client_socket.recv(512).decode()
            if self.game_is_active: self.handleMsg(msg)
            if 'ENTERING' in msg: self.startGame(msg); print('Match Starting')
            

    def disconnect(self):
        print('disconnecting')
        self.sendMsg('!DISCONNECT')
        self.is_active = False
        self.client_socket.shutdown(socket.SHUT_RDWR)

    def startGame(self, msg):
        self.team = int(msg.encode()[-2:])
        self.game_is_active = True

    def handleMsg(self, msg):
        if '&' in msg: sub_reqs = msg.split('&')
        else: sub_reqs = [msg]

        for sub_req in sub_reqs:
            item = sub_req.split(':')
            if item[0] == 'BOARD':
                num_list = [int(num) for num in item[1].split(' ')]
                new_board = np.reshape(num_list, (8, 8))
                self.board = new_board
            elif item[0] == 'POS_MOVES_LIST':
                if item[1] != '':
                    str_moves = item[1].split(' ')
                    self.possible_moves = [tuple([int(i) for i in str_pos.split(',')]) for str_pos in str_moves]
                else: self.possible_moves = []
            elif item[0] == 'MOVE_MADE':
                str_moves = item[1].split(' ')
                self.previous_moves = [tuple([int(i) for i in str_pos.split(',')]) for str_pos in str_moves]
                self.possible_moves = []
                self.turn *= -1
            
        
    def sendMsg(self, data):
        if isinstance(data, dict):
            data = '&'.join(key+':'+val for key, val in data.items())
        self.client_socket.send(data.encode())

    def setupGame(self):

        self.board = np.zeros((8, 8), int)
        self.turn = 1
        self.selected_piece = None
        self.previous_moves = []
        self.possible_moves = []

    def createImages(self):
        images = {}
        for i in range(1, 7):
            images[i] = pygame.image.load(f'Images/Chess_{i}.png')
            images[-i] = pygame.image.load(f'Images/Chess_{-i}.png')
        
        return images

    def render(self):
        game_surface = pygame.Surface((self.size,)*2)
        get_color = lambda x, y: [(222, 188, 153), (106, 78, 66)][int((x+y)%2 == 0)]

        for y in range(len(self.board)):
            for x in range(len(self.board[0])):
                board_pos = (x*self.square_size, y*self.square_size)
                col = get_color(x, y)
                if (x, y) in self.previous_moves: col = (col[0]//1.5, col[1]//1.5, col[2])
                if (x, y) in self.possible_moves: col = (col[0]//2, col[1], col[2]//2)
                pygame.draw.rect(game_surface, col, pygame.Rect(*board_pos, self.square_size, self.square_size))

                item = self.board[y][x]
                if item != 0:
                    game_surface.blit(self.images[item], (x*self.square_size+(self.square_size/2 - 30), y*self.square_size+(self.square_size/2 - 30)))

        return game_surface

    def handleClick(self, pos):
        if self.turn != self.team: return
        (x, y) = new_pos = (pos[0]// 50, pos[1] // 50)
        if new_pos in self.possible_moves:
            send_msg = {'MAKE_MOVE' : ','.join(str(i) for i in self.selected_piece)+' '+','.join(str(i) for i in new_pos)}
            self.sendMsg(send_msg)
            self.turn *= -1
            self.previous_moves = [self.selected_piece, new_pos]
            self.possible_moves = []
            self.selected_piece = None
        if new_pos == self.selected_piece:
            self.possible_moves = []
            self.selected_piece = None
        if self.board[y][x] != 0 and self.board[y][x] / abs(self.board[y][x]) == self.team:
            send_msg = {'POSSIBLE_MOVES' : ','.join(str(i) for i in new_pos)}
            self.selected_piece = (x, y)
            self.sendMsg(send_msg)

        

if __name__ == '__main__':
    args = parseArgs()
    game = ClientPygameRenderer(args.host, args.port)
