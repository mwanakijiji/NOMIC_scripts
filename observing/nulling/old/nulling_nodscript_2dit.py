#!/usr/bin/python
#nulling sequence script
#DD-130916
#DD-140310: added home for NIL_OPW
#DD-141003: added time delay in wait4AOrunning
#DD-141104: added continuous acquisition between nods
#DD-141109: added option for LMIRCAM // observation
#DD-141110: added 16-bit acquisition for low number of coadds
#DD-150201: added option for second DIT
#DD-150202: added nodding direction parameter
#DD-150203: added the possibility to skip the photometry
#DD-150204: improved speed
#DD-150302: now send command to NOMIC/LMIRCam in one line for speed
#DD-160217: now take data while waiting for AO (background bias minimization)

from pyindi import * 
import os 
import time

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=False)

def wait4AOrunning():
	while True:
		pi.setINDI("LBTO.Dictionary.Name=L_AOStatus;Value=")
		lstatus = pi.getINDI("LBTO.Dictionary.Value")
		pi.setINDI("LBTO.Dictionary.Name=R_AOStatus;Value=")
		rstatus = pi.getINDI("LBTO.Dictionary.Value")
		print lstatus, rstatus
		time.sleep(0.02)
		if rstatus == "AORunning" and lstatus == "AORunning":
			break

# Running parameters
n_nod     = 2   # Number of nod pairs before the photometry
offy      = 2.3 # Nodding y offset in arcsec
sign      = 1   # Nodding direction (-1 for up -> down, 1 for down -> up) 
save      = 0   # Whether to save (=1) or not (=0)
skip_phot = 0   # 1 to skip the photometry
sleep     = 0.2 # Sleep time before GO (mandatory for stability)
       
#Running parameters NOMIC
dit_n1  = 0.036
dit_n2  = 0           # 0 to turn off double DIT
n_coadd = 1
n_null1 = 1000        # number of frames per nod for DIT1
n_null2 = 1000	      # number of frames per nod for DIT2
n_phot1 = 200
n_phot2 = 0
n_bckg  = 200

#Running parameters LMIRCAM
dit_l   = 0       # 0 to turn off LMIRCAM data acquisition
n_spec  = 100
n_fr    = 100
n_bg_l  = 100  

#Set fits header to nulling (obstype = 2) and spectro (obstype = 1)
pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=2;Comment=observation type", wait=False)
if dit_l > 0:
	pi.setINDI("LMIRCAM.EditFITS.Keyword=OBSTYPE;Value=1;Comment=observation type", wait=False)

#Get current NIL_OPW position
opw_pos = pi.getINDI("Warm.NIL_OPW_status.PosNum", wait=False)

# NULLING SEQUENCE
# Loop over the nod positions
for j in range(n_nod):
	
	# NULL SEQUENCE (Nod down)
	#Turn off log, contacq, save data, and display + set integration parameters
	pi.setINDI("NOMIC.Command.text", "0 loglevel 0 contacq %i savedata 0 autodispwhat %f %i %i lbtintpar" % (save, dit_n1, n_coadd, n_null1), wait=True)
	time.sleep(sleep)
	if dit_l > 0:
		pi.setINDI("LMIRCAM.Command.text", "0 loglevel 0 contacq %i savedata %f %i %i lbtintpar" % (save, dit_l, n_coadd, n_spec), wait=True)
		pi.setINDI("LMIRCAM.Command.text", "go", timeout=500, wait=False)		
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)
	if dit_n2 > 0:	
		pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar" % (dit_n2, n_coadd, n_null2), timeout=150, wait=True)
		time.sleep(sleep)
		pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)	
	# Open phase loop
	pi.setINDI("PLC.CloseLoop.Yes=Off")
	
	# NULL SEQUENCE (Nod up)
	# Move OPW
	# pi.setINDI("Warm.NIL_OPW.command", "_home_", timeout=20, wait=True)  # Home not working as of Nov 2014
	pi.setINDI("Warm.NIL_OPW.command",  "%i" % (opw_pos-sign*1500), wait=False)
	#Nod the telescope
	pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY","LBTO.OffsetPointing.OffsetX", 0, "LBTO.OffsetPointing.OffsetY", (sign*offy), "LBTO.OffsetPointing.Side", "both", "LBTO.OffsetPointing.Type", "REL", wait=False) 
	#Set integration parameters back to 1 frame (and take background)
	if dit_l > 0:
		pi.setINDI("LMIRCAM.Command.text", "rawbg", timeout=50000, wait=True) # This fails for some reason
		pi.setINDI("LMIRCAM.Command.text", "%f %i %i lbtintpar" % (dit_l, n_coadd, 1), timeout=150, wait=False)
	pi.setINDI("NOMIC.Command.text", "rawbg 1 autodispwhat", timeout=50000, wait=True)
	time.sleep(sleep)
	#Take frames
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)

	# Turn on display, don't save data, continuous acquisition
	pi.setINDI("NOMIC.Command.text", " 0 savedata 1 contacq", wait=True)
	if dit_l > 0:	
		pi.setINDI("LMIRCAM.Command.text", "0 savedata 1 contacq", wait=False)
	# Take nulling data while waiting for AO and phase loops
	# pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)
	#Now pause to recover fringes
	input("Press 1")
	#Turn off contacq, save data, and turn off display
	pi.setINDI("NOMIC.Command.text", "0 contacq %i savedata 0 autodispwhat %f %i %i lbtintpar" % (save, dit_n1, n_coadd, n_null1), timeout=100, wait=True)
	if dit_l > 0:	
		pi.setINDI("LMIRCAM.Command.text", "0 contacq %i savedata %f %i %i lbtintpar" % (save, dit_l, n_coadd, n_spec), timeout=100, wait=True)
		pi.setINDI("LMIRCAM.Command.text", "go", timeout=500, wait=False)
	time.sleep(1)		
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)
	if dit_n2 > 0:
		pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar" % (dit_n2, n_coadd, n_null2), timeout=150, wait=True)
		time.sleep(0.5)	
		pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)	
	# Open phase loop
	pi.setINDI("PLC.CloseLoop.Yes=Off")

	#Nod the telescope (except for last nod)
	if j != n_nod-1:
		# Move OPW
		# pi.setINDI("Warm.NIL_OPW.command", "_home_", timeout=20, wait=True)  # Home not working as of Nov 2014
	        pi.setINDI("Warm.NIL_OPW.command",  "%i" % (opw_pos), wait=False)
		# Nod telescope
		pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY","LBTO.OffsetPointing.OffsetX", 0, "LBTO.OffsetPointing.OffsetY", (-1*sign*offy), "LBTO.OffsetPointing.Side", "both", "LBTO.OffsetPointing.Type", "REL", timeout=150, Wait=False) 
		#Set integration parameters back to 1 frame
		if dit_l > 0:	
			# pi.setINDI("LMIRCAM.Command.text", "rawbg", timeout=50000, wait=True) # This fails for some reason	
			pi.setINDI("LMIRCAM.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit_l, n_coadd, 1), timeout=150, wait=True)
			pi.setINDI("LMIRCAM.Command.text", "0 savedata 1 contacq", wait=False)
		pi.setINDI("NOMIC.Command.text", "rawbg 100 sleep", timeout=50000, wait=True)
		pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit_n1, n_coadd, 1), timeout=150, wait=True)
		# Turn on display, don't save data, continuous acquisition
		pi.setINDI("NOMIC.Command.text", "1 autodispwhat 0 savedata 1 contacq", wait=True)			
		#Now pause to recover fringes
		input("Press 1")

		
# PHOTOMETRY SEQUENCE
if skip_phot < 1:
	#Nod one telescope
	pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY","LBTO.OffsetPointing.OffsetX", 0, "LBTO.OffsetPointing.OffsetY", (-1*sign*offy), "LBTO.OffsetPointing.Side", "right", "LBTO.OffsetPointing.Type", "REL", timeout=150, Wait=False)
	#Set fits header (OBSTYPE=0 for photometry)
	pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=0;Comment=observation type")
	if dit_l > 0:
		pi.setINDI("LMIRCAM.EditFITS.Keyword=OBSTYPE;Value=0;Comment=observation type")
	#Set integration parameters back to 1 frame
	if dit_l > 0:
		pi.setINDI("LMIRCAM.Command.text", "rawbg", timeout=50000, wait=True)
		pi.setINDI("LMIRCAM.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit_l, n_coadd, 1), timeout=150, wait=True)
	pi.setINDI("NOMIC.Command.text", "rawbg", timeout=50000, wait=True)
	pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar" % (dit_n1, n_coadd, 1), timeout=15, wait=True)
	# Turn on display, don't save data, continuous acquisition
	pi.setINDI("NOMIC.Command.text", "1 autodispwhat 0 savedata 1 contacq", wait=False)
	if dit_l > 0:
		pi.setINDI("LMIRCAM.Command.text", "0 savedata 1 contacq", wait=False)
	#Now pause to recover AO
	wait4AOrunning()
	#Turn off contacq, save data, and turn off display
	pi.setINDI("NOMIC.Command.text", "0 contacq %i savedata 0 autodispwhat %f %i %i lbtintpar" % (save,dit_n1, n_coadd, n_phot1), wait=False)
	if dit_l > 0:
		pi.setINDI("LMIRCAM.Command.text", "0 contacq %i savedata %f %i %i lbtintpar" % (save, dit_l, n_coadd, n_fr), wait=True)
		pi.setINDI("LMIRCAM.Command.text", "go", timeout=500,wait=False)
	time.sleep(1)
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000,wait=True)	
	if dit_n2 > 0:
		pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit_n2, n_coadd, n_phot2), timeout=15, wait=True)
		pi.setINDI("NOMIC.Command.text", "go", timeout=50000,wait=True)	

	# SHORT BACKGROUND SEQUENCE
	#Nod the telescope
	pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY","LBTO.OffsetPointing.OffsetX", 0, "LBTO.OffsetPointing.OffsetY", 5, "LBTO.OffsetPointing.Side", "both", "LBTO.OffsetPointing.Type", "REL", timeout=150, Wait=False) 
	#Set fits header
	pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=3;Comment=observation type")
	if dit_l > 0:
		pi.setINDI("LMIRCAM.EditFITS.Keyword=OBSTYPE;Value=3;Comment=observation type")
	#Set integration parameters back to 1
	if dit_l > 0:
		pi.setINDI("LMIRCAM.Command.text", "rawbg", timeout=50000, wait=True)
		pi.setINDI("LMIRCAM.Command.text", "%f %i %i lbtintpar" % (dit_l, n_coadd, 1), timeout=150, wait=False)
	pi.setINDI("NOMIC.Command.text", "rawbg", timeout=50000, wait=True)
	pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit_n1, n_coadd, 1), timeout=15, wait=True)
	# Turn on display, don't save data, continuous acquisition
	pi.setINDI("NOMIC.Command.text", "1 autodispwhat 0 savedata 1 contacq", wait=True)
	if dit_l > 0:
		pi.setINDI("LMIRCAM.Command.text", "0 savedata 1 contacq", wait=True)
	#Now pause to recover fringes
	wait4AOrunning()
	#Turn off contacq, save data, and turn off display
	pi.setINDI("NOMIC.Command.text", "0 contacq 0 autodispwhat %i savedata %f %i %i lbtintpar" % (save, dit_n1, n_coadd, n_bckg), wait=True)
	if dit_l > 0:
		pi.setINDI("LMIRCAM.Command.text", "0 contacq %i savedata %f %i %i lbtintpar" % (save, dit_l, n_coadd, n_bg_l), wait=True)
		pi.setINDI("LMIRCAM.Command.text", "go", timeout=500, wait=False)
	time.sleep(1)			
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)
	if dit_n2 > 0:
		pi.setINDI("NOMIC.Command.text", "%f %i %i lbtintpar 500 sleep" % (dit_n2, n_coadd, n_bckg), timeout=15, wait=True)
		pi.setINDI("NOMIC.Command.text", "go", timeout=50000,wait=True)
	

#Restore log information and turn off data saving
pi.setINDI("NOMIC.Command.text", "1 loglevel 0 savedata", wait=False)
if dit_l > 0:
	pi.setINDI("LMIRCAM.Command.text", "1 loglevel 0 savedata", wait=False)
