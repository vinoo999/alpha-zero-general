import numpy as np
from chess.ChessGame import display
from .ChessUtil import *
from chess.ChessConstants import *



class RandomPlayer():
    def __init__(self, game):
        self.game = game

    def play(self, board):
        a = np.random.randint(self.game.getActionSize())
        valids = self.game.getValidMoves(board, 1)
        while valids[a]!=1:
            a = np.random.randint(self.game.getActionSize())
        return a

class HumanChessPlayer():
    def __init__(self, game):
        self.game = game

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

            display(board)
            print("Enter an action: [moveFrom moveTo promotion-if-applicable]\n")
            a = input()

            a_split = a.split()
            print("a_split: " + str(a_split)) 
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

















class HumanOthelloPlayer():
    def __init__(self, game):
        self.game = game

    def play(self, board):
        # display(board)
        valid = self.game.getValidMoves(board, 1)
        for i in range(len(valid)):
            if valid[i]:
                print(int(i/self.game.n), int(i%self.game.n))
        while True:
            a = input()

            x,y = [int(x) for x in a.split(' ')]
            a = self.game.n * x + y if x!= -1 else self.game.n ** 2
            if valid[a]:
                break
            else:
                print('Invalid')

        return a


class GreedyOthelloPlayer():
    def __init__(self, game):
        self.game = game

    def play(self, board):
        valids = self.game.getValidMoves(board, 1)
        candidates = []
        for a in range(self.game.getActionSize()):
            if valids[a]==0:
                continue
            nextBoard, _ = self.game.getNextState(board, 1, a)
            score = self.game.getScore(nextBoard, 1)
            candidates += [(-score, a)]
        candidates.sort()
        return candidates[0][1]
