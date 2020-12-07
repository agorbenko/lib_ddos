#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the class Simulation, to simulate a DDOS attack"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from copy import deepcopy
import os
import random

from tqdm import trange

from ..graphers import Animater, Grapher
from ..attackers import Attacker, Basic_Attacker
from .. import managers
from ..simulation_objects import User
from .. import utils


class DDOS_Simulator:
    """Simulates a DDOS attack"""

    __slots__ = ["graph_kwargs", "good_users", "attackers", "users",
                 "managers", "grapher", "attacker_cls", "next_unused_user_id",
                 "user_cls", "og_unused_user_id", "og_num_attackers", "og_num_users"]

    runnable_simulators = []

    # https://stackoverflow.com/a/43057166/8903959
    def __init_subclass__(cls, **kwargs):
        """This method essentially creates a list of all subclasses"""

        super().__init_subclass__(**kwargs)

        cls.runnable_simulators.append(cls)

    def __init__(self,
                 num_users: int,
                 num_attackers: int,
                 num_buckets: int,
                 threshold: int,
                 Manager_Child_Classes: list,
                 stream_level=utils.Log_Levels.INFO,
                 # The graph kwargs
                 graph_dir: str = os.path.join("/tmp", "lib_ddos_simulator"),
                 tikz=False,
                 save=False,
                 high_res=False,
                 attacker_cls=Basic_Attacker,
                 user_cls=User):
        """Initializes simulation"""

        self.og_num_attackers = num_attackers
        self.og_num_users = num_users
        self.graph_kwargs = {"stream_level": stream_level,
                             "graph_dir": graph_dir,
                             "tikz": tikz,
                             "save": save,
                             "high_res": high_res}

        self.good_users = [user_cls(x) for x in range(num_users)]

        self.attackers = self.get_attackers(num_attackers, attacker_cls)

        self.users = self.good_users + self.attackers

        self.next_unused_user_id = len(self.users)
        self.og_unused_user_id = self.next_unused_user_id
        # Shuffle so attackers are not at the end
        random.shuffle(self.users)
        # Creates manager and distributes users evenly across buckets
        self.managers = [X(num_buckets, deepcopy(self.users), threshold)
                         for X in Manager_Child_Classes]

        # Creates graphing class to capture data
        self.grapher = Grapher(self.managers,
                               len(self.good_users),
                               len(self.attackers),
                               **self.graph_kwargs)
        self.attacker_cls = attacker_cls
        self.user_cls = user_cls

    def run(self, num_rounds: int, animate=False, graph_trials=True):
        """Runs simulation"""

        for manager in self.managers:
            sim_args = [manager, num_rounds, animate, graph_trials]

            if animate:
                # Animates sim
                animater = self.animate_sim(*sim_args)
            # TYPICAL USE CASE BELOW
            else:
                # Animater is None
                animater = self.init_and_run_sim(*sim_args)

        # Returns latest utility, used for combination graphing
        return self.grapher.graph(graph_trials, self.attacker_cls)

    def animate_sim(self, *sim_args):
        """Animates simulation

        Note that sim is run twice
        The first time it records stats for sim
        Second time it simulates
        Not efficient, but it takes 1 sec to run so whatevs
        """

        [manager, num_rounds, animate, graph_trials] = sim_args
        # Sets up animator and turns
        random_seed = random.random()
        # Animations runs this twice to know how large to make anims
        for i in range(2):
           animater = self.init_and_run_sim(*sim_args, random_seed, i)
        animater.run_animation(num_rounds - 1)
        return animater

    def init_and_run_sim(self,
                         manager,
                         num_rounds,
                         animate,
                         graph_trials,
                         random_seed=None,
                         i=None):
        """Initializes sim for a single manager and runs"""

        # Sets up animator and turns
        animater, turns = self.init_sim(manager,
                                        num_rounds,
                                        animate,
                                        graph_trials,
                                        random_seed,
                                        i)
        self.run_sim(turns, manager, i, animater)
        return animater

    def init_sim(self,
                 manager,
                 num_rounds,
                 animate,
                 graph_trials,
                 seed=None,
                 i=None):
        """Sets up animator and turn list

        Seeds sim if animating so that each
        of the two runs is the same"""

        animater = None

        if seed is not None:
            # Seeded so that exactly the same trial is run twice
            random.seed(seed)
            self.next_unused_user_id = self.og_unused_user_id
            manager.reinit()
            if i == 1:
                # We can only animate one manager at a time
                animater = Animater(manager,
                                    self.__class__,
                                    self.attacker_cls,
                                    self.user_cls,
                                    **self.graph_kwargs)

        # If we are graphing for just one manager
        # Print and turn on tqdm
        if graph_trials:
            turns = trange(num_rounds,
                           desc=f"Running {manager.__class__.__name__}")
        # If we are comparing managers, multiprocessing is used
        # So no tqdm as to not have garbled output
        else:
            turns = range(num_rounds)

        return animater, turns

    def run_sim(self, turns, manager, i, animater):
        """Runs actual simulation"""

        for turn in turns:
            # Attackers attack, users record stats
            self.user_actions(manager, turn)
            # Record data
            self.record(turn, manager, i, animater)
            # Manager detects and removes suspicious users, then shuffles
            # Then reset buckets to not attacked
            manager.take_action(turn)
            self.connect_disconnect_users(manager, turn)

########################
### Helper Functions ###
########################

    def user_actions(self, manager, turn):
        """Attackers attack, adds 1 to user lifetime"""

        manager.get_animation_statistics()
        # Attackers attack first
        for user in manager.connected_attackers:
            user.take_action(manager, turn)
        # Users go second
        for user in manager.connected_good_users:
            user.take_action(manager, turn)

    def record(self, turn, manager, animate, animater):
        """Records statistics for graphs"""

        self.grapher.capture_data(turn, manager)
        if animater is not None and animate == 1:
            animater.capture_data(manager)

    def get_attackers(self, num_attackers, attacker_cls):
        """Initializes attackers for sim"""

        return [attacker_cls(x + len(self.good_users))
                for x in range(num_attackers)]

    def connect_disconnect_users(self, manager, round_num):
        """Connects and disconnects users"""

        # Gets users that are disconnecting
        disconnected_user_ids = []
        for user in manager.connected_users:
            if user.disconnect(round_num):
                disconnected_user_ids.append(user.id)

        # Manager connects and disconnects users all at once
        manager.connect_disconnect(self.add_users(manager, round_num),
                                   self.user_cls,
                                   self.add_attackers(manager, round_num),
                                   self.attacker_cls,
                                   disconnected_user_ids)

    def add_users(self, *args, **kwargs):
        """Adds users to sim (connects them). Override this method

        Should return a list of user ids to add"""

        return []

    def add_attackers(self, *args, **kwargs):
        """Adds attackers to sim (connects them). Override this method

        Should return a list of attackers to add"""

        return []

if len(DDOS_Simulator.runnable_simulators) == 0:
    DDOS_Simulator.runnable_simulators.insert(0, DDOS_Simulator)
