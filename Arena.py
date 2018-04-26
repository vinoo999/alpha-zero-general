from pytorch_classification.utils import Bar, AverageMeter
import multiprocessing as mp
import numpy as np
import time, copy
from utils import *

class Arena():
    """
    An Arena class where any 2 agents can be pit against each other.
    """
    def __init__(self, player1, player2, game, display=None, num_workers=1):
        """
        Input:
            player 1,2: two functions that takes board as input, return action
            game: Game object
            display: a function that takes board as input and prints it (e.g.
                     display in othello/OthelloGame). Is necessary for verbose
                     mode.

        see othello/OthelloPlayers.py for an example. See pit.py for pitting
        human players/other baselines with each other.
        """
        self.player1 = player1
        self.player2 = player2
        self.game = game
        self.display = display
        self.num_workers = num_workers

    # DEPRICATED -- use arena_worker instead
    def playGame(self, verbose=False):
        """
        Executes one episode of a game.

        Returns:
            either
                winner: player who won the game (1 if player1, -1 if player2)
            or
                draw result returned from the game that is neither 1, -1, nor 0.
        """
        players = [self.player2, None, self.player1]
        curPlayer = 1
        board = self.game.getInitBoard()
        it = 0
        while self.game.getGameEnded(board, curPlayer)==0:
            it+=1
            if verbose:
                assert(self.display)
                print("Turn ", str(it), "Player ", str(curPlayer))
                self.display(board)
            action = players[curPlayer+1](self.game.getCanonicalForm(board, curPlayer))

            valids = self.game.getValidMoves(self.game.getCanonicalForm(board, curPlayer),1)

            if valids[action]==0:
                print("**********************")
                print(action)
                print(np.where(valids>0))
                assert valids[action] >0
            board, curPlayer = self.game.getNextState(board, curPlayer, action)
        if verbose:
            assert(self.display)
            print("Game over: Turn ", str(it), "Result ", str(self.game.getGameEnded(board, 1)))
            self.display(board)
        return self.game.getGameEnded(board, 1)


    def arena_worker(self, work_queue, done_queue, i, player1, player2):
        print("[Worker " + str(i) + "] Started!")

        while True:
            data = work_queue.get()
            player = data["player"]
            game = data["game"]
            verbose = data["verbose"]
            eps = data["i"]

            start = time.time()

            players = [player2, None, player1] if player == 1 else [player1, None, player2]
            board = game.getInitBoard()
            curPlayer = 1
            it = 0

            while game.getGameEnded(board, curPlayer) == 0:
                it += 1
                if verbose:
                    print("Turn ", str(it), "Player ", str(curPlayer))
                    self.display(board)

                action = players[curPlayer + 1](game.getCanonicalForm(board, curPlayer))
                valids = game.getValidMoves(game.getCanonicalForm(board, curPlayer), 1)  # TODO: Is this check necessary?

                if valids[action] == 0:
                    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<< ERROR >>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print(action)
                    print(np.where(valids > 0))
                    assert valids[action] > 0

                # The action is valid
                board, curPlayer = game.getNextState(board, curPlayer, action)
                if self.game.webserver: self.game.result.put(None)

            res = game.getGameEnded(board, 1)

            if verbose:
                print("Game over: Turn ", str(it), "Result ", str(res))
                if self.game.webserver: self.game.result.put(res * curPlayer)
                self.display(board)

            # Return the result of the game from the HUMAN (player 1) perspective
            # NOTE: This is not the same thing as game.getGameEnded(board, curPlayer)
            done_queue.put((time.time() - start, res * curPlayer))


    def playGames(self, num, verbose=False):
        """
        Plays num games in which player1 starts num/2 games and player2 starts
        num/2 games.

        Returns:
            oneWon: games won by player1
            twoWon: games won by player2
            draws:  games won by nobody
        """
        tracker = ParallelRuntimes(self.num_workers)
        bar = Bar('Arena.playGames', max=num)

        oneWon = 0
        twoWon = 0
        draws = 0

        # # Multiprocess pitting
        # proccesses = []
        # work_queue = mp.Queue()
        # done_queue = mp.Queue()

        # print("[Master] Spawning Workers...")

        # # Spawn workers
        # for i in range(self.num_workers):
        #     tup = (work_queue, done_queue, i, self.player1, self.player2)
        #     proc = mp.Process(target=self.arena_worker, args=tup)
        #     proc.start()

        #     proccesses.append(proc)

        # print("[Master] Adding work...")

        # # Add work to queue
        # first_half = int(num / 2)
        # for i in range(first_half):
        #     data = dict()
        #     data["i"] = i
        #     data["player"] = 1
        #     data["game"] = copy.deepcopy(self.game)
        #     data["verbose"] = verbose

        #     work_queue.put(data)

        # second_half = num - first_half
        # for i in range(second_half):
        #     data = dict()
        #     data["i"] = i
        #     data["player"] = -1            # Switch players
        #     data["game"] = copy.deepcopy(self.game)
        #     data["verbose"] = verbose

        #     work_queue.put(data)

        # print("[Master] Waiting for results...")

        # Wait for results to come in
        first_half = int(num / 2)
        for i in range(first_half):
            start = time.time()
            
            gameResult = self.playGame()

            if gameResult == 1:
                oneWon += 1
            elif gameResult == -1:
                twoWon += 1
            else:
                draws += 1

            # bookkeeping + plot progress
            tracker.update(time.time() - start)
            bar.suffix = '({eps}/{maxeps}) Eps Time: {et:.3f}s | Total: {total:} | ETA: {eta:}'.format(
                           eps=i + 1, maxeps=num, et=tracker.avg(), total=bar.elapsed_td, 
                           eta=tracker.eta(i + 1, num))
            bar.next()

        self.player1, self.player2 = self.player2, self.player1

        second_half = num - first_half
        for i in range(second_half):
            start = time.time()
            
            gameResult = self.playGame()

            if gameResult == -1:
                oneWon += 1
            elif gameResult == 1:
                twoWon += 1
            else:
                draws += 1

            # bookkeeping + plot progress
            tracker.update(time.time() - start)
            bar.suffix = '({eps}/{maxeps}) Eps Time: {et:.3f}s | Total: {total:} | ETA: {eta:}'.format(
                           eps=i + first_half + 1, maxeps=num, et=tracker.avg(), total=bar.elapsed_td, 
                           eta=tracker.eta(i + 1, num))
            bar.next()

        # print("[Master] Killing workers...")

        # # Kill workers
        # for p in proccesses:
        #     p.terminate()
        #     p.join()

        bar.finish()

        print("Wins: " + str(oneWon) + ", Loses: "+str(twoWon)+", Draws: "+str(draws))
        return oneWon, twoWon, draws
