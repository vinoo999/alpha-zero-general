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

def NNetWorker(g, q):
    nnet = nn(g)

    work_queue = q.work_queue
    done_queue = q.done_queue

    while True:
        # print("[NNet Worker] Waiting for work...")
        board = work_queue.get()
        # print("[NNet Worker] Got work! Working...")
        res = nnet.predict(board)
        # print("[NNet Worker] Done with work! Sending results...")
        done_queue.put(res)
        # print("[NNet Worker] Done!")


def main():
    #mp.set_start_method('spawn')

    g = Game()

    work_queue = mp.Queue()
    done_queue = mp.Queue()
    nnet = NNetQueue(work_queue, done_queue)
    mp.Process(target=NNetWorker, args=(g, nnet)).start()

    # if args.load_model:
    #     nnet.load_checkpoint(args.load_folder_file[0], args.load_folder_file[1])

    c = Coach(g, nnet, args)

    # if args.load_model:
    #     print("Load trainExamples from file")
    #     c.loadTrainExamples()

    c.learn()


if __name__=="__main__":
    main()