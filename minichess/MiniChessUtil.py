import re
import copy
from MiniChessConstants import *
import sys
from itertools import permutations

def translate(pos, variant='alamo'):

    if variant == 'alamo':
        chess_file = pos[0]
        chess_rank = pos[1]
        f = ALAMO_FILE_MAPPING[chess_file]
        r = ALAMO_RANK_MAPPING[int(chess_rank)]
        return (f,r)

def map_piece(piece, player):
    ''' piece is p,b,k,n,q
    player is 1 for white, -1 for black
    '''
    return player * PIECE_MAPPING[piece]

def decode_piece(num):
    if num == 0:
        return '.'
    elif num > 0:
        return PIECE_DECODER[num].lower()
    elif num < 0:
        return PIECE_DECODER[-1*num].upper() 


def enumerate_all_pos(variant='alamo'):

    if variant == 'alamo':
        ranks = ['1','2','3','4','5','6']
        files = ['a','b','c','d','e','f']

        positions = []
        for i in range(len(files)):
            for j in range(len(ranks)):
                positions.append(files[i]+ranks[j])


    return positions


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
