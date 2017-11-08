#!/usr/bin/python
# move SPC piston until PLC reports SNR is good

from pyindi import *
pi = PyINDI()

steps_per_micron = 50	# scale
microns = 20 		# microns

cmd = ">" + str(steps_per_micron*microns)

snrok = 0
while (snrok < 1):
    pi.setINDI("Ubcs.SPC_TRANS.command", cmd, timeout=10)
    snrok = pi.getINDI("PLC.PCamHeader.PCFTOK")
    print snrok
