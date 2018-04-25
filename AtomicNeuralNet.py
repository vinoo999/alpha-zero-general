from chess.keras.NNet import NNetWrapper as nn
from utils import *

import multiprocessing as mp

class NNetSync():
    def __init__(self):
        """
        Convenience class for NNetWorker and AtomicNNet
        """
        self.work_queue = mp.Queue()
        self.done_queue = mp.Queue()
        self.lock = mp.Lock()


def NNetWorker(game, nsync): 
    """
    Workaround for multiprocessing errors when using Queue. Have to
    have queue passed from parent to child process in order for everything
    to work. Also there can only be one NNet, so multiple mcts_worker 
    threads share this NNet.
    """
    nnet = nn(game)

    work_queue = nsync.work_queue
    done_queue = nsync.done_queue

    while True:
        data = work_queue.get()

        if data["inst"] == "predict":
            res = nnet.predict(data["board"])

        elif data["inst"] == "save":
            print("[NNetWorker] Got save...")
            nnet.save_checkpoint(folder=data["folder"], filename=data["filename"])
            res = "OK"

        elif data["inst"] == "load":
            print("[NNetWorker] Got load...")
            nnet.load_checkpoint(folder=data["folder"], filename=data["filename"])
            res = "OK"

        elif data["inst"] == "train":
            print("[NNetWorker] Got train...")
            nnet.train(work["examples"])
            res = "OK"

        done_queue.put(res)


class AtomicNNet():
    def __init__(self, nsync):
        self.nsync = nsync

    def train(self, example):
        self.nsync.lock.acquire()

        data = dict()
        data["inst"] = "train"
        data["examples"] = example

        self.nsync.work_queue.put(data)
        self.nsync.done_queue.get()

        self.nsync.lock.release()


    def predict(self, board):
        self.nsync.lock.acquire()

        data = dict()
        data["inst"] = "predict"
        data["board"] = board

        self.nsync.work_queue.put(data)
        res = self.nsync.done_queue.get()

        self.nsync.lock.release()

        return res


    def save_checkpoint(self, folder='checkpoint', filename='checkpoint.pth.tar'):
        self.nsync.lock.acquire()

        data = dict()
        data["inst"] = "save"
        data["folder"] = folder
        data["filename"] = filename

        self.nsync.work_queue.put(data)
        self.nsync.done_queue.get()

        self.nsync.lock.release()


    def load_checkpoint(self, folder='checkpoint', filename='checkpoint.pth.tar'):
        self.nsync.lock.acquire()

        data = dict()
        data["inst"] = "load"
        data["folder"] = folder
        data["filename"] = filename

        self.nsync.work_queue.put(data)
        self.nsync.done_queue.get()

        self.nsync.lock.release()

