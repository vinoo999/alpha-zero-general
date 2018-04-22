import Arena
from MCTS import MCTS
from chess.ChessGame import ChessGame, display
from chess.ChessPlayers import *
#from chess.keras.NNet import NNetWrapper as NNet

import numpy as np
from utils import *

"""
use this script to play any two agents against each other, or play manually with
any agent.
"""

g = ChessGame()

# all players
rp = RandomPlayer(g).play
#gp = GreedyOthelloPlayer(g).play
#hp = HumanChessPlayer(g).play
#abp = AlphaBetaPlayer(g).play

# nnet players
#n1 = NNet(g)
#n1.load_checkpoint('temp/','checkpoint_1.pth.tar')
#n2 = NNet(g)
#n2.load_checkpoint('temp/','checkpoint_2.pth.tar')
#n3 = NNet(g)
#n3.load_checkpoint('temp/','checkpoint_3.pth.tar')
#n4 = NNet(g)
#n4.load_checkpoint('temp/','checkpoint_4.pth.tar')
#n5 = NNet(g)
#n5.load_checkpoint('temp/','checkpoint_5.pth.tar')

#example_file = 'temp/checkpoint_4.pth.tar.examples'
#networks = [n1, n2,n3, n4,n5]


#ensemble_player = EnsemblePlayer(g,networks,example_file).play

#args1 = dotdict({'numMCTSSims': 50, 'cpuct': 1.0})
#mcts1 = MCTS(g, n1, args1)
#n1p = lambda x: np.argmax(mcts1.getActionProb(x, temp=0))
# #n1p = lambda x: np.argmax(n1.predict(x))

#n2 = NNet(g)
#n2.load_checkpoint('/home/jason/alpha-zero-general/temp/','temp.pth.tar')
#args2 = dotdict({'numMCTSSims': 50, 'cpuct': 1.0})
#mcts2 = MCTS(g, n2, args2)
#n2p = lambda x: np.argmax(mcts2.getActionProb(x, temp=0))





arena = Arena.Arena(rp, rp, g, display=display)

print(arena.playGames(100, verbose=False))
