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

    #############################################################
    ############################ SET UP METHODS #################
    #############################################################

    def __init__(self, fen=None):
        "Set up initial board configuration."

        self.board = np.empty((128,))
        self.kings = {w: EMPTY, b: EMPTY}
        self.turn = WHITE
        self.castling = {w: 0, b: 0}
        self.ep_square = EMPTY
        self.half_moves = 0
        self.move_number = 1
        self.history = []
        self.header = {}

        if fen is None:
            self.load(DEFAULT_POSITION)
        else:
            self.load(fen)

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

    def clear(self):
        self.board = np.empty((128,))
        self.kings = {'w': EMPTY, 'b': EMPTY}
        self.turn = WHITE
        self.castling = {'w': 0, 'b': 0}
        self.ep_square = EMPTY
        self.half_moves = 0
        self.move_number = 1
        self.history = []
        self.header = {}
        self.update_setup(generate_fen(self))

    def reset(self):
        self.load(DEFAULT_POSITION)
        return

    def update_setup(self, fen):
        '''/* called when the initial board setup is changed with put() or remove().
         * modifies the SetUp and FEN properties of the header object.  if the FEN is
         * equal to the default position, the SetUp and FEN are deleted
         * the setup is only updated if history.length is zero, ie moves haven't been
         * made.
         */'''
        if (len(self.history) > 0):
            return

        if (fen != DEFAULT_POSITION):
            self.header['SetUp'] = '1'
            self.header['FEN'] = fen
        else:
            self.header['SetUp'] = None
            self.header['FEN'] = None
        }

    def load(self, fen):
        tokens = re.split(('\s+',fen))
        position = tokens[0]
        square = 0

        if (not validate_fen(fen)['valid']):
            return False

        self.clear()

        for i in range(len(position)):
            piece = position[i]

            if (piece == '/'):
                square += 8
            elif (is_digit(piece)):
                square += parseInt(piece, 10)
            else:
                color = WHITE if piece < 'a' else BLACK
                put({'type': piece.lower(), 'color': color}, algebraic(square))
                square+=1
            
        

        self.turn = tokens[1]

        if (tokens[2].indexOf('K') > -1) {
            self.castling['w'] |= BITS['KSIDE_CASTLE']
        }
        if (tokens[2].indexOf('Q') > -1) {
            self.castling['w'] |= BITS['QSIDE_CASTLE']
        }
        if (tokens[2].indexOf('k') > -1) {
            self.castling['b'] |= BITS['KSIDE_CASTLE']
        }
        if (tokens[2].indexOf('q') > -1) {
            self.castling['b'] |= BITS['QSIDE_CASTLE']
        }

        self.ep_square = EMPTY if (tokens[3] == '-') ? else SQUARES[tokens[3]]
        self.half_moves = int(tokens[4])
        self.move_number = int(tokens[5])

        self.update_setup(generate_fen())

        return True

    def set_header(self, args):
        for i in range(0, len(args), 2):
            if (type(args[i]) == str and \
                type(args[i + 1]) == str):
                self.header[args[i]] = args[i + 1]
        return self.header


    ##############################################################
    ################ MOVES #######################################
    ###############################################################
    def get(self, square):
        piece = self.board[SQUARES[square]]
        return {'type': piece['type'], 'color': piece['color']} if piece else None

    def put(self, piece, square):
        # /* check for valid piece object */
        if piece is dict:
            if (!('type' in piece.keys() and 'color' in piece.keys())):
                return False

        # /* check for piece */
        if piece[type].lower() in SYMBOLS:
            return False

        # /* check for valid square */
        if square not in SQUARES.keys():
            return False

        sq = SQUARES[square]

        # /* don't let the user place more than one king */
        if (piece['type'] == KING and \
            !(kings[piece['color']] == EMPTY or kings[piece['color']] == sq)):
            return False
        }

        self.board[sq] = {'type': piece['type'], 'color': piece['color']}
        if (piece['type'] == KING):
            kings[piece['color']] = sq

        self.update_setup(generate_fen(self))

        return True

    def remove(self, square):
        piece = self.get(square)
        self.board[SQUARES[square]] = None
        if (piece and piece['type'] == KING):
            kings[piece['color']] = EMPTY

        self.update_setup(generate_fen(self))

        return piece

    def build_move(self, from_sq, to_sq, flags, promotion=None):

        move = {
            'color': turn,
            'from': from_sq,
            'to': to,
            'flags': flags,
            'piece': self.board[from_sq]['type']
        }

        if (promotion):
            move['flags'] |= BITS['PROMOTION']
            move['promotion'] = promotion

        if (self.board[to_sq]):
            move['captured'] = board[to_sq]['type']
        elif (flags & BITS['EP_CAPTURE']):
            move['captured'] = PAWN
        return move

    def add_move(self, moves, from_sq, to_sq, flags):
        # /* if pawn promotion */
        if (self.board[from_sq]['type'] == PAWN and \
            (rank(to_sq) == RANK_8 or rank(to_sq) == RANK_1)):
            pieces = [QUEEN, ROOK, BISHOP, KNIGHT]
            i = 0
            while i < len(pieces):
                moves.append(self.build_move(from_sq, to_sq, flags, pieces[i]))
                i+=1
        else:
            moves.append(self.build_move(from_sq, to_sq, flags))
        
        return

    def generate_moves(self, options=None):
        moves = []
        us = self.turn
        them = swap_color(us)
        second_rank = {BLACK: RANK_7, WHITE: RANK_2}

        first_sq = SQUARES['a8']
        last_sq = SQUARES['h1']
        single_square = False

        # /* do we want legal moves? */
        legal = options['legal'] if (options is dict and 'legal' in options.keys()) else True

        # /* are we generating moves for a single square? */
        if (options is dict and 'square' in options.keys()):
            if (options['square'] in SQUARES.keys()):
                first_sq = SQUARES[options['square']]
                last_sq = SQUARES[options['square']]
                single_square = True
            else:
                # /* invalid square */
                return []

        for i in range(first_sq, last_sq+1):
            # /* did we run off the end of the board */
            if (i & 0x88):
                i += 7
                continue
            piece = self.board[i]

            # Check if piece/square is one of the current turns pieces
            if (piece is None or piece['color'] != us):
                continue

            ########################################
            ########### PAWN MOVES #################
            ########################################
            if (piece['type'] == PAWN):
                # /* single square, non-capturing */
                square = i + PAWN_OFFSETS[us][0]
                if (self.board[square] == None):
                    self.add_move(moves, i, square, BITS['NORMAL'])

                    # /* double square */
                    square = i + PAWN_OFFSETS[us][1]
                    if (second_rank[us]== rank(i) and self.board[square] is None):
                        self.add_move(moves, i, square, BITS['BIG_PAWN'])

                # /* pawn captures */
                for j in range(2,4):
                    square = i + PAWN_OFFSETS[us][j]
                    if (square & 0x88): 
                        continue

                    if (board[square] is not None and \
                        board[square]['color'] == them):
                        self.add_move(moves, i, square, BITS['CAPTURE'])
                    elif (square == ep_square):
                        self.add_move(moves, i, ep_square, BITS['EP_CAPTURE'])

            #######################################
            ####### ALL OTHER PIECES ##############
            #######################################
            else:
                j = 0
                while j < len(PIECE_OFFSETS[piece['type']]):
                    offset = PIECE_OFFSETS[piece['type']][j]
                    square = i

                    while (True):
                        square += offset
                        if (square & 0x88):
                            break

                        if (self.board[square] is None):
                            add_move(board, moves, i, square, BITS['NORMAL'])
                        else:
                            if (self.board[square]['color'] == us):
                                break
                            self.add_move(moves, i, square, BITS['CAPTURE'])
                            break

                        # /* break, if knight or king */
                        if (piece['type'] == 'n' or piece['type'] == 'k'):
                            break
                    j+=1
        
        #############################################
        ########### CASTLING ########################
        #############################################
        if ((not single_square) or last_sq == kings[us]):
            # /* king-side castling */
            if (castling[us] & BITS['KSIDE_CASTLE']):
                castling_from = kings[us]
                castling_to = castling_from + 2

                if (self.board[castling_from + 1] == None and \
                    self.board[castling_to]       == None and \
                    !attacked(them, kings[us]) and \
                    !attacked(them, castling_from + 1) and \
                    !attacked(them, castling_to)):
                    self.add_move(moves, kings[us] , castling_to,
                        BITS['KSIDE_CASTLE'])

            # /* queen-side castling */
            if (castling[us] & BITS['QSIDE_CASTLE']) {
                castling_from = kings[us]
                castling_to = castling_from - 2

                if (board[castling_from - 1] == None and \
                    board[castling_from - 2] == None and \
                    board[castling_from - 3] == None and \
                    !attacked(them, kings[us]) and \
                    !attacked(them, castling_from - 1) and \
                    !attacked(them, castling_to)):
                    self.add_move(moves, kings[us], castling_to,\
                        BITS['QSIDE_CASTLE'])

        # /* return all pseudo-legal moves (this includes moves that allow the king
        #  * to be captured)
        #  */
        if (not legal):
            return moves

        # /* filter out illegal moves */
        legal_moves = []
        i = 0
        while (i< len(moves)):
            self.make_move(moves[i])
            if (!king_attacked(us)):
                legal_moves.append(moves[i])
            self.undo_move()
            i+= 1

        return legal_moves

    def attacked(self, color, square):
        for i in range(SQUARES['a8'], SQUARES['h1']):
            # /* did we run off the end of the board */
            if (i & 0x88):
                i += 7
                continue

            # /* if empty square or wrong color */
            if (self.board[i] is None or self.board[i]['color'] != color):
                continue

            piece = self.board[i]
            difference = i - square
            index = difference + 119

            if (ATTACKS[index] & (1 << SHIFTS[piece['type']])):
                if (piece['type'] == PAWN):
                    if (difference > 0):
                        if (piece['color'] == WHITE):
                            return True
                    else:
                        if (piece['color'] == BLACK):
                            return True
                    continue

                # /* if the piece is a knight or a king */
                if (piece['type'] == 'n' or piece['type'] == 'k'):
                    return True

                offset = RAYS[index]
                j = i + offset

                blocked = False
                while (j != square) {
                    if (self.board[j] is not None):
                        blocked = True
                        break
                    j += offset

                if (not blocked):
                    return True

        return False

    def king_attacked(self, color):
        return self.attacked(swap_color(color), kings[color])

    def in_check(self):
        return self.king_attacked(self.turn)

    def in_checkmate(self):
        return self.in_check() and len(self.generate_moves()) == 0

    def in_stalemate(self):
        return not self.in_check() and len(self.generate_moves()) == 0

    def insufficient_material(self):
        pieces = {}
        bishops = []
        num_pieces = 0
        sq_color = 0

        for i in range(SQUARES['a8'], SQUARES['h1']+1):
            sq_color = (sq_color + 1) % 2
            if (i & 0x88):
                i += 7
                continue

            piece = self.board[i]
            if (piece) {
                pieces[piece['type']] = pieces[piece['type']] + 1 if (piece['type'] in pieces.keys()) else 1
                if (piece['type'] == BISHOP):
                    bishops.append(sq_color)
                num_pieces+=1
            }
        }

        #/* k vs. k */
        if (num_pieces == 2):
            return True

        #/* k vs. kn .... or .... k vs. kb */
        elif (num_pieces == 3 and (pieces[BISHOP] == 1 or pieces[KNIGHT] == 1)):
            return True

        #/* kb vs. kb where any number of bishops are all on the same color */
        elif (num_pieces == pieces[BISHOP] + 2):
            tot = 0
            length = len(bishops)
            for i in range(length):
                tot += bishops[i]
            if (tot == 0 or tot == length):
                return True
        
        return False

    def in_threefold_repetition(self):
        # /* TODO: while this function is fine for casual use, a better
        #  * implementation would use a Zobrist key (instead of FEN). the
        #  * Zobrist key would be maintained in the make_move/undo_move functions,
        #  * avoiding the costly that we do below.
        #  */
        moves = []
        positions = {}
        repetition = False

        while True:
            move = self.undo_move()
            if (not move):
                break
            moves.append(move)

        while (True):
            # /* remove the last two fields in the FEN string, they're not needed
            #  * when checking for draw by rep */
            fen = generate_fen(self).split(' ')[0:4].join(' ')

            # /* has the position occurred three or move times */
            positions[fen] = positions[fen] +1 if (fen in positions) else 1
            if (positions[fen] >= 3) {
                repetition = True
            }

            if (not len(moves)):
                break
            
            self.make_move(moves.pop())

        return repetition

    def push(self, move):
        self.history.append({
            'move': move,
            'kings': {'b': self.kings['b'], 'w': self.kings['w']},
            'turn': self.turn,
            'castling': {'b': self.castling['b'], 'w': self.castling['w']},
            'ep_square': self.ep_square,
            'half_moves': self.half_moves,
            'move_number': self.move_number
        })
        return

    def make_move(move):
        us = self.turn
        them = swap_color(us)
        self.push(move)

        self.board[move['to']] = self.board[move['from']]
        self.board[move['from']] = None

        # /* if ep capture, remove the captured pawn */
        if (move['flags'] & BITS['EP_CAPTURE']):
            if (self.turn == BLACK):
                self.board[move['to'] - 16] = None
            else:
                self.board[move['to'] + 16] = None

        # /* if pawn promotion, replace with new piece */
        if (move['flags'] & BITS['PROMOTION']):
            self.board[move['to']] = {'type': move['promotion'], 'color': us}

        # /* if we moved the king */
        if (board[move['to']]['type'] == KING):
            kings[board[move['to']]['color']] = move['to']]

            # /* if we castled, move the rook next to the king */
            if (move['flags'] & BITS['KSIDE_CASTLE']):
                castling_to = move['to'] - 1
                castling_from = move['to'] + 1
                self.board[castling_to] = self.board[castling_from]
                self.board[castling_from] = None
            elif (move['flags'] & BITS['QSIDE_CASTLE']):
                castling_to = move['to'] + 1
                castling_from = move['to'] - 2
                self.board[castling_to] = self.board[castling_from]
                self.board[castling_from] = None

            # /* turn off castling */
            self.castling[us] = None
        }

        # /* turn off castling if we move a rook */
        if (self.castling[us]):
            i = 0
            while i < len(ROOKS[us]):
                if (move['from'] == ROOKS[us][i]['square'] and \
                    self.castling[us] & ROOKS[us][i]['flag']):
                    self.castling[us] ^= ROOKS[us][i]['flag']
                    break
                i+=1

        # /* turn off castling if we capture a rook */
        if (self.castling[them]):
            i = 0
            while i < len(ROOKS[them]):
                if (move['to']] == ROOKS[them][i]['square'] and \
                    self.castling[them] & ROOKS[them][i]['flag']):
                    self.castling[them] ^= ROOKS[them][i]['flag']
                    break
                }
                i+=1

        # /* if big pawn move, update the en passant square */
        if (move['flags'] & BITS['BIG_PAWN']):
            if (turn == 'b'):
                self.ep_square = move['to'] - 16
            else:
                self.ep_square = move['to'] + 16
        else:
            self.ep_square = EMPTY

        # /* reset the 50 move counter if a pawn is moved or a piece is captured */
        if (move['piece'] == PAWN):
            self.half_moves = 0
        elif (move['flags'] & (BITS['CAPTURE'] | BITS['EP_CAPTURE'])):
            self.half_moves = 0
        else:
            self.half_moves+=1

        if (self.turn == BLACK):
            self.move_number+=1

        self.turn = swap_color(self.turn)
        return

    def undo_move():
        old = history.pop()
        if (old is None):
            return None

        move = old['move']
        self.kings = old['kings']
        self.turn = old['turn']
        self.castling = old['castling']
        self.ep_square = old['ep_square']
        self.half_moves = old['half_moves']
        self.move_number = old['move_number']

        us = self.turn
        them = swap_color(self.turn)

        self.board[move['from']] = self.board[move['to']]
        self.board[move['from']]['type'] = move['piece']  # to undo any promotions
        self.board[move['to']] = None

        if (move['flags'] & BITS['CAPTURE']):
            self.board[move['to']] = {'type': move['captured'], 'color': them}
        elif (move['flags'] & BITS['EP_CAPTURE']):
            if (us == BLACK):
                index = move['to'] - 16
            else:
                index = move['to'] + 16
            self.board[index] = {'type': PAWN, 'color': them}


        if (move['flags'] & (BITS['KSIDE_CASTLE'] | BITS['QSIDE_CASTLE'])):
            if (move['flags'] & BITS['KSIDE_CASTLE']):
                castling_to = move['to'] + 1
                castling_from = move['to'] - 1
            elif (move['flags'] & BITS['QSIDE_CASTLE']):
                castling_to = move['to'] - 2
                castling_from = move['to'] + 1

            self.board[castling_to] = self.board[castling_from]
            self.board[castling_from] = None

        return move


    def get_disambiguator(self, move, sloppy):
        '''/* this function is used to uniquely identify ambiguous moves */'''
        moves = self.generate_moves({legal: !sloppy})

        from_sq = move['from']
        to_sq = move['to']
        piece = move['piece']

        ambiguities = 0
        same_rank = 0
        same_file = 0

        i = 0
        while i < len(moves):
            ambig_from = moves[i]['from']
            ambig_to = moves[i]['to']
            ambig_piece = moves[i]['piece']

            # /* if a move of the same piece type ends on the same to square, we'll
            #  * need to add a disambiguator to the algebraic notation
            #  */
            if (piece == ambig_piece and from_sq != ambig_from and to_sq == ambig_to):
                ambiguities+=1
                if (rank(from_sq) == rank(ambig_from)):
                    same_rank+=1
                if (col_file(from_sq) == col_file(ambig_from)):
                    same_file+=1

        if (ambiguities > 0):
            # /* if there exists a similar moving piece on the same rank and file as
            #  * the move in question, use the square as the disambiguator
            #  */
            if (same_rank > 0 and same_file > 0):
                return algebraic(from_sq)
            # /* if the moving piece rests on the same file, use the rank symbol as the
            #  * disambiguator
            #  */
            elif (same_file > 0):
                return algebraic(from_sq)[1]
            # /* else use the file symbol */
            else:
                return algebraic(from_sq)[0]

        return None

    ####################################################
    ################### Other Things ###################
    ####################################################
    def get_board(self):
        output = []
        row    = []

        for i in range(SQUARES['a8'], SQUARES['h1']+1):
            if (board[i] == null) {
                row.append(None)
            else:
                row.append({'type': board[i]['type'], 'color': board[i]['color']})
            
            if ((i + 1) & 0x88):
                output.append(row)
                row = []
                i += 8

        return output

    def get_pgn(self, options=None):
        return None

    def move(self, options=None):
        '''/* The move function can be called with in the following parameters:
         *
         * .move('Nxb7')      <- where 'move' is a case-sensitive SAN string
         *
         * .move({ from: 'h7', <- where the 'move' is a move object (additional
         *         to :'h8',      fields are ignored)
         *         promotion: 'q',
         *      })
         */'''

        # // allow the user to specify the sloppy move parser to work around over
        # // disambiguation bugs in Fritz and Chessbase
        sloppy = options['sloppy'] if (options is dict and 'sloppy' in options.keys()) else false

        move_obj = None

        if (move is str):
            move_obj = move_from_san(move, sloppy);
        elif (move is dict):
            moves = self.generate_moves();

            # /* convert the pretty move object to an ugly move object */
            for (i in range(len(moves))):
                if (move['from'] == algebraic(moves[i]['from']) and \
                    move['to'] == algebraic(moves[i]['to']) and \
                    (!('promotion' in moves[i].keys()) or \
                    move['promotion'] == moves[i]['promotion'])):
                    move_obj = moves[i]
                    break

        # /* failed to find move */
        if (!move_obj):
            return None

        # /* need to make a copy of move because we can't generate SAN after the
        #  * move is made
        #  */
        pretty_move = make_pretty(self, move_obj)

        self.make_move(move_obj)

        return pretty_move

    def get_history(self, options):
        reversed_history = []
        move_history = []
        verbose = (options is dict and 'verbose' in options.keys() and \
        options['verbose']);

        while (len(history) > 0):
            reversed_history.append(self.undo_move())

        while (len(reversed_history) > 0) {
            var move = reversed_history.pop();
            if (verbose) {
                move_history.append(make_pretty(self, move));
            } else {
                move_history.append(move_to_san(self, move));
            }
            self.make_move(move);
        }

        return move_history;

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

