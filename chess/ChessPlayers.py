from chess.ChessGame import display
from chess.ChessLogic import Board
from chess.ChessUtil import *
from chess.ChessConstants import *

import numpy as np
from queue import Queue

class RandomPlayer():
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
        self.queue = Queue(maxsize=1)

    def play(self, board):
        # display(board)
        #Collect valid moves for this position
        valid = self.game.getValidMoves(board, 1)
        #for i in range(len(valid)):
        #    if valid[i]:
                #print(int(i/self.game.n), int(i%self.game.n))
        
        #Grab human move and play it if valid
        while True:
            color = 0 if board[8,2] == 1 else 1

            #display(board)
            #print("Enter an action: [moveFrom moveTo promotion-if-applicable]\n")

            # Old Method: just get input from user
            #a = raw_input()

            # New Method: wait until user makes move on GUI (aka. browser)
            a = self.queue.get()

            a_split = a.split()
            #print("a_split: " + str(a_split))

            if len(a_split) < 2:
                print("Improper move format. Enter again.")
                continue

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

            print("moveFrom:" + str(moveFrom) )
            print("moveTo: " + str(moveTo))
            print("file1_idx: " + str(file1_idx))
            print("rank1_idx: " + str(rank1_idx))


            #Check to see if a promotion is applicable [Knight: 'n', Bishop: 'b', Rook: 'r', Queen: 'q']
            if len(a_split) == 3:
                promo_piece = a_split[2]

                #Map the promotion letter to a number
                promotion = MCTS_MAPPING[promo_piece]-2

                offset = 64*64

                #Map the moveFrom/MoveTo to ints and find the move direction. 0: promote takes right, 1: advance, 2: promote takes left
                direction = abs(SQUARES[moveFrom] - SQUARES[moveTo]) - 16 + 1

                num = promotion*4 + direction + 16*(2*file1_idx + color) + offset
            else:
                num = (8*file1_idx + rank1_idx)*64 + 8*file2_idx + rank2_idx


            if valid[num]:
                break
            else:
                print('Invalid')

        print(num)

        return num

