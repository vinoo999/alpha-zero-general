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

    def __init__(self, variant='alamo'):
        "Set up initial board configuration."

        self.variant = variant
        self.kings = {}
        if variant == 'alamo':
            self.init_alamo()

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


    def get_legal_moves(self, player):
        '''player is a number 1 for white -1 for black'''
        positions = enumerate_all_pos(self.variant)
        num_ranks = self.board.shape[0]
        num_files = self.board.shape[1]

        for pos in positions:
            f, r = translate(pos, self.variant)



