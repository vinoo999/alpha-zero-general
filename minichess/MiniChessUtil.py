import re
import copy
from MiniChessConstants import *
import sys
from itertools import permutations
import numpy as np
import sys

def translate(pos, variant='alamo'):
    ''' Take pos in algebraic format and return (rank,file)'''
    if variant == 'alamo':
        chess_file = pos[0]
        chess_rank = pos[1]
        f = ALAMO_FILE_MAPPING[chess_file]
        r = ALAMO_RANK_MAPPING[int(chess_rank)]
        return (r,f)

def algebraic(r,f, variant='alamo'):
    """
    Input:
        r: piece rank
        f: piece file
    Return:
        algebraic incoding ("a1") of the piece's position
    """

    if variant == 'alamo':
        ranks = ['1','2','3','4','5','6']
        files = ['a','b','c','d','e','f']
        return files[f] + ranks[6-r-1]

def encode_square(pos, variant='alamo'):
    '''
    Input: Algebraic position
    Output: Number value of square
    '''
    r,f = translate(pos)
    r_limit = BOARD_SIZE['alamo'][0]
    return r*r_limit + f

def decode_square(num, variant='alamo'):
    '''
    Input: Number value of square
    Output: Algebraic position
    '''
    r_limit = BOARD_SIZE['alamo'][0]
    r = num // r_limit
    f = num % r_limit
    return(algebraic(r,f,variant))


def map_piece(piece, player):
    ''' piece is p,b,k,n,q
    player is 1 for white, -1 for black
    '''
    return player * PIECE_MAPPING[piece]

def decode_piece(num, get_color = False):
    """
        Input:
            num: a number +/-1,2,3,5,9,100 representing a game piece
        Return:
            if get_color flag:
                    return (piece's lowercase character ("q"), and it's color)
            else:
                    return piece's character, upper for white, lower for black
    """
    if get_color:
        if num == 0:
            return (None, None)
        else:
            return (PIECE_DECODER[abs(num)].lower(), np.sign(num))
    else:
        if num == 0:
            return '.'
        elif num > 0:
            return PIECE_DECODER[num].upper()
        elif num < 0:
            return PIECE_DECODER[-1*num].lower()

def reverse_square(pos, variant='alamo'):
    '''
    Take an algebraic position and mirror it across the origin
    '''
    r,f = translate(pos)
    r_limit, f_limit = BOARD_SIZE[variant]
    r_new = r_limit - r
    f_new = f_limit - f
    return algebraic(r_new, f_new, variant)


def encode_move(move, color, variant='alamo'):
    from_pos = move['from']
    to_pos = move['to']
    promotion = move['promotion']

    r_limit, f_limit = BOARD_SIZE[variant]

    if color == -1: # Player is Black
        from_pos = reverse_square(from_pos)
        to_pos = reverse_square(to_pos)

    if not promotion:
        square1 = encode_square(from_pos, variant)
        square2 = encode_square(to_pos, variant)
        return r_limit*f_limit*square1 + square2
    else:
        offset = (r_limit*f_limit)**2

        r1,f1 = translate(from_pos)
        r2,f2 = translate(to_pos)

        direction = f2-f1+1
        rank_abbrv = 0 if r1 == 1 else 1
        
        promo_integer = [QUEEN, ROOK, KNIGHT, BISHOP].index(promotion)

        num = f_limit*2*(2*f1 + rank_abbrv) + promo_integer*4 + direction + offset
        return num

def decode_move(num, color, variant='alamo'):
    r_limit, f_limit = BOARD_SIZE[variant]

    if num < (r_limit*f_limit)**2: # not a promotion
        square1 = num // (r_limit*f_limit)
        square2 = num % (r_limit*f_limit)
        from_pos = decode_square(square1)
        to_pos = decode_square(square2)
        promotion = None
    
    else: # promotion
        num = num - (r_limit*f_limit)**2

        first_encoding = num // (f_limit*2)
        second_encoding = num % (f_limit*2)

        f1 = first_encoding//2
        rank_abbrv = first_encoding % 2
        r1 = 

        promo_integer = second_encoding//4
        direction = second_encoding % 4
        f2 = f1 + direction - 1




    if color == -1: # Player is Black
        from_pos = reverse_square(from_pos, variant)
        to_pos = reverse_square(to_pos, variant)

    move = {'from': from_pos, 'to': to_pos, 'promotion': promotion}
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
        num_ranks, num_files = BOARD_SIZE[variant]
        if (color == WHITE and r==1 and r2==0) or \
        (color == BLACK and r==num_ranks-2 and r2==num_ranks-1):
            if variant == 'alamo':
                possible_promos = ['k','r','q']
            return possible_promos
        else:
            return [None]

def get_potential_dests(r, f, piece, color, variant='alamo'):
    '''
    Return all squares in algebraic form that fall in the possible
    desitinations of a piece. Ignores validity
    '''
    r_limit, f_limit = BOARD_SIZE[variant]
    possibilities = []
    if piece == PAWN:
        possibilities.append(algebraic(r-color, f, variant))
        if f-1 != 0:
            possibilities.append(algebraic(r-color, f-1, variant))
        if f+1 < f_limit:
            possibilities.append(algebraic(r-color, f+1, variant))
    if piece == KNIGHT:
        if r+1<r_limit:
            if f+2<f_limit:
                possibilities.append(algebraic(r+1, f+2, variant))
            if f-2>= 0:
                possibilities.append(algebraic(r+1, f-2, variant))
        if r-1 >= 0:
            if f+2<f_limit:
                possibilities.append(algebraic(r-1, f+2, variant))
            if f-2>= 0:
                possibilities.append(algebraic(r-1, f-2, variant))
        if r+2<r_limit:
            if f+1<f_limit:
                possibilities.append(algebraic(r+2, f+1, variant))
            if f-1>= 0:
                possibilities.append(algebraic(r+2, f-1, variant))
        if r-2>=0:
            if f+1<f_limit:
                possibilities.append(algebraic(r-2, f+1, variant))
            if f-1>= 0:
                possibilities.append(algebraic(r-2, f-1, variant))

    if piece == KING:
        if r+1 < r_limit:
            possibilities.append(algebraic(r+1, f, variant))
        if r-1 >= 0:
            possibilities.append(algebraic(r-1, f, variant))
        if f+1 < f_limit:
            possibilities.append(algebraic(r, f+1, variant))
        if f-1 >= 0:
            possibilities.append(algebraic(r, f-1, variant))
        if r+1 < r_limit and f+1 < f_limit:
            possibilities.append(algebraic(r+1, f+1, variant))
        if r+1 < r_limit and f-1 >= 0:
            possibilities.append(algebraic(r+1, f-1, variant))
        if r-1 >= 0 and f+1 < f_limit:
            possibilities.append(algebraic(r-1, f+1, variant))
        if r-1 >= 0 and f-1 >= 0:
            possibilities.append(algebraic(r-1, f-1, variant))

    if piece == ROOK:
        for i in range(r_limit):
            if i == r:
                continue
            possibilities.append(algebraic(i, f, variant))
        for i in range(f_limit):
            if i == f:
                continue
            possibilities.append(algebraic(r, i, variant))

    if piece == QUEEN:
        for i in range(r_limit):
            if i == r:
                continue
            possibilities.append(algebraic(i, f, variant))
        for i in range(f_limit):
            if i == f:
                continue
            possibilities.append(algebraic(r, i, variant))
        
        for i in range(r+1, r_limit):
            if f+(i-r) < f_limit:
                possibilities.append(algebraic(i, f+i-r, variant))
            if f-(i-r) >= f_limit:
                possibilities.append(algebraic(i, f-(i-r), variant))
        for i in range(0, r):
            if f+(r-i) < f_limit:
                possibilities.append(algebraic(i, f+r-i, variant))
            if f-(r-i) >= f_limit:
                possibilities.append(algebraic(i, f-(r-i), variant))


    return possibilities

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
    
    for chess_rank in range(board.shape[0]):
        for chess_file in range(board.shape[1]):
            if chess_file == 0:
                s += ' ' + str(board.shape[0]-chess_rank) + ' |'
            s += ' '  + decode_piece(board[chess_rank,chess_file]) + ' '
        s += '|\n'
    s += '   +-------------------+\n'
    s += '     a  b  c  d  e  f \n'

    return s
