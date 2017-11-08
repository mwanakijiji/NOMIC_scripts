#!/usr/bin/python
#NAC nulling sequence script
#DD-140528

from pyindi import * 
import os 

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=False)
		
#Running parameters
dit    = 0.028
ncoadd = 1
n_null = 2500
n_phot = 2500
n_bckg = 500
n_seq  = 2

#turn off contacq
pi.setINDI("NOMIC.Command.text", "0 contacq")

#turn on save data
pi.setINDI("NOMIC.Command.text", "1 savedata")

#set fits header to nulling
pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=2;Comment=observation type")
#pi.setINDI("LMIRCAM.EditFITS.Keyword=OBSTYPE;Value=1;Comment=observation type")

#set integration parameters
pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit, ncoadd, n_null), timeout=15)

#get NIL_OPW position
#opw_pos = pi.getINDI("Warm.NIL_OPW.*")

#Loop over the sequences
for j in range(n_seq):
	
	# NULL SEQUENCE (Nod down)
	# Take data (assumed that we are at null in the bottom chop position when executing the script)
	#pi.setINDI("LMIRCAM.Command.text", "go", timeout=500,wait=False)		
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000,wait=True)		
	# Open phase loop
	pi.setINDI("PLC.CloseLoop.Yes=Off")
	
	# NULL SEQUENCE (Nod up)
	#Now pause to recover fringes
	input("Press 1")
	# Take data (assumed that we are at null in the bottom chop position when executing the script)
	#pi.setINDI("LMIRCAM.Command.text", "go", timeout=500,wait=False)
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000,wait=True)
	# Open phase loop
	pi.setINDI("PLC.CloseLoop.Yes=Off")
		
# PHOTOMETRY SEQUENCE
#set fits header
pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=0;Comment=observation type")
#set integration parameters
pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit, ncoadd, n_phot), timeout=15)
# Take data (assumed that we are at null in the bottom chop position when executing the script)
pi.setINDI("NOMIC.Command.text", "go", timeout=50000,wait=True)	

# BACKGROUND SEQUENCE
#set fits header
pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=3;Comment=observation type")
#set integration parameters
pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit, ncoadd, n_bckg), timeout=15)
# Take data (assumed that we are at null in the bottom chop position when executing the script)
pi.setINDI("NOMIC.Command.text", "go", timeout=50000,wait=True)

#turn off save data
pi.setINDI("NOMIC.Command.text", "0 savedata")
