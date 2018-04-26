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