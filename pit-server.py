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

ncp_new = "saves/save-bc5a3cffa65"                        # Checkpoint path
ncf_new = "best.pth.tar"                                  # Checkpoint file
nca_new = { 'numMCTSSims': 100, 'cpuct': 1.0, 'temp': 0 } # NNet args

ncp_old = "saves/save-bc5a3cffa65"                        # Checkpoint path
ncf_old = "best.pth.tar"                                  # Checkpoint file
nca_old = { 'numMCTSSims': 25, 'cpuct': 1.0, 'temp': 0 }  # NNet args

class GameWrapper():
    def __init__(self, sess_id, p1, p2, gm):
        self.g = ChessGame()
        self.result_queue = Queue()

        self.sess_id = sess_id
        self.gm = gm

        if p1 == "human":
            print("Initializing human...")
            self.player1 = HumanNetworkChessPlayer(self.g, self.result_queue)
        elif p1 == "nnet-new":
            self.player1 = NNetNetworkPlayer(self.g, ncp_new, ncf_new, nca_new)
        elif p1 == "nnet-old":
            self.player1 = NNetNetworkPlayer(self.g, ncp_old, ncf_old, nca_old)
        elif p1 == "alpha-beta":
            self.player1 = AlphaBetaNetworkPlayer(self.g)
        else:
            self.player1 = RandomNetworkPlayer(self.g)

        if p2 == "human":
            self.player2 = HumanNetworkChessPlayer(self.g, self.result_queue)
        elif p2 == "nnet-new":
            self.player2 = NNetNetworkPlayer(self.g, ncp_new, ncf_new, nca_new)
        elif p2 == "nnet-old":
            self.player2 = NNetNetworkPlayer(self.g, ncp_old, ncf_old, nca_old)
        elif p2 == "alpha-beta":
            self.player2 = AlphaBetaNetworkPlayer(self.g)
        else:
            print("Initializing random...")
            self.player2 = RandomNetworkPlayer(self.g)

        self.p1p = self.player1.play
        self.p2p = self.player2.play

    def arena_hook(self, result_queue):
        arena = Arena.Arena(self.p1p, self.p2p, self.g, display=display, result_queue=result_queue)
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

    player1 = request.args.get("player1")
    player2 = request.args.get("player2")
    game_mode = request.args.get("game_mode")

    # Initialize a new game
    new_game = GameWrapper(sess_id, player1, player2, game_mode)
    arena = Thread(target=new_game.arena_hook, args=(new_game.result_queue,))
    arena.daemon = True
    arena.start()

    # Add game to dictionary
    games[sess_id] = new_game

    return sess_id

@app.route("/get_move", methods=["GET"])
def get_move():
    sess_id = request.args.get("sess_id")
    turn_color = request.args.get("turn")

    if turn_color == "w":
        move = games[sess_id].player1.queue.get()
    else:
        move = games[sess_id].player2.queue.get()

    move["result"] = games[sess_id].result_queue.get()

    return json.dumps(move)

@app.route("/make_move", methods=["POST"])
def make_move():
    sess_id = request.form.get("sess_id")
    turn_color = request.form.get("turn")
    move = request.form.get("move")

    if turn_color == "w":
        games[sess_id].player1.queue.put(move)
    else:
        games[sess_id].player2.queue.put(move)

    res = games[sess_id].result_queue.get()
    return json.dumps({ "result": res })

@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    return send_from_directory('chess', path)

def web_server_hook():
    app.run(host='0.0.0.0')


args = dotdict({
    'nnet_workers': 2
})

def main():
    # Start webserver
    web_server = Thread(target=web_server_hook)
    web_server.daemon = True
    web_server.start()

    web_server.join()


if __name__ == "__main__":
    main()

