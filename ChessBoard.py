# Jack O'Connor
# Pygame Chess Project
# ChessBoard.py

import numpy as np
import copy


class Piece:

    def __init__(self, value):
        self.value = value
        self.team = int(value / abs(value))
        self.has_moved = False


class ChessBoard:

    def __init__(self, promotionCallback=lambda pos: 2, test=False):
        self._board = self.createBoard()
        self.promotionCallback = promotionCallback
        self.test = test

    @property
    def board(self): return self._board

    @board.getter
    def board(self): return self._board


    def createBoard(self):
        board = np.zeros((8, 8), object)
        board[0] = [-5, -4, -3, -2, -1, -3, -4, -5]
        board[1] = [-6]*8
        board[-2] = [6]*8
        board[-1] = [5, 4, 3, 2, 1, 3, 4, 5]

        for i in range(len(board)):
            board[i] = [Piece(val) if val != 0 else 0 for val in board[i]]

        return board


    def movePiece(self, start, end):

        possibleMoves, specialMoves = self.getPossibleMoves(start, special=True)
        if end in possibleMoves:
            for move in specialMoves:
                if move['move'] == (start, end):
                    if move['type'] == 'castle':
                        for (start_pos, end_pos) in move['additionalMoves']:
                            self._board[end_pos[1]][end_pos[0]] = self._board[start_pos[1]][start_pos[0]]
                            self._board[start_pos[1]][start_pos[0]] = 0
                    elif move['type'] == 'promotion':
                        if not self.test:
                            self._board[start[1]][start[0]].value = self._board[start[1]][start[0]].team * self.promotionCallback(end)
                        else:
                            self._board[start[1]][start[0]].value = self._board[start[1]][start[0]].team * 2

            self._board[end[1]][end[0]] = self._board[start[1]][start[0]]
            self._board[start[1]][start[0]] = 0
            if not self.test:
                self._board[end[1]][end[0]].has_moved = True
        else:
            print("Not a valid move:", start, end)



    def getBoardValues(self):
        return np.array(list(map(lambda l: [item.value if item != 0 else 0 for item in l], self.board)), int)


    def duplicateBoard(self):
        return copy.deepcopy(self)

    def checkForCheck(self, team):
        king = None
        for y in range(len(self.board)):
            for x in range(len(self.board[0])):
                if self.board[y][x] != 0 and self.board[y][x].value == team: king = (x, y)

        for y in range(len(self.board)):
            if any(king in self.getPossibleMoves((x, y), checking=True) for x in range(len(self.board[0])) if self.board[y][x] != 0): return True

        return False


    def getPossibleMoves(self, pos, checking=False, special=False):
        moves = []
        specialMoves = []
        (x, y) = pos
        piece = self.board[y][x]
        team = int(piece.value / abs(piece.value))

        if abs(piece.value) == 6:
            if self.board[y-team][x] == 0:
                moves.append((x, y-team))
                if piece.has_moved == False and self.board[y-2*team][x] == 0: moves.append((x, y-2*team))
            if x < 7 and 0 <= y-team <= 7:
                if self.board[y-team][x+1] != 0 and self.board[y-team][x+1].team != team: moves.append((x+1, y-team))
            if x > 0 and 0 <= y-team <= 7:
                if self.board[y-team][x-1] != 0 and self.board[y-team][x-1].team != team: moves.append((x-1, y-team))

            for move in moves:
                if move[1] == int(3.5-team*3.5): specialMoves.append({'type':'promotion','move':(pos, move)})
        elif abs(piece.value) == 5:
            for i in range(2, 9, 2): moves += self.createMovePath(pos, i)
        elif abs(piece.value) == 4:
            moves.append((pos[0]+1, pos[1]-2))
            moves.append((pos[0]-1, pos[1]-2))
            moves.append((pos[0]+1, pos[1]+2))
            moves.append((pos[0]-1, pos[1]+2))
            moves.append((pos[0]+2, pos[1]-1))
            moves.append((pos[0]-2, pos[1]-1))
            moves.append((pos[0]+2, pos[1]+1))
            moves.append((pos[0]-2, pos[1]+1))
        elif abs(piece.value) == 3:
            for i in range(1, 8, 2): moves += self.createMovePath(pos, i)
        elif abs(piece.value) == 2:
            for i in range(1, 9): moves += self.createMovePath(pos, i)
        elif abs(piece.value) == 1:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (j, i) != (0, 0): moves.append((x+j, y+i))

            if pos == (4, 0) or pos == (4, 7):
                for (rookX, mult) in [(0, 1), (7, -1)]:
                    if self.board[y][rookX] != 0:
                        if all(i == 0 for i in (self.board[y][min(rookX+mult, x-mult):max(rookX, x)])):
                            if abs(self.board[y][rookX].value) == 5 and self.board[y][rookX].team == team and self.board[y][rookX].has_moved == False:
                                moves.append((x - 2*mult, y))
                                specialMoves.append({'type':'castle','move':(pos, (x - 2*mult, y)),'additionalMoves':[((rookX, y), (x - mult, y))]})

        
        for move in moves[:]:
            if 0 > move[0] or move[0] > 7 or 0 > move[1] or move[1] > 7:
                moves.remove(move)
                continue
            dest = self.board[move[1]][move[0]]
            if dest != 0:
                if dest.team == team:
                    moves.remove(move)
                    continue
            if not checking and not self.test:
                testBoard = self.duplicateBoard()
                testBoard.test = True
                testBoard.movePiece(pos, move)
                if testBoard.checkForCheck(team):
                    moves.remove(move)

        if not special:   
            return moves
        else:
            return moves, specialMoves


    def createMovePath(self, pos, direction):
        moves = []
        (x, y) = pos
        piece = self.board[y][x]

        for i in range(1, 9):
            neighbor_list = [(x-i, y-i), (x, y-i), (x+i, y-i), (x+i, y), (x+i, y+i), (x, y+i), (x-i, y+i), (x-i, y)]
            moves.append(neighbor_list[direction-1])

        path = []
        for move in moves[:]:
            if 0 > move[0] or move[0] > 7 or 0 > move[1] or move[1] > 7: break
            movePiece = self.board[move[1]][move[0]]

            if movePiece == 0:
                path.append(move)
            else:
                if movePiece.team != piece.team:
                    path.append(move)
                break

        return path
