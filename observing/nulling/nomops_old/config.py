# This is the configuration file. Define input parameters here.

"""
The routine config.py contains full sets of input parameters for the
functions provided by the nomops package. Each set of parameters is stored
in a python dictionary.

Usage (example):
 >> from nompos import *       # optional
 >> import config
 >> print(config.hosts_std['nod_throw']

You can modify single entries in a config dictionary:
 >> config.hosts_std['nod_throw'] = 1.5

However, it is good practice to make a copy of the config first so the
original can be reloaded if needed. nomops provides a command for that:
 >> my_cfg = custom_cfg(config.hosts_std)

There is also a pretty print command available from nomops (just making
use of the PyINDI ppD command):
 >> disp(config.hosts_std)

Currently available configurations:
- hosts_std: Standard configuration file for HOSTS nulling observations

List of entries in each configuration dictionary:
=================================================
Camera controls:
- nomic_nsequences_null: int, number of integrations per sequence
- save_lmircam: bool, True for saving frames from LMIRCAM, False otherwise
- save_nomic: bool, True for saving frames from nomic, False otherwise

Telescope controls:
- nod_throw: float, length of a single nod offset in arcsec
""" 

hosts_std = {} # Standard configuration file for HOSTS nulling observations
# Telescope controls:
hosts_std['nod_throw'] = 1.3                     # float, length of a single nod offset in arcsec
# Camera controls:
hosts_std['nomic_nsequences_null'] = 1000        # int, number of integrations per sequence
hosts_std['save_lmircam'] = False                # bool, True for saving frames from LMIRCAM, False otherwise
hosts_std['save_nomic'] = True                   # bool, True for saving frames from nomic, False otherwise


cfg_1 = {}
cfg_1['a'] = 5.0
cfg_1['b'] = 2.0

cfg_2 = {}
cfg_2['a'] = 2.0
cfg_2['b'] = 1.0

