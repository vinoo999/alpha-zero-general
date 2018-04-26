import re
from .MiniChessConstants import *
from .MiniChessUtil import *
import numpy as np
import copy

class Board():

    #############################################################
    ############################ SET UP METHODS #################
    #############################################################

    def __init__(self, mcts_board = None, variant='alamo'):
        "Set up initial board configuration."

        self.variant = variant
        self.kings = {}
        self.turn = 1
        self.half_moves = 0
        self.total_moves = 0
        self.state_count = 0

        if variant == 'alamo':
            if mcts_board is None:
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

    def load(self,mcts_board):

        """
        Input: 
            mcts_board: a mcts np array board
        Output: 
            set all parameters of the board
        """
        # print(mcts_board.shape)
        mcts_board = copy.deepcopy(mcts_board)
        self.board = mcts_board[0:6, :]

        last_row = mcts_board[6,:]

        self.kings[1], self.kings[-1] = decode_square(last_row[0]), decode_square(last_row[1])
        self.turn = last_row[2]
        self.half_moves = last_row[3]
        self.total_moves = last_row[4]
        self.state_count = last_row[5]


    def get_board_mcts(self):
        """
        Return:
            A modifed board (mcts) that has game state knowledge appended as it's last row
            Last row is as follows:
                1) position white king  2) position black king,
                3) current player color 4) number of half moves
                5) number of full moves 6) board state count
        """

        #Convert algebraic position of the white/black king to int
        white_king_pos, black_king_pos = encode_square(self.kings[1]), encode_square(self.kings[-1])

        last_row = np.array([white_king_pos, black_king_pos,
                             self.turn, self.half_moves,
                             self.total_moves, self.state_count
                            ])

        return np.vstack([self.board, last_row])


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
                # print("IN CHECK")
                # print(ascii(self.board))
                # print("Player: ", player)
                self.do_move({'from':to_square, 'to':from_square, 'promotion':None})
                self.board[r2,f2] = temp
                self.total_moves -= 2
                continue
            self.do_move({'from':to_square, 'to':from_square, 'promotion':None})
            self.total_moves -= 2
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

    def insufficient_material(self, color):
        num_pieces = 0
        for i in range(self.board.shape[0]):
            for j in range(self.board.shape[1]):
                if self.board[i,j]:
                    num_pieces += 1
        if num_pieces == 2:
            return True
        else:
            return False

    def in_threefold_repitition(self, color):
        if self.state_count == 3:
            return True
        else:
            return False

    def in_check(self, color):
        '''returns if the player (1 for white, -1 for black) is in check'''
        my_king = self.kings[color]
        legal_moves = self._get_pseudo_legal_moves(-color)
        for move in legal_moves:
            if move['to'] == my_king:
                # print("******")
                # print(move['from'], move['to'])
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
        piece, color = decode_piece(value, get_color=True)
        if move['promotion']:
            value = map_piece(move['promotion'], color)
        self.board[to_r, to_f] = value
        self.board[from_r, from_f] = 0
        self.turn = -self.turn
        self.total_moves += 1
        
        if piece == PAWN or captured:
            self.half_moves = 0
        else:
            self.half_moves += 1

        if piece == KING:
            self.kings[color] = algebraic(to_r,to_f)

        return captured


