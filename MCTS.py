from chess.ChessUtil import decode_move, algebraic
from chess.ChessGame import display
from random import shuffle
import math, sys, copy
import numpy as np

EPS = 1e-8

class MCTS():
    """
    This class handles the MCTS tree.
    """

    def __init__(self, game, nnet, args, is_training=False):
        self.game = game
        self.nnet = nnet
        self.args = args
        self.Qsa = {}       # stores Q values for s,a (as defined in the paper)
        self.Nsa = {}       # stores #times edge s,a was visited
        self.Ns = {}        # stores #times board s was visited
        self.Ps = {}        # stores initial policy (returned by neural net)

        self.Es = {}        # stores game.getGameEnded ended for board s
        self.Vs = {}        # stores game.getValidMoves for board s

        self.is_training = is_training

    def getActionProb(self, canonicalBoard, temp=1):
        """
        This function performs numMCTSSims simulations of MCTS starting from
        canonicalBoard.

        Returns:
            probs: a policy vector where the probability of the ith action is
                   proportional to Nsa[(s,a)]**(1./temp)
        """
        for i in range(self.args.numMCTSSims):
            # Have to copy game state so we don't wreck state_counts and cause a 
            # three-fold draw from the MCTS search
            tmp_game = copy.deepcopy(self.game)
            self.search(canonicalBoard, is_root_node=True)
            self.game = tmp_game

        s = self.game.stringRepresentation(canonicalBoard)
        counts = [self.Nsa[(s,a)] if (s,a) in self.Nsa else 0 for a in range(self.game.getActionSize())]

        if temp == 0:
            bestA = np.argmax(counts)
            probs = [0] * len(counts)
            probs[bestA] = 1
            return probs

        counts = [x ** (1. / temp) for x in counts]
        probs = [x / float(sum(counts)) for x in counts]
        return probs


    def search(self, canonicalBoard, is_root_node=False):
        """
        This function performs one iteration of MCTS. It is recursively called
        till a leaf node is found. The action chosen at each node is one that
        has the maximum upper confidence bound as in the paper.

        Once a leaf node is found, the neural network is called to return an
        initial policy P and a value v for the state. This value is propogated
        up the search path. In case the leaf node is a terminal state, the
        outcome is propogated up the search path. The values of Ns, Nsa, Qsa are
        updated.

        NOTE: the return values are the negative of the value of the current
        state. This is done since v is in [-1,1] and if v is the value of a
        state for the current player, then its value is -v for the other player.

        Returns:
            v: the negative of the value of the current canonicalBoard
        """

        s = self.game.stringRepresentation(canonicalBoard)

        game_end_score = self.game.getGameEnded(canonicalBoard, 1)
        if game_end_score != 0:
            return -game_end_score

        if s not in self.Ps:
            # leaf node
            self.Ps[s], v = self.nnet.predict(canonicalBoard)
            valids = self.game.getValidMoves(canonicalBoard, 1)
            self.Ps[s] = self.Ps[s]*valids      # masking invalid moves
            sum_Ps_s = np.sum(self.Ps[s])
            if sum_Ps_s > 0:
                self.Ps[s] /= sum_Ps_s    # renormalize
            else:
                # if all valid moves were masked make all valid moves equally probable
                
                # NB! All valid moves may be masked if either your NNet architecture is insufficient or you've get overfitting or something else.
                # If you have got dozens or hundreds of these messages you should pay attention to your NNet and/or training process.   
                print("All valid moves were masked, do workaround.")
                self.Ps[s] = self.Ps[s] + valids
                self.Ps[s] /= np.sum(self.Ps[s])

            self.Vs[s] = valids
            self.Ns[s] = 0
            return -v

        valids = self.Vs[s]
        cur_best = -float('inf')
        best_act = -1

        # pick the action with the highest upper confidence bound
        all_actions = list(range(self.game.getActionSize()))
        shuffle(all_actions)

        if is_root_node and self.is_training:
            d_i = 0
            d_a = self.args.dirichlet_alpha
            dir_noise = np.random.dirichlet([d_a] * np.sum(valids))

        for a in all_actions:
            if valids[a]:
                p = self.Ps[s][a]
                if is_root_node and self.is_training:
                    d_e = self.args.dirichlet_noise
                    p = (1 - d_e) * p + d_e * dir_noise[d_i]
                    d_i += 1

                if (s,a) in self.Qsa:
                    u = self.Qsa[(s,a)] + self.args.cpuct * p * math.sqrt(self.Ns[s]) / (1 + self.Nsa[(s,a)])
                else:
                    u = self.args.cpuct * p * math.sqrt(self.Ns[s] + EPS)     # Q = 0 ?

                if u > cur_best:
                    cur_best = u
                    best_act = a

        a = best_act

        where = np.where(valids==1)
        testing = list(map(decode_move, list(np.where(valids==1))[0]))
        next_s, next_player = self.game.getNextState(canonicalBoard, 1, a)
        next_s = self.game.getCanonicalForm(next_s, next_player)
        v = self.search(next_s)

        if (s,a) in self.Qsa:
            self.Qsa[(s,a)] = (self.Nsa[(s,a)]*self.Qsa[(s,a)] + v)/(self.Nsa[(s,a)]+1)
            self.Nsa[(s,a)] += 1

        else:
            self.Qsa[(s,a)] = v
            self.Nsa[(s,a)] = 1

        self.Ns[s] += 1
        return -v
