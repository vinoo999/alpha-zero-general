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
        self.turn = 1
        if variant == 'alamo':
            if not mcts_board:
                self.init_alamo()
            else: 
                self.load(mcts_board)

    def init_alamo(self):
        '''Get alamo board'''
        self.board = np.zeros((6,6), dtype=int)
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


    def _get_pseudo_legal_moves(self, player):
        '''returns all legal moves based on position including ones that would 
        put a king in check'''
        positions = enumerate_all_pos(self.variant)
        num_ranks = self.board.shape[0]
        num_files = self.board.shape[1]

        legal_moves = []
        for from_square in positions:
            r, f = translate(from_square, self.variant)
            piece_num = self.board[r,f]
            piece, color = decode_piece(piece_num, get_color=True)
            if not piece_num or color != player:
               continue 

            possibilities = get_potential_dests(r,f,piece, color, variant=self.variant)
            for dest_square in possibilities:
                r2,f2 = translate(dest_square)
                piece2, color2 = decode_piece(self.board[r2,f2], get_color=True)
                promotions = get_possible_promotions(from_square, dest_square, piece, color, variant=self.variant)  
                
                #####################################################
                ####            LEGALITY CHECK                  #####
                #####################################################
                # Check if piece present in destination and can be taken if not continue
                if (piece2 and (color == color2 or (color == -color2 and piece == PAWN and f == f2))):
                    continue
                # Check if pawn can move in this direction
                if ((not piece2) and piece == PAWN and f != f2):
                    continue
                # Check if blocked
                if self.is_blocked(piece, from_square, dest_square):
                    continue

                for promo in promotions:
                    legal_moves.append({'from':from_square, 'to':dest_square, 'promotion':promo})
        return legal_moves

    def get_legal_moves(self, player):
        '''
        player is a number 1 for white -1 for black
        returns all legal moves in the form (promotion is none if no promo)
        {'from': 'a2', 'to':'a1', 'promotion':'q'}
        '''
        move_potentials = self._get_pseudo_legal_moves(player)
        legal_moves = []
        for move in move_potentials:
            # Check if King attacked by temporary changing state
            from_square = move['from']
            to_square = move['to']
            r,f = translate(from_square)
            r2,f2 = translate(to_square)
            temp = self.board[r2,f2]
            self.do_move({'from':from_square, 'to':to_square, 'promotion':None})
            if self.in_check(player):
                self.do_move({'from':to_square, 'to':from_square, 'promotion':None})
                self.board[r2,f2] = temp
                continue
            self.do_move({'from':to_square, 'to':from_square, 'promotion':None})
            self.board[r2,f2] = temp
            legal_moves.append(move)

        return legal_moves


    def is_blocked(self, piece, from_square, to_square):
        '''
        For a path from from_square to to_square return if the path is blocked
        by some other piece
        '''
        # TODO: Change for other variants, alamo there is no double move for pawn
        if piece == KING or piece == PAWN or piece == KNIGHT:
            return False

        r1,f1 = translate(from_square)
        r2,f2 = translate(to_square)

        df = 0 if f2-f1 == 0 else int((f2-f1)/abs(f2-f1))
        dr = 0 if r2-r1 == 0 else int((r2-r1)/abs(r2-r1))

        cur_square = [r1,f1]
        while ((cur_square[0] != r2-dr or dr==0) and (cur_square[1] != f2-df or df == 0)):
            cur_square = [cur_square[0]+dr, cur_square[1]+df]
            if self.board[cur_square[0],cur_square[1]]:
                return True
        return False 


    def in_checkmate(self, color):
        '''returns if the player=color (1 for white, -1 for black) is in 
        checkmate'''
        if self.in_check(color) and len(self.get_legal_moves(color)) == 0:
            return True
        else:
            return False

    def in_stalemate(self, color):
        '''returns if the player (1 for white, -1 for black) is in a stalemate'''
        if (not self.in_check(color)) and len(self.get_legal_moves(color)) == 0:
            return True
        else: 
            return False

    def in_check(self, color):
        '''returns if the player (1 for white, -1 for black) is in check'''
        my_king = self.kings[color]
        legal_moves = self._get_pseudo_legal_moves(-color)
        for move in legal_moves:
            if move['to'] == my_king:
                return True
        return False

    def do_move(self, move):
        '''
        Does not validate a move
        move of the form {'from': 'a2', 'to':'a1', 'promotion':'q'}
        moves piece in from to the square in to
        returns the piece that was in to 
        '''
        from_r, from_f = translate(move['from'])
        to_r, to_f = translate(move['to'])
        value = self.board[from_r, from_f]
        captured = self.board[to_r, to_f]
        captured, _ = decode_piece(captured, get_color=True)
        if move['promotion']:
            piece, color = decode_piece(value, get_color=True)
            value = map_piece(move['promotion'], color)
        self.board[to_r, to_f] = value
        self.board[from_r, from_f] = 0
        return captured


