#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the class Simulation, to simulate a DDOS attack"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

import random

from .ddos_simulator import DDOS_Simulator

from ..simulation_objects import Fluid_User
from ..attackers import Attacker


class Fluid_DDOS_Simulator(DDOS_Simulator):
    """Simulates a DDOS attack"""

    def __init__(self, *args, **kwargs):
        kwargs["user_cls"] = Fluid_User
        super(Fluid_DDOS_Simulator, self).__init__(*args, **kwargs)

    def add_users(self, manager, round_num):
        """Adds users to sim (connects them). Override this method

        Should return a list of user ids to add"""

        random.seed(str(manager.json) + str(round_num))
        og_users = self.og_num_attackers + self.og_num_users
        og_percent_users = self.og_num_users / og_users

        current_good_users = len([1 for x in manager.connected_users
                                 if not isinstance(x, Attacker)])
        current_attackers = len(manager.connected_users) - current_good_users
        current_percent_users = current_good_users / len(manager.connected_users)
        connected = len(manager.connected_users)

        ids = []
        while random.random() > og_percent_users:
            _id = self.next_unused_user_id
            self.next_unused_user_id += 1
            ids.append(_id)
        while current_percent_users < og_percent_users:
            _id = self.next_unused_user_id
            self.next_unused_user_id += 1
            ids.append(_id)
            current_good_users += 1
            connected += 1
            current_percent_users = current_good_users / connected

        return ids

    def add_attackers(self, manager, round_num):
        """Adds attackers to sim (connects them). Override this method

        Should return a list of attackers to add"""

        # NOTE: must always use random.seed
        # NOTE: encode this elsewhere
        random.seed(str(manager.json) + str(round_num))
        og_users = self.og_num_attackers + self.og_num_users
        percent_attackers = self.og_num_attackers / og_users

        current_good_users = len([1 for x in manager.connected_users
                                 if not isinstance(x, Attacker)])
        current_attackers = len(manager.connected_users) - current_good_users
        current_percent_attackers = current_attackers / len(manager.connected_users)
        connected = len(manager.connected_users)

        ids = []

        while random.random() > .5:
            _id = self.next_unused_user_id
            self.next_unused_user_id += 1
            ids.append(_id)
            current_attackers += 1
            connected += 1

        while current_percent_attackers < percent_attackers:
            _id = self.next_unused_user_id
            self.next_unused_user_id += 1
            ids.append(_id)
            current_attackers+=1
            connected += 1
            current_percent_attackers = current_attackers / connected

        return ids
