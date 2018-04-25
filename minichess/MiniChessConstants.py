#######################################################
# BOARD CONSTANTS
#######################################################
BLACK = 'b'
WHITE = 'w'

EMPTY = ('','')

PAWN = 'p'
KNIGHT = 'n'
BISHOP = 'b'
ROOK = 'r'
QUEEN = 'q'
KING = 'k'

COLOR_MAPPING = {WHITE: 1, BLACK: -1}

PIECE_MAPPING = {
    'p' : 1,
    'n' : 2,
    'b' : 3,
    'r' : 5,
    'q' : 9,
    'k' : 100,
}

PIECE_DECODER = {
    1 : 'p',
    2 : 'n',
    3 : 'b',
    5 : 'r',
    9 : 'q',
    100 : 'k'
}

ALAMO_RANK_MAPPING = {
    6: 0,
    5: 1,
    4: 2,
    3: 3,
    2: 4,
    1: 5 
}

ALAMO_FILE_MAPPING = {
    'a': 0,
    'b': 1,
    'c': 2,
    'd': 3,
    'e': 4,
    'f': 5
}

ALAMO_INIT_STATE = {
    'a1': (WHITE, ROOK), 'b1': (WHITE, KNIGHT), 'c1': (WHITE, QUEEN), 'd1': (WHITE, KING), 'e1': (WHITE, KNIGHT), 'f1': (WHITE,ROOK),
    'a2': (WHITE, PAWN), 'b2': (WHITE, PAWN), 'c2': (WHITE, PAWN), 'd2': (WHITE, PAWN), 'e2': (WHITE, PAWN), 'f2': (WHITE, PAWN), 
    'a3': EMPTY, 'b3': EMPTY, 'c3': EMPTY, 'd3': EMPTY, 'e3': EMPTY, 'f3': EMPTY, 
    'a4': EMPTY, 'b4': EMPTY, 'c4': EMPTY, 'd4': EMPTY, 'e4': EMPTY, 'f4': EMPTY, 
    'a5': (BLACK, PAWN), 'b5': (BLACK, PAWN), 'c5': (BLACK, PAWN), 'd5': (BLACK, PAWN), 'e5': (BLACK, PAWN), 'f5': (BLACK, PAWN), 
    'a6': (BLACK, ROOK), 'b6': (BLACK, KNIGHT), 'c6': (BLACK, QUEEN), 'd6': (BLACK, KING), 'e6': (BLACK, KNIGHT), 'f6': (BLACK,ROOK)
}
