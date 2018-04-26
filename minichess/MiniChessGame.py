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
                            
            + 1:            do nothing
        """
        return 6**4 + 6*2*3*4 + 1

    def getNextState(self, board, player, action):
        """
        Input:
            board: current board
            player: current player (1 or -1)
            action: action taken by current player

        Returns:
            nextBoard: board after applying action
            nextPlayer: player who plays in the next turn (should be -player)
        """
        pass

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
        pass

    def getGameEnded(self, board, player):
        """
        Input:
            board: current board
            player: current player (1 or -1)

        Returns:
            r: 0 if game has not ended. 1 if player won, -1 if player lost,
               small non-zero value for draw.
               
        """
        pass

    def getCanonicalForm(self, board, player):
        """
        Input:
            board: current board
            player: current player (1 or -1)

        Returns:
            canonicalBoard: returns canonical form of board. The canonical form
                            should be independent of player. For e.g. in chess,
                            the canonical form can be chosen to be from the pov
                            of white. When the player is white, we can return
                            board as is. When the player is black, we can invert
                            the colors and return the board.
        """
        pass

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
        pass

    def stringRepresentation(self, board):
        """
        Input:
            board: current board

        Returns:
            boardString: a quick conversion of board to a string format.
                         Required by MCTS for hashing.
        """
        pass



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
    print(ascii(game))
