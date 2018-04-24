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
    def __init__(self, g):
        self.work_queue = mp.Queue()
        self.done_queue = mp.Queue()
        self.nnet = nn(g)

    def NNetWorker(self):
        while True:
            # print("[NNet Worker] Waiting for work...")
            board = self.work_queue.get()
            # print("[NNet Worker] Got work! Working...")
            res = self.nnet.predict(board)
            # print("[NNet Worker] Done with work! Sending results...")
            self.done_queue.put(res)
            # print("[NNet Worker] Done!")


def main():
    #mp.set_start_method('spawn')

    g = Game()

    #work_queue = mp.Queue()
    #done_queue = mp.Queue()
    nnet = NNetQueue(g)

    mp.Process(target=nnet.NNetWorker).start()

    # if args.load_model:
    #     nnet.load_checkpoint(args.load_folder_file[0], args.load_folder_file[1])

    c = Coach(g, nnet, args)

    # if args.load_model:
    #     print("Load trainExamples from file")
    #     c.loadTrainExamples()

    c.learn()


if __name__=="__main__":
    main()