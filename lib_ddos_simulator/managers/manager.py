#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the class Manager, which manages a cloud"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

import random

from ..attackers import Attacker
from ..simulation_objects import Bucket, User, User_Status
from ..utils import split_list


class Manager:
    """Simulates a manager for a DDOS attack"""

    __slots__ = ["users", "_threshold", "buckets", "attackers_detected",
                 "og_num_buckets", "max_users_y",
                 "max_buckets", "og_user_order", "bucket_id", "og_json",
                 "downed_json", "will_be_connected_users", "next_unused_id",
                 "num_attackers_guess"]

    runnable_managers = []

    # https://stackoverflow.com/a/43057166/8903959
    def __init_subclass__(cls, **kwargs):
        """This method essentially creates a list of all subclasses"""

        super().__init_subclass__(**kwargs)

        assert hasattr(cls, "runnable"), "Must add runnable class attr"

        # Only attack if it's runnable
        if cls.runnable:
            # Ignore all sus funcs > 0, too many managers
            if (hasattr(cls, "suspicion_func_num")
                    and cls.suspicion_func_num != 0):
                pass
            else:
                cls.runnable_managers.append(cls)
                Manager.runnable_managers.append(cls)

        for q in [Manager, cls]:
            # Sorts alphabetically
            q.runnable_managers = list(sorted(set(q.runnable_managers),
                                              key=lambda x: x.__name__))

    def __init__(self,
                 num_buckets: int,
                 users: list,
                 threshold: int = 0,
                 # Used in animations
                 max_users_y=0,
                 max_buckets=0):
        """inits buckets and stores threshold"""

        if hasattr(self, "start_number_of_buckets"):
            num_buckets = self.start_number_of_buckets

        self.num_attackers_guess = None
        self.users = {x.id: x for x in users}
        # NOTE: should prob change this and have self.users
        # NOTE: be a property iterating over self.buckets
        self.og_user_order = [x.id for x in users]
        self._threshold = threshold
        self.og_num_buckets = num_buckets
        self.buckets = []
        # Divide users evenly among buckets
        for _id, user_chunk in enumerate(split_list(users,
                                                    num_buckets)):
            self.buckets.append(Bucket(user_chunk, _id))
        self.bucket_id = _id + 1

        if max_buckets > 0:
            self.add_additional_buckets(max_buckets)
        self.attackers_detected = 0

        # Simple error checks
        self.validate()

        # Animation statistics
        self.max_users_y = max_users_y
        self.max_buckets = max_buckets
        self.get_animation_statistics()

        self.will_be_connected_users = {}
        self.next_unused_id = max(x.id for x in users) + 1
        for user in users:
            user.status = User_Status.CONNECTED
            user.conn_lt = 0
            user.turns_attacked_in_a_row = 0

    def reinit(self):
        users_dict = self.users.copy()
        for user in users_dict.values():
            user.suspicion = 0
            user.conn_lt = 0
            user.dose_atk_risk = 0
            user.status = None
        self.__init__(self.og_num_buckets,
                      # Reorder users to how they were originally
                      [users_dict[x] for x in self.og_user_order],
                      self._threshold,
                      max_users_y=self.max_users_y,
                      max_buckets=self.max_buckets)
        og_ids = set(self.og_user_order)
        self.will_be_connected_users = {}
        for _id, user in users_dict.items():
            if _id not in og_ids:
                self.will_be_connected_users[user.__class__] =\
                    self.will_be_connected_users.get(user.__class__, [])
                self.will_be_connected_users[user.__class__].append(user)
        for user_cls, user_list in self.will_be_connected_users.items():
            self.will_be_connected_users[user_cls] = list(sorted(user_list))
            for user in user_list:
                user.bucket = None
                
    def take_action(self, turn=0):
        """Actions to take every turn"""

        self.get_animation_statistics()
        self.record_dose_events()
        # Detects and removes suspicious users, then shuffles
        self.detect_and_shuffle(turn)
        # All buckets are no longer attacked for the next round
        self.reset_buckets()

    def record_dose_events(self):
        """Only DOSE does this, ignore"""
        pass

    def get_new_bucket(self):
        try:
            bucket = self.non_used_buckets[0]
            return self.non_used_buckets[0]
        except IndexError:
            self.buckets.append(Bucket(id=self.bucket_id))
            self.bucket_id += 1
            return self.buckets[-1]

    def get_new_buckets(self, num_to_get):
        buckets = []
        non_used_buckets = self.non_used_buckets
        for i in range(num_to_get):
            try:
                buckets.append(non_used_buckets[i])
            except IndexError:
                self.buckets.append(Bucket(id=self.bucket_id))
                self.bucket_id += 1
                buckets.append(self.buckets[-1])
        return buckets

    def get_new_user(self, user_cls, user_id=None):
        """Tries to get user out of will be connected users

        if not exists, returns a new instance
        """

        try:
            if user_id is None:
                user_list = self.will_be_connected_users[user_cls]
                user = user_list.pop(0)
            else:
                index = None
                for i, user in enumerate(self.will_be_connected_users[user_cls]):
                    if user.id == user_id:
                        index = i
                user = self.will_be_connected_users[user_cls].pop(index)
        except (IndexError, KeyError):
            user = user_cls(user_id if user_id is not None
                            else self.next_unused_id)
            if user_id is not None:
                self.next_unused_id += 1
        except TypeError:
            input("not working, forget it")
            user = user_cls(user_id if user_id is not None
                            else self.next_unused_id)
            if user_id is not None:
                self.next_unused_id += 1


        return user

    def add_additional_buckets(self, max_buckets):
        """Must add additional buckets depending on algo"""

        new_buckets = max_buckets - len(self.buckets)
        for _ in range(new_buckets):
            self.buckets.append(Bucket(id=self.bucket_id))
            self.bucket_id += 1

    def validate(self):
        """Simple error checks"""

        assert len(self.users) > 0, "No users? Surely a bug?"
        for user in self.users.values():
            assert user.bucket in self.buckets

    @property
    def attacked_buckets(self):
        """Return all attacked buckets"""

        return [x for x in self.used_buckets if x.attacked]

    @property
    def non_attacked_buckets(self):
        """Returns all non attacked buckets"""

        return [x for x in self.used_buckets if not x.attacked]

    @property
    def attacked_users(self):
        """Returns all attacked users"""

        attacked_users = []
        for bucket in self.attacked_buckets:
            attacked_users.extend(bucket.users)
        return attacked_users

    def reset_buckets(self):
        """Sets all buckets to not be attacked"""

        self.get_animation_statistics()
        for bucket in self.buckets:
            bucket.attacked = False

    def remove_attackers(self):
        """Removes buckets and attackers if bucket is attacker and len is 1"""

        caught_attackers = []
        for bucket in self.used_buckets:
            if bucket.attacked and len(bucket) == 1:
                self.attackers_detected += 1
                for user in bucket.users:
                    user.status = User_Status.ELIMINATED
                caught_attackers.extend(bucket.users)
                bucket.users = []
                bucket.attacked = True
        return caught_attackers

    @property
    def attackers(self):
        """Returns all attackers"""

        return [x for x in self.users.values() if isinstance(x, Attacker)]

    @property
    def used_buckets(self):
        """Returns all buckets with users"""

        return [x for x in self.buckets if len(x) > 0]

    @property
    def unused_buckets(self):
        """Returns all unused buckets"""

        return [x for x in self.buckets if len(x.users) == 0]

    @property
    def non_used_buckets(self):
        return self.unused_buckets

    def get_animation_statistics(self):
        cur_max_users_y = max(len(x) for x in self.buckets)
        self.max_users_y = max(cur_max_users_y, self.max_users_y)
        self.max_buckets = max(len(self.buckets), self.max_buckets)

    def connect_disconnect(self,
                           newly_connected_user_ids,
                           user_cls,
                           newly_connected_attacker_ids,
                           attacker_cls,
                           disconnected_user_ids,
                           test_kwarg=False):
        """Adds and removes user from sim"""

        if len(newly_connected_user_ids) > 0 or len(newly_connected_attacker_ids) > 0:
            self.connect_users(newly_connected_user_ids,
                               user_cls,
                               newly_connected_attacker_ids,
                               attacker_cls)
        if len(disconnected_user_ids) > 0:
            self.disconnect_users(disconnected_user_ids)
        self.get_animation_statistics()
        return newly_connected_user_ids

    def connect_users(self,
                      user_ids_to_conn,
                      user_cls,
                      attacker_ids_to_conn,
                      attacker_cls):
        """Add users to bucket. Set status to connected.

        Makes sure user user isn't connected or eliminated"""

        users = []
        assert user_ids_to_conn is not None
        assert attacker_ids_to_conn is not None

        for id_list, user_type in zip([user_ids_to_conn, attacker_ids_to_conn],
                                      [user_cls, attacker_cls]):
            for _id in id_list:
                if _id in self.users:
                    if self.users[_id].status == User_Status.ELIMINATED:
                        logging.info("User eliminated, not adding")
                    elif self.users[_id].status == User_Status.DISCONNECTED:
                        users.append(self.users[_id])
                        assert isinstance(self.users[_id], user_type)
                    elif self.users[_id].status == User_Status.CONNECTED:
                        raise Exception("connecting a connected user")
                    else:
                        raise Exception("Unkown user status type")
                else:
                    users.append(self.get_new_user(user_type, user_id=_id))
        random.seed(str(self.json) + str(user_ids_to_conn) + str(attacker_ids_to_conn))
        random.shuffle(users)
        for user in users:
            self.connect_user(user)

    def connect_user(self, user):
        # SHOULD REALLY be changed to add from a bucket func
        self.used_buckets[-1].users.append(user)
        user.bucket = self.used_buckets[-1]
        if user.id not in self.users:
            self.users[user.id] = user
        user.status = User_Status.CONNECTED
        user.conn_lt = 0
        user.turns_attacked_in_a_row = 0

    def disconnect_users(self, disconnect_user_ids):
        """Disconnect users. Set status to disconnected"""

        for _id in disconnect_user_ids:
            user = self.users[_id]
            assert user.status == User_Status.CONNECTED
            user.bucket.users.remove(user)
            user.status = User_Status.DISCONNECTED

    def eliminate_users_list(self, user_ids):
        for _id in user_ids:
            user = self.users[_id]
            assert user.status == User_Status.CONNECTED
            user.bucket.users.remove(user)
            user.status = User_Status.ELIMINATED


    @property
    def json(self):
        """For flask app, returns json of {bucket_id: user_ids}"""

        buckets = {bucket.id: list(sorted([x.id for x in bucket.users]))
                   for bucket in self.used_buckets}
        users = {user.id: user.bucket.id for user in
                list(sorted(self.connected_users))}
                 
        eliminated = list(sorted(x.id for x in self.eliminated_users))
        disconnected = list(sorted(x.id for x in self.disconnected_users))
        return {"bucket_mapping": buckets,
                "user_mapping": users,
                "eliminated_users": eliminated,
                "disconnected_users": disconnected,
                "manager": self.__class__.__name__}

    def get_buckets_by_ids(self, ids):
        """Returns a list of buckets by ids"""

        return [x for x in self.buckets if x.id in set(ids)]

    @property
    def connected_users(self):
        return self._get_connected_users()

    def _get_connected_users(self, filter_func=None):
        if filter_func is None:
            return [x for x in self.users.values()
                    if x.status == User_Status.CONNECTED]
        else:
            return [x for x in self.users.values()
                    if x.status == User_Status.CONNECTED
                    and filter_func(x)]

    @property
    def eliminated_users(self):
        return [x for x in self.users.values()
                if x.status == User_Status.ELIMINATED]

    @property
    def disconnected_users(self):
        return [x for x in self.users.values()
                if x.status == User_Status.DISCONNECTED]

    @property
    def serviced_users(self):
        return self._get_connected_users(lambda x: x.bucket.attacked is False)

    @property
    def attacked_users(self):
        return self._get_connected_users(lambda x: x.bucket.attacked is True)

    @property
    def connected_attackers(self):
        return self._get_connected_users(lambda x: isinstance(x, Attacker))

    @property
    def connected_good_users(self):
        return self._get_connected_users(lambda x: not isinstance(x, Attacker))
