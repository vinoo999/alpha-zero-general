import Arena
from MCTS import MCTS
from chess.ChessGame import ChessGame, display
from chess.ChessPlayers import *
from chess.keras.NNet import NNetWrapper as NNet

import numpy as np
from utils import *

from flask import Flask, request, send_from_directory, send_file
from threading import Thread
import json, random, string

"""
use this script to play any two agents against each other, or play manually with
any agent.
"""

ncp = "saves/save-bc5a3cffa65"                       # Checkpoint path
ncf = "best.pth.tar"                                 # Checkpoint file
nca = { 'numMCTSSims': 50, 'cpuct': 1.0, 'temp': 0 } # NNet args

class GameWrapper():
    def __init__(self, sess_id):
        self.g  = ChessGame()                              # Initialize chess game
        self.r  = NNetNetworkPlayer(self.g, ncp, ncf, nca) # Initialize computer player
        self.rp = self.r.play
        self.h  = HumanNetworkChessPlayer(self.g)          # Initialize human player
        self.hp = self.h.play

        self.sess_id = sess_id

    def arena_hook(self):
        arena = Arena.Arena(self.hp, self.rp, self.g, display=display)
        arena.playGames(2, verbose=True)


# Dictionary of all the games, key is sess_id, value is GameWrapper class
games = dict()

# Web server code for GUI
app = Flask(__name__, static_url_path='/chess')

@app.route("/new_game", methods=["GET"])
def new_game():
    """
    Client is requesting new game, send them their session id and create 
    new game instance
    """

    # Generate a random session id
    sess_id = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))

    # Initialize a new game
    new_game = GameWrapper(sess_id)
    arena = Thread(target=new_game.arena_hook)
    arena.daemon = True
    arena.start()

    # Add game to dictionary
    games[sess_id] = new_game

    return sess_id

@app.route("/get_move", methods=["GET"])
def get_move():
    sess_id = request.args.get("sess_id")
    move = json.dumps(games[sess_id].r.queue.get())
    return move

@app.route("/make_move", methods=["POST"])
def make_move():
    sess_id = request.form.get("sess_id")
    games[sess_id].h.queue.put(request.form.get("move"))
    return "OK"

@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    return send_from_directory('chess', path)

def web_server_hook():
    app.run(host='0.0.0.0')


def main():
    web_server = Thread(target=web_server_hook)
    web_server.daemon = True
    web_server.start()


    # nnet players
    # n1 = NNet(g)
    # n1.load_checkpoint('./pretrained_models/chess/keras/','6x6 checkpoint_145.pth.tar')
    # args1 = dotdict({'numMCTSSims': 50, 'cpuct':1.0})
    # mcts1 = MCTS(g, n1, args1)
    # n1p = lambda x: np.argmax(mcts1.getActionProb(x, temp=0))


    #n2 = NNet(g)
    #n2.load_checkpoint('/dev/8x50x25/','best.pth.tar')
    #args2 = dotdict({'numMCTSSims': 25, 'cpuct':1.0})
    #mcts2 = MCTS(g, n2, args2)
    #n2p = lambda x: np.argmax(mcts2.getActionProb(x, temp=0))

    web_server.join()


if __name__ == "__main__":
    main()

