#!/usr/bin/python
#Darks/flats/linearity script
#DD-130617
#DD-150207-increased sleep time per Bill's recommendation
#DD-151222-now change object name

# Note (Eckhart, Denis & Steve, 05/16/2017): As of 20170331, a good combination of filters to use for finely-sampled linearity data is N07904-9N_070 and W-10145-9. Change the for-loops below to 'range(200)'.

import time
from pyindi import * 

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=True)

#turn on save data
pi.setINDI("NOMIC.Command.text", "1 savedata 1 autodispwhat 0 loglevel", wait=True)

#set object name
pi.setINDI("NOMIC.EditFITS.Keyword=OBJNAME;Value=test;Comment=Object name")

#set filters to flat
#pi.setINDI("Warm.NOMIC_FW1.command", "Nprime", timeout=20, wait=True)
pi.setINDI("NOMIC.EditFITS.Keyword=FLAG;Value=FLT;Comment=SCI/CAL/DRK/FLT")

#save frames
for j in range(200):
	print float(j+1)*0.007
	pi.setINDI("NOMIC.Command.text", "%f 1 10 lbtintpar 2000 sleep" % ((j+1)*0.007), timeout=300, wait=True)
	pi.setINDI("NOMIC.Command.text", "go", timeout=3000, wait=True)
	
#set filters to dark
pi.setINDI("Warm.NOMIC_FW2.command", "Blank+tape", timeout=20, wait=True)
pi.setINDI("NOMIC.EditFITS.Keyword=FLAG;Value=DRK;Comment=SCI/CAL/DRK/FLT")

#save frames
for j in range(200):
	print float(j+1)*0.007
	pi.setINDI("NOMIC.Command.text", "%f 1 10 lbtintpar 2000 sleep" % ((j+1)*0.007), timeout=300, wait=True)
	pi.setINDI("NOMIC.Command.text", "go", timeout=3000, wait=True)

#turn off save data
pi.setINDI("NOMIC.Command.text", "0 savedata 1 autodispwhat 1 loglevel")

