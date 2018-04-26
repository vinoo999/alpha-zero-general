from __future__ import print_function
import sys
from .MiniChessLogic import Board
from .MiniChessUtil import *
from .MiniChessConstants import *
sys.path.append('..')
from Game import Game
import numpy as np
import copy
from collections import defaultdict

class MiniChessGame(Game):

    def __init__(self):
        self.n = 6
        self.state_counts = defaultdict(int)

    def getInitBoard(self):
        """
        Returns:
            startBoard: a representation of the board (ideally this is the form
                        that will be the input to your neural network)
        """
        game = Board()
        self.state_counts = defaultdict(int)
        return np.array(game.get_board_mcts())
        


    def getBoardSize(self):
        """
        Returns:
            (x,y): a tuple of board dimensions
        """
        return (self.n+1, self.n)

    def getActionSize(self):
        """
        Returns:
            actionSize: number of all possible actions

            + 6^4:          from -> to (6x6: from, 6x6: to)

            + 6*2*3*4:12    spaces to promote into
                            each has 3 spaces from-- forward, left, right)
                            and 4 promotion piece types
        """
        return 6**4 + 6*2*3*4

    def getNextState(self, board, player, action):
        """
        Input:
            board: current board
            player: current player (1 or -1)
            action: integer action taken by current player

        Returns:
            nextBoard: board after applying action
            nextPlayer: player who plays in the next turn (should be -player)
        """
        b = Board(mcts_board=board)

        #Build dictionary holding algebraic expressions {from:pos1, to:pos2, promo: optional)
        move = decode_move(action, player)

        #Perform the move on the game board
        b.do_move(move)

        #Grab the new mcts board
        next_board = b.get_board_mcts()

        #Remove state info for hashing the state
        self.state_counts[self.stringRepresentation(next_board)] += 1

        #TODO: not returning a deep copied board, handle this
        return (next_board, -player)


    def getValidMoves(self, board, player):
        """
        Input:
            board: current board
            player: current player

        Returns:
            validMoves: a binary vector of length self.getActionSize(), 1 for
                        moves that are valid from the current board and player,
                        0 for invalid moves
        """

        valids = [0]*self.getActionSize()

        b = Board(mcts_board=board)

        legal_moves = b.get_legal_moves(player)

        # print(player)
        # print(legal_moves)
        # display(board)
        for move in legal_moves:

            #Pass move dict into encode_move to return the valid move's index
            move_index = encode_move(move, player)
            valids[move_index] = 1

        return np.array(valids)


    def getGameEnded(self, board, player):
        """
        Input:
            board: current board
            player: current player (1 or -1)

        Returns:
            r: 0 if game has not ended. 1 if player won, -1 if player lost,
               small non-zero value for draw.
               
        """

        b = Board(mcts_board=board)

        #Grab board rep without halfmoves and statecount for indexing dict
        board_string = self.stringRepresentation(board)

        #Check if a draw occured
        if b.in_stalemate(player) or b.insufficient_material(player) or b.half_moves >= 50 or self.state_counts[board_string] >= 3:
            return 1e-2

        #Check if current player is in checkmate (loss)
        if b.in_checkmate(player):
            return -1

        #Check if other player is in checkmate (win)
        if b.in_checkmate(-player):
            return 1

        #Continue playing, game isnt over yet
        return 0



    def getCanonicalForm(self, board, player):
        """
        Input:
            board: current board in MCTS Form
            player: current player (1 or -1)

        Returns:
            canonicalBoard: returns canonical form of board. The canonical form
                            should be independent of player. For e.g. in chess,
                            the canonical form can be chosen to be from the pov
                            of white. When the player is white, we can return
                            board as is. When the player is black, we can invert
                            the colors and return the board.
        """

        if player == 1:

            return copy.deepcopy(board)
        else:
            #Create a deep copy of board so as to not impact the original
            board_copy = copy.deepcopy(board)

            #Board without last row holding game info (exclusive 0:6)
            just_board = board_copy[0:6,:] * -1

            #Change board orientation for black player
            canonical_board = np.flipud(just_board)
            canonical_board = np.fliplr(canonical_board)

            #Attach the last row of game info back
            canonical_board = np.vstack([canonical_board, board_copy[6,:]])

            #Swap king positions in the last row


            #Grab algebraic positions from number value of position
            white_king_pos = decode_square(canonical_board[6,0])
            black_king_pos = decode_square(canonical_board[6,1])

            #Reverse king positions by mirroring across the origin
            rev_white_king_pos = reverse_square(white_king_pos)
            rev_black_king_pos = reverse_square(black_king_pos)

            #Encode both positions as number values again
            wkp = encode_square(rev_white_king_pos)
            bkp = encode_square(rev_black_king_pos)

            #Flip the two king positions because now black player is white
            canonical_board[6,0] = bkp
            canonical_board[6,1] = wkp

            #Update current player
            canonical_board[6,2] = player

            return canonical_board

    def getSymmetries(self, board, pi):
        """
        Input:
            board: current board
            pi: policy vector of size self.getActionSize()

        Returns:
            symmForms: a list of [(board,pi)] where each tuple is a symmetrical
                       form of the board and the corresponding pi vector. This
                       is used when training the neural network from examples.
        """
        return [(board,pi)]


    def stringRepresentation(self, board):
        """
        Input:
            board: deep copied board so our changes here dont affect original

        Returns:
            boardString: a quick conversion of board to a string format.
                         Removes some variable information for hashing.
                         Required by MCTS for hashing.
        """

        #Deep copy the board to prevent modifying original
        board_copy = copy.deepcopy(board)

        #Remove half_moves info
        board_copy[6,3] = 0
        #Remove full_moves info
        board_copy[6,4] = 0
        #Remove state_count info
        board_copy[6,5] = 0
        
        return board_copy.tostring()
        



    def getScore(self, board, player):
        """
        Input:
            board: current board
            player: current player

        Returns:
            score: a sum of all pieces over the board from perspective of player
        """
        return evaluate_board(board, player)



def display(board):
    game = Board(mcts_board=board)
    print(ascii(game.board))
