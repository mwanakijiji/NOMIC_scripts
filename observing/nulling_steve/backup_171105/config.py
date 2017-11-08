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
- nomic_dither_opd: bool, True to enable OPD dithering, False otherwise
- nomic_dither_opd_ndits: list of ints, number of frames taken at each OPD dither position (starts integrating first, then sends first offset)
- nomic_dither_opd_off0: first offset from nominal setpoint for OPD dither pattern (if 0.0, first integration starts at nominal setpoint)
- nomic_dither_opd_pattern: list of floats, offsets to perform OPD dither pattern (starts integrating first, then sends first offset), Unit: rad at 11um
- nomic_nsequences_null: int, number of integrations per sequence
- save_lmircam: bool, True for saving frames from LMIRCAM, False otherwise
- save_nomic: bool, True for saving frames from nomic, False otherwise

Telescope controls:
- nod_throw: float, length of a single nod offset in arcsec
""" 

#===============================================================================
#===============================================================================
hosts_std = {} # Standard configuration file for HOSTS nulling observations
#===============================================================================

# Telescope controls:
hosts_std['phasecam_beam2_offset_nod']        = 2            # int, offset of PHASECAM's beam 2 after a nod (in pixels)
hosts_std['nod_throw']                        = 2.3          # float, length of a single nod offset in arcsec
hosts_std['off_throw']                        = 5.0          # float, length of a single offset in arcsec used to take background frames
hosts_std['opw_offset_nod']                   = 1300         # int, offset of the PHASECAM pupil wheel after a nod
hosts_std['pzt']                              = 'UBC'        # string, 'UBC' or 'NAC', defines which PZTs to use

# Camera controls:
hosts_std['nomic_dither_opd']                 = True         # bool, True to enable OPD dithering, False otherwise
hosts_std['nomic_dither_opd_ndits']           = [50, 50, 50, 50]   # list of ints, number of frames taken at each OPD dither position (starts integrating first, then sends first offset)
hosts_std['nomic_dither_opd_off0']            = 0.0          # first offset from nominal setpoint for OPD dither pattern (if 0.0, first integration starts at nominal setpoint)
hosts_std['nomic_dither_opd_pattern']         = [-0.2, 0.2, 0.2, -0.2]   # list of floats, offsets to perform OPD dither pattern (starts integrating first, then sends first offset), Unit: rad at 11um
hosts_std['nomic_nsequences_bkgd']            = 1000         # int, maximum number of integrations for background
hosts_std['nomic_nsequences_dark']            = 500          # int, number of dark frames to be taken 
hosts_std['nomic_nsequences_null']            = 2000         # int, number of integrations per nod for nulling observations
hosts_std['nomic_nsequences_phot']            = 500          # int, number of integrations for photometry
hosts_std['nomic_nwait_phase_loop']           = 100          # int, number of background frames taken in a row while waiting for phase loop to close
hosts_std['nomic_nwait_AO_loop']              = 100          # int, number of background frames taken in a row while waiting for AO loop to close
hosts_std['save_lmircam']                     = False        # bool, True for saving frames from LMIRCAM, False otherwise
hosts_std['save_nomic']                       = True         # bool, True for saving frames from NOMIC, False otherwise

# Setpoint controls:
hosts_std['nomic_setpoint_img_stack']         = 3            # int, number of images stacked in one OPD position for flux computation during setpoint search
hosts_std['nomic_setpoint_max_step']          = 45           # Maximum single step width to change the setpoint, set to HUGE number for no constraint.
hosts_std['nomic_setpoint_n_confirm']         = 2            # Number of successful setpoint confirmations required
hosts_std['nomic_setpoint_n_scan']            = 5            # int, ODD NUMBER, number of OPD steps to scan for setpoint search
hosts_std['nomic_setpoint_output']            = 'none'       # string, 'screen', 'file', 'both', or 'none', indicates if and how to plot during setpoint search
hosts_std['nomic_setpoint_savedata']          = False        # bool, True for saving frames from NOMIC during setpoint search
hosts_std['nomic_setpoint_scan_range']        = [-360,360]   # vector of two int, range of setpoints to scan around initial setpoint in deg

#===============================================================================
#===============================================================================

