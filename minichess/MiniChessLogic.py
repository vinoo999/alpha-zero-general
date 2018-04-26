'''
Author: Eric P. Nichols
Date: Feb 8, 2008.
Board class.
Board data:
  1=white, -1=black, 0=empty
  first dim is column , 2nd is row:
     pieces[1][7] is the square in column 2,
     at the opposite end of the board in row 8.
Squares are stored and manipulated as (x,y) tuples.
x is the column, y is the row.
'''
import re
from MiniChessConstants import *
from MiniChessUtil import *
import numpy as np

class Board():

    #############################################################
    ############################ SET UP METHODS #################
    #############################################################

    def __init__(self, mcts_board = None, variant='alamo'):
        "Set up initial board configuration."

        self.variant = variant
        self.kings = {}
        if variant == 'alamo':
            if not mcts_board:
                self.init_alamo()
            else: 
                self.load(mcts_board)

    def init_alamo(self):
        '''Get alamo board'''
        self.board = np.zeros((6,6))

        positions = enumerate_all_pos('alamo')
        for pos in positions:
            i,j = translate(pos, 'alamo')
            color, piece = ALAMO_INIT_STATE[pos]
            if piece:
                num_color = COLOR_MAPPING[color]
                num_piece = PIECE_MAPPING[piece]
                if piece == KING:
                    self.kings[color] = pos
                self.board[i,j] = num_color*num_piece
            else:
                self.board[i,j] = 0
        return

    def load(mcts_board):
        self.board = mcts_board

    def get_board_mcts(self):
        return self.board

    def get_legal_moves(self, player):
        '''
        player is a number 1 for white -1 for black
        returns all legal moves in the form (promotion is none if no promo)
        {'from': 'a2', 'to':'a1', 'promotion':'q'}
        '''
        positions = enumerate_all_pos(self.variant)
        num_ranks = self.board.shape[0]
        num_files = self.board.shape[1]

        legal_moves = []
        for from_square in positions:
            r, f = translate(from_square, self.variant)
            piece_num = self.board[r,f]
            piece, color = decode_piece(piece_num, get_color=True)
            if not piece_num:
               continue 

            possibilities = get_potential_dests(r,f,piece, color, variant=self.variant)
            for dest_square in possibilities:
                r2,f2 = translate(dest_square)
                piece2, color2 = decode_piece(self.board[r2,f2], get_color=True)
                promotions = get_possible_promotions(from_square, dest_suare, piece, color, variant=self.variant)  
                if piece2 and color == color2:
                    continue
                
                for promo in promotions:
                    legal_moves.append({'from':from_squre, 'to':dest_square, 'promotion':promo})

        return legal_moves


