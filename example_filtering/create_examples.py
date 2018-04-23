import numpy as np
import os
from scipy import stats
from pickle import Unpickler, Pickler
import sys
def loadTrainExamples(examples_file):
    if not os.path.isfile(examples_file):
        print(examples_file)
        print("File not found")
    else:
        print("File Found")
        with open(examples_file, "rb") as f:
            return Unpickler(f).load()


def saveTrainExamples(fname, examples):
    with open(fname, "wb+") as f:
        Pickler(f).dump(examples)
    f.closed

if __name__=="__main__":
    

    
    for i in range(len(sys.argv)):
        if i == 0:
            continue

        examples_file = sys.argv[i]
        examples = loadTrainExamples(examples_file)

        final_examples = []
        for e in examples:
            final_examples.extend(e)
            print("length examples: {}".format(len(e)))
        input_boards, target_pis, target_vs = list(zip(*final_examples))

        input_boards = np.asarray(input_boards)
        target_pis = np.asarray(target_pis)
        target_vs = np.asarray(target_vs)

        wins = np.where(target_vs ==1 )[0]
        draws = np.where(np.abs(target_vs) != 1)[0]
        losses = np.where(target_vs == -1)[0]
        
        filtered_draws = np.random.choice(draws, min(len(wins), len(losses)))
        
        good_games = np.concatenate((wins,losses, filtered_draws))
        if i == 1:
            final_input_boards =  input_boards[good_games]
            final_target_pis = target_pis[good_games]
            final_target_vs = target_vs[good_games]
        else:
            final_input_boards = np.concatenate((final_input_boards, input_boards[good_games]))
            final_target_pis = np.concatenate((final_target_pis, target_pis[good_games]))
            final_target_vs = np.concatenate((final_target_vs, target_vs[good_games]))
        
        print("Total games ({}): {}".format(i, len(target_vs)))
        print("Num exampelse: ", len(examples))
        print("Wins: {}\n{}".format(len(wins),wins))
        print("Draws: {}\n{}".format(len(draws), draws))
        print("Losses: {}\n{}".format(len(losses), losses))

    wins = np.where(final_target_vs ==1 )[0]
    draws = np.where(np.abs(final_target_vs) != 1)[0]
    losses = np.where(final_target_vs == -1)[0]

    final_examples = [ [(final_input_boards[i], final_target_pis[i], final_target_vs[i])] for i in range(len(final_target_vs)) ]

    print("Total games ({}): {}".format(i, len(final_target_vs)))
    print("Wins: {}\n{}".format(len(wins),wins))
    print("Draws: {}\n{}".format(len(draws), draws))
    print("Losses: {}\n{}".format(len(losses), losses))

    saveTrainExamples("filtered_examples.pth.tar.examples", final_examples)
        
 

