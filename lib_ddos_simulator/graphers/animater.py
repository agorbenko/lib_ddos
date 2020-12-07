#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains the class Animater to animate ddos simulations"""

"""
NOTE TO ANY FUTURE DEVS:

I got a little carried away with this thing, and it needs a serious refactor
But animations are quite useless, and every time I look at this file I try
to improve the animations, so I'm not going to do it.


If you wrote a manager and the animation is breaking, chances are you:
1. Got rid of a bucket when you shouldn't have
2. Created a new bucket when you should've called manager.get_new_bucket()
3. Got rid of a user when you should've added to manager.eliminated_users
4. Created a user mid round (not functional)
5. Your animation is too complex (try a small one, like 9 users)

If you ever need to change this, please just contact me
jfuruness@gmail.com
and I'll fix it.
"""


__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from copy import deepcopy
from enum import Enum
import os
import math

import matplotlib
import matplotlib as mpl
dpi = 120
# https://stackoverflow.com/a/51955985/8903959
mpl.rcParams['figure.dpi'] = dpi
import matplotlib
matplotlib.rcParams['figure.dpi'] = dpi
mpl.rcParams['figure.dpi'] = dpi
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import animation
import numpy as np
from tqdm import tqdm

from .base_grapher import Base_Grapher

from ..attackers import Attacker
from ..simulation_objects import Bucket, User
from ..managers import Manager

class Bucket_States(Enum):
    USED = 1
    UNUSED = 0
    ATTACKED = -1

class Animater(Base_Grapher):
    """animates a DDOS attack"""

    slots__ = ["_data", "ax", "round", "max_users", "fig",
                 "name", "round_text", "frames_per_round",
                 "total_rounds", "manager", "ogbuckets", "ogusers",
                 "detected_location", "blue_to_yellow",
                 "yellow_to_blue", "track_suspicions"]

    def __init__(self,
                 manager,
                 sim_cls,
                 user_cls,
                 attacker_cls,
                 **kwargs):
        """Initializes simulation"""


        super(Animater, self).__init__(**kwargs)

        self.sim_cls = sim_cls
        self.user_cls = user_cls
        self.attacker_cls = attacker_cls

        self.disconnected_location = (-20, -20)

        self.low_dpi = 60
        if self.high_res:
            # Anything higher than 600 and you need to drastically increase bitrate
            # But increasing bitrate causes it to crash on other machines
            self.high_dpi = 120
            # https://stackoverflow.com/a/51955985/8903959
            mpl.rcParams['figure.dpi'] = self.high_dpi
            matplotlib.rcParams['figure.dpi'] = self.high_dpi

        if manager.max_users_y >= 40:
            self.row_cutoff = 100
        else:
            self.row_cutoff = 32
        assert self.tikz is False, "Can't save animation as tikz afaik"
        self.manager = manager
        self.ogbuckets = deepcopy(manager.buckets)
        self.max_users, self.fig, self.ax = self._format_graph()
        #assert self.save or len(manager.users) <= 40,\
        #    "Matplotlib can't handle that many users"
        self.ogusers = deepcopy(self.users)

        fontsize = 12
        matplotlib.rcParams.update({'font.size': 10})


        if manager.max_buckets > 10:
            fontsize -= 3


        if manager.max_users_y > 10:
            fontsize -= 3
            matplotlib.rcParams.update({'font.size': 5})

        if manager.max_buckets > 20:
            fontsize -= 2
        if manager.max_buckets >= 100:
            fontsize -= 4
        if ("dose" in manager.__class__.__name__.lower()
            or "sieve" in manager.__class__.__name__.lower()):
            fontsize -= 2.5

        if self.high_res:
            # 3 is difference between low res and high res dpi
            fontsize = fontsize / 1

        matplotlib.rcParams.update({'font.size': fontsize})

        self._create_bucket_patches()
        self._create_user_patches()
        self.name = manager.__class__.__name__ 
        self.frames_per_round = 50
        if self.save:
            self.frames_per_round = 100
        self.total_rounds = 0
        self.detected_location = (-10, -10,)

        # Frames left before turning non attacked to attacked
        self.percent_left_before_change = .2

        # Reason we limit # of color changes is because
        # We only do the atk in last 10% of frames in the round
        self.blue_to_yellow = [self.color_fader(c1="b", c2="y", mix=x/int(self.frames_per_round * self.percent_left_before_change))
                               for x in range(int(self.frames_per_round * self.percent_left_before_change))]
        self.blue_to_yellow[0] = "b"
        self.blue_to_yellow[-1] = "y"
        self.yellow_to_blue = [self.color_fader(mix=x/self.frames_per_round)
                               for x in range(self.frames_per_round)]
        self.yellow_to_blue[0] = "y"
        self.yellow_to_blue[-1] = "b"

        #assert isinstance(manager, Sieve_Manager_Base), "Can't do that manager yet"

    def color_fader(self, c1="y", c2="b", mix=0):
        """Returns colors from c1 to c2"""

        # https://stackoverflow.com/a/50784012/8903959
        c1=np.array(mpl.colors.to_rgb(c1))
        c2=np.array(mpl.colors.to_rgb(c2))
        return mpl.colors.to_hex((1-mix)*c1 + mix*c2)

    @property
    def users(self):
        will_be_conn = []
        for user_list in self.manager.will_be_connected_users.values():
            will_be_conn.extend(user_list)
        return list(self.manager.users.values()) + will_be_conn

    @property
    def buckets(self):
        return self.manager.buckets

    def capture_data(self, manager: Manager):
        """Captures data for the round"""

        self.total_rounds += 1

        # add to the points array
        for bucket in manager.buckets:
            user_y = User.patch_padding + bucket.patch.get_y()
            for user in bucket.users:
                circle_y = User.patch_radius + user_y
                user.points.append((bucket.patch_center(), circle_y,))
                # Get suspicion due to DOSE
                user.suspicions.append(user.get_suspicion())
                user_y = circle_y + User.patch_radius
                user_y += (User.patch_padding * 2)
            if bucket.attacked:
                bucket.states.append(Bucket_States.ATTACKED)
            elif len(bucket) == 0:
                bucket.states.append(Bucket_States.UNUSED)
            else:
                bucket.states.append(Bucket_States.USED)

        for user in manager.eliminated_users:
            user.points.append(self.detected_location)
            #user.detected = True
            user.suspicions.append(0)

        for user in manager.disconnected_users:
            user.points.append(self.disconnected_location)
            user.suspicions.append(0)

        for user_list in manager.will_be_connected_users.values():
            for user in user_list:
                user.points.append(self.disconnected_location)
                user.suspicions.append(0)


    def run_animation(self, total_rounds):
        """Graphs data

        Saves all data to an mp4 file. Note, you can increase or
        decrease total number of frames in this function"""

        frames = total_rounds * self.frames_per_round
        anim = animation.FuncAnimation(self.fig, self.animate,
                                       init_func=self.init,
                                       frames=frames,
                                       interval=40,
                                       blit=True if self.save else False)

        self.save_graph(anim)


    def save_graph(self, anim):
        """Saves animation, overwrites Base_Grapher method"""

        # self.save is an attr of Base_Grapher
        if self.save:

            pbar = tqdm(desc="Saving video",
                        total=self.frames_per_round * (self.total_rounds - 1))
            # Callback function for saving animation
            def callback(current_frame_number, total_frames):
                pbar.update()

            # graph_dir comes from inherited class
            path = os.path.join(self.graph_dir, f'{self._get_round_text(0).replace("Round 0", "")}.mp4')

            dpi = self.high_dpi if self.high_res else self.low_dpi
            # NOTE: bitrate barely impacts the speed that it saves
            bitrate = 12000 if self.high_res else 12000

            # assert bitrate <= 3000 and dpi <= 1200, "Too high quality, breaks"
            # FFwriter=animation.FFMpegFileWriter(bitrate=bitrate)
            # https://stackoverflow.com/a/14666461/8903959
            anim.save(path, progress_callback=callback, dpi=dpi, bitrate=bitrate)
            #anim.save(path, progress_callback=callback, dpi=dpi, bitrate=bitrate, writer=FFwriter)
            pbar.close()
        else:
            plt.show()

    def _format_graph(self):
        """Formats graph properly

        Basically makes graph colorful"""

        if self.save:
            matplotlib.use("Agg")
        plt.style.use('dark_background')
        # https://stackoverflow.com/a/48958260/8903959
        matplotlib.rcParams.update({'text.color': "black"})

        # NOTE:
        # I'm not sure this fig is ever used
        # Should prob be removed
        fig = plt.figure()
        # NOTE: Increasing figure size makes it take way longer
        fig.set_size_inches(16, 9)
        

        max_users = self.manager.max_users_y

        
        rows = math.ceil(len(self.buckets) / self.row_cutoff)

        ax = plt.axes(xlim=(0, min(len(self.buckets), self.row_cutoff)* Bucket.patch_length()),
                      ylim=(0, (max_users * User.patch_length() + Bucket.patch_padding) * rows+ 1))
        ax.set_axis_off()
        ax.margins(0)

        gradient_image(ax,
                       direction=0,
                       extent=(0, 1, 0, 1),
                       transform=ax.transAxes,
                       cmap=plt.cm.Oranges,
                       cmap_range=(0.1, 0.6))

        return max_users, fig, ax

    def _create_bucket_patches(self):
        """Creates patches of users and buckets"""

        self.bucket_patches = []
        bucket_rows = [[]]
        for i, bucket in enumerate(reversed(self.buckets)):
            if i % self.row_cutoff == 0 and i != 0:

                bucket_rows.append([])
                bucket_rows[-1].append(bucket)
            else:
                bucket_rows[-1].append(bucket)

        ordered_bucket_rows = []
        for bucket_row in bucket_rows:
            ordered_bucket_rows.append(list(reversed(bucket_row)))

        x = Bucket.patch_padding
        y = 0

        for bucket_row in reversed(ordered_bucket_rows):
            for bucket in bucket_row:
                kwargs = {"fc": bucket.og_face_color}
                patch_type = FancyBboxPatch
                kwargs["boxstyle"] = "round,pad=0.1"

                bucket.patch = patch_type((x, y),
                                          Bucket.patch_width,
                                          self.max_users * User.patch_length(),
                                          **kwargs)

                bucket.patch.set_boxstyle("round,pad=0.1, rounding_size=0.5")

                x += Bucket.patch_length()
                self.bucket_patches.append(bucket.patch)

            # Next row
            y += bucket.patch_height
            x = Bucket.patch_padding


    def _create_user_patches(self):
        """Creates patches of users"""

        self.user_patches = []
        for user in self.users:
            if user.bucket is None or user.bucket.patch is None:
                bucket_patch_center = self.disconnected_location[0]
            else:
                bucket_patch_center = user.bucket.patch_center()
            user.patch = plt.Circle((bucket_patch_center, 5),
                                    User.patch_radius,
                                    fc=user.og_face_color)
            if isinstance(user, Attacker):
                user.horns = plt.Polygon(0 * self.get_horn_array(user),
                                         fc=user.og_face_color,
                                         **dict(ec="k"))
                user.horns.set_linewidth(.4 if self.high_res else .5)
            user.text = plt.text(bucket_patch_center,
                                 5,
                                 f"{user.id}",
                                 horizontalalignment='center',
                                 verticalalignment='center')
            self.user_patches.append(user.patch)

    def init(self):
        """inits the animation

        Sets z order: bucket->horns->attacker/user->text"""

        for bucket in self.buckets:
            self.ax.add_patch(bucket.patch)
            bucket.patch.set_zorder(1)
            if bucket.states[0] == Bucket_States.UNUSED:
                bucket.patch.set_alpha(0)
            elif bucket.states[0] == Bucket_States.ATTACKED:
                # Change this to not be hardcoded
                bucket.patch.set_facecolor("y")
        zorder = 2
        max_sus = 0
        for user in self.users:
            max_sus = max(max(user.suspicions), max_sus)
            user.patch.center = user.points[0]

            self.ax.add_patch(user.patch)
            if isinstance(user, Attacker):
                user.horns.set_zorder(zorder)
                zorder += 1
                self.ax.add_patch(user.horns)
                user.horns.set_xy(self.get_horn_array(user))
            user.patch.set_zorder(zorder)
            zorder += 1
            user.text.set_y(user.points[0][1])
            user.text.set_zorder(zorder)
            zorder += 1

        self.track_suspicions = max_sus != 0

        round_text_kwargs = dict(facecolor='white', alpha=1)
        if self.high_res:
            round_text_kwargs["boxstyle"] = "square,pad=.05"

        self.round_text = plt.text(self.ax.get_xlim()[1] * .5,
                                   self.ax.get_ylim()[1] - .5,
                                   self._get_round_text(0),
                                   fontsize=12 if self.high_res else 12,
                                   bbox=round_text_kwargs,
                                   horizontalalignment='center',
                                   verticalalignment='center')


        return self.return_animation_objects()

    def animate(self, i):
        """Animates the frame

        moves all objects partway to the next point. Basically,
        determines the final destination, and moves 1/frames_per_round
        of the way there. It only moves users, and so must move horns
        and text of the user as well
        """

        self.animate_users(i)
        self.animate_buckets(i)
        self.animate_round_text(i)
        return self.return_animation_objects(i)

    def animate_users(self, i):
        for user in self.users:
            current_point = user.points[i // self.frames_per_round]
            future_point = user.points[(i // self.frames_per_round) + 1]
            if current_point != future_point or i % self.frames_per_round != 0:
                remainder = i - ((i // self.frames_per_round)
                                 * self.frames_per_round)
                next_point_x1_contr = current_point[0] * (
                    (self.frames_per_round - remainder) / self.frames_per_round)
                next_point_x2_contr = future_point[0] * (
                    remainder / self.frames_per_round)
                next_point_y1_contr = current_point[1] * (
                    (self.frames_per_round - remainder) / self.frames_per_round)
                next_point_y2_contr = future_point[1] * (
                    remainder / self.frames_per_round)
                next_point = (next_point_x1_contr + next_point_x2_contr,
                              next_point_y1_contr + next_point_y2_contr)
                user.patch.center = next_point
                if isinstance(user, Attacker):
                    user.horns.set_xy(self.get_horn_array(user))
                user.text.set_x(next_point[0])
                user.text.set_y(next_point[1])
            if (future_point == self.detected_location
                and current_point != self.detected_location
                and i % self.frames_per_round== 0):
                user.text.set_text("Detected")
                user.patch.set_facecolor("grey")
            elif (future_point == self.disconnected_location
                  and current_point != self.disconnected_location
                  and i % self.frames_per_round== 0):
                  user.text.set_text("Disconnected")
                  user.patch.set_facecolor("purple")
            else:
                if self.track_suspicions and i % self.frames_per_round == 0:
                    text = f"{user.suspicions[(i//self.frames_per_round) + 1]:.1f}"
                    user.text.set_text(f"{user.id:2.0f}:{text}")
                if i == 0:
                    user.patch.set_facecolor(user.og_face_color)
                if (current_point not in [self.disconnected_location, self.detected_location]
                    and future_point not in [self.disconnected_location, self.detected_location]):
                    user.patch.set_facecolor(user.og_face_color)
                    text = user.text.get_text().lower()
                    # String comparisons no!!!
                    if "disconnected" in text or "detected" in text:
                        text = str(user.id)
                        user.text.set_text(text)

    def animate_buckets(self, i):
        for bucket in self.buckets:
            current_state = bucket.states[i // self.frames_per_round]
            future_state = bucket.states[(i // self.frames_per_round) + 1]

            # Transition between used and unused
            if future_state == Bucket_States.UNUSED and current_state != Bucket_States.UNUSED:
                bucket.patch.set_alpha( 1 - ((i % self.frames_per_round) / self.frames_per_round))
            elif current_state == Bucket_States.UNUSED and future_state != Bucket_States.UNUSED:
                bucket.patch.set_alpha((i % self.frames_per_round) / self.frames_per_round)

            # Transition between attacked and not attacked
            if current_state == Bucket_States.ATTACKED and future_state != Bucket_States.ATTACKED:
                bucket.patch.set_facecolor(self.yellow_to_blue[i % self.frames_per_round])
            elif future_state == Bucket_States.ATTACKED and current_state != Bucket_States.ATTACKED:
                frames_left_in_round = self.frames_per_round - (i % self.frames_per_round)
                if frames_left_in_round <= self.percent_left_before_change * self.frames_per_round:
                    frames_before_change = int(self.frames_per_round * self.percent_left_before_change)
                    color_index = frames_before_change - frames_left_in_round
                    bucket.patch.set_facecolor(self.blue_to_yellow[color_index])

    def animate_round_text(self, i):
        if i % self.frames_per_round != 0:
            return
        self.round_text.set_visible(False)
        self.round_text.remove()
        round_text_kwargs = dict(facecolor='white', alpha=1)
        if self.high_res:
            # https://stackoverflow.com/a/29127933/8903959
            round_text_kwargs["boxstyle"] = "square,pad=.05"
        # This is why it works best with that sizing
        self.round_text = plt.text(self.ax.get_xlim()[1] * .5,
                                   self.ax.get_ylim()[1] - .5,
                                   self._get_round_text(i),
                                   fontsize=12 if self.high_res else 12,
                                   bbox=round_text_kwargs,
                                   horizontalalignment='center',
                                   verticalalignment='center')

    def return_animation_objects(self, *args):
        horns = [x.horns for x in self.users if isinstance(x, Attacker)]

        objs = [x.patch for x in self.users] + [x.text for x in self.users]
        objs += [self.round_text] + horns
        objs += [x.patch for x in self.buckets]
        return objs

    def get_horn_array(self, user):
        """Returns the horn array for the attackers"""

        horn_array = np.array(
                        [user.patch.center,
                         [user.patch.center[0] - User.patch_radius,
                          user.patch.center[1]],
                         [user.patch.center[0] - User.patch_radius,
                          user.patch.center[1] + User.patch_radius],
                         user.patch.center,
                         [user.patch.center[0] + User.patch_radius,
                          user.patch.center[1]],
                         [user.patch.center[0] + User.patch_radius,
                          user.patch.center[1] + User.patch_radius],
                         user.patch.center
                         ])
        return horn_array

    def _get_round_text(self, round_num):
        return (f"{self.name}: "
                f"Round {round_num // self.frames_per_round}     "
                f"{self.sim_cls.__name__}|||"
                f"{self.user_cls.__name__}|||"
                f"{self.attacker_cls.__name__}")
 


# Basically just makes the colors pretty
# https://matplotlib.org/3.1.0/gallery/lines_bars_and_markers/gradient_bar.html
def gradient_image(ax, extent, direction=0.3, cmap_range=(0, 1), **kwargs):
    """
    Draw a gradient image based on a colormap.

    Parameters
    ----------
    ax : Axes
        The axes to draw on.
    extent
        The extent of the image as (xmin, xmax, ymin, ymax).
        By default, this is in Axes coordinates but may be
        changed using the *transform* kwarg.
    direction : float
        The direction of the gradient. This is a number in
        range 0 (=vertical) to 1 (=horizontal).
    cmap_range : float, float
        The fraction (cmin, cmax) of the colormap that should be
        used for the gradient, where the complete colormap is (0, 1).
    **kwargs
        Other parameters are passed on to `.Axes.imshow()`.
        In particular useful is *cmap*.
    """

    np.random.seed(19680801)
    phi = direction * np.pi / 2
    v = np.array([np.cos(phi), np.sin(phi)])
    X = np.array([[v @ [1, 0], v @ [1, 1]],
                  [v @ [0, 0], v @ [0, 1]]])
    a, b = cmap_range
    X = a + (b - a) / X.max() * X
    im = ax.imshow(X, extent=extent, interpolation='bicubic',
                   vmin=0, vmax=1, **kwargs)
    return im
