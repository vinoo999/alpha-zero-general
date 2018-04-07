import numpy as np
from chess.ChessGame import display
from .ChessUtil import *



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
        for i in range(len(valid)):
            if valid[i]:
                print(int(i/self.game.n), int(i%self.game.n))
        
        #Grab human move and play it if valid
        while True:
            display(board)
            print("Enter an action: [moveFrom moveTo promotion-if-applicable]\n")
            a = input()

            a_split = a.split()

            moveFrom, moveTo = a_split[0], a_split[1]

            
            #Go from a human-readable action (a9->a8) to an action encoding
                #moveFrom = algebraic(move['from'])
                #moveTo = algebraic(move['to'])

            print("moveFrom: " + str(moveFrom)) 

            file1 = moveFrom[0]
            rank1 = moveFrom[1]
            file2 = moveTo[0]
            rank2 = moveTo[1]

            file1_idx = 'abcdefgh'.index(file1)
            file2_idx = 'abcdefgh'.index(file2)
            rank1_idx = '87654321'.index(rank1)
            rank2_idx = '87654321'.index(rank2)
            
            print("file1: " + str(file1)) 
            print("rank1: " + str(rank1))
            print("file1_idx: " + str(file1_idx)) 
            print("rank1_idx: " + str(rank1_idx)) 

            #Check to see if a promotion is applicable [Knight: 'n', Bishop: 'b', Rook: 'r', Queen: 'q']
            if len(a_split) == 3:
                promotion = MCTS_MAPPING[move['promotion']]-2 # move range to 0-3
                offset = 64*64
                direction = abs(moveFrom[1] - moveTo[1]) + 1
                    # 0 means promote takes right
                    # 1 means advance
                    # 2 means promote takes left
                rank_abbrv = 0 if move['color'] == WHITE else 1
                num = promotion*4 + direction + 16*(2*file1_idx + rank_abbrv) + offset
            else:
                num = (8*file1_idx + rank1_idx)*64 + 8*file2_idx + rank2_idx


            if valid[num]:
                break
            else:
                print('Invalid')





        #     #Build the proper representation of the action
        #     a = 



        #     action = self.game.n * 


        #     x,y = [int(x) for x in a.split(' ')]
        #     a = self.game.n * x + y if x!= -1 else self.game.n ** 2
        #     if valid[a]:
        #         break
        #     else:
        #         print('Invalid')

        # return a

       # print("num: " + str(num))
        # print(algebraic(num))
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
