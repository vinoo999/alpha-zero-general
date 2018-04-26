from chess.keras.NNet import NNetWrapper as nn
from utils import *

import multiprocessing as mp
import random


class NNetSync():
    """
    Convenience class for NNetWorker and AtomicNNet
    """
    def __init__(self):
        self.work_queue = mp.Queue()
        self.done_queue = mp.Queue()
        self.done_lock = mp.Lock()


def NNetWorker(game, nsync, i): 
    """
    Workaround for multiprocessing errors when using Queue. Have to
    have queue passed from parent to child process in order for everything
    to work. Also there can only be one NNet, so multiple mcts_worker 
    threads share this NNet.
    """

    print("[NNet Worker " + str(i) + "] Started!")

    nnet = nn(game)

    lock = nsync.done_lock
    work_queue = nsync.work_queue
    done_queue = nsync.done_queue

    while True:
        data_id, data = work_queue.get()
        #print("[NNet Worker " + str(i) + "] Got Work!")

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
            nnet.train(data["examples"])
            res = "OK"

        #print("[NNet Worker " + str(i) + "] Done!")
        done_queue.put((data_id, res))


class NNetManager():
    def __init__(self, nnet_workers):
        self.global_lock = mp.Lock()
        self.nsyncs = []
        self.curr = 0

        assert(nnet_workers > 0)

        for i in range(nnet_workers):
            self.nsyncs.append(NNetSync())

    def nsync(self, i):
        return self.nsyncs[i]

    def incr_counter(self):
        return 0 if self.curr >= len(self.nsyncs) - 1 else self.curr + 1

    def schedule(self):
        """
        Round robin scheduler. Just grab queues in order because each job
        is relatively the same in terms of computational time required. Maybe
        look into putting a job on the least busy queue? Prob not necessary,
        and could actually be worse because of the extra overhead.
            @return the index of the queue
        """

        self.global_lock.acquire() # Protect critical section

        q_idx = self.curr
        self.curr = self.incr_counter()

        self.global_lock.release()

        return q_idx


    def put(self, data, q_idx=None):
        """
        Put data on the work_queue returned by schedule(). Non-blocking.
            @args(data) work to put on queue
            @return tuple of index of queue and data_id of data
        """

        # Get a queue according to scheduler if one isn't already provided
        if q_idx is None: q_idx = self.schedule()

        # Generate a 256-bit random hex string
        data_id = "%x" % random.getrandbits(256)

        # Put work on queue
        self.nsyncs[q_idx].work_queue.put((data_id, data))

        return (q_idx, data_id)


    def get(self, q_idx, data_id):
        """
        Blocks until data with data_id is put on done_queue at q_idx.
            @args(q_idx) index of done_queue to get from
            @args(data_id) data_id of data we are waiting for
            @return data from done_queue
        """

        while True:
            # Make sure no other get threads are pulling from the queue
            self.nsyncs[q_idx].done_lock.acquire()

            # Check every item currently in the queue
            done_queue = self.nsyncs[q_idx].done_queue
            for i in range(done_queue.qsize()):
                tup = done_queue.get()

                # Check if item is our item (ie. if the ids match)
                if tup[0] == data_id:
                    self.nsyncs[q_idx].done_lock.release()
                    return tup[1]

                # Nope, not our item, put it back on the done_queue 
                # for someone else to grab
                done_queue.put(tup)

            # Didn't find our item, try again..
            self.nsyncs[q_idx].done_lock.release()


    def predict(self, board):
        """
        Predict() is thread-safe, it can be called concurrently from 
        different threads.
        """
        data = dict()
        data["inst"] = "predict"
        data["board"] = board

        q_idx, data_id = self.put(data)
        res = self.get(q_idx, data_id)  # Blocks here

        return res


    def train(self, example):
        """
        Train() is not thread-safe, it should not be called concurrently
        from different threads. Train() always trains the first NNet.
        """
        data = dict()
        data["inst"] = "train"
        data["examples"] = example

        q_idx, data_id = self.put(data, q_idx=0) # Send instruction to first nnet
        self.get(q_idx, data_id)                 # Blocks here

        # Done


    def save_checkpoint(self, folder='checkpoint', filename='checkpoint.pth.tar'):
        """
        Save() is not thread-safe, it should not be called concurrently
        from different threads. Train() always saves the first NNet.
        """
        data = dict()
        data["inst"] = "save"
        data["folder"] = folder
        data["filename"] = filename

        q_idx, data_id = self.put(data, q_idx=0) # Send instruction to first nnet
        self.get(q_idx, data_id)                 # Blocks here

        # Done


    def load_checkpoint(self, folder='checkpoint', filename='checkpoint.pth.tar'):
        """
        Load() is not thread-safe, it should not be called concurrently
        from different threads. Train() will reload all neural networks.
        """
        data = dict()
        data["inst"] = "load"
        data["folder"] = folder
        data["filename"] = filename

        # Send load requests to every nnet
        metadata = []
        for i in range(len(self.nsyncs)):
            metadata.append(self.put(data, q_idx=i))

        # Wait for all nnets to finish
        for q_idx, data_id in metadata:
            self.get(q_idx, data_id)    # Blocks here

        # Done

