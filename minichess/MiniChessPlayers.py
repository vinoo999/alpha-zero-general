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
            move_index = encode_move(move, 1)
            if valid[move_index]:
            	break
            else:
            	print("Invalid move. Enter again.")

        return move_index










