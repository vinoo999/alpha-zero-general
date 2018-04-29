import sys
sys.path.append('..')
from utils import *
from keras.models import *
from keras.layers import *
from keras.optimizers import *

import tensorflow as tf
from keras.backend.tensorflow_backend import set_session

import argparse

class ChessNNet():
    def __init__(self, game, args):
        # GPU Configuration
        config = tf.ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = 0.3
        set_session(tf.Session(config=config))

        # game params
        self.board_x, self.board_y = game.getBoardSize()
        self.action_size = game.getActionSize()
        self.args = args

        # Neural Net
        self.input_boards = Input(shape=(self.board_x, self.board_y))    # s: batch_size x board_x x board_y

        x_image = Reshape((self.board_x, self.board_y, 1))(self.input_boards)                # batch_size  x board_x x board_y x 1
        h_conv1 = Activation('relu')(BatchNormalization(axis=3)(Conv2D(args.num_channels, 5, padding='same')(x_image)))         # batch_size  x board_x x board_y x num_channels

        h_conv2 = Activation('relu')(BatchNormalization(axis=3)(Conv2D(args.num_channels, 3, padding='same')(h_conv1)))         # batch_size  x board_x x board_y x num_channels
        h_conv3 = BatchNormalization(axis=3)(Conv2D(args.num_channels, 3, padding='same')(h_conv2))        # batch_size  x (board_x-2) x (board_y-2) x num_channels
        h_res1 = Activation('relu')(Add()([h_conv1, h_conv3]))

        h_conv4 = Activation('relu')(BatchNormalization(axis=3)(Conv2D(args.num_channels, 3, padding='same')(h_res1)))        # batch_size  x (board_x-4) x (board_y-4) x num_channels
        h_conv5 = BatchNormalization(axis=3)(Conv2D(args.num_channels, 3, padding='same')(h_conv4))        # batch_size  x (board_x-4) x (board_y-4) x num_channels
        h_res2 = Activation('relu')(Add()([h_res1, h_conv5]))

        h_conv6 = Activation('relu')(BatchNormalization(axis=3)(Conv2D(args.num_channels, 3, padding='same')(h_res2)))        # batch_size  x (board_x-4) x (board_y-4) x num_channels
        h_conv7 = BatchNormalization(axis=3)(Conv2D(args.num_channels, 3, padding='same')(h_conv6))        # batch_size  x (board_x-4) x (board_y-4) x num_channels
        h_res3 = Activation('relu')(Add()([h_res2, h_conv7]))

        h_conv8 = Activation('relu')(BatchNormalization(axis=3)(Conv2D(args.num_channels, 3, padding='same')(h_res3)))        # batch_size  x (board_x-4) x (board_y-4) x num_channels
        h_conv9 = BatchNormalization(axis=3)(Conv2D(args.num_channels, 3, padding='same')(h_conv8))        # batch_size  x (board_x-4) x (board_y-4) x num_channels
        h_res4 = Activation('relu')(Add()([h_res3, h_conv9]))

        h_conv5_flat = Flatten()(h_res4)       
        s_fc1 = Dropout(args.dropout)(Activation('relu')(BatchNormalization(axis=1)(Dense(1024)(h_conv5_flat))))  # batch_size x 1024
        s_fc2 = Dropout(args.dropout)(Activation('relu')(BatchNormalization(axis=1)(Dense(512)(s_fc1))))          # batch_size x 1024
        self.pi = Dense(self.action_size, activation='softmax', name='pi')(s_fc2)   # batch_size x self.action_size
        self.v = Dense(1, activation='tanh', name='v')(s_fc2)                    # batch_size x 1

        self.model = Model(inputs=self.input_boards, outputs=[self.pi, self.v])

        # Fix for async flask bug; see https://github.com/keras-team/keras/issues/2397
        self.model._make_predict_function()
        self.graph = tf.get_default_graph()

        self.model.compile(loss=['categorical_crossentropy','mean_squared_error'], optimizer=Adam(args.lr))
