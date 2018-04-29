from pytorch_classification.utils import Bar, AverageMeter
from chess.keras.NNet import NNetWrapper as nn
from chess.ChessUtil import decode_move
from chess.ChessGame import display
from collections import deque
from _pickle import Pickler, Unpickler
from Arena import Arena
from MCTS import MCTS
from utils import *

import time, os, sys, copy, random
import multiprocessing as mp
import numpy as np


class Coach():
    """
    This class executes the self-play + learning. It uses the functions defined
    in Game and NeuralNet. args are specified in main.py.
    """
    def __init__(self, game, nnet, args):
        self.game = game
        self.nnet = nnet
        self.pnet = nn(self.game)  # the competitor network
        self.args = args
        #self.mcts = MCTS(self.game, self.nnet, self.args)
        self.trainExamplesHistory = []    # history of examples from args.numItersForTrainExamplesHistory latest iterations
        self.skipFirstSelfPlay = False # can be overriden in loadTrainExamples()


    # DEPRICATED -- use coach_worker instead
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


    def coach_worker(self, work_queue, done_queue, i):
        """
        Localized version of learn() and executeEpisode() that is thread-safe. Args
        game, nnet, and args should be their own localized copies. This function may
        mutate these objects.
        """

        print("[Coach Worker " + str(i) + "] Started!")

        # Grab work from queue and decode the work data
        while True:
            data = work_queue.get()
            game = data["game"]

            start = time.time()

            # Create our MCTS instance
            mcts = MCTS(game, self.nnet, self.args, is_training=True)

            # Start "executeEpisode()"
            trainExamples = []
            board = game.getInitBoard()
            curPlayer = 1
            episodeStep = 0

            while True:
                episodeStep += 1
                canonicalBoard = game.getCanonicalForm(board, curPlayer)

                temp = int(episodeStep < self.args.tempThreshold)
                pi = mcts.getActionProb(canonicalBoard, temp=temp)

                sym = game.getSymmetries(canonicalBoard, pi)
                for b, p in sym:
                    trainExamples.append([b, curPlayer, p, None])

                action = np.random.choice(len(pi), p=pi)
                board, curPlayer = game.getNextState(board, curPlayer, action)
                res = game.getGameEnded(board, curPlayer)

                if res != 0:
                    examples = [(x[0], x[2], res * ((-1) ** (x[1] != curPlayer))) for x in trainExamples]
                    done_queue.put((time.time() - start, examples))
                    break


    def learn(self):
        """
        Performs numIters iterations with numEps episodes of self-play in each
        iteration. After every iteration, it retrains neural network with
        examples in trainExamples (which has a maximium length of maxlenofQueue).
        It then pits the new neural network against the old one and accepts it
        only if it wins >= updateThreshold fraction of games.
        """

        for i in range(1, self.args.numIters + 1):
            # bookkeeping
            print('------ITER ' + str(i) + '------')
            # examples of the iteration
            if not self.skipFirstSelfPlay or i > 1:
                iterationTrainExamples = deque([], maxlen=self.args.maxlenOfQueue)
    
                tracker = ParallelRuntimes(self.args.mcts_workers)
                bar = Bar('Self Play', max=self.args.numEps)
    
                # Multiprocess self-play
                proccesses = []
                work_queue = mp.Queue()
                done_queue = mp.Queue()

                print("[Master] Spawning Workers...")

                # Spawn workers
                for ep in range(self.args.mcts_workers):
                    tup = (work_queue, done_queue, ep)
                    proc = mp.Process(target=self.coach_worker, args=tup)
                    proc.start()

                    proccesses.append(proc)

                print("[Master] Adding work...")

                # Add work to queue
                for eps in range(self.args.numEps):
                    data = dict()
                    data["i"] = eps
                    data["game"] = copy.deepcopy(self.game)

                    work_queue.put(data)

                print("[Master] Waiting for results...")

                # Wait for results to come in
                for ep in range(self.args.numEps):
                    runtime, examples = done_queue.get()
                    
                    # Drop 80% of draws
                    to_add = False
                    loss_rate = self.args.filter_draw_rate
                    if abs(examples[0][2]) != 1:
                        if random.random() >= loss_rate:
                            to_add = True
                    else:
                        to_add = True

                    if to_add:
                        iterationTrainExamples += examples

                    tracker.update(runtime)
                    bar.suffix = '({eps}/{maxeps}) Eps Time: {et:.3f}s | Total: {total:} | ETA: {eta:}'.format(
                                  eps=ep + 1, maxeps=self.args.numEps, et=tracker.avg(), total=bar.elapsed_td, 
                                  eta=tracker.eta(ep + 1, self.args.numEps))
                    bar.next()

                print("[Master] Killing workers...")

                # Kill workers
                for p in proccesses:
                    p.terminate()
                    p.join()

                print("[Master] iter={} adding {} examples".format(i, len(iterationTrainExamples)))
                self.trainExamplesHistory.append(iterationTrainExamples)

                bar.finish()

                
            if len(self.trainExamplesHistory) > self.args.numItersForTrainExamplesHistory:
                print("len(trainExamplesHistory) =", len(self.trainExamplesHistory), " => remove the oldest trainExamples")
                self.trainExamplesHistory.pop(0)
            # backup history to a file
            # NB! the examples were collected using the model from the previous iteration, so (i-1)  
            self.saveTrainExamples(i)
            
            # shuffle examlpes before training
            trainExamples = []
            for e in self.trainExamplesHistory:
                trainExamples.extend(e)
            random.shuffle(trainExamples)

            # training new network, keeping a copy of the old one
            self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')

            # normal network, don't use parallel code
            self.pnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            pmcts = MCTS(copy.deepcopy(self.game), self.pnet, self.args)
            
            self.nnet.train(trainExamples)

            nmcts = MCTS(copy.deepcopy(self.game), self.nnet, self.args)

            print('PITTING AGAINST PREVIOUS VERSION (player1 = previous, player2 = new)')
            arena = Arena(lambda x: np.argmax(pmcts.getActionProb(x, temp=0)),
                          lambda x: np.argmax(nmcts.getActionProb(x, temp=0)), 
                          self.game, num_workers=self.args.mcts_workers)
            pwins, nwins, draws = arena.playGames(self.args.arenaCompare)

            print('NEW/PREV WINS : %d / %d ; DRAWS : %d' % (nwins, pwins, draws))
            if pwins+nwins > 0 and float(nwins)/(pwins+nwins) < self.args.updateThreshold:
                print('REJECTING NEW MODEL')
                self.nnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            else:
                print('ACCEPTING NEW MODEL')
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename=self.getCheckpointFile(i))
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')

                # Load so all nnets are updated accordingly
                self.nnet.load_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')


    def getCheckpointFile(self, iteration):
        return 'checkpoint_' + str(iteration) + '.pth.tar'

    def saveTrainExamples(self, iteration):
        folder = self.args.checkpoint
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.join(folder, self.getCheckpointFile(iteration)+".examples")
        print("Saving examples: " + filename)
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
