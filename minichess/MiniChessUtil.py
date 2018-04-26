import re
import copy
from MiniChessConstants import *
import sys
from itertools import permutations
import numpy as np

def translate(pos, variant='alamo'):
    ''' Take pos in algebraic format and return (rank,file)'''
    if variant == 'alamo':
        chess_file = pos[0]
        chess_rank = pos[1]
        f = ALAMO_FILE_MAPPING[chess_file]
        r = ALAMO_RANK_MAPPING[int(chess_rank)]
        return (r,f)

def algebraic(r,f, variant='alamo'):
    ''' take position in r,f format and return algebraic (a1) format'''
    if variant == 'alamo':
        ranks = ['1','2','3','4','5','6']
        files = ['a','b','c','d','e','f']
        return files[f] + ranks[6-r-1]

def map_piece(piece, player):
    ''' piece is p,b,k,n,q
    player is 1 for white, -1 for black
    '''
    return player * PIECE_MAPPING[piece]

def decode_piece(num, get_color = False):
    '''take a number +/-1,2,3,5,9,100 and return the piece associated'''
    if get_color:
        if num == 0:
            return (None, None)
        else:
            return (PIECE_DECODER[abs(num)].lower(), np.sign(num))
    else:
        if num == 0:
            return '.'
        elif num > 0:
            return PIECE_DECODER[num].lower()
        elif num < 0:
            return PIECE_DECODER[-1*num].upper()

def encode_move(from_pos, to_pos, promotion=None, variant='alamo'):
    r,f = translate(pos)
    pass

def decode_move(num, variant='alamo'):
    pass

def enumerate_all_pos(variant='alamo'):

    if variant == 'alamo':
        ranks = ['1','2','3','4','5','6']
        files = ['a','b','c','d','e','f']

        positions = []
        for i in range(len(files)):
            for j in range(len(ranks)):
                positions.append(files[i]+ranks[j])

    return positions

def get_possible_promotions(from_square, to_square, piece, color, variant='alamo'):
    '''
    Return all allowed promotions. Also check if promotion is possible given state
    Does not check file. Expected that this is a legal move.'''
    if piece != PAWN:
        return [None]
    else:
        r,f = translate(from_square)
        r2,f2 = translate(to_square)
        num_ranks = BOARD_SIZE[variant]
        if (color == WHITE and r==1 and r2==0) or \
        (color == BLACK and r==num_ranks-2 and r2==num_ranks-1):
            if variant == 'alamo':
                possible_promos = ['k','r','q']
            return possible_promos
        else:
            return [None]

def get_potential_dests(r, f, piece, color, variant='alamo'):
    piece_num = 0
    pass

def evaluate_board(board, player):
    """
    Input: 
        mcts_board:
        player:

    Return:
        score: score of the board relative to the current player
    """
    score = 0
    num_rows, num_cols = board.shape(board)

    for row in range(num_rows):
        for col in range(num_cols):

            piece_abs_value = abs(board[row,col])

            #Ignore all positions on the board without a piece
            if piece_abs_value == 0:
                continue

            #Add the relative value of the piece
            piece_color = -1 if board[row,col] < 0 else 1
            score += piece_abs_value * piece_color * player

    return score

def ascii(board):
    s = '   +--------------------+\n'
    
    for chess_rank in range(board.shape[0]-1, -1, -1):
        for chess_file in range(board.shape[1]):
            if chess_file == 0:
                s += ' ' + str(chess_rank+1) + ' |'
            
            s += ' '  + decode_piece(board[chess_rank,chess_file]) + ' '
        s += '|\n'
    s += '   +-------------------+\n'
    s += '     a  b  c  d  e  f \n'

    return s
