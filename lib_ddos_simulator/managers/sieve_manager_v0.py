#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the class Sieve_Manager, which manages a cloud

This manager inherits Manager class and uses Sieve shuffling algorithm
"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from .sieve_manager_base import Sieve_Manager_Base


class Sieve_Manager_V0(Sieve_Manager_Base):
    """Sieve Manager detect and shuffle algorithm version 1"""

    def detect_and_shuffle(self, turn_num: int):
        """Performs sieve shuffle algorithm

        First updates suspicion of users.
        Then sorts users by suspicion.
        Then splits users into num buckets/2 chunks
        Then for each chunk, put in two buckets randomly
        """

        self._update_suspicion()
        self._reorder_buckets(self.buckets)
        self._sort_buckets(self.buckets)


class Sieve_Manager_V0_S0(Sieve_Manager_V0):
    suspicion_func_num = 0


class Sieve_Manager_V0_S1(Sieve_Manager_V0):
    suspicion_func_num = 1


class Sieve_Manager_V0_S2(Sieve_Manager_V0):
    suspicion_func_num = 2
