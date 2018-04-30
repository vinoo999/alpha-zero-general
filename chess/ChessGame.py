from __future__ import print_function
from .ChessLogic import Board
from .ChessUtil import *
from .ChessConstants import *
from collections import defaultdict
import numpy as np
import copy, sys

sys.path.append('..')
from Game import Game

class ChessGame(Game):
    def __init__(self):
        self.n = 8
        self.state_counts = defaultdict(int)

    def getInitBoard(self):
        self.state_counts = defaultdict(int)
        return np.array(Board().get_board_mcts())

    def getBoardSize(self):
        return (self.n + 1, self.n)

    def getActionSize(self):
        # return number of actions
        # 64*64 = number of moves from square a -> square b
        # 16*4 = 16 different moves for a pawn to promote to 4 different things
        # return self.n**4 + 64*4 + 1
        return 4353


    def getNextState(self, board, player, action):
        # if player takes action on board, return next (board,player)
        # action must be a valid move
        game = Board(mcts_board=board)
        
        player_color = WHITE if player==1 else BLACK

        if action == self.getActionSize()-1:
            game.turn = swap_color(game.turn)

            next_board = np.array(game.get_board_mcts())
            self.state_counts[self.stringRepresentation(next_board)] += 1

            return (next_board, -player)

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
            self.state_counts[self.stringRepresentation(next_board)] += 1

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

            tmp_player = 1 if tmp%2 == 0 else -1
            file2 = 'abcdefgh'[(tmp//2) - (direction-1)*tmp_player]

            pos1 = file1 + rank1
            pos2 = file2 + rank2

            move = {'from' : pos1, 'to' : pos2, 'promotion' : MCTS_DECODER[promotion]}
            game.do_move(move)

            next_board = np.array(game.get_board_mcts())
            self.state_counts[self.stringRepresentation(next_board)] += 1

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
        b = Board(mcts_board=board)
        str_rep_no_move = self.stringRepresentation(board)
        
        if b.turn == WHITE and b.in_checkmate():
            return -1 * player

        if b.in_stalemate() or b.insufficient_material() or b.half_moves >= 50 or self.state_counts[str_rep_no_move] >= 3:
            return 1e-2

        if b.turn == BLACK and b.in_checkmate():
            return 1 * player
        
        return 0


    def getCanonicalForm(self, board, player):
        # We play by color rather than by flipping the board
        return copy.deepcopy(board)

    def getSymmetries(self, board, pi):
        # Chess is not symmetrical
        return [(board,pi)]

    def stringRepresentation(self, board):
        # Right now the last row stores the number of half moves and num moves. 
        # Like 3 fold rep, all we care about is board state. 
        temp1 = board[8,6]
        temp2 = board[8,7]

        board[8,6] = 0   # Zero out half moves
        board[8,7] = 0   # Zero out num moves

        res = board.tostring()

        board[8,6] = temp1
        board[8,7] = temp2

        return res

    def getScore(self, board, player):
        return evaluate_board(board, player)

def display(board):
    game = Board(mcts_board=board)
    print(ascii(game))
