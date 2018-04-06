import re
import copy
from .ChessConstants import *

# /*****************************************************************************
 # * UTILITY FUNCTIONS
 # ****************************************************************************/

def generate_fen(chess):
    empty = 0
    fen = ''

    i = SQUARES['a8']
    while i < SQUARES['h1'] + 1:
    # for i in range(SQUARES['a8'], SQUARES['h1']+1):
        if (chess.board[i] == None):
            empty+=1
        else:
            if (empty > 0):
                fen += str(empty)
                empty = 0
            color = chess.board[i]['color']
            piece = chess.board[i]['type']

            fen += piece.upper() if (color == WHITE) else piece.lower()

        if ((i + 1) & 0x88):
            if (empty > 0):
                fen += str(empty)

            if (i != SQUARES['h1']):
                # print("ADDING A /: {} {}".format(i, fen))
                fen += '/'

            empty = 0
            i += 8

        i+=1

    cflags = ''
    if (chess.castling[WHITE] & BITS['KSIDE_CASTLE']):
        cflags += 'K'
    if (chess.castling[WHITE] & BITS['QSIDE_CASTLE']):
        cflags += 'Q'
    if (chess.castling[BLACK] & BITS['KSIDE_CASTLE']):
        cflags += 'k'
    if (chess.castling[BLACK] & BITS['QSIDE_CASTLE']):
        cflags += 'q'

    # /* do we have an empty castling flag? */
    cflags = cflags or '-'
    chess.epflags = '-' if (chess.ep_square == EMPTY) else algebraic(chess.ep_square)


    out_arr = [fen, chess.turn, cflags, chess.epflags, chess.half_moves, chess.move_number]
    out_arr = map(str, out_arr)
    return ' '.join(out_arr)

def validate_fen(fen):
        errors = {
            0: 'No errors.',
            1: 'FEN string must contain six space-delimited fields.',
            2: '6th field (move number) must be a positive integer.',
            3: '5th field (half move counter) must be a non-negative integer.',
            4: '4th field (en-passant square) is invalid.',
            5: '3rd field (castling availability) is invalid.',
            6: '2nd field (side to move) is invalid.',
            7: '1st field (piece positions) does not contain 8 \'/\'-delimited rows.',
            8: '1st field (piece positions) is invalid [consecutive numbers].',
            9: '1st field (piece positions) is invalid [invalid piece].',
            10: '1st field (piece positions) is invalid [row too large].',
            11: 'Illegal en-passant square',
        }

        # 1st criterion: 6 space-seperated fields? */
        tokens = re.split('\s+', fen)
        if (len(tokens) != 6):
            return {'valid': False, 'error_number': 1, 'error': errors[1]}
        

        # 2nd criterion: move number field is a integer value > 0? */
        if (not tokens[5].isdigit() or int(tokens[5]) <= 0):
            return {'valid': False, 'error_number': 2, 'error' : errors[2]}
        

        # 3rd criterion: half move counter is an integer >= 0? */
        if (not tokens[4].isdigit() or int(tokens[4]) < 0):
            return {'valid': False, 'error_number': 3, 'error': errors[3]}
        

        # 4th criterion: 4th field is a valid e.p.-string? */
        if (not re.search('^(-|[abcdefgh][36])$', tokens[3])):
            return {'valid': False, 'error_number': 4, 'error': errors[4]}
        

        # 5th criterion: 3th field is a valid castle-string? */
        if( not re.search('^(KQ?k?q?|Qk?q?|kq?|q|-)$',tokens[2])) :
            return {'valid': False, 'error_number': 5, 'error': errors[5]}
        

        # 6th criterion: 2nd field is "w" (white) or "b" (black)? */
        if (not re.search('^(w|b)$', tokens[1])) :
            return {'valid': False, 'error_number': 6, 'error': errors[6]}
        

        # 7th criterion: 1st field contains 8 rows? */
        rows = tokens[0].split('/')
        if (len(rows) != 8):
            return {'valid': False, 'error_number': 7, 'error': errors[7]}
        

        # 8th criterion: every row is valid? */
        for i in range(len(rows)):
            # check for right sum of fields AND not two numbers in succession */
            sum_fields = 0
            previous_was_number = False

            for k in range(len(rows[i])): 
                if (rows[i][k].isdigit()):
                    if (previous_was_number):
                        return {'valid': False, 'error_number': 8, 'error': errors[8]}
                    sum_fields += int(rows[i][k])
                    previous_was_number = True
                else:
                    if (not re.search('^[prnbqkPRNBQK]$',rows[i][k])):
                        return {'valid': False, 'error_number': 9, 'error': errors[9]}
                    sum_fields += 1
                    previous_was_number = False
            if (sum_fields != 8):
                return {'valid': False, 'error_number': 10, 'error': errors[10]}

        if (tokens[3] != '-' and ((tokens[3][1] == '3' and tokens[1] == 'w') or \
            (tokens[3][1] == '6' and tokens[1] == 'b'))):
            return {'valid': False, 'error_number': 11, 'error': errors[11]}

        # everything's okay! */
        return {'valid': True, 'error_number': 0, 'error': errors[0]}

def move_to_san(chess, move, sloppy=None) :
    '''/* convert a move from 0x88 coordinates to Standard Algebraic Notation
     * (SAN)
     *
     * @param {boolean} sloppy Use the sloppy SAN generator to work around over
     * disambiguation bugs in Fritz and Chessbase.  See below:
     *
     * r1bqkbnr/ppp2ppp/2n5/1B1pP3/4P3/8/PPPP2PP/RNBQK1NR b KQkq - 2 4
     * 4. ... Nge7 is overly disambiguated because the knight on c6 is pinned
     * 4. ... Ne7 is technically the valid SAN
     */'''

    output = ''
    # print("MOVE:", move)
    # print("FLAGS:", move['flags'])
    # print("FROM: {} TO: {}".format(move['from'], move['to']))
    if (move['flags'] & BITS['KSIDE_CASTLE']):
        output = 'O-O'
    elif (move['flags'] & BITS['QSIDE_CASTLE']):
        output = 'O-O-O'
    else:
        disambiguator = chess.get_disambiguator(move, sloppy)

        if (move['piece'] != PAWN):
            # print("PIECE: ",move['piece'])
            # print("DISAMBIG: ", disambiguator)
            output += move['piece'].upper() + disambiguator

        if (move['flags'] & (BITS['CAPTURE'] | BITS['EP_CAPTURE'])):
            if (move['piece'] == PAWN):
                output += algebraic(move['from'])[0]
            output += 'x'

        output += algebraic(move['to'])

        if (move['flags'] & BITS['PROMOTION']):
            output += '=' + move['promotion'].upper()

    chess.make_move(move)
    if (chess.in_check()):
        if (chess.in_checkmate()):
            output += '#'
        else:
            output += '+'
    chess.undo_move()

    return output

def ascii(chess):
    board = chess.board
    s = '   +------------------------+\n'
    i = SQUARES['a8']
    while i < SQUARES['h1'] + 1:
    # for i in range(SQUARES['a8'], SQUARES['h1']+1):
        # /* display the rank */
        if (col_file(i) == 0):
            s += ' ' + '87654321'[rank(i)] + ' |'
        # /* empty piece */
        if (board[i] == None):
            s += ' . '
        else:
            piece = board[i]['type']
            color = board[i]['color']
            symbol = piece.upper() if (color == WHITE) else piece.lower()
            s += ' ' + symbol + ' '
        if ((i + 1) & 0x88):
            s += '|\n'
            i += 8

        i += 1
    s += '   +------------------------+\n'
    s += '     a  b  c  d  e  f  g  h\n'

    return s

# // parses all of the decorators out of a SAN string
def stripped_san(move):
    return move.replace('=','').replace('[+#]?[?!]*$','')


def rank(i):
    return i >> 4

def col_file(i):
    return i & 15

def algebraic(i):
    f = col_file(i)
    r = rank(i)
    files = 'abcdefgh'
    ranks = '87654321'
    return files[f] + ranks[r]

def mirror_num(i):
    f = col_file(i)
    r = rank(i)
    files = 'abcdefgh'
    ranks = '12345678'
    pos = files[f] + ranks[r]
    return SQUARES[pos]

def swap_color(c):
    return BLACK if c==WHITE else WHITE

def is_digit(c):
    return c.isdigit()
# /* pretty = external move object */
def make_pretty(chess, ugly_move):
    move = copy.deepcopy(ugly_move)
    move['san'] = move_to_san(chess, move, False)
    move['to'] = algebraic(move['to'])
    move['from'] = algebraic(move['from'])

    flags = ''

    for flag in BITS:
        if (BITS[flag] & move['flags']):
            flags += FLAGS[flag]
    move['flags'] = flags

    return move

def evaluate_board(mcts_board, player):
    board = mcts_board[0:8,:]

    val = 0
    for i in range(8):
        for j in range(8):
            piece = MCTS_DECODER[abs(board[i,j])]
            sign = -1 if board[i,j] < 0 else 1
            val += get_piece_value(piece,i,j, sign)

    return val

def get_piece_value(piece, i, j, color):
    eval_map = {
        'p' : PAWN_EVAL,
        'n' : KNIGHT_EVAL,
        'b' : BISHOP_EVAL,
        'r' : ROOK_EVAL,
        'q' : QUEEN_EVAL,
        'k' : KING_EVAL
    }

    eval_offset = {
        'p' : 10,
        'n' : 30,
        'b' : 30,
        'r' : 50,
        'q' : 90,
        'k' : 900
    }

    eval_mat = eval_map[piece]

    if piece > 0:
        return eval_offset[piece] + eval_mat[j][i]
    else:
        return color*(eval_offset[piece] + eval_mat[::-1][j][i])


def trim(str):
    return str.replace('^\s+|\s+$', '')

##########################################
# DEBUGGING UTILITIES
########################################
def perft(chess, depth):
    moves = chess.generate_moves({legal: false})
    nodes = 0
    color = turn

    i = 0
    while i < len(moves):
        make_move(moves[i])
        if (not king_attacked(color)):
            if (depth - 1 > 0):
                child_nodes = perft(depth - 1)
                nodes += child_nodes
            else:
                nodes+=1
        chess.undo_move()
        i+=1
    return nodes

def decode_move(action):

    if action == 64*64-1:
        return "Switch Player"

    elif action < 64*64+64*4+1 - 64*4 - 1:
        tmp = action // 64
        file1 = 'abcdefgh'[tmp//8]
        rank1 = '87654321'[tmp%8]
        pos1 = file1 + rank1
        tmp2 = action % 64
        file2 = 'abcdefgh'[tmp2//8]
        rank2 = '87654321'[tmp2%8]
        pos2 = file2 + rank2

        move = {'from' : pos1, 'to' : pos2}

        return move

    else:
        action_offset = action - 64*64
        tmp = action_offset // 16
        file1 = 'abcdefgh'[tmp//2]
        rank1 = '72'[tmp%2]
        rank2 = '81'[tmp%2]

        tmp2 = action_offset % 16
        promotion = tmp2//4 + 2
        direction = tmp2%4

        player = 1 if tmp%2 == 0 else -1
        file2 = 'abcdefgh'[(tmp//2) - (direction-1)*player]

        pos1 = file1 + rank1
        pos2 = file2 + rank2
        move = {'from' : pos1, 'to' : pos2, 'promotion' : MCTS_DECODER[promotion]}

        return move



