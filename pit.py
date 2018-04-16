import Arena
from MCTS import MCTS
from chess.ChessGame import ChessGame, display
from chess.ChessPlayers import *
from chess.keras.NNet import NNetWrapper as NNet

import numpy as np
from utils import *

from flask import Flask, request, send_from_directory
from threading import Thread
import json

"""
use this script to play any two agents against each other, or play manually with
any agent.
"""

# Initialize Chess game
g = ChessGame()

# Initialize players
r = RandomPlayer(g)
rp = r.play

h = HumanChessPlayer(g)
hp = h.play


# Web server code for GUI
app = Flask(__name__, static_url_path='/chess')

@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
	return send_from_directory('chess', path)

@app.route("/make_move", methods=["POST"])
def make_move():
	h.queue.put(request.form.get("move"))
	return "OK"

@app.route("/get_move", methods=["GET"])
def get_move():
	return json.dumps(r.queue.get())

def web_server_hook():
	app.run()
	print("Web Server Initialized!")


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


	arena = Arena.Arena(hp, rp, g, display=display)
	print(arena.playGames(2, verbose=True))

	web_server.join()


if __name__ == "__main__":
	main()

