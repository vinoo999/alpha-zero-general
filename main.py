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

    'max_threads': 8,
    'parallel': True,

    'checkpoint': './temp/',
    'load_model': False,
    'load_folder_file': ('/dev/models/8x100x50','best.pth.tar'),
    'numItersForTrainExamplesHistory': 20,

})


class NNetQueue():
    def __init__(self, work_queue, done_queue, lock):
        self.work_queue = work_queue
        self.done_queue = done_queue
        self.lock = lock

def NNetWorker(g, q): 
    nnet = nn(g)

    work_queue = q.work_queue
    done_queue = q.done_queue

    while True:
        # print("[NNet Worker] Waiting for work...")

        work = work_queue.get()

        if work["instruction"] == "predict":
            # print("[NNet Worker] Got predict! Working...")
            res = nnet.predict(work["board"])

        elif work["instruction"] == "save":
            # print("[NNet Worker] Got save_checkpoint! Working...")
            self.nnet.save_checkpoint(folder=work["folder"], filename=work["filename"])
            res = "OK"

        elif work["instruction"] == "load":
            # print("[NNet Worker] Got load_checkpoint! Working...")
            self.nnet.load_checkpoint(folder=work["folder"], filename=work["filename"])
            res = "OK"

        elif work["instruction"] == "train":
            self.nnet.train(work["examples"])
            res = "OK"

        # print("[NNet Worker] Done with work! Sending results...")
        done_queue.put(res)


def main():
    #mp.set_start_method('spawn')

    g = Game()

    lock = mp.Lock()
    work_queue = mp.Queue()
    done_queue = mp.Queue()
    nnet = NNetQueue(work_queue, done_queue, lock)
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
