#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a class that inherits from Attacker"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

import random

from .attacker import Attacker


class Random_Attacker(Attacker):
    """Attacks at random self._percent_change_attack of the time"""

    runnable = False

    def _attack(self, manager, turn):
        random.seed(str(manager.json) + str(turn))
        if random.random() < self._percent_chance_attack:
            self.bucket.attacked = True


class Fifty_Percent_Attacker(Random_Attacker):
    """Attacks at random 50% of the time"""

    runnable = True
    _percent_chance_attack = .5


class Fifty_Percent_Lone_Attacker(Fifty_Percent_Attacker):
    """Attacks at 50% of the time, if no attacker attacked it's bucket"""

    lone = True
