import re
import copy
from MiniChessConstants import *
import sys
from itertools import permutations

def translate(pos, variant='alamo'):
    ''' Take pos in a1 format and return (rank,file)'''
    if variant == 'alamo':
        chess_file = pos[0]
        chess_rank = pos[1]
        f = ALAMO_FILE_MAPPING[chess_file]
        r = ALAMO_RANK_MAPPING[int(chess_rank)]
        return (r,f)

def map_piece(piece, player):
    ''' piece is p,b,k,n,q
    player is 1 for white, -1 for black
    '''
    return player * PIECE_MAPPING[piece]

def decode_piece(num):
    '''take a number +/-1,2,3,5,9,100 and return the piece associated'''
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

            piece_key = abs(board[row,col])

            #Ignore all positions on the board without a piece
            if piece_key == 0:
                continue

            #Grab the letter representation of the piece with it's key
            piece = PIECE_DECODER[piece_key]

            #Add the relative value of the piece
            piece_color = -1 if board[row,col] < 0 else 1
            score += PIECE_MAPPING[piece] * piece_color * player

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