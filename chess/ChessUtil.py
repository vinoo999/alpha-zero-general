import re
import copy
from ChessConstants import *
from ChessLogic import make_move
# /*****************************************************************************
 # * UTILITY FUNCTIONS
 # ****************************************************************************/


# /* convert a move from 0x88 coordinates to Standard Algebraic Notation
#  * (SAN)
#  *
#  * @param {boolean} sloppy Use the sloppy SAN generator to work around over
#  * disambiguation bugs in Fritz and Chessbase.  See below:
#  *
#  * r1bqkbnr/ppp2ppp/2n5/1B1pP3/4P3/8/PPPP2PP/RNBQK1NR b KQkq - 2 4
#  * 4. ... Nge7 is overly disambiguated because the knight on c6 is pinned
#  * 4. ... Ne7 is technically the valid SAN
#  */
def move_to_san(move, sloppy) :

    output = ''

    if (move['flags'] & BITS['KSIDE_CASTLE']):
        output = 'O-O'
    elif (move['flags'] & BITS['QSIDE_CASTLE']):
        output = 'O-O-O'
    else:
        disambiguator = get_disambiguator(move, sloppy)

        if (move['piece'] !== PAWN):
            output += move.piece.toUpperCase() + disambiguator

        if (move['flags'] & (BITS['CAPTURE'] | BITS['EP_CAPTURE']):
            if (move['piece'] == PAWN):
                output += algebraic(move['from'])[0]
            output += 'x'

        output += algebraic(move['to'])

        if (move['flags'] & BITS['PROMOTION']):
            output += '=' + move['promotion'].toUpperCase()
    }

    make_move(move)
    if (in_check()):
        if (in_checkmate()):
            output += '#'
        else:
            output += '+'
    undo_move()

    return output
}

# // parses all of the decorators out of a SAN string
def stripped_san(move):
    return move.replace('=','').replace('[+#]?[?!]*$','');

def rank(i):
    return i >> 4;

def file(i):
    return i & 15;

def algebraic(i):
     f = file(i), r = rank(i);
    return 'abcdefgh'.substring(f,f+1) + '87654321'.substring(r,r+1);

def swap_color(c):
    return BLACK if c==WHITE else WHITE

def is_digit(c):
    return '0123456789'.indexOf(c) !== -1;

# /* pretty = external move object */
def make_pretty(ugly_move):
    move = copy.deepcopy(ugly_move);
    move['san'] = move_to_san(move, False);
    move['to'] = algebraic(move['to']);
    move['from'] = algebraic(move['from']);

    flags = '';

    for ( flag in BITS) {
        if (BITS[flag] & move.flags) {
            flags += FLAGS[flag];
        }
    }
    move['flags'] = flags;

    return move;

def clone(obj):
    dupe = (obj instanceof Array) ? [] : {}

    for ( property in obj):
        if (typeof property === 'object'):
            dupe[property] = clone(obj[property])
        else:
            dupe[property] = obj[property]

    return dupe;

def trim(str):
    return str.replace('^\s+|\s+$', '');

##########################################
# DEBUGGING UTILITIES
########################################
def perft(depth) {
     moves = generate_moves({legal: false});
     nodes = 0;
     color = turn;

    for ( i = 0, len = moves.length; i < len; i++) {
        make_move(moves[i]);
        if (!king_attacked(color)) {
            if (depth - 1 > 0) {
                 child_nodes = perft(depth - 1);
                nodes += child_nodes;
            } else {
                nodes++;
            }
        }
        undo_move();
    }

    return nodes;
}