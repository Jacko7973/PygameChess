# Jack O'Connor
# Pygame Chess Project
# PygameChess.py

import sys
import numpy
import pygame
from pygame.locals import *

from ChessBoard import ChessBoard
from ClientBoard import ClientBoard
from PygameChessBoard import PygameChessBoard

class PygameChess:

    def __init__(self):
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
                sys.exit()
            elif event.type == MOUSEBUTTONUP:
                (x, y) = event.pos
                if 50 <= x < 450 and 50 <= y < 450:
                    self.board_object.handleClick((x-50, y-50))

        self.canvas.fill((230, 230, 230))
        self.canvas.blit(self.board_object.render(), (50, 50))

    
    def setupGame(self):
        self.board_object = PygameChessBoard(ChessBoard(), self.board_size[0])



if __name__ == '__main__':
    game = PygameChess()