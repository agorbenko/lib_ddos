#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Folder contains all attacker classes"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from .basic_attacker import Basic_Attacker, Basic_Lone_Attacker
from .random_attacker import Fifty_Percent_Attacker
from .random_attacker import Fifty_Percent_Lone_Attacker

# Done here to fill subclasses
from .attacker import Attacker
