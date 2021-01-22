# Jack O'Connor
# Pygame Chess Project
# PygameChessBoard.py

import numpy
import pygame

from ChessBoard import ChessBoard

class PygameChessBoard:

    def __init__(self, board:ChessBoard, side_len):
        self.chess_board = board
        self.square_size = side_len // 8
        self.size = self.square_size * 8

        self.images = self.createImages()

        self.turn = 1
        self.selected_piece = None
        self.possible_moves = []
        self.previous_moves = []

    def render(self):
        game_surface = pygame.Surface((self.size,)*2)
        get_color = lambda x, y: [(222, 188, 153), (106, 78, 66)][int((x+y)%2 == 0)]

        for y in range(len(self.chess_board.board)):
            for x in range(len(self.chess_board.board[0])):
                board_pos = (x*self.square_size, y*self.square_size)
                col = get_color(x, y)
                if (x, y) in self.previous_moves: col = (col[0]//1.5, col[1]//1.5, col[2])
                if (x, y) in self.possible_moves: col = (col[0]//2, col[1], col[2]//2)
                pygame.draw.rect(game_surface, col, pygame.Rect(*board_pos, self.square_size, self.square_size))

                item = self.chess_board.board[y][x]
                if item != 0:
                    game_surface.blit(self.images[item.value], (x*self.square_size+(self.square_size/2 - 30), y*self.square_size+(self.square_size/2 - 30)))

        return game_surface


    def createImages(self):
        images = {}
        for i in range(1, 7):
            images[i] = pygame.image.load(f'Images/Chess_{i}.png')
            images[-i] = pygame.image.load(f'Images/Chess_{-i}.png')
        
        return images

    def handleClick(self, pos):
        grid_pos = (pos[0] // self.square_size, pos[1] // self.square_size)

        if grid_pos in self.possible_moves:
            self.chess_board.movePiece(self.selected_piece, grid_pos)
            self.possible_moves = []
            self.previous_moves = [self.selected_piece, grid_pos]
            self.selected_piece = None
            self.turn *= -1
            return
        
        if self.selected_piece and self.selected_piece == grid_pos:
            self.possible_moves = []
            self.selected_piece = None
            return
        elif self.chess_board.board[grid_pos[1]][grid_pos[0]] != 0 and self.chess_board.board[grid_pos[1]][grid_pos[0]].team == self.turn:
            self.possible_moves = self.chess_board.getPossibleMoves(grid_pos)
            self.selected_piece = grid_pos
            return
        else:
            self.possible_moves = []
            self.selected_piece = None

        