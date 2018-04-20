from chess.ChessGame import display
from chess.ChessLogic import Board
from chess.ChessUtil import *
from chess.ChessConstants import *

import numpy as np
import copy
from queue import Queue





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


    def __init__(self, game):
        self.game = game
        self.depth = 3

    def play(self, board):
        """Equivalent to minimaxRoot function in javascript"""
        """Returns the best move as variable *num* """
        depth = self.depth
        infinity = float('inf')

        #Get available moves for the initial board state
        new_game_moves = self.game.getValidMoves(board, player)

        #Start off the player with their worst possible score
        best_move = -infinity #Change to "best_move_score" and "best_move"
        best_move_found = None



        for i in range(len(new_game_moves)):

            new_game_move = new_game_moves[i]

            #Create a board copy so that we dont mess up the root

            board_copy = copy.deepcopy(board)
            new_board_state = game.get_state(board, new_game_move)
            
            player_turn = board[8][3]

            value = minimax(depth - 1, board, game, -infinity, infinity, player_turn)
            if(value >= bestMove):
                bestMove = value
                bestMoveFound = newGameMove

        return bestMoveFound


    def minimax(self, depth, board, game, alpha, beta, player):
        #position_count+=1

        #Base case where we've reached the max depth to explore
        if depth == 0:
            return -self.game.getScore(board, player)


        new_game_moves = self.game.getValidMoves(board, player)

        #if maximizing player (assume 1 for now)
        if(player==1):
            best_move = -infinity

            for i in range(len(new_game_moves)):

                #This should capture ugly_move and undo in one
                #Create a board copy so that we dont mess up the root
                canonical_board = self.game.getCanonicalForm(board, curPlayer)
                board_copy = copy.deepcopy(canonical_board)
                #1-player to flip between player 1 and 0
                best_move = Math.max(bestMove, minimax(depth - 1, game, alpha, beta, 1-player))
                
                alpha = Math.max(alpha, bestMove);
                if (beta <= alpha):
                    return bestMove

        else:
            best_move = infinity
            for i in range(new_game_moves):
                best_move = Math.min(bestMove, minimax(depth - 1, game, alpha, beta, 1-player))

                beta = Math.min(beta, bestMove)

                if (beta <= alpha):
                    return bestMove

            return bestMove






















#class AlphaBetaPlayer():
#     """First build a game deep """
#     #Alpha: best already explored option along path to root for maximizer
#     #Beta: best already explored option along path to root for minimizer
#     def __init__(self, game):
#         self.game = game
#     def play(self, board):
#         """Returns the best move as variable *num* """
#         rootNode = generateGameTree()
#         best_state = alpha_beta_search(rootNode)
#     def generateGameTree(self, current_board, n_levels):
#         """Method to generate a game tree N moves out to work on"""
#         #Get integer representation with generate moves from chessGame
#         #Get all available moves from current position in game tree
#         starting_valid_moves = self.game.getValidMoves()
#         #Go n levels deep in the tree
#         #def getValidMoves(self, board, player):

















