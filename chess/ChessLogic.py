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
from ChessConstants import *
from ChessUtil import *

class Board():
    
    def __init__(self):
        "Set up initial board configuration."

        board = np.zeros(128)
        kings = {w: EMPTY, b: EMPTY}
        turn = WHITE
        castling = {w: 0, b: 0}
        ep_square = EMPTY
        half_moves = 0
        move_number = 1
        history = []
        header = {}

        load(DEFAULT_POSITION)

        self.n = n
        # Create the empty board array.
        self.pieces = [None]*self.n
        for i in range(self.n):
            self.pieces[i] = [0]*self.n

        # Set up the initial 4 pieces.
        self.pieces[int(self.n/2)-1][int(self.n/2)] = 1
        self.pieces[int(self.n/2)][int(self.n/2)-1] = 1
        self.pieces[int(self.n/2)-1][int(self.n/2)-1] = -1
        self.pieces[int(self.n/2)][int(self.n/2)] = -1

    def load(fen):
        tokens = re.split(('\s+',fen)
        position = tokens[0]
        square = 0

        if (!validate_fen(fen)['valid']):
            return False

        clear()

        for i in range(len(position)):
            piece = position.charAt(i)

            if (piece === '/'):
                square += 8
            elif (is_digit(piece)):
                square += parseInt(piece, 10)
            else:
                color = WHITE if piece < 'a' else BLACK
                put({type: piece.toLowerCase(), color: color}, algebraic(square))
                square++
            
        

        turn = tokens[1]

        if (tokens[2].indexOf('K') > -1) {
            castling.w |= BITS.KSIDE_CASTLE
        }
        if (tokens[2].indexOf('Q') > -1) {
            castling.w |= BITS.QSIDE_CASTLE
        }
        if (tokens[2].indexOf('k') > -1) {
            castling.b |= BITS.KSIDE_CASTLE
        }
        if (tokens[2].indexOf('q') > -1) {
            castling.b |= BITS.QSIDE_CASTLE
        }

        ep_square = (tokens[3] === '-') ? EMPTY : SQUARES[tokens[3]]
        half_moves = parseInt(tokens[4], 10)
        move_number = parseInt(tokens[5], 10)

        update_setup(generate_fen())

        return True


    # TODO: this function is pretty much crap - it validates structure but
    # completely ignores content (e.g. doesn't verify that each side has a king)
    # ... we should rewrite this, and ditch the silly error_number field while
    # we're at it
    #
    
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


    # add [][] indexer syntax to the Board
    def __getitem__(self, index): 
        return self.pieces[index]

    def countDiff(self, color):
        """Counts the # pieces of the given color
        (1 for white, -1 for black, 0 for empty spaces)"""
        count = 0
        for y in range(self.n):
            for x in range(self.n):
                if self[x][y]==color:
                    count += 1
                if self[x][y]==-color:
                    count -= 1
        return count

    def get_legal_moves(self, color):
        """Returns all the legal moves for the given color.
        (1 for white, -1 for black
        """
        moves = set()  # stores the legal moves.

        # Get all the squares with pieces of the given color.
        for y in range(self.n):
            for x in range(self.n):
                if self[x][y]==color:
                    newmoves = self.get_moves_for_square((x,y))
                    moves.update(newmoves)
        return list(moves)

    def has_legal_moves(self, color):
        for y in range(self.n):
            for x in range(self.n):
                if self[x][y]==color:
                    newmoves = self.get_moves_for_square((x,y))
                    if len(newmoves)>0:
                        return True
        return False

    def get_moves_for_square(self, square):
        """Returns all the legal moves that use the given square as a base.
        That is, if the given square is (3,4) and it contains a black piece,
        and (3,5) and (3,6) contain white pieces, and (3,7) is empty, one
        of the returned moves is (3,7) because everything from there to (3,4)
        is flipped.
        """
        (x,y) = square

        # determine the color of the piece.
        color = self[x][y]

        # skip empty source squares.
        if color==0:
            return None

        # search all possible directions.
        moves = []
        for direction in self.__directions:
            move = self._discover_move(square, direction)
            if move:
                # print(square,move,direction)
                moves.append(move)

        # return the generated move list
        return moves

    def execute_move(self, move, color):
        """Perform the given move on the board flips pieces as necessary.
        color gives the color pf the piece to play (1=white,-1=black)
        """

        #Much like move generation, start at the new piece's square and
        #follow it on all 8 directions to look for a piece allowing flipping.

        # Add the piece to the empty square.
        # print(move)
        flips = [flip for direction in self.__directions
                      for flip in self._get_flips(move, direction, color)]
        assert len(list(flips))>0
        for x, y in flips:
            #print(self[x][y],color)
            self[x][y] = color

    def _discover_move(self, origin, direction):
        """ Returns the endpoint for a legal move, starting at the given origin,
        moving by the given increment."""
        x, y = origin
        color = self[x][y]
        flips = []

        for x, y in Board._increment_move(origin, direction, self.n):
            if self[x][y] == 0:
                if flips:
                    # print("Found", x,y)
                    return (x, y)
                else:
                    return None
            elif self[x][y] == color:
                return None
            elif self[x][y] == -color:
                # print("Flip",x,y)
                flips.append((x, y))

    def _get_flips(self, origin, direction, color):
        """ Gets the list of flips for a vertex and direction to use with the
        execute_move function """
        #initialize variables
        flips = [origin]

        for x, y in Board._increment_move(origin, direction, self.n):
            #print(x,y)
            if self[x][y] == 0:
                return []
            if self[x][y] == -color:
                flips.append((x, y))
            elif self[x][y] == color and len(flips) > 0:
                #print(flips)
                return flips

        return []

    @staticmethod
    def _increment_move(move, direction, n):
        # print(move)
        """ Generator expression for incrementing moves """
        move = list(map(sum, zip(move, direction)))
        #move = (move[0]+direction[0], move[1]+direction[1])
        while all(map(lambda x: 0 <= x < n, move)): 
        #while 0<=move[0] and move[0]<n and 0<=move[1] and move[1]<n:
            yield move
            move=list(map(sum,zip(move,direction)))
            #move = (move[0]+direction[0],move[1]+direction[1])

