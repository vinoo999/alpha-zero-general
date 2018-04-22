import numpy as np
import os
from scipy import stats
from pickle import Unpickler
import sys
def loadTrainExamples(examples_file):
    if not os.path.isfile(examples_file):
        print(examples_file)
        print("File not found")
    else:
        print("File Found")
        with open(examples_file, "rb") as f:
            return Unpickler(f).load()


if __name__=="__main__":
    examples_file = sys.argv[1]
    examples = loadTrainExamples(examples_file)

    final_examples = []
    for e in examples:
        final_examples.extend(e)
        print("Example length: {}".format(len(e)))
    input_boards, target_pis, target_vs = list(zip(*final_examples))

    input_boards = np.asarray(input_boards)
    target_pis = np.asarray(target_pis)
    target_vs = np.asarray(target_vs)

    wins = np.where(target_vs ==1 )[0]
    draws = np.where(target_vs == 1e-8)[0]
    draws2 = np.where(target_vs == -1e-8)[0]
    losses = np.where(target_vs == -1)[0]
    print("Total games: {}".format(len(target_vs)))
    print(len(examples))
    print("Wins: {}\n{}".format(len(wins),wins))
    print("Draws: {}\n{}".format(len(draws), draws))
    print("Draws2: {}\n{}".format(len(draws2), draws2))
    print("Losses: {}\n{}".format(len(losses), losses))



