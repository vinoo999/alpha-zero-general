import sys
sys.path.append('..')
from utils import *

import argparse
# from keras.models import *
# from keras.layers import *
# from keras.optimizers import *

class ChessNNet():
    def __init__(self, game, args):
        import keras.models as km
        import keras.layers as kl
        import keras.optimizers as ko

        # game params
        self.board_x, self.board_y = game.getBoardSize()
        self.action_size = game.getActionSize()
        self.args = args

        # Neural Net
        self.input_boards = kl.Input(shape=(self.board_x, self.board_y))    # s: batch_size x board_x x board_y

        x_image = kl.Reshape((self.board_x, self.board_y, 1))(self.input_boards)                # batch_size  x board_x x board_y x 1
        h_conv1 = kl.Activation('relu')(kl.BatchNormalization(axis=3)(kl.Conv2D(args.num_channels, 3, padding='same')(x_image)))         # batch_size  x board_x x board_y x num_channels
        h_conv2 = kl.Activation('relu')(kl.BatchNormalization(axis=3)(kl.Conv2D(args.num_channels, 3, padding='same')(h_conv1)))         # batch_size  x board_x x board_y x num_channels
        h_conv3 = kl.Activation('relu')(kl.BatchNormalization(axis=3)(kl.Conv2D(args.num_channels, 3, padding='valid')(h_conv2)))        # batch_size  x (board_x-2) x (board_y-2) x num_channels
        h_conv4 = kl.Activation('relu')(kl.BatchNormalization(axis=3)(kl.Conv2D(args.num_channels, 3, padding='valid')(h_conv3)))        # batch_size  x (board_x-4) x (board_y-4) x num_channels
        h_conv4_flat = kl.Flatten()(h_conv4)       
        s_fc1 = kl.Dropout(args.dropout)(kl.Activation('relu')(kl.BatchNormalization(axis=1)(kl.Dense(1024)(h_conv4_flat))))  # batch_size x 1024
        s_fc2 = kl.Dropout(args.dropout)(kl.Activation('relu')(kl.BatchNormalization(axis=1)(kl.Dense(512)(s_fc1))))          # batch_size x 1024
        self.pi = kl.Dense(self.action_size, activation='softmax', name='pi')(s_fc2)   # batch_size x self.action_size
        self.v = kl.Dense(1, activation='tanh', name='v')(s_fc2)                    # batch_size x 1

        self.model = km.Model(inputs=self.input_boards, outputs=[self.pi, self.v])

        # Fix for async flask bug; see https://github.com/keras-team/keras/issues/2397
        self.model._make_predict_function()
        self.graph = ko.tf.get_default_graph()

        self.model.compile(loss=['categorical_crossentropy','mean_squared_error'], optimizer=ko.Adam(args.lr))
