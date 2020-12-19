#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file runs the simulations with cmd line arguments"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from argparse import ArgumentParser
import os
from sys import argv

from .api import create_app
from .attackers import Basic_Attacker
from .ddos_simulators import DDOS_Simulator, Fluid_DDOS_Simulator
from .managers import Manager
from .utils import Log_Levels
from .graphers import Combination_Grapher


def main():
    """Runs simulations with command line arguments"""


    model_folder = os.path.join(os.getcwd(), "model")
    import tensorflow as tf
    if not os.path.exists(model_folder):
        #model = tf.keras.models.load_model(model_folder + "/tf_model")
        os.makedirs(model_folder)

    import tensorflow as tf
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from sklearn import preprocessing
    
    from subprocess import check_call
    check_call("wget https://raw.githubusercontent.com/jfuruness/ddos_fvecs/main/ddos_fvecs.csv", shell=True)
    
    # There are only two columns in this data
    data = pd.read_csv('ddos_fvecs.csv')
    check_call("rm ddos_fvecs.csv", shell=True)
    print(data.shape)
    # Make this a 2d array of size NXD where D=1 rather than a 1D array of length N
    X = data.iloc[:, :-1]#preprocessing.MinMaxScaler().fit_transform(data.iloc[:, :-1])
    Y = data.iloc[:, -1]

    if not os.path.exists(model_folder + "/tf_model"):
        model = tf.keras.models.Sequential([
          tf.keras.layers.Flatten(input_shape=[9]),
          tf.keras.layers.Dense(32, activation="relu"),
          tf.keras.layers.Dropout(.2),
          tf.keras.layers.Dense(16, activation="relu"),
          tf.keras.layers.Dropout(.1),
          tf.keras.layers.Dense(8, activation="relu"),
          tf.keras.layers.Dropout(.05),
          tf.keras.layers.Dense(2, activation="sigmoid")
        ])
    
        # Learning rate scheduler
        def schedule(epoch, lr):
          if epoch >= 50:
            return 0.0001
          else:
            return 0.001
    
        scheduler = tf.keras.callbacks.LearningRateScheduler(schedule)
        model.compile(optimizer="adam",
                      loss="sparse_categorical_crossentropy",
                      metrics=["accuracy"])
        r = model.fit(X, Y, epochs=1, callbacks=[scheduler])
    
    
        plt.plot(r.history['loss'], label='loss')
        model.save(os.path.join(model_folder, "tf_model1"))

    if not os.path.exists(model_folder + "/tf_model2"):
        model = tf.keras.models.Sequential([
          tf.keras.layers.Flatten(input_shape=[9]),
          tf.keras.layers.Dense(16, activation="relu"),
          tf.keras.layers.Dropout(.1),
          tf.keras.layers.Dense(8, activation="relu"),
          tf.keras.layers.Dropout(.05),
          tf.keras.layers.Dense(2, activation="sigmoid")
        ])

        # Learning rate scheduler
        def schedule(epoch, lr):
          if epoch >= 50:
            return 0.0001
          else:
            return 0.001

        scheduler = tf.keras.callbacks.LearningRateScheduler(schedule)
        model.compile(optimizer="adam",
                      loss="sparse_categorical_crossentropy",
                      metrics=["accuracy"])
        r = model.fit(X, Y, epochs=1, callbacks=[scheduler])


        plt.plot(r.history['loss'], label='loss')
        model.save(os.path.join(model_folder, "tf_model2"))
    if not os.path.exists(model_folder + "/tf_model3"):
        model = tf.keras.models.Sequential([
          tf.keras.layers.Flatten(input_shape=[9]),
          tf.keras.layers.Dense(32, activation="relu"),
          tf.keras.layers.Dense(16, activation="relu"),
          tf.keras.layers.Dense(8, activation="relu"),
          tf.keras.layers.Dense(2, activation="sigmoid")
        ])

        # Learning rate scheduler
        def schedule(epoch, lr):
          if epoch >= 50:
            return 0.0001
          else:
            return 0.001

        scheduler = tf.keras.callbacks.LearningRateScheduler(schedule)
        model.compile(optimizer="adam",
                      loss="sparse_categorical_crossentropy",
                      metrics=["accuracy"])
        r = model.fit(X, Y, epochs=1, callbacks=[scheduler])


        plt.plot(r.history['loss'], label='loss')
        model.save(os.path.join(model_folder, "tf_model3"))



    
    parser = ArgumentParser(description="Runs a DDOS simulation")
    parser.add_argument("--num_users", type=int, dest="num_users", default=21)
    parser.add_argument("--num_attackers", type=int, dest="num_attackers", default=9)
    parser.add_argument("--num_buckets", type=int, dest="num_buckets", default=3)
    parser.add_argument("--threshold", type=int, dest="threshold", default=10)
    parser.add_argument("--rounds", type=int, dest="rounds", default=7)
    parser.add_argument("--debug", dest="debug", default=False, action='store_true')
    parser.add_argument("--animate", dest="animate", default=False, action='store_true')
    parser.add_argument("--graph_combos", dest="graph_combos", default=False, action='store_true')
    parser.add_argument("--combination_grapher", dest="graph_combos", default=False, action='store_true')
    parser.add_argument("--tikz", dest="tikz", default=False, action="store_true")
    parser.add_argument("--save", dest="save", default=False, action="store_true")
    parser.add_argument("--high_res", dest="high_res", default=False, action="store_true")
    parser.add_argument("--trials", type=int, dest="trials", default=2)
    parser.add_argument("--graph_dir", type=str, dest="graph_dir", default=os.path.join("/tmp", "lib_ddos_simulator"))
    parser.add_argument("--api", dest="api", default=False, action="store_true")


    args = parser.parse_args()

    if args.api:
        create_app().run(debug=True)
    elif args.animate:
        for sim_cls in [DDOS_Simulator.runnable_simulators[1]]:
            for atk_cls in [Basic_Attacker]:
                # NOTE: for optimal animations,
                # use 24, 4, 8, 10 for users, attackers, buckets, threshold
                sim_cls(args.num_users,  # number of users
                        args.num_attackers,  # number of attackers
                        args.num_buckets,  # number of buckets
                        args.threshold,  # Threshold
                        Manager.runnable_managers,
                        graph_dir=args.graph_dir,
                        save=args.save,
                        stream_level=Log_Levels.DEBUG if args.debug else Log_Levels.INFO,
                        high_res=args.high_res,
                        attacker_cls=atk_cls).run(args.rounds,
                                                  animate=True,
                                                  graph_trials=False)
    elif args.graph_combos:
        Combination_Grapher(stream_level=Log_Levels.DEBUG if args.debug else Log_Levels.INFO,
                            graph_dir=args.graph_dir,
                            tikz=args.tikz,
                            save=args.save,
                            high_res=args.high_res).run(trials=args.trials)
    else:
        for sim_cls in DDOS_Simulator.runnable_simulators:
            sim_cls(args.num_users,
                    args.num_attackers,
                    args.num_buckets,
                    args.threshold,
                    Manager.runnable_managers,
                    stream_level=Log_Levels.DEBUG if args.debug else Log_Levels.INFO,
                    graph_dir=args.graph_dir,
                    save=args.save,
                    tikz=args.tikz,
                    high_res=args.high_res).run(args.rounds)
