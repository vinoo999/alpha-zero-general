from collections import deque
from Arena import Arena
from MCTS import MCTS
import numpy as np
from pytorch_classification.utils import Bar, AverageMeter
from chess.keras.NNet import NNetWrapper as nn
import time, os, sys
from pickle import Pickler, Unpickler
from random import shuffle
from chess.ChessUtil import decode_move
from chess.ChessGame import display
from queue import Queue
import multiprocessing as mp
import copy

class pickler_dict():
    def __init__(self, d):
        self.d = d

    def __getattr__(self, name):
        # assert hasattr(self, '_data')
        return self.d[name]

    def __getstate__(self):
        return self.d

    # def __setstate__(self, tmp):
    #     self.d = tmp


class Coach():
    """
    This class executes the self-play + learning. It uses the functions defined
    in Game and NeuralNet. args are specified in main.py.
    """
    def __init__(self, game, nnet, args):
        self.game = game
        self.nnet = nnet
        self.pnet = self.nnet.__class__(self.game)  # the competitor network
        self.args = args
        self.mcts = MCTS(self.game, self.nnet, self.args)
        self.trainExamplesHistory = []    # history of examples from args.numItersForTrainExamplesHistory latest iterations
        self.skipFirstSelfPlay = False # can be overriden in loadTrainExamples()


    # DEPRICATED -- use mcts_worker instead
    # def executeEpisode(self):
    #     """
    #     This function executes one episode of self-play, starting with player 1.
    #     As the game is played, each turn is added as a training example to
    #     trainExamples. The game is played till the game ends. After the game
    #     ends, the outcome of the game is used to assign values to each example
    #     in trainExamples.

    #     It uses a temp=1 if episodeStep < tempThreshold, and thereafter
    #     uses temp=0.

    #     Returns:
    #         trainExamples: a list of examples of the form (canonicalBoard,pi,v)
    #                        pi is the MCTS informed policy vector, v is +1 if
    #                        the player eventually won the game, else -1.
    #     """
    #     trainExamples = []
    #     board = self.game.getInitBoard()
    #     self.curPlayer = 1
    #     episodeStep = 0

    #     while True:
    #         episodeStep += 1
    #         canonicalBoard = self.game.getCanonicalForm(board,self.curPlayer)
    #         temp = int(episodeStep < self.args.tempThreshold)
    #         pi = self.mcts.getActionProb(canonicalBoard, temp=temp)
    #         sym = self.game.getSymmetries(canonicalBoard, pi)
    #         for b,p in sym:
    #             trainExamples.append([b, self.curPlayer, p, None])

    #         action = np.random.choice(len(pi), p=pi)
            
    #         board, self.curPlayer = self.game.getNextState(board, self.curPlayer, action)

    #         r = self.game.getGameEnded(board, self.curPlayer)

    #         if r!=0:
    #             return [(x[0],x[2],r*((-1)**(x[1]!=self.curPlayer))) for x in trainExamples]


    def mcts_worker(self, in_queue, out_queue, bar, eps_time, lock, num, num_eps):
        """
        Localized version of learn() and executeEpisode() that is thread-safe. Args
        game, nnet, and args should be their own localized copies. This function may
        mutate these objects.
        """

        print("[Worker " + str(num) + "] Started!")

        # Grab work from queue and decode the work data
        while True:
            print("[Worker " + str(num) + "] Waiting for work...")
            work = in_queue.get()
            print("[Worker " + str(num) + "] Got work! Running MCTS simulation...")
            i = work["i"]
            game = work["game"]
            nnet = work["nnet"]
            # args = work["args"]

            # Create our MCTS instance
            mcts = MCTS(game, nnet, self.args)

            # Start "executeEpisode()"
            trainExamples = []
            board = game.getInitBoard()
            curPlayer = 1
            episodeStep = 0

            print("[Worker " + str(num) + "] Starting game...")

            while True:
                print("[Worker " + str(num) + "] Game iteration...")
                episodeStep += 1

                print("[Worker " + str(num) + "] Getting canonical board...")

                canonicalBoard = game.getCanonicalForm(board, curPlayer)

                print("[Worker " + str(num) + "] Getting action prob...")

                temp = int(episodeStep < self.args.tempThreshold)
                pi = mcts.getActionProb(canonicalBoard, temp=temp)

                print("[Worker " + str(num) + "] Getting symmetries...")

                sym = game.getSymmetries(canonicalBoard, pi)
                for b, p in sym:
                    trainExamples.append([b, curPlayer, p, None])

                print("[Worker " + str(num) + "] Next.")

                action = np.random.choice(len(pi), p=pi)
                board, curPlayer = game.getNextState(board, curPlayer, action)
                res = game.getGameEnded(board, curPlayer)

                print("[Worker " + str(num) + "] Next..")

                if res != 0:
                    print("[Worker " + str(num) + "] Game done!")
                    out_queue.put([(x[0], x[2], r * ((-1) ** (x[1] != curPlayer))) for x in trainExamples])

                    print("[Worker " + str(num) + "] Aquiring lock...")

                    # Grab lock and update bar
                    lock.aquire()

                    print("[Worker " + str(num) + "] Obtained lock!")

                    eps_time.update(time.time() - end)
                    end = time.time()
                    bar.suffix = '({eps}/{maxeps}) Eps Time: {et:.3f}s | Total: {total:} | ETA: {eta:}'.format(
                                  eps=work["i"], maxeps=num_eps, et=eps_time.avg, total=bar.elapsed_td, eta=bar.eta_td)
                    bar.next()

                    print("[Worker " + str(num) + "] Releasing lock...")

                    lock.release()

                    print("[Worker " + str(num) + "] Done!")

                    break

                print("[Worker " + str(num) + "] Game iteration done.")


    def learn(self, nnq):
        """
        Performs numIters iterations with numEps episodes of self-play in each
        iteration. After every iteration, it retrains neural network with
        examples in trainExamples (which has a maximium length of maxlenofQueue).
        It then pits the new neural network against the old one and accepts it
        only if it wins >= updateThreshold fraction of games.
        """

        for i in range(1, self.args.numIters+1):
            # bookkeeping
            print('------ITER ' + str(i) + '------')
            # examples of the iteration
            if not self.skipFirstSelfPlay or i>1:
                iterationTrainExamples = deque([], maxlen=self.args.maxlenOfQueue)
    
                eps_time = AverageMeter()
                bar = Bar('Self Play', max=self.args.numEps)
                end = time.time()
    
                # Multiprocess self-play
                proccesses = []
                lock = mp.Lock()
                work_queue = mp.Queue()
                done_queue = mp.Queue()

                # Spawn workers
                for i in range(self.args.max_threads):
                    tup = (work_queue, done_queue, bar, eps_time, lock, i, self.args.numEps)
                    proc = mp.Process(target=self.mcts_worker, args=tup)
                    proc.start()

                    proccesses.append(proc)

                # Add work to queue
                for eps in range(self.args.numEps):
                    # print("[Master] Adding work...")
                    data = dict()
                    data["i"] = eps
                    data["game"] = copy.deepcopy(self.game)
                    data["nnet"] = nnq
                    # data["args"] = self.args

                    # Workaround for mp.queue bug (it's actually an issue with pickler which it uses)
                    work_queue.put(data)

                print("[Master] Waiting for results...")

                # Wait for results to come in
                for i in range(self.args.numEps):
                    iterationTrainExamples += done_queue.get()

                print("[Master] Killing workers...")

                # Kill workers
                for p in proccesses:
                    p.terminate()
                    p.join()

                bar.finish()

                # TODO: Parallelize executeEpisode() calls
                # self.mcts = MCTS(copy.deepcopy(self.game), self.nnet, self.args)   # reset search tree
                # iterationTrainExamples += self.executeEpisode()

                # save the iteration examples to the history 
                #self.trainExamplesHistory.append(iterationTrainExamples)
                
            if len(self.trainExamplesHistory) > self.args.numItersForTrainExamplesHistory:
                print("len(trainExamplesHistory) =", len(self.trainExamplesHistory), " => remove the oldest trainExamples")
                self.trainExamplesHistory.pop(0)
            # backup history to a file
            # NB! the examples were collected using the model from the previous iteration, so (i-1)  
            self.saveTrainExamples(i-1)
            
            # shuffle examlpes before training
            trainExamples = []
            for e in self.trainExamplesHistory:
                trainExamples.extend(e)
            shuffle(trainExamples)

            # training new network, keeping a copy of the old one
            self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            self.pnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            pmcts = MCTS(copy.deepcopy(self.game), self.pnet, self.args)
            
            self.nnet.train(trainExamples)
            nmcts = MCTS(copy.deepcopy(self.game), self.nnet, self.args)

            print('PITTING AGAINST PREVIOUS VERSION')
            arena = Arena(lambda x: np.argmax(pmcts.getActionProb(x, temp=0)),
                          lambda x: np.argmax(nmcts.getActionProb(x, temp=0)), self.game)
            pwins, nwins, draws = arena.playGames(self.args.arenaCompare)

            print('NEW/PREV WINS : %d / %d ; DRAWS : %d' % (nwins, pwins, draws))
            if pwins+nwins > 0 and float(nwins)/(pwins+nwins) < self.args.updateThreshold:
                print('REJECTING NEW MODEL')
                self.nnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            else:
                print('ACCEPTING NEW MODEL')
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename=self.getCheckpointFile(i))
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')                

    def getCheckpointFile(self, iteration):
        return 'checkpoint_' + str(iteration) + '.pth.tar'

    def saveTrainExamples(self, iteration):
        folder = self.args.checkpoint
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, self.getCheckpointFile(iteration)+".examples")
        with open(filename, "wb+") as f:
            Pickler(f).dump(self.trainExamplesHistory)
        f.closed

    def loadTrainExamples(self):
        modelFile = os.path.join(self.args.load_folder_file[0], self.args.load_folder_file[1])
        examplesFile = modelFile+".examples"
        if not os.path.isfile(examplesFile):
            print(examplesFile)
            r = input("File with trainExamples not found. Continue? [y|n]")
            if r != "y":
                sys.exit()
        else:
            print("File with trainExamples found. Read it.")
            with open(examplesFile, "rb") as f:
                self.trainExamplesHistory = Unpickler(f).load()
            f.closed
            # examples based on the model were already collected (loaded)
            self.skipFirstSelfPlay = True
