#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains utility functions for api"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import functools
import os
import pkg_resources
import random

from flask import request, jsonify

from ..attackers import Attacker
from ..simulation_objects import User


# https://stackoverflow.com/a/32965521/8903959
version = pkg_resources.get_distribution('lib_ddos_simulator').version

def format_json(desc="", req_args=[], version=version):
    """Try catch around api calls that formats json with matadata"""

    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func(*args2, **kwargs):
            # Inside the decorator
            try:
                metadata = {"metadata": {"desc": desc,
                                         "url": request.url,
                                         "system_id": request.args.get("sys_id"),
                                         "version": version}}
                for arg in req_args:
                    if request.args.get(arg) is None:
                        raise Exception(f"{arg} is None but is required")
                # Get the results from the function
                return jsonify({**{"data": func(*args2, **kwargs)},
                                **metadata})
            except Exception as e:
                if "PYTEST_CURRENT_TEST" in os.environ:
                    raise e
                # Never allow the API to crash. This should record errors
                print(e)
                return jsonify({"ERROR":
                                f"{e} Please contact jfuruness@gmail.com"})
        return function_that_runs_func
    return my_decorator


def init_sim(app, user_ids, num_buckets, manager_cls, system_id):
    """inits simulation"""

    users = [User(x) for x in user_ids]
    random.shuffle(users)
    # Threshold is used in test code
    app.managers[system_id] = manager_cls(num_buckets,
                                          users,
                                          -1)


def complete_turn(app, downed_bucket_ids, system_id):
    """Records stats and manager takes actions"""

    manager = app.managers[system_id]

    for user in manager.connected_users:
        user.take_action()
    if len(downed_bucket_ids) > 0:
        for bucket in manager.get_buckets_by_ids(downed_bucket_ids):
            bucket.attacked = True
    # Turn is used in test code
    manager.take_action(turn=-1)

def connect_disconnect_uids(app, connecting_uids, disconnecting_uids, sys_id):
    """Connects and disconnects users"""

    app.managers[sys_id].connect_disconnect(connecting_uids,
                                            User,
                                            [],  # Connecting Attackers
                                            None,  # Attacker cls
                                            disconnecting_uids,
                                            test_kwarg=True)
