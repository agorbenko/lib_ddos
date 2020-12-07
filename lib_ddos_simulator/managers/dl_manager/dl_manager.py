#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the class DOSE_Manager, which manages a cloud

This manager inherits Manager class and uses DOSE shuffling algorithm
"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from ..manager import Manager

from ...utils import split_list


class DL_Manager(Manager):
    runnable = True

    RPR = 1

    def __init__(self, *args, **kwargs):
        super(DOSE_Manager, self).__init__(*args, **kwargs)

    def detect_and_shuffle(self, *args):
        """DOSE algorithm"""

        self.remove_attackers()

        users = []

        for bucket in self.used_buckets:
            users.extend(bucket.users)
            user.bucket = None

        random.seed(manager.json)
        random.shuffle(users)
        new_bucket_amnt = sum(self.get_risk(x.fvec)
                              for x in bucket.users) / self.RPR
        if int(new_bucket_amnt) != new_bucket_amnt:
            new_bucket_amnt = int(new_bucket_amnt) + 1
        else:
            new_bucket_amnt = int(new_bucket_amnt)
        if new_bucket_amnt < 1:
            assert False, "No users?"
        else:
            if new_bucket_amnt > len(users):
                new_bucket_amnt = len(users)
        user_chunks = split_list(users, int(new_bucket_amnt))
        for user_chunk in user_chunks:
            self.get_new_bucket().reinit(user_chunk)

    def get_risk(self, fvec):
        return .5
