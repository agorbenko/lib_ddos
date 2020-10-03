#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file runs the simulations with cmd line arguments"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from argparse import ArgumentParser
from logging import DEBUG
import os
from sys import argv

from .ddos_simulator import DDOS_Simulator
from .managers import Sieve_Manager_Base, Protag_Manager, Bounded_Manager
from .utils import config_logging
from .graphers import Combination_Grapher

def main():
    """Runs simulations with command line arguments"""

    parser = ArgumentParser(description="Runs a DDOS simulation")
    # NOTE: these defaults are chosen that way because they work for the animator
    # Changing these defaults will result in worse animations
    parser.add_argument("--num_users", type=int, dest="num_users", default=48)
    parser.add_argument("--num_attackers", type=int, dest="num_attackers", default=12)
    parser.add_argument("--num_buckets", type=int, dest="num_buckets", default=8)
    parser.add_argument("--threshold", type=int, dest="threshold", default=10)
    parser.add_argument("--rounds", type=int, dest="rounds", default=20)
    parser.add_argument("--debug", dest="debug", default=False, action='store_true')
    parser.add_argument("--animate", dest="animate", default=False, action='store_true')
    parser.add_argument("--graph_combos", dest="graph_combos", default=False, action='store_true')
    parser.add_argument("--combination_grapher", dest="graph_combos", default=False, action='store_true')
    parser.add_argument("--tikz", dest="tikz", default=False, action="store_true")

    parser.add_argument("--save", dest="save", default=False, action="store_true")
    parser.add_argument("--high_res", dest="high_res", default=False, action="store_true")
    parser.add_argument("--trials", type=int, dest="trials", default=100)
    parser.add_argument("--graph_dir", type=str, dest="graph_dir", default=os.path.join("/tmp", "lib_ddos_simulator"))


    args = parser.parse_args()
    if args.debug:
        config_logging(DEBUG)

    if args.animate:
        # NOTE: for optimal animations,
        # use 24, 4, 8, 10 for users, attackers, buckets, threshold
        DDOS_Simulator(args.num_users,  # number of users
                       args.num_attackers,  # number of attackers
                       args.num_buckets,  # number of buckets
                       args.threshold,  # Threshold
                       [Protag_Manager,
                        Bounded_Manager] + Sieve_Manager_Base.runnable_managers,
                       graph_dir=args.graph_dir,
                       save=args.save,
                       high_res=args.high_res).run(args.rounds, animate=True)
    elif args.graph_combos:
        Combination_Grapher(graph_dir=args.graph_dir,
                            tikz=args.tikz,
                            save=args.save,
                            high_res=args.high_res).run(trials=args.trials)
    else:
        all_managers = (Sieve_Manager.runnable_managers +
                        Miad_Manager.runnable_managers +
                        [Protag_Manager, KPO_Manager, Bounded_Manager])
        DDOS_Simulator(args.num_users,
                       args.num_attackers,
                       args.num_buckets,
                       args.threshold,
                       all_managers,
                       graph_dir=args.graph_dir,
                       save=args.save,
                       tikz=args.tikz,
                       high_res=args.high_res).run(args.rounds)
