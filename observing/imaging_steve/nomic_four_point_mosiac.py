#!/usr/bin/python

# Quick script to do a four point mosaicking with NOMIC (plus one sky offset, so five positions in total).
# Instructions:
# 1) Preset to target, close both AO loops.
# 2) Put target in the upper-left position of the mosaic.
# 3) Set up camera (DIT, n_sequences).
# 4) Modify parameters below to set nodding and sky offset distances and telescope side to use.
# 5) Run script with >> ./nomic_four_point_mosaic.py

from pyindi import * 
import numpy as np

#===============================
# Parameters(modify as needed):
#===============================
savedata = 1        # Want to save data? (0 = No!, 1 = Yes!)
del_x = 8.5         # offset in x direction [arcsec], absolute (positive) value
del_y = 12.0        # offset in y direction [arcsec], absolute (positive) value
offset_sky = 20.0   # offset to sky (down from the lower-left position) [arcsec], absolute (positive) value
side = 'left'       # which side to use ('left' or 'right')
n_cycles = 5        # number of nodding cycles
#===============================

pi = PyINDI()
  
# Set up camera for integration.
pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)

# cycle through nod positions
offsets = [[del_x, 0], [0, -del_y], [-del_x, 0], [0, -offset_sky], [0, offset_sky + del_y]]

for i_cycles in range(n_cycles):
  print ''
  print 'Starting nodding cycle ' + str(i_cycle + 1) + ' of ' + str(n_cycles) + '.'
  for i_pos in range(5):
    print '  Position ' + str(i_pos + 1) + ' of 5.'
    # Integrate
    sleep(0.3)
    pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
    
    # Use background.
    sleep(0.3)
    pi.setINDI('NOMIC.Command.text', 'rawbg', timeout=50000, wait=True)
    
    # Nod the telescope
    pi.setINDI('LBTO.OffsetPointing.CoordSys', 'DETXY', 'LBTO.OffsetPointing.OffsetX', offsets[i][0], 'LBTO.OffsetPointing.OffsetY', offsets[i][1], 'LBTO.OffsetPointing.Side', side, 'LBTO.OffsetPointing.Type', 'REL', wait=True)

print 'Script finished.'
