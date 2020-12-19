#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the class DOSE_Manager, which manages a cloud

This manager inherits Manager class and uses DOSE shuffling algorithm
"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

import random
import numpy as np
import os

from ..manager import Manager

from ...simulation_objects import User_Status
from ...utils import split_list


class DL_Manager2(Manager):
    runnable = True

    RPR = 1

    def __init__(self, *args, **kwargs):
        super(DL_Manager2, self).__init__(*args, **kwargs)
        import tensorflow as tf
        model_folder = os.path.join(os.getcwd(), "model")
        self.model = tf.keras.models.load_model(model_folder + "/tf_model2")

    def detect_and_shuffle(self, *args):
        """DOSE algorithm"""

        if self.model == None:
            import tensorflow as tf
            model_folder = os.path.join(os.getcwd(), "model")
            self.model = tf.keras.models.load_model(model_folder + "/tf_model2")


        self.remove_attackers()

        users = []

        for bucket in self.used_buckets:
            users.extend(bucket.users)
#            bucket.users = []
#        for user in users:
#            user.bucket = None

        random.seed(str(self.json))
        random.shuffle(users)
        results = self.model.predict([x.fvec for x in users])
        for user, score in zip(users, results):
            user.sus = score[1]
        for bucket in self.used_buckets[1:]:
            bucket.users = []
        new_users = list(sorted(users, key=lambda x:x.sus))
        uber_new_users = []
        for user in new_users:
#            print(f"{user.__class__.__name__}: {user.sus}")
            if user.sus > .2:
                self.attackers_detected += 1
                if "ttacker" not in str(user.__class__):
                    print(f"wrong {user.sus}")
                user.status = User_Status.ELIMINATED
            else:
                uber_new_users.append(user)
#        input()
#        input(len(self.connected_users))
        good_users = [x for x in uber_new_users if x.sus < .1]
        bad_users = [x for x in uber_new_users if x.sus >= .1]
        self.used_buckets[0].reinit(good_users)
        new_users = bad_users
        user_chunks = [[]]
        counter = 0
        cur_sus = 0
        while counter < len(new_users):
            sus = new_users[counter].sus
            if cur_sus + sus > 1:
                user_chunks.append([new_users[counter]])
                cur_sus = sus
            else:
                user_chunks[-1].append(new_users[counter])
                cur_sus += sus
            counter += 1
        for user_chunk in user_chunks:
            self.get_new_bucket().reinit(user_chunk)
