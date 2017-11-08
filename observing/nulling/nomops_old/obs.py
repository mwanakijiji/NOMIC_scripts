#!/usr/bin/python

import config
from nomops import *

cfg = custom_cfg(config.hosts_std)
disp(cfg)

cfg['save_nomic'] = False

for n_test in range(0, 100):
  print '===================='
  print 'Test number ', n_test + 1
  print '===================='
  take_null(cfg)

