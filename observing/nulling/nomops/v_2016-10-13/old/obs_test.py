#!/usr/bin/python

from nomops import *

cfg = custom_cfg(config.hosts_std)

cfg['save_nomic'] = False
cfg['nomic_nsequences_null'] = 500
cfg['nomic_nsequences_bkgd'] = 100
cfg['nomic_nsequences_phot'] = 50

#take_null(cfg)
#sleep(10)
#take_background(cfg)
#sleep(10)
#take_photometry(cfg)
#sleep(10)
wait_phase_loop(cfg)
sleep(10)
take_photometry(cfg)

