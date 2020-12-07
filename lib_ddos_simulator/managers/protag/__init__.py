#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This folder contains all the protag managers for DDOS simulation"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"

from .protag_manager_base import Protag_Manager_Base
from .protag_manager_merge import Protag_Manager_Merge
from .protag_manager_no_merge import Protag_Manager_No_Merge
