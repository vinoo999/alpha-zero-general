from Coach import Coach
from chess.ChessGame import ChessGame as Game
from chess.keras.NNet import NNetWrapper as nn
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
    'parallel': True,

    'checkpoint': './temp/',
    'load_model': False,
    'load_folder_file': ('/dev/models/8x100x50','best.pth.tar'),
    'numItersForTrainExamplesHistory': 20,

})


class NNetQueue():
    def __init__(self, work_queue, done_queue):
        self.work_queue = work_queue
        self.done_queue = done_queue


def main():
    #mp.set_start_method('spawn')

    g = Game()
    nnet = nn(g)

    mp.Process(target=nnet.worker).start()

    if args.load_model:
        nnet.load_checkpoint(args.load_folder_file[0], args.load_folder_file[1])

    c = Coach(g, nnet, args)

    if args.load_model:
        print("Load trainExamples from file")
        c.loadTrainExamples()

    c.learn(NNetQueue(nnet.work_queue, nnet.done_queue))


if __name__=="__main__":
    main()