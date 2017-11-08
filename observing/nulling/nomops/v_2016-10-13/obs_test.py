#!/usr/bin/python

from nomops import *

cfg = custom_cfg(config.hosts_std)

cfg['save_nomic'] = False
cfg['nomic_nsequences_null'] = 500
cfg['nomic_nsequences_bkgd'] = 100
cfg['nomic_nsequences_phot'] = 50

take_null(cfg)

info('Test info, waiting 30 sec')

sleep(30)

take_photometry(cfg)

request('Test request, waiting 30 sec')

sleep(30)

take_background(cfg)

