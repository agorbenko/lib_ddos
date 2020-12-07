#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the Combination_Grapher to graph ddos simulations"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from copy import deepcopy
import os

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from statistics import mean, variance
from math import sqrt
from multiprocessing import cpu_count
from pathos.multiprocessing import ProcessingPool
import json

from .base_grapher import Base_Grapher

from ..attackers import Attacker
# Done this way to avoid circular imports
from ..ddos_simulators import ddos_simulator
from ..managers import Manager
from ..utils import Log_Levels

class Worst_Case_Attacker:
    """placeholder

    Later used to graph the worst case attacker graph"""
    pass

class Combination_Grapher(Base_Grapher):
    """Compares managers against each other

    Plots total utility over all rounds on the Y axis
    Plots % of users that are attackers on the X axis
    """

    __slots__ = ["second_legend"]

    def __init__(self, *args, **kwargs):
        super(Combination_Grapher, self).__init__(*args, **kwargs)
        self.second_legend = []

    def run(self,
            ddos_sim_cls_list=None,
            managers=Manager.runnable_managers,#[x for x in Manager.runnable_managers if "DL" not in str(x.__name__)],
            attackers=Attacker.runnable_attackers,
            # Note that for range, last number is not included
            num_buckets_list=[1],
            # Note that this is the users per bucket, not total users
            users_per_bucket_list=[100],
            num_rounds_list=[100],
            trials=2):
        """Runs in parallel every possible scenario

        Looks complicated, but no real way to simplify it
        so deal with it"""

        if ddos_sim_cls_list is None:
            ddos_sim_cls_list =\
                [ddos_simulator.DDOS_Simulator.runnable_simulators[1]]

        # Initializes graph path
        self.make_graph_dir(destroy=True)

        # Total number of scenarios
        pbar_total = (len(ddos_sim_cls_list) *
                      len(num_buckets_list) *
                      len(users_per_bucket_list) *
                      len(num_rounds_list) *
                      (len(attackers) + 1))  # Add 1 to attacker for worst case

        _pathos_simulators_list = []
        _pathos_num_buckets_list = []
        _pathos_users_per_bucket = []
        _pathos_num_rounds = []
        for num_buckets in num_buckets_list:
            for users_per_bucket in users_per_bucket_list:
                for num_rounds in num_rounds_list:
                    for attacker in attackers + [Worst_Case_Attacker]:
                        for sim_cls in ddos_sim_cls_list:
                            self.get_attacker_graph_dir(attacker)

                        _pathos_simulators_list.append(sim_cls)
                        _pathos_num_buckets_list.append(num_buckets)
                        _pathos_users_per_bucket.append(users_per_bucket)
                        _pathos_num_rounds.append(num_rounds)

        p = ProcessingPool(nodes=cpu_count())
        total = len(_pathos_num_rounds)
        full_args = [_pathos_simulators_list,
                     [attackers] * total,
                     _pathos_num_buckets_list,
                     _pathos_users_per_bucket,
                     _pathos_num_rounds,
                     [managers] * total,
                     [trials] * total,
                     list(range(total)),
                     list([pbar_total] * total)]

        # If we are debugging, no multiprocessing
        # https://stackoverflow.com/a/1987484/8903959
        for i in range(total):
            try:
                current_args = [x[i] for x in full_args]
                self.get_graph_data(*current_args)
            except Exception as e:
                from pprint import pprint
                pprint(current_args)
                raise e
        # Get rid of carriage returns
        print()

    def get_graph_data(self,
                       ddos_sim_cls,
                       attackers,
                       num_buckets,
                       users_per_bucket,
                       num_rounds,
                       managers,
                       trials,
                       num,
                       total_num):
        """Gets data for graphing and graphs it"""

        ddos_sim_cls = deepcopy(ddos_sim_cls)
        attackers = deepcopy(attackers)
        managers = deepcopy(managers)

        scenario_data = {manager: {attacker: {"X": [],
                                              "Y": [],
                                              "YERR": []}
                                   for attacker in attackers}
                         for manager in managers}

        for attacker in attackers:
            self.print_progress(attacker, total_num)
            percent_attackers_list = [i / 100 for i in range(10, 52, 20)]

            for manager in managers:
                manager_data = scenario_data[manager][attacker]
                for percent_attackers in percent_attackers_list:
                    manager = deepcopy(manager)
                    attacker = deepcopy(attacker)
                    manager_data["X"].append(percent_attackers)
                    Y = []
                    # TRIALS
                    for _ in range(trials):
                        # Get the utility for each trail and append it
                        Y.append(self.run_scenario(ddos_sim_cls,
                                                   attacker,
                                                   num_buckets,
                                                   users_per_bucket,
                                                   num_rounds,
                                                   percent_attackers,
                                                   manager))
                    manager_data["Y"].append(mean(Y))
                    err_length = 1.645 * 2 * (sqrt(variance(Y))/sqrt(len(Y)))
                    manager_data["YERR"].append(err_length)

            self.graph_scenario(ddos_sim_cls,
                                scenario_data,
                                num_buckets,
                                users_per_bucket,
                                num_rounds,
                                attacker)

        # Graphs worst case scenario
        worst_case_data = self.worst_case_data(managers,
                                               scenario_data,
                                               attackers)
        self.graph_scenario(ddos_sim_cls,
                            worst_case_data,
                            num_buckets,
                            users_per_bucket,
                            num_rounds,
                            Worst_Case_Attacker,
                            write_json=True)

    def run_scenario(self,
                     ddos_sim_cls,
                     attacker,
                     num_buckets,
                     users_per_bucket,
                     num_rounds,
                     percent_attackers,
                     manager):
        """Runs a trial for simulation"""

        users = num_buckets * users_per_bucket
        attackers = int(users * percent_attackers)
        good_users = users - attackers
        # No longer used, but maybe in the future
        threshold = 0
        print(str(attacker) + " " + str(percent_attackers))
        sim = ddos_sim_cls(good_users,
                           attackers,
                           num_buckets,
                           threshold,
                           [manager],
                           stream_level=self.stream_level,
                           graph_dir=self.graph_dir,
                           tikz=self.tikz,
                           save=self.save,
                           attacker_cls=attacker)
        # dict of {manager: final utility}
        utilities_dict = sim.run(num_rounds, graph_trials=False)
        return utilities_dict[manager]

    def worst_case_data(self, managers, scenario_data, attackers):
        """Creates a json of worst case attacker data"""

        # Create json of worst case attackers
        worst_case_scenario_data = {manager: {Worst_Case_Attacker: {"X": [],
                                                                    "Y": [],
                                                                    "YERR": [],
                                                                    "ATKS": []}
                                              }
                                    for manager in managers}
        for manager, manager_data in scenario_data.items():
            xs = manager_data[attackers[0]]["X"]
            for i, x in enumerate(xs):
                # should be changed to be abs max but whatevs
                min_utility = 100000000000000000000000
                worst_case_atk = None
                yerr = None
                for attacker in attackers:
                    if manager_data[attacker]["Y"][i] < min_utility:
                        min_utility = manager_data[attacker]["Y"][i]
                        worst_case_atk = attacker
                        yerr = manager_data[attacker]["YERR"][i]
                atk = Worst_Case_Attacker
                cur_data_point = worst_case_scenario_data[manager][atk]
                cur_data_point["X"].append(x)
                cur_data_point["Y"].append(min_utility)
                cur_data_point["YERR"].append(yerr)
                cur_data_point["ATKS"].append(worst_case_atk.__name__)

        return worst_case_scenario_data

    def graph_scenario(self,
                       ddos_sim_cls,
                       scenario_data,
                       num_buckets,
                       users_per_bucket,
                       num_rounds,
                       attacker,
                       write_json=False):

        fig, axs, title = self._get_formatted_fig_axs(ddos_sim_cls,
                                                      scenario_data,
                                                      num_buckets,
                                                      users_per_bucket,
                                                      num_rounds, attacker)
        for manager_i, manager in enumerate(scenario_data):
            self.populate_axs(axs,
                              scenario_data,
                              manager,
                              attacker,
                              manager_i,
                              write_json=write_json)

        self.add_legend(axs)

        graph_dir = self.get_attacker_graph_dir(attacker)
        graph_path = os.path.join(graph_dir, f"{title}.png")
        self.save_graph(os.path.join(graph_dir, f"{title}.png"), plt, fig=fig)

        if write_json:
            self.write_json(graph_path, scenario_data)

    def _get_formatted_fig_axs(self,
                               sim_cls,
                               scenario_data,
                               num_buckets,
                               users_per_bucket,
                               num_rounds,
                               attacker):
        """Creates and formats axes"""

        fig, axs = plt.subplots(figsize=(20, 10))
        title = (f"Sim: {sim_cls.__name__}, "
                 f"Scenario: og_buckets: {num_buckets}, "
                 f"users: {users_per_bucket * num_buckets}, "
                 f"rounds: {num_rounds}, attacker_cls: {attacker.__name__}")
        fig.suptitle(title)

        # Gets maximum y value to set axis
        max_y_limit = 0
        for _, manager_data in scenario_data.items():
            if max(manager_data[attacker]["Y"]) > max_y_limit:
                max_y_limit = max(manager_data[attacker]["Y"])
        # Sets y limit
        axs.set_ylim(-1, max_y_limit + 5)
        # Add labels to axis
        axs.set(xlabel="Percent Attackers", ylabel="Utility (Users/buckets)")

        return fig, axs, title

    def get_attacker_graph_dir(self, attacker):
        """Returns attacker graph dir"""

        graph_dir = os.path.join(self.graph_dir, attacker.__name__)
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)
        return graph_dir

    def print_progress(self, attacker, total_num):
        """Prints total number of files generated"""

        # https://stackoverflow.com/a/16910957/8903959
        cpt = sum([len([x for x in files if "json" not in x.lower()])
                   for r, d, files in os.walk(self.graph_dir)])
        print(f"Starting: {cpt + 1}/{total_num}", end="      \r")

    def populate_axs(self,
                     axs,
                     scenario_data,
                     manager,
                     attacker,
                     manager_i,
                     write_json=False):
        """Plots error bar"""

        axs.errorbar(scenario_data[manager][attacker]["X"],  # X val
                     scenario_data[manager][attacker]["Y"],  # Y value
                     yerr=scenario_data[manager][attacker]["YERR"],
                     label=f"{manager.__name__}",
                     ls=self.styles(manager_i),
                     # https://stackoverflow.com/a/26305286/8903959
                     marker=self.markers(manager_i))
        # This means we are graphing worst case
        if write_json:
            self.overlay_scatter_plot(axs,
                                      scenario_data,
                                      manager,
                                      attacker,
                                      manager_i,
                                      write_json)

    def overlay_scatter_plot(self,
                             axs,
                             scenario_data,
                             manager,
                             attacker,
                             manager_i,
                             write_json):
        """Overlays error bars with worst case attacker colors"""

        # Get list of colors
        color_dict = self.get_worst_case_atk_color_dict()
        colors = [color_dict[atk_name] for atk_name in
                  scenario_data[manager][attacker]["ATKS"]]
        axs.scatter(scenario_data[manager][attacker]["X"],
                    scenario_data[manager][attacker]["Y"],
                    c=colors,
                    s=45,
                    zorder=3,
                    marker=self.markers(manager_i))

        # Sort worst case attacker by freq
        atk_freq_dict = {}
        for atk in scenario_data[manager][attacker]["ATKS"]:
            atk_freq_dict[atk] = atk_freq_dict.get(atk, 0) + 1
        atks = list(reversed(sorted(atk_freq_dict, key=atk_freq_dict.get)))

        self.second_legend.extend(atks)

    def get_worst_case_atk_color_dict(self):
        """Returns a dictionary of attacker to colors"""

        # https://matplotlib.org/3.1.1/gallery/color/named_colors.html
        colors = ["black", "dimgray", "lightcoral", "firebrick", "sienna",
                  "bisque", "gold", "olive", "lawngreen", "turquoise", "teal",
                  "deepskyblue", "midnightblue", "mediumpurple", "darkviolet",
                  "deeppink", "lightpink", "chocolate", "darkkhaki",
                  "powderblue"]

        new_colors_needed = len(Attacker.runnable_attackers) - len(colors)
        assert new_colors_needed <= 0, f"Add {new_colors_needed} more colors"
        return {attacker.__name__: colors[i]
                for i, attacker in enumerate(Attacker.runnable_attackers)}

    def add_legend(self, axs):
        """Adds legend. Potentially combine with grapher class"""

        # https://stackoverflow.com/a/4701285/8903959
        box = axs.get_position()
        axs.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        handles, labels = axs.get_legend_handles_labels()

        # Put a legend to the right of the current axis
        first = axs.legend(handles,
                           labels,
                           loc='center left',
                           bbox_to_anchor=(1, 0.5))

        # If we are adding a second legend for worst case attacker colors
        if len(self.second_legend) > 0:
            color_dict = self.get_worst_case_atk_color_dict()
            legend_elements = [mpatches.Patch(color=color_dict[atk], label=atk)
                               for atk in set(self.second_legend)]

            # https://riptutorial.com/matplotlib/example/32429/multiple-legends-on-the-same-axes
            # https://matplotlib.org/3.1.1/gallery/text_labels_and_annotations/custom_legends.html
            axs.legend(handles=legend_elements,
                       loc='upper right',
                       bbox_to_anchor=(1, 1))
            axs.add_artist(first)
            self.second_legend = []

    def write_json(self, graph_path, scenario_data):
        """Writes json file"""

        with open(graph_path.replace("png", "json"), "w") as f:
            data = {m.__name__: {atk.__name__: end_dict
                                 for atk, end_dict in m_data.items()}
                    for m, m_data in scenario_data.items()}
            json.dump(data, f)
