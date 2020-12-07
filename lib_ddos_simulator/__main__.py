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
