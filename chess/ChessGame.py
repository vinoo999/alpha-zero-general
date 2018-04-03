from __future__ import print_function
import sys
from .ChessLogic import Board
from .ChessUtil import *
from .ChessConstants import *
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
        # 64*64 = number of moves from square a -> square b
        # 16*4 = 16 different moves for a pawn to promote to 4 different things
        return self.n**4 + 64*4 + 1


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

        elif action < self.getActionSize() - 64*4 - 1:
            tmp = action // 64
            file1 = 'abcdefgh'[tmp//8]
            rank1 = '87654321'[tmp%8]
            pos1 = file1 + rank1
            tmp2 = action % 64
            file2 = 'abcdefgh'[tmp2//8]
            rank2 = '87654321'[tmp2%8]
            pos2 = file2 + rank2

            move = {'from' : pos1, 'to' : pos2}
            game.do_move(move)
            next_board = np.array(game.get_board_mcts())

            return (next_board, -player)

        else:
            action_offset = action - 64*64
            tmp = action_offset // 16
            file1 = 'abcdefgh'[tmp//2]
            rank1 = '72'[tmp%2]
            rank2 = '81'[tmp%2]

            tmp2 = action_offset % 16
            promotion = tmp2//4 + 2
            direction = tmp2%4
            file2 = 'abcdefgh'[(tmp//2) + (direction-1)*player]

            pos1 = file1 + rank1
            pos2 = file2 + rank2
            move = {'from' : pos1, 'to' : pos2, 'promotion' : MCTS_DECODER[promotion]}

            game.do_move(move)
            next_board = np.array(game.get_board_mcts())
            return (next_board, -player)

    def getValidMoves(self, board, player):
        # return a fixed size binary vector
        valids = [0]*self.getActionSize()
        b = Board(mcts_board=board)
        legalMoves = b.generate_moves({'legal': True})
        for move in legalMoves:
            pos1 = algebraic(move['from'])
            pos2 = algebraic(move['to'])

            file1 = pos1[0]
            rank1 = pos1[1]
            file2 = pos2[0]
            rank2 = pos2[1]

            file1_idx = 'abcdefgh'.index(file1)
            file2_idx = 'abcdefgh'.index(file2)
            rank1_idx = '87654321'.index(rank1)
            rank2_idx = '87654321'.index(rank2)
            
            if 'promotion' in move.keys():
                promotion = MCTS_MAPPING[move['promotion']]-2 # move range to 0-3
                offset = 64*64
                direction = abs(move['from'] - move['to']) - 16 + 1
                    # 0 means promote takes right
                    # 1 means advance
                    # 2 means promote takes left
                rank_abbrv = 0 if move['color'] == WHITE else 1
                num = promotion*4 + direction + 16*(2*file1_idx + rank_abbrv) + offset
            else:
                num = (8*file1_idx + rank1_idx)*64 + 8*file2_idx + rank2_idx

            
            valids[num] = 1

        return np.array(valids)

    def getGameEnded(self, board, player):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost
        # player = 1
        b = Board(mcts_board=board)
        b.turn = WHITE if player == 1 else BLACK

        if b.in_checkmate():
            return -1
        if b.in_stalemate() or b.insufficient_material():
            return 1e-5
        b.turn = swap_color(b.turn)
        if b.in_checkmate():
            return 1
        
        return 0

    def getCanonicalForm(self, board, player):
        if player == 1: # WHITE
            return board

        new_board = -1*board[0:8,:][::-1]

        old_row = board[len(board)-1]
        row = np.zeros(old_row.shape)

        row[0] = mirror_num(old_row[0]) # king 1
        row[1] = mirror_num(old_row[1]) # king 2
        row[2] = old_row[2]*-1
        row[3] = old_row[4]
        row[4] = old_row[3]
        row[5] = -1 if old_row[5] == -1 else mirror_num(old_row[5])
        row[6] = old_row[6]
        row[7] = old_row[7]

        new_board = np.vstack((new_board, row))
        # return state if player==1, else return -state if player==-1
        return new_board

    def getSymmetries(self, board, pi):
        '''Chess is not symmetrical'''
        return [(board,pi)]

    def stringRepresentation(self, board):
        # 8x8 numpy array (canonical board)
        return board.tostring()

    def getScore(self, board, player):
        b = Board(mcts_board=board)
        return evaluate_board(board, player)

def display(board):
    game = Board(mcts_board=board)
    print(ascii(game))
