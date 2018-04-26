from chess.ChessGame import display
from chess.ChessLogic import Board
from chess.ChessUtil import *
from chess.ChessConstants import *
from chess.keras.NNet import NNetWrapper as NNet
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


class NNetNetworkPlayer():
    def __init__(self, game, ckpt_path, ckpt_file, args):
        self.queue = Queue(maxsize=1)
        self.nnet = NNet(game)
        self.args = dotdict(args)

        self.nnet.load_checkpoint(ckpt_path, ckpt_file)

        self.mcts = MCTS(game, self.nnet, self.args)

    def play(self, board):
        tmp = self.args["temp"] if "temp" in self.args else 0
        action = np.argmax(self.mcts.getActionProb(board, temp=tmp))

        move = decode_move(action)

        b = Board(mcts_board=board)
        moves = b.generate_moves({'legal': True})

        ugly_move = None
        for i in range(len(moves)):
            if (move['from'] == algebraic(moves[i]['from']) and move['to'] == algebraic(moves[i]['to']) and \
                (('promotion' not in moves[i].keys()) or move['promotion'] == moves[i]['promotion'])):
                ugly_move = moves[i]
                break

        assert ugly_move != None
        print("SELECTED MOVE: " + str(ugly_move))

        self.queue.put(ugly_move)
        return action


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


class RandomNetworkPlayer():
    def __init__(self, game):
        self.game = game
        self.queue = Queue(maxsize=1)

    def play(self, board):

        # Pulled from getValidMoves(), we need the dictionary encoding of the move for the GUI
        b = Board(mcts_board=board)
        legalMoves = b.generate_moves({'legal': True})
        move = legalMoves[np.random.randint(len(legalMoves))]
        self.queue.put(move)

        # Encode "dictionary move" into "number move" format
        pos1 = algebraic(move['from'])
        pos2 = algebraic(move['to'])

        file1 = pos1[0]
        rank1 = pos1[1]
        file2 = pos2[0]
        rank2 = pos2[1]

        file1_idx = 'abcdefgh'.index(file1)
        file2_idx = 'abcdefgh'.index(file2)
        rank1_idx = '87654321'.index(rank1)
        rank2_idx = '87654321'.index(rank2)

        if 'promotion' in move.keys():
            promotion = MCTS_MAPPING[move['promotion']]-2 # move range to 0-3
            offset = 64*64
            direction = abs(move['from'] - move['to']) - 16 + 1
                # 0 means promote takes right
                # 1 means advance
                # 2 means promote takes left
            rank_abbrv = 0 if move['color'] == WHITE else 1
            num = promotion*4 + direction + 16*(2*file1_idx + rank_abbrv) + offset
        else:
            num = (8*file1_idx + rank1_idx)*64 + 8*file2_idx + rank2_idx

        return num


class HumanChessPlayer():
    def __init__(self, game):
        self.game = game

    def play(self, board):
        # display(board)
        color = 0 if board[8,2] == 1 else 1
        valid = self.game.getValidMoves(board, 1)
        # for i in range(len(valid)):
        #     if valid[i]:
        #         print(int(i/self.game.n), int(i%self.game.n))
        while True:

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

            if len(splits) >= 2:
                pos1 = splits[0]
                pos2 = splits[1]

                file1 = pos1[0]
                rank1 = pos1[1]
                file2 = pos2[0]
                rank2 = pos2[1]

                file1_idx = 'abcdefgh'.index(file1)
                file2_idx = 'abcdefgh'.index(file2)
                rank1_idx = '87654321'.index(rank1)
                rank2_idx = '87654321'.index(rank2)

                if len(splits) == 3:
                    promotion = MCTS_MAPPING[splits[2]]-2 # move range to 0-3
                    offset = 64*64
                    direction = abs(SQUARES[pos1] - SQUARES[pos2]) - 16 + 1
                        # 0 means promote takes right
                        # 1 means advance
                        # 2 means promote takes left
                    num = promotion*4 + direction + 16*(2*file1_idx + color) + offset

                else:
                    num = (8*file1_idx + rank1_idx)*64 + 8*file2_idx + rank2_idx

                print("end here-------------")
            if valid[num]:
                break
            else:
                print('Invalid')

        return num


class HumanNetworkChessPlayer():
    def __init__(self, game, result_queue):
        self.game = game
        self.queue = Queue(maxsize=1)
        self.result_queue = result_queue

    def play(self, board):

        valid = self.game.getValidMoves(board, 1)
        
        #Grab human move and play it if valid
        while True:
            color = 0 if board[8,2] == 1 else 1

            # New Method: wait until user makes move on GUI (aka. browser)
            a = self.queue.get()

            a_split = a.split()
            #print("a_split: " + str(a_split)) 
            moveFrom, moveTo = a_split[0], a_split[1]

            #Ensure the piece locations are properly formatted (i.e "a1")
            if len(moveFrom) != 2 or len(moveTo) != 2:
                print("Improper position format. Enter again.")
                self.result_queue.put(None)
                continue

            #Ensure the promotion piece is valid
            if len(a_split) == 3 and a_split[2] not in ['n', 'b', 'r', 'q']:
                print("Improper promotion format. Enter again.")
                self.result_queue.put(None)
                continue

            #Go from a human-readable action (a9->a8) to an action encoding
            file1 = moveFrom[0]
            rank1 = moveFrom[1]
            file2 = moveTo[0]
            rank2 = moveTo[1]

            file1_idx = 'abcdefgh'.index(file1)
            file2_idx = 'abcdefgh'.index(file2)
            rank1_idx = '87654321'.index(rank1)
            rank2_idx = '87654321'.index(rank2)

            #Check to see if a promotion is applicable [Knight: 'n', Bishop: 'b', Rook: 'r', Queen: 'q']
            if len(a_split) == 3:
                promo_piece = a_split[2]
                promotion = MCTS_MAPPING[promo_piece]-2 # move range to 0-3
                offset = 64*64
                #direction = abs(int(moveFrom[1]) - int(moveTo[1])) + 1
                direction = abs(SQUARES[moveFrom] - SQUARES[moveTo]) - 16 + 1
                    # 0 means promote takes right
                    # 1 means advance
                    # 2 means promote takes left
                num = promotion*4 + direction + 16*(2*file1_idx + color) + offset
            else:
                num = (8*file1_idx + rank1_idx)*64 + 8*file2_idx + rank2_idx


            if valid[num]:
                break
            else:
                print('Invalid')
                self.result_queue.put(None)
                continue

        return num








"""
/
9x8 mcts board

passing around this board state: self.game.getCanonicalForm(board, curPlayer)

load_mcts:load board as game current board

for each state get all valid moves
    
    game.nextmove
    next_state = game.getnextstate
    return a tuple score, state it was at

    copy.deepcopy on the board to not effect

    board class, and board-array, and the game. Were talking about board-array

    load mcts creates board object from board array
"""
#----------------------------------------------------------------------------------------
#-------------------------------AlphaBetaPlayer------------------------------------------
#----------------------------------------------------------------------------------------

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
        self.depth =2

    def play(self, board):
        """Returns the best move as variable *num* """
        """board is the canonical board"""

        depth = self.depth

        infinity = float('inf')

        player = board[8][2]

        is_maximising_player = True


        #Get available moves for the initial board state
        new_game_moves = self.game.getValidMoves(board, player)
        new_game_moves = [i for i, e in enumerate(new_game_moves) if e != 0]

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
            value = self.minimax(depth - 1, new_board_state, self.game, -infinity, infinity, 1-player, not is_maximising_player)#1-player)

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

        # print("Number of moves available: " + str(len(new_game_moves)))
        # print("COLOR: {} \nBEST MOVES: {} \n SCORES {} \n DECISION: {} \n DECISION SCORE: {}".format(player, list(map(decode_move, best_moves)), best_moves_scores, decode_move(best_move), best_move_score))
        # print("Finished a decision.")
        
        #end = timer()
        #print("Time elapsed: " + str(end - start))

        return best_move


    def minimax(self, depth, board, game, alpha, beta, player, is_maximising_player):
 
        infinity = float('inf')

        #Base case where we've reached the max depth to explore
        if depth == 0:
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

                best_move_score = max(best_move_score, self.minimax(depth - 1, new_board_state, tmp_game, -infinity, infinity, 1-player, not is_maximising_player))

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

                best_move_score = min(best_move_score, self.minimax(depth - 1, new_board_state, self.game, -infinity, infinity, 1-player, not is_maximising_player))

                #Decrement the count so that we dont include boards that were touched in the search tree
                self.game.state_counts[self.game.stringRepresentation(new_board_state)] -= 1

                beta = min(beta, best_move_score)

                if (beta <= alpha):
                    return best_move_score

            return best_move_score

#----------------------------------------------------------------------------------------
#-----------------------------AlphaBetaNetworkPlayer-------------------------------------
#----------------------------------------------------------------------------------------

class AlphaBetaNetworkPlayer(): 
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
        self.queue = Queue(maxsize=1)

    def play(self, board):
        """Returns the best move as variable *num* """
        """board is the canonical board"""

        depth = self.depth
        infinity = float('inf')
        player = board[8][2]
        is_maximising_player = True

        #Get available moves for the initial board state
        new_game_moves = self.game.getValidMoves(board, player)
        new_game_moves = [i for i, e in enumerate(new_game_moves) if e != 0]


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
            value = self.minimax(depth - 1, new_board_state, self.game, -infinity, infinity, 1-player, not is_maximising_player)#1-player)

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

        # print("Number of moves available: " + str(len(new_game_moves)))
        # print("COLOR: {} \nBEST MOVES: {} \n SCORES {} \n DECISION: {} \n DECISION SCORE: {}".format(player, list(map(decode_move, best_moves)), best_moves_scores, decode_move(best_move), best_move_score))
        # print("Finished a decision.")
        
        #end = timer()
        #print("Time elapsed: " + str(end - start))



        #Convert the move to a network-compatible representation
        move = decode_move(best_move)
        #print("decoded best move: " + str(move))


        b = Board(mcts_board=board)
        moves = b.generate_moves({'legal': True})

        ugly_move = None
        for i in range(len(moves)):
            #print("algebraic")
            #print(algebraic(moves[i]['from']))

            if (move['from'] == algebraic(moves[i]['from']) and move['to'] == algebraic(moves[i]['to']) and \
                (('promotion' not in moves[i].keys()) or move['promotion'] == moves[i]['promotion'])):
                ugly_move = moves[i]
                break

        assert ugly_move != None
        print("SELECTED MOVE: " + str(ugly_move))

        self.queue.put(ugly_move)




        return best_move


    def minimax(self, depth, board, game, alpha, beta, player, is_maximising_player):
 
        infinity = float('inf')

        #Base case where we've reached the max depth to explore
        if depth == 0:
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

                best_move_score = max(best_move_score, self.minimax(depth - 1, new_board_state, tmp_game, -infinity, infinity, 1-player, not is_maximising_player))

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

                best_move_score = min(best_move_score, self.minimax(depth - 1, new_board_state, self.game, -infinity, infinity, 1-player, not is_maximising_player))

                #Decrement the count so that we dont include boards that were touched in the search tree
                self.game.state_counts[self.game.stringRepresentation(new_board_state)] -= 1

                beta = min(beta, best_move_score)

                if (beta <= alpha):
                    return best_move_score

            return best_move_score






































class EnsemblePlayer():

    def __init__(self, game, networks, example_file):
        self.game = game
        print(len(networks))
        self.weights = np.zeros((len(networks),))
        self.networks = networks

        beta = 0.1
        batch_size = 64

        examples = self.loadTrainExamples(example_file)
        final_examples = []
        for e in examples:
            final_examples.extend(e)
        input_boards, target_pis, target_vs = list(zip(*final_examples))
        
        input_boards = np.asarray(input_boards)
        target_pis = np.asarray(target_pis)
        target_vs = np.asarray(target_vs)

        scores = {}
        num_nets = len(networks)
        for i in range(num_nets):
            network = networks[i]
            loss = network.nnet.model.evaluate(x = input_boards, y = [target_pis, target_vs], batch_size=batch_size, verbose=1)
            scores[i] = loss[0]
            print("Loss: ", loss)

        top_nets = sorted(scores, key=scores.get)

        sum_exp_betas = np.sum(np.exp(beta*np.arange(1,num_nets+1)))

        print(self.weights.shape)
        for j in range(num_nets):
            top_net_num = top_nets[j]
            print(top_net_num)
            self.weights[top_net_num] = np.exp(beta*(num_nets - j))/sum_exp_betas


    def predict(self, board):
        return_pi = np.zeros(self.game.getActionSize())
        return_v = 0
        
        board = board[np.newaxis, :, :]
        for i in range(len(self.networks)):
            network = self.networks[i]
            pi, v = network.nnet.model.predict(board)
            return_pi += self.weights[i]*pi[0]
            return_v += self.weights[i]*v[0]

        return return_pi, return_v


    def play(self, board):
        args = dotdict({'numMCTSSims': 50, 'cpuct': 1.0})
        mcts = MCTS(self.game, self, args)
        return np.argmax(mcts.getActionProb(board, temp=0))


    def loadTrainExamples(self, examples_file):
        if not os.path.isfile(examples_file):
            print(examples_file)
            print("File with trainExamples not found.")
            sys.exit()
        else:
            print("File with trainExamples found. Read it.")
            with open(examples_file, "rb") as f:
                return Unpickler(f).load()

