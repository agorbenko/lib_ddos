#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This folder contains all the managers for DDOS simulation"""

__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com, agorbenko97@gmail.com"
__status__ = "Development"


from .dl_manager import DL_Manager
from .dl_manager2 import DL_Manager2
from .dl_manager3 import DL_Manager3
from .dose import DOSE_Manager, DOSE_Attack_Event
# Commented out due to bugs in sudo code of their paper
# from .motag import Motag_Manager
from .protag import Protag_Manager_Base
from .protag import Protag_Manager_Merge
from .protag import Protag_Manager_No_Merge

# Done here to force init
from .manager import Manager
