#!/usr/bin/python

import config
from nomops import *
from time import sleep

extra_wait = 7.0

cfg = custom_cfg(config.hosts_std)
disp(cfg)

#cfg['save_nomic'] = False

# nod pair 1
request('Search for setpoint (run setpoint script?) and hit return when done.'); raw_input()
take_null(cfg)

nod(cfg, 'up')
sleep(extra_wait)
wait_phase_loop(cfg)

request('Search for setpoint (run setpoint script?) and hit return when done.'); raw_input()
take_null(cfg)

# nod pair 2
nod(cfg, 'down')
sleep(extra_wait)
wait_phase_loop(cfg)

request('Search for setpoint (run setpoint script?) and hit return when done.'); raw_input()
take_null(cfg)

nod(cfg, 'up')
sleep(extra_wait)
wait_phase_loop(cfg)

request('Search for setpoint (run setpoint script?) and hit return when done.'); raw_input()
take_null(cfg)

# nod pair 3
nod(cfg, 'down')
sleep(extra_wait)
wait_phase_loop(cfg)

request('Search for setpoint (run setpoint script?) and hit return when done.'); raw_input()
take_null(cfg)

nod(cfg, 'up')
sleep(extra_wait)
wait_phase_loop(cfg)

request('Search for setpoint (run setpoint script?) and hit return when done.'); raw_input()
take_null(cfg)

# photometry
nod(cfg, 'down', side='left')
sleep(extra_wait)
wait_AO_loop(cfg, take_bkg=False)

sleep(extra_wait)
take_photometry(cfg)

# background
nod(cfg, 'up', side='left')
sleep(extra_wait)
wait_AO_loop(cfg, take_bkg=False)

offset_background(cfg, 'up')
wait_AO_loop(cfg, take_bkg=False)

sleep(extra_wait)
take_background(cfg)

#resetting for new observation on this target

offset_background(cfg, 'down')
wait_AO_loop(cfg, take_bkg=False)
sleep(extra_wait)
sleep(extra_wait)
sleep(extra_wait)
nod(cfg, 'down')
wait_AO_loop(cfg, take_bkg=False)


request('Done, restart script or preset to next target.')

