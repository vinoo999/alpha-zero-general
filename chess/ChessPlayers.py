from chess.ChessGame import display
from chess.ChessLogic import Board
from chess.ChessUtil import *
from chess.ChessConstants import *
from chess.keras.NNet import NNetWrapper as NNet
from MCTS import MCTS
from utils import *

import numpy as np
import copy
from queue import Queue
import math
from timeit import default_timer as timer
import time


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
    def __init__(self, game):
        self.game = game
        self.queue = Queue(maxsize=1)

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
                continue

            #Ensure the promotion piece is valid
            if len(a_split) == 3 and a_split[2] not in ['n', 'b', 'r', 'q']:
                print("Improper promotion format. Enter again.")
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






class AlphaBetaPlayer(): 
    #Alpha: best already explored option along path to root for maximizer
    #Beta: best already explored option along path to root for minimizer
    """NOTE: We're treating player 1 as the maximizing player and player 2 as minimizing"""
    """
        Do we need deepcopy for each board in the recursive call?
        Do we need player_turn = board[8][2] in each recursive call or just is max player?
        Why do we return without checking everything in alphabeta? if (beta <= alpha): return best_move
    """

    def __init__(self, game):
        self.game = game
        self.depth = 1

    def play(self, board):
        """Returns the best move as variable *num* """
        """board is the canonical board"""
        depth = self.depth

        infinity = float('inf')

        player = board[8][2]

        pos_player_start = True if player==0 else False

        is_maximising_player = True

        print("Start playing")
        print("player number: " + str(player))

        #Get available moves for the initial board state
        new_game_moves = self.game.getValidMoves(board, player)
        new_game_moves = [i for i, e in enumerate(new_game_moves) if e != 0]

        #print("starting available moves: " + str(len(new_game_moves)))
        #Start off the player with their worst possible score
        best_move_score = -infinity #Change to "best_move_score" and "best_move"
        best_move = None

        best_moves_scores = [-infinity, -infinity, -infinity]
        best_moves = [0, 0, 0]

        print("start timer")
        start = timer()

        #Iterate over initial moves and pass into the minimax function to recurse on
        for i in range(len(new_game_moves)):
            #print("--------------------------------------------------------------")
            #print("Generating a move on i= " + str(i))
            #print("--------------------------------------------------------------")

            new_game_move = new_game_moves[i]

            #Create a board copy so that we dont affect the root
            board_copy = copy.deepcopy(board)

            #Apply the move to the starting board to generate a new board (get next state is tuple holding board and count)
            new_board_state = self.game.getNextState(board_copy, player, new_game_move)[0]

            
            #Play the game starting with this move up to 'depth' and assess it's value
            value = self.minimax(depth - 1, board_copy, self.game, -infinity, infinity, 1-player, not is_maximising_player)#1-player)
            
            print()

            #Grab the best move and return
            if(value >= best_move_score):
                best_move_score = value
                best_move = new_game_move
                print("*************************\n Best Move: {} , best_move_score: {} , value {}".format(decode_move(best_move), best_move_score, value))
            else:
                print("LWEHRLEWH************************************")

            #Find the minimum of the highest score values, and see if our new score is larger (i.e should be inserted into the 3 best move array)
            min_score = infinity
            worst_move = i
            for i in range(len(best_moves)):
                if best_moves_scores[i] < min_score:
                    min_score = best_moves_scores[i]
                    worst_move = i
            if best_move_score > min_score:
                best_moves_scores[worst_move] = best_move_score
                best_moves[worst_move] = best_move



        print("COLOR: {} \nBEST MOVES: {} \n SCORES {} \n DECISION: {}".format(player, list(map(decode_move, best_moves)), best_moves_scores, decode_move(best_move)))

        print("Finished a decision.")
        
        end = timer()
        print("Time elapsed: " + str(end - start))

        print(best_move)
        return best_move


    def minimax(self, depth, board, game, alpha, beta, player, is_maximising_player):
        #position_count+=1
        #print("In minimax at depth: " + str(depth))
        #print("player is: " + str(player))

        infinity = float('inf')
        #print("player: " +str(player))
        #Base case where we've reached the max depth to explore
        if depth == 0:
            #print("At depth zero!------------------------------------------------------------------")
            #print("The score is: " + str(-self.game.getScore(board, player)))
            #Negate for what reason?

            #Essentially a call to Evaluate_board()
            return -self.game.getScore(board, player)

        #Get all available moves stemming from the passed board state
        new_game_moves = self.game.getValidMoves(board, player)
        new_game_moves = [i for i, e in enumerate(new_game_moves) if e != 0]

        #print("available moves: " + str(new_game_moves))

        #if maximizing player (assume 1 for now)
        if(is_maximising_player):#1-player)):
            # print("Maximising player", len(new_game_moves))
            # print("is_maximising_player = " + str(is_maximising_player))
            # print("Currently in recurisve call with player: " + str(player))
            # print("Player to be passed into next recursive call: " + str(1-player))
            # print("is_maximising_player to be passed = " + str( not is_maximising_player))
            # print("The depth is: " + str(depth))
            # print("")

            #print("")
            #print("player number: " + str(player))
            #Start best player at the worst possible score
            best_move_score = -infinity

            for i in range(len(new_game_moves)):
                #print("i in max player is: " + str(i))
                new_game_move = new_game_moves[i]
                #player_turn = board[8][2]
                time_copying = time.time()
                board_copy = copy.deepcopy(board)
                tmp_game = copy.deepcopy(self.game)
                time_end_copying = time.time()
                #print("Deep Copy Maximizer: {}".format(time_end_copying-time_copying))
                new_board_state = tmp_game.getNextState(board_copy, player, new_game_move)[0]

                # "1-player" to flip between player 1 and 0 instead of is_maximising_player
                #print("call to minimax on player: " + str(1-player))
                #print("above best move, depth-1 = " + str(depth-1))
                time_next_state = time.time()
                best_move_score = max(best_move_score, self.minimax(depth - 1, new_board_state, tmp_game, -infinity, infinity, 1-player, not is_maximising_player))#1-player)
                time_end_next_state = time.time()
                #print("Get next state time  maximizer: {}".format(time_end_next_state-time_next_state))


                #Decrement the count so that we dont include boards that were touched in the search tree
                self.game.state_counts[self.game.stringRepresentation(new_board_state)] -= 1



                #print("best_move")
                #print(best_move)
                alpha = max(alpha, best_move_score)

                # print("alpha: " + str(alpha))
                # print("beta: " + str(beta))

                if (beta <= alpha):
                    #print("------------------will return a move! ()-------------------------------------")
                    return best_move_score
            #print("------------------will return a move!-------------------------------------")
            return best_move_score

        else:
            # print("Minimizing player", len(new_game_moves))
            # print("is_maximising_player = " + str(is_maximising_player))
            # print("Currently in recurisve call with player: " + str(player))
            # print("Player to be passed into next recursive call: " + str(1-player))
            # print("is_maximising_player to be passed = " + str( not is_maximising_player))
            # print("The depth is: " + str(depth))

            #print("")
            #print("player number: " + str(player))
            #print("len(new_game_moves): " +str(len(new_game_moves)))
            best_move_score = infinity

            for i in range(len(new_game_moves)):

                new_game_move = new_game_moves[i]


                time_copying = time.time()
                board_copy = copy.deepcopy(board)
                tmp_game = copy.deepcopy(self.game)
                time_end_copying = time.time()
                #print("Deep Copy Minimizer: {}".format(time_end_copying-time_copying))


                time_next_state = time.time()
                new_board_state = tmp_game.getNextState(board_copy, player, new_game_move)[0]
                time_end_next_state = time.time()
                #print("Get next state time minimizer: {}".format(time_end_next_state-time_next_state))
                #print("in mini, i = " + str(i))

                best_move_score = min(best_move_score, self.minimax(depth - 1, new_board_state, self.game, -infinity, infinity, 1-player, not is_maximising_player))#1-player)
                #print("Mini------best_move")
                #print(best_move)

                #Decrement the count so that we dont include boards that were touched in the search tree
                self.game.state_counts[self.game.stringRepresentation(new_board_state)] -= 1

                beta = min(beta, best_move_score)

                if (beta <= alpha):
                    #print("------------------will return a move! ()-------------------------------------")
                    return best_move_score

            #print("------------------will return a move!-------------------------------------")
            return best_move_score













