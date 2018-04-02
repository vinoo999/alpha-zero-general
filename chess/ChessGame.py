from __future__ import print_function
import sys
from ChessLogic import Board
from ChessUtil import swap_color, ascii
from ChessConstants import *
sys.path.append('..')
from Game import Game
import numpy as np
import copy


class ChessGame(Game):
    def __init__(self):
        self.n = 8

    def getInitBoard(self):
        # return initial board (numpy board)
        game = Board()
        return np.array(game.get_board_mcts())

    def getBoardSize(self):
        # (a,b) tuple
        return (self.n+1, self.n)

    def getActionSize(self):
        # return number of actions
        return self.n**4 + 16*4 + 1


    def getNextState(self, board, player, action):
        # if player takes action on board, return next (board,player)
        # action must be a valid move

        game = Board(mcts_board=board)
        player_color = WHITE if player==1 else BLACK
        if game.turn != player_color:
            return (None, None)

        if action == self.getActionSize()-1:
            game.turn = swap_color(game.turn)
            board = np.array(game.get_board_mcts())
            return (board, -player)

        elif action < self.getActionSize() - 16*4 - 1:
            tmp = action // 64
            rank1 = 'abcdefgh'[tmp//8]
            file1 = '87654321'[tmp%8]
            pos1 = rank1 + file1
            tmp2 = action % 64
            rank2 = 'abcdefgh'[tmp2//8]
            file2 = '87654321'[tmp2%8]
            pos2 = rank2 + file2

            move = {'from' : pos1, 'to' : pos2}
            game.do_move(move)
            next_board = np.array(game.get_board_mcts())

            return (next_board, -player)

        else:
            game.turn = swap_color(game.turn)
            board = np.array(game.get_board_mcts())
            return (board, -player)



        move = (int(action/self.n), action%self.n)
        b.execute_move(move, player)
        return (b.pieces, -player)

    def getValidMoves(self, board, player):
        # return a fixed size binary vector
        valids = [0]*self.getActionSize()
        b = Board(self.n)
        b.pieces = np.copy(board)
        legalMoves =  b.get_legal_moves(player)
        if len(legalMoves)==0:
            valids[-1]=1
            return np.array(valids)
        for x, y in legalMoves:
            valids[self.n*x+y]=1
        return np.array(valids)

    def getGameEnded(self, board, player):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost
        # player = 1
        b = Board(self.n)
        b.pieces = np.copy(board)
        if b.has_legal_moves(player):
            return 0
        if b.has_legal_moves(-player):
            return 0
        if b.countDiff(player) > 0:
            return 1
        return -1

    def getCanonicalForm(self, board, player):
        # return state if player==1, else return -state if player==-1
        return player*board

    def getSymmetries(self, board, pi):
        '''Chess is not symmetrical return size 1 list of [board]'''
        return [board]

    def stringRepresentation(self, board):
        # 8x8 numpy array (canonical board)
        return board.tostring()

    def getScore(self, board, player):
        b = Board(self.n)
        b.pieces = np.copy(board)
        return b.countDiff(player)

def display(board):
    game = Board(mcts_board=board)
    print(ascii(game))
