#!/usr/bin/python

import config
from nomops import *
from time import sleep

cfg = custom_cfg(config.hosts_std)

take_darks(cfg)

