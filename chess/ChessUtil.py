import re
import copy
from ChessConstants import *

# /*****************************************************************************
 # * UTILITY FUNCTIONS
 # ****************************************************************************/

def generate_fen(chess):
    board = chess.board
    empty = 0
    fen = ''

    for (i in range(SQUARES.a8, SQUARES.h1+1)):
        if (board[i] == None):
            empty+=1
        else:
            if (empty > 0):
                fen += empty
                empty = 0
            color = board[i]['color']
            piece = board[i]['type']

            fen += piece.upper() if (color === WHITE) else piece.lower()

        if ((i + 1) & 0x88):
            if (empty > 0):
                fen += empty

            if (i != SQUARES.h1):
                fen += '/'

            empty = 0
            i += 8

    cflags = ''
    if (castling[WHITE] & BITS.KSIDE_CASTLE):
        cflags += 'K'
    if (castling[WHITE] & BITS.QSIDE_CASTLE):
        cflags += 'Q'
    if (castling[BLACK] & BITS.KSIDE_CASTLE):
        cflags += 'k'
    if (castling[BLACK] & BITS.QSIDE_CASTLE):
        cflags += 'q'

    # /* do we have an empty castling flag? */
    cflags = cflags or '-'
    epflags = '-' if (ep_square === EMPTY) else algebraic(ep_square)

    return [fen, turn, cflags, epflags, half_moves, move_number].join(' ')

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
        if (tokens.length != 6):
            return {'valid': False, 'error_number': 1, 'error': errors[1]}
        

        # 2nd criterion: move number field is a integer value > 0? */
        if (tokens[5] is None or int(tokens[5] <= 0)):
            return {'valid': False, 'error_number': 2, 'error:' errors[2]}
        

        # 3rd criterion: half move counter is an integer >= 0? */
        if (tokens[4] is None or int(tokens[4]) < 0)):
            return {'valid': False, 'error_number': 3, 'error:' errors[3]}
        

        # 4th criterion: 4th field is a valid e.p.-string? */
        if (not re.search('^(-|[abcdefgh][36])$', tokens[3]):
            return {'valid': False, 'error_number': 4, 'error:' errors[4]}
        

        # 5th criterion: 3th field is a valid castle-string? */
        if( not re.search('^(KQ?k?q?|Qk?q?|kq?|q|-)$',tokens[2])) :
            return {'valid': False, 'error_number': 5, 'error:' errors[5]}
        

        # 6th criterion: 2nd field is "w" (white) or "b" (black)? */
        if (not re.search('^(w|b)$', tokens[1])) :
            return {'valid': False, 'error_number': 6, 'error:' errors[6]}
        

        # 7th criterion: 1st field contains 8 rows? */
        rows = tokens[0].split('/')
        if (len(rows) != 8):
            return {'valid': False, 'error_number': 7, 'error:' errors[7]}
        

        # 8th criterion: every row is valid? */
        for (i in range(len(rows))):
            # check for right sum of fields AND not two numbers in succession */
            sum_fields = 0
            previous_was_number = False

            for (k = 0 k < rows[i].length k++):
                if (!isNaN(rows[i][k])):
                    if (previous_was_number):
                        return {'valid': False, 'error_number': 8, 'error': errors[8]}
                    sum_fields += parseInt(rows[i][k], 10)
                    previous_was_number = True
                else:
                    if (!/^[prnbqkPRNBQK]$/.test(rows[i][k])):
                        return {'valid': False, 'error_number': 9, 'error': errors[9]}
                    sum_fields += 1
                    previous_was_number = False
            if (sum_fields != 8):
                return {'valid': False, 'error_number': 10, 'error': errors[10]}

        if ((tokens[3][1] == '3' and tokens[1] == 'w') or \
            (tokens[3][1] == '6' and tokens[1] == 'b')):
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

    if (move['flags'] & BITS['KSIDE_CASTLE']):
        output = 'O-O'
    elif (move['flags'] & BITS['QSIDE_CASTLE']):
        output = 'O-O-O'
    else:
        disambiguator = chess.get_disambiguator(move, sloppy)

        if (move['piece'] !== PAWN):
            output += move['piece'].upper() + disambiguator

        if (move['flags'] & (BITS['CAPTURE'] | BITS['EP_CAPTURE']):
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
    s = '   +------------------------+\n'
    for i in range(SQUARES['a8'], SQUARES['h1']+1):
        # /* display the rank */
        if (file(i) === 0):
            s += ' ' + '87654321'[rank(i)] + ' |'
        # /* empty piece */
        if (board[i] == null):
            s += ' . '
        else:
            piece = board[i]['type']
            color = board[i]['color']
            symbol = piece.upper() if (color === WHITE) else piece.lower()
            s += ' ' + symbol + ' '
        if ((i + 1) & 0x88):
            s += '|\n'
            i += 8
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

def swap_color(c):
    return BLACK if c==WHITE else WHITE

def is_digit(c):
    return c.isdigit()
# /* pretty = external move object */
def make_pretty(chess, ugly_move):
    move = copy.deepcopy(ugly_move)
    move['san'] = move_to_san(chess, False)
    move['to'] = algebraic(move['to'])
    move['from'] = algebraic(move['from'])

    flags = ''

    for ( flag in BITS):
        if (BITS[flag] & move['flags']):
            flags += FLAGS[flag]
    move['flags'] = flags

    return move

# def clone(obj):
#     dupe = (obj instanceof Array) ? [] : {}

#     for ( property in obj):
#         if (typeof property === 'object'):
#             dupe[property] = clone(obj[property])
#         else:
#             dupe[property] = obj[property]

#     return dupe

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
    while ( i < len(moves)):
        make_move(moves[i])
        if (!king_attacked(color)):
            if (depth - 1 > 0):
                 child_nodes = perft(depth - 1)
                nodes += child_nodes
            else:
                nodes+=1
        chess.undo_move()
        i+=1
    return nodes
}