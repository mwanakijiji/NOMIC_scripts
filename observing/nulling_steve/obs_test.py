#!/usr/bin/python

import config
from nomops import *
from time import sleep

extra_wait = 7.0

cfg = custom_cfg(config.hosts_std)
disp(cfg)

#cfg['save_nomic'] = False

# nod pair 1
take_null(cfg)
