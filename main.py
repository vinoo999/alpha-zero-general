from Coach import Coach
from chess.ChessGame import ChessGame as Game
from chess.keras.NNet import NNetWrapper as nn
from AtomicNeuralNet import *
from utils import *

import multiprocessing as mp

args = dotdict({
    'numIters': 5,
    'numEps': 100,
    'tempThreshold': 15,
    'updateThreshold': 0.6,
    'maxlenOfQueue': 200000,
    'numMCTSSims': 25,
    'arenaCompare': 40,
    'cpuct': 1,

    'max_threads': 2,

    'checkpoint': './temp/',
    'load_model': True,
    'load_folder_file': ('saves/save-bc5a3cffa65','best.pth.tar'),
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
