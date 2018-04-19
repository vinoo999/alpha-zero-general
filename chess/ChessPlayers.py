import numpy as np
from chess.ChessGame import display
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


class AlphaBetaPlayer():
    def __init__(self, game):
        self.game = game






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
