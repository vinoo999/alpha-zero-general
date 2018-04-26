from Coach import Coach
from chess.ChessGame import ChessGame as Game
from chess.keras.NNet import NNetWrapper as nn
#from othello.OthelloGame import OthelloGame as Game
#from othello.keras.NNet import NNetWrapper as nn

from AtomicNeuralNet import *
from utils import *

import multiprocessing as mp

args = dotdict({
    'numIters': 100,            # Total number of iterations of self-play, training, and evaluation
    'numEps': 100,              # Number of self-play examples generated per iteration
    'tempThreshold': 100,       # Number of stochastic MCTS simulations per training game
    'updateThreshold': 0.6,     # Percent minimum number of wins during evaluation to accept new model
    'maxlenOfQueue': 200000,    # Max number of examples in training data
    'numMCTSSims': 150,         # Number of MCTS simulations per move
    'arenaCompare': 25,         # Number of games in evaluation step
    'cpuct': 1,                 # MCTS exploration vs exploitation parameter

    'mcts_workers': 2,
    'nnet_workers': 1,

    'checkpoint': './temp/',
    'load_model': False,
    'load_folder_file': ('saves/','best.pth.tar'),
    'numItersForTrainExamplesHistory': 20,

})

def main():
    g = Game()

    nsync = NNetSync()
    nnet = AtomicNNet(nsync)
    mp.Process(target=NNetWorker, args=(g, nsync)).start()

    if args.load_model:
        nnet.load_checkpoint(args.load_folder_file[0], args.load_folder_file[1])

    c = Coach(g, nnet, args)

    if args.load_model:
        print("Load trainExamples from file")
        c.loadTrainExamples()

    c.learn()

if __name__=="__main__":
    main()
