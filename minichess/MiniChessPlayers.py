from minichess.MiniChessGame import display
from minichess.MiniChessLogic import Board
from minichess.MiniChessUtil import *
from minichess.MiniChessConstants import *
from minichess.keras.NNet import NNetWrapper as NNet
from MCTS import MCTS
from utils import *

from _pickle import Unpickler
import numpy as np
import copy
from queue import Queue
import math
from timeit import default_timer as timer
import time
import os
from utils import *
from MCTS import MCTS




class RandomPlayer():
    def __init__(self, game):
        self.game = game

    def play(self, board):
        #np.random.seed(int(time.time()))
        a = np.random.randint(self.game.getActionSize())
        valids = self.game.getValidMoves(board, 1)
        while valids[a]!=1:
            a = np.random.randint(self.game.getActionSize())
        return a

class NNetPlayer():
    def __init__(self, game, ckpt_path, ckpt_file, args):
        self.nnet = NNet(game)
        self.args = dotdict(args)

        self.nnet.load_checkpoint(ckpt_path, ckpt_file)

        self.mcts = MCTS(game, self.nnet, self.args)

    def play(self, board):
        tmp = self.args["temp"] if "temp" in self.args else 0
        move = np.argmax(self.mcts.getActionProb(board, temp=tmp))
        return move



class HumanChessPlayer():
    def __init__(self, game):
        self.game = game

    def play(self, board):
        # display(board)
        #TODO: Are we always assuming oriented as player = 1???????
        valid = self.game.getValidMoves(board, 1)
        new_game_moves = [i for i, e in enumerate(valid) if e != 0]
        player = board[6][2]


        print("Current board for player: " +str(player))
        print("Number of moves available: " + str(len(new_game_moves)))

        display(board)
        print("legal moves:")
        for i in range(len(new_game_moves)):
            print(str(decode_move(new_game_moves[i], player)))


        while True:
            display(board)
            a = input("Enter move in the following format: from to [promotion]\n")

            splits = a.split(' ')

            if len(splits) < 2:
                print("Improper move format. Enter again.")
                continue

            moveFrom, moveTo = splits[0], splits[1]


            #Ensure the piece locations are properly formatted (i.e "a1")
            if len(moveFrom) != 2 or len(moveTo) != 2:
                print("Improper position format. Enter again.")
                continue

            #Ensure the promotion piece is valid
            if len(splits) == 3 and splits[2] not in ['n', 'b', 'r', 'q']:
                print("Improper promotion format. Enter again.")
                continue

            #Properly entered promotion
            elif len(splits) == 3:
            	promotion = splits[2]

            #Not a promotable move
            else:
            	promotion = None


            #Generate the move dictionary to pass to encode_move
            move = {'from':moveFrom, 'to':moveTo, 'promotion':promotion}
            print("move: " +str(move))

            move_index = encode_move(move, player)
            print("move_index: " +str(move_index))

            print("cast back: " + str(decode_move(move_index)))

            if valid[move_index]:
            	break
            else:
            	print("Invalid move. Enter again.")

        return move_index



class AlphaBetaPlayer(): 
    #Alpha: best already explored option along path to root for maximizer
    #Beta: best already explored option along path to root for minimizer
    """NOTE: We're treating player 1 as the maximizing player and player 2 as minimizing"""
    """
        Do we need deepcopy for each board in the recursive call?
        Do we need player_turn = board[8][2] in each recursive call or just is max player?
        Why do we return without checking everything in alphabeta? if (beta <= alpha): return best_move
        CHECK DEPTH!
    """

    def __init__(self, game):
        self.game = game
        self.depth = 2

    def play(self, board):
        """Returns the best move as variable *num* """
        """board is the canonical board"""

        depth = self.depth

        infinity = float('inf')

        player =1

        is_maximising_player = True


        #Get available moves for the initial board state
        new_game_moves = self.game.getValidMoves(board, player)
        new_game_moves = [i for i, e in enumerate(new_game_moves) if e != 0]

        # print("Current board for player: " +str(player))
        # print("Number of moves available: " + str(len(new_game_moves)))

        # display(board)
        # print("legal moves:")
        # for i in range(len(new_game_moves)):
        #     print(str(decode_move(new_game_moves[i], player)))

        

        legal_moves_values = [0]*len(new_game_moves)


        #Start off the player with their worst possible score
        best_move_score = -infinity
        best_moves_scores = [-infinity, -infinity, -infinity]

        #Default moves to zero (just as a placeholder)
        best_move = 0
        best_moves = [0, 0, 0]

        #start = timer()

        #Iterate over initial moves and pass into the minimax function to recurse on
        for i in range(len(new_game_moves)):

            new_game_move = new_game_moves[i]

            #Create a board copy so that we dont affect the root
            board_copy = board#copy.deepcopy(board)

            #Apply the move to the starting board to generate a new board (get next state is tuple holding board and count)
            new_board_state = self.game.getNextState(board_copy, player, new_game_move)[0]

            
            #Play the game starting with this move up to 'depth' and assess it's value
            value = self.minimax(depth - 1, new_board_state, self.game, -infinity, infinity, -player, not is_maximising_player)#1-player)

            legal_moves_values[i] = value

            #Grab the best move and return
            if(value >= best_move_score):
                best_move_score = value
                best_move = new_game_move

            #Find the minimum of the three highest score values
            min_score = infinity
            worst_move = i
            for i in range(len(best_moves)):
                if best_moves_scores[i] < min_score:
                    min_score = best_moves_scores[i]
                    worst_move = i

            #Insert the new move if it's score is larger than the smallest of the three prior largest
            if best_move_score > min_score:
                best_moves_scores[worst_move] = value
                best_moves[worst_move] = new_game_move

        #print("COLOR: {} \nBEST MOVES: {} \n SCORES {} \n DECISION: {} \n DECISION SCORE: {}".format(player, list(map(decode_move, best_moves, player)), best_moves_scores, decode_move(best_move, player), best_move_score))        print("COLOR: {} \n DECISION: {} \n DECISION SCORE: {}".format(player, decode_move(best_move, player), best_move_score))
        print("COLOR: {} \nBEST MOVES: {} \n SCORES {} \n DECISION: {} \n DECISION SCORE: {}".format(player, [decode_move(m,player) for m in best_moves], best_moves_scores, decode_move(best_move, player), best_move_score))

        #print("COLOR: {} \n DECISION: {} \n DECISION SCORE: {}".format(player, decode_move(best_move, player), best_move_score))
        # print("COLOR: {} \nBEST MOVES: {} \n SCORES {} \n DECISION: {} \n DECISION SCORE: {}".format(player, [decode_move(m,player) for m in best_moves], best_moves_scores, decode_move(best_move, player), best_move_score))

        #end = timer()
        #print("Time elapsed: " + str(end - start))

        return best_move


    def minimax(self, depth, board, game, alpha, beta, player, is_maximising_player):
 
        infinity = float('inf')
        print("---------------------------------------------------------")
        print("At depth:" + str(depth))
        display(board)
        print("score: " + str(self.game.getScore(board, player)))
        print("---------------------------------------------------------")

        #Base case where we've reached the max depth to explore
        if depth == 0:
            # print("---------------------------------------------------------")
            # print("At depth 0")
            # display(board)
            # print("score: " + str(self.game.getScore(board, player)))
            # print("---------------------------------------------------------")
            return self.game.getScore(board, player)

        #Get all available moves stemming from the new board state
        new_game_moves = self.game.getValidMoves(board, player)
        new_game_moves = [i for i, e in enumerate(new_game_moves) if e != 0]

        if(is_maximising_player):

            #Start player at the worst possible score
            best_move_score = -infinity

            for i in range(len(new_game_moves)):

                new_game_move = new_game_moves[i]
                board_copy = board#copy.deepcopy(board)
                tmp_game = self.game#copy.deepcopy(self.game)
                new_board_state = tmp_game.getNextState(board_copy, player, new_game_move)[0]

                best_move_score = max(best_move_score, self.minimax(depth - 1, new_board_state, tmp_game, -infinity, infinity, -player, not is_maximising_player))

                #Decrement the count so that we dont include boards that were touched in the search tree
                self.game.state_counts[self.game.stringRepresentation(new_board_state)] -= 1

                alpha = max(alpha, best_move_score)

                if (beta <= alpha):
                    return best_move_score

            return best_move_score

        else:

            best_move_score = infinity

            for i in range(len(new_game_moves)):

                new_game_move = new_game_moves[i]

                board_copy = board#copy.deepcopy(board)
                tmp_game = self.game#copy.deepcopy(self.game)

                new_board_state = tmp_game.getNextState(board_copy, player, new_game_move)[0]

                best_move_score = min(best_move_score, self.minimax(depth - 1, new_board_state, self.game, -infinity, infinity, -player, not is_maximising_player))

                #Decrement the count so that we dont include boards that were touched in the search tree
                self.game.state_counts[self.game.stringRepresentation(new_board_state)] -= 1

                beta = min(beta, best_move_score)

                if (beta <= alpha):
                    return best_move_score

            return best_move_score







