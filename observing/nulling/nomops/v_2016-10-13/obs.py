#!/usr/bin/python

import config
from nomops import *

cfg = custom_cfg(config.hosts_std)
disp(cfg)

cfg['save_nomic'] = False

take_null(cfg)

