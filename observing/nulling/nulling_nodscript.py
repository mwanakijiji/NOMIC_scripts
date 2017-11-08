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
#DD-160219: moved LMIRCam and second DIT options to separate scripts in order to maximize efficiency 
#DD-160219: added wait delay before taking data (allow for beams to move out of the way)
#DD-160325: added option to choose between NAC and UBC
#DD-160413: added a limit on number of background frames taken between null nods + restored confirm statement
# SE - 2016-04-25 -- Changed the way the "ask for manual confirmation" is done. Now more intuitive and consistent with setpoint script.
# SE - 2016-04-27 -- ROIs on NOMIC display now move with the nods.
# SE - 2016-04-29 -- Correct a bug in the camera setups that left the camera in continuous acquisition of sequences of many frames.

# import Python libraries
from pyindi import * 
import os 
import time
import numpy as np

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=False)

# Define AO waiting function
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
n_nod     = 1     # Number of nod pairs before the photometry
offy      = 2.3   # Nodding y offset in arcsec (up-down)
sign      = 1     # Nodding direction (-1 for up -> down, 1 for down -> up) 
save      = 1     # Whether to save (=1) or not (=0)
skip_phot = 0     # 1 to skip the photometry
sleep     = 0.5   # Sleep time before GO (mandatory for stability)
sleep_ao  = 3.5   # Sleep before we take data after nodding. !!! Must be at least 3.5 seconds !!!! (as of February 2016)
offset_b2 = 2     # Offset of PHASECAM's beam 2 between the two nod positions (in pixels)
pzt       = 'UBC' # Specified which PZTs are used ("NAC" or "UBC")      

#Integration parameters 
dit     = 0.0287
n_coadd = 1
n_null  = 1000         # number of frames per nod for DIT (default is 1000)
n_wait  = 100          # number of frames to take while we wait for phase loop to close (default is 100)
n_phot  = 500          # number of photometric frames (default is 200)
n_bckg  = n_null       # number of background frames at the end (default is n_phot)

# ROI info
ROIIDs = [1,2,3]
ROI_nod = np.int(offy / 0.018)     # Nodding offset in pix

# Confirm initial ROI positions
if raw_input("Now move ROIs into position and run setpoint script. Press [ENTER] when done or [c] + [ENTER] to abort. ") == "c": quit()

#Set fits header to nulling (obstype = 2)
pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=2;Comment=observation type", wait=False)

#Set integration parameters
pi.setINDI("NOMIC.Command.text", "0 contacq 0 loglevel %i savedata %f %i %i lbtintpar" % (save, dit, n_coadd, n_null), wait=True)

#Get current NIL_OPW position
opw_pos = pi.getINDI("Warm.NIL_OPW_status.PosNum", wait=False)

#Get beam 2 Y position
settings  = pi.getINDI('PLC.%sSettings.*' % (pzt), wait=True)
beam2_y   = settings["PLC.%sSettings.Beam2_y" % (pzt)]

# NULLING SEQUENCE
# Loop over the nod positions
for j in range(n_nod):
	
	# NULL SEQUENCE (Nod down)
	#Turn off log, contacq, save data, and display + set integration parameters
	pi.setINDI("NOMIC.Command.text", "0 contacq 0 autodispwhat %i obssequences %i savedata" % (n_null, save), wait=True)
	time.sleep(sleep)   # Mandatory to avoid crash (despite the wait=True above)
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)
	
	# Open phase loop
	pi.setINDI("PLC.CloseLoop.Yes=Off")
	
	# Move OPW
	# pi.setINDI("Warm.NIL_OPW.command", "_home_", timeout=20, wait=True)  # Home not working as of Nov 2014
	pi.setINDI("Warm.NIL_OPW.command",  "%i" % (opw_pos-sign*2500), wait=False)
		
	# Nod the telescope
	pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY","LBTO.OffsetPointing.OffsetX", 0, "LBTO.OffsetPointing.OffsetY", (sign*offy), "LBTO.OffsetPointing.Side", "both", "LBTO.OffsetPointing.Type", "REL", wait=False)
	
	# Move ROI positions
	for i in range(0, len(ROIIDs)):
		qroi = dict([('NOMIC.QueryROI.ROIID', ROIIDs[i]), ('NOMIC.QueryROI.X', 0.0), ('NOMIC.QueryROI.Y', 0.0), ('NOMIC.QueryROI.H', 0.0), ('NOMIC.QueryROI.W', 0.0)])
		pi.setINDI(qroi)
		qroi = pi.getINDI('NOMIC.QueryROI.ROIID', 'NOMIC.QueryROI.X', 'NOMIC.QueryROI.Y', 'NOMIC.QueryROI.H', 'NOMIC.QueryROI.W')
		droi = dict([('NOMIC.DefROI.ROIID', ROIIDs[i]), ('NOMIC.DefROI.X', qroi['NOMIC.QueryROI.X']), ('NOMIC.DefROI.Y', qroi['NOMIC.QueryROI.Y'] + sign * ROI_nod), ('NOMIC.DefROI.H', qroi['NOMIC.QueryROI.H']), ('NOMIC.DefROI.W', qroi['NOMIC.QueryROI.W'])])
		pi.setINDI(droi)
	
	# Move beam 2 position
	settings['PLC.%sSettings.Beam2_y' % (pzt)] = beam2_y + offset_b2
	pi.setINDI(settings) 
	
	# Turn on display (and take background)
	pi.setINDI("NOMIC.Command.text", "rawbg 1 autodispwhat %i obssequences" % (n_wait), timeout=50000, wait=True)
	time.sleep(sleep_ao)
	
	# Take frames immediately (background bias minimization)
	# Take frame while phase loop is open
	n_done = 0 
	while n_done < n_null and not pi.getINDI("PLC.CloseLoop.Yes"):
		pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)
		n_done += n_wait		

	# Go into continuous mode
	pi.setINDI("NOMIC.Command.text", "1 obssequences 0 savedata")
        time.sleep(sleep)
	pi.setINDI("NOMIC.Command.text", "1 obssequences 1 contacq", timeout=50000, wait=True)	
	
        # Ask to run setpoint script
	if raw_input("Confirm that phase loop is stable and run setpoint script. Press [ENTER] when done or [c] + [ENTER] to abort. ") == "c": quit()

	# Now take null sequence
	pi.setINDI("NOMIC.Command.text", "0 contacq 0 autodispwhat %i obssequences %i savedata" % (n_null, save), wait=True)
	time.sleep(sleep)   # Mandatory to avoid crash (despite the wait=True above)
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)
	
	# Open phase loop
	pi.setINDI("PLC.CloseLoop.Yes=Off")

	#Nod the telescope (except for last nod)
	if j != n_nod-1:
		# Move OPW
		# pi.setINDI("Warm.NIL_OPW.command", "_home_", timeout=20, wait=True)  # Home not working as of Nov 2014
		pi.setINDI("Warm.NIL_OPW.command",  "%i" % (opw_pos), wait=False)
		
		# Nod telescope
		pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY","LBTO.OffsetPointing.OffsetX", 0, "LBTO.OffsetPointing.OffsetY", (-1*sign*offy), "LBTO.OffsetPointing.Side", "both", "LBTO.OffsetPointing.Type", "REL", timeout=150, wait=False) 
		
		# Move ROI positions
		for i in range(0, len(ROIIDs)):
			qroi = dict([('NOMIC.QueryROI.ROIID', ROIIDs[i]), ('NOMIC.QueryROI.X', 0.0), ('NOMIC.QueryROI.Y', 0.0), ('NOMIC.QueryROI.H', 0.0), ('NOMIC.QueryROI.W', 0.0)])
			pi.setINDI(qroi)
			qroi = pi.getINDI('NOMIC.QueryROI.ROIID', 'NOMIC.QueryROI.X', 'NOMIC.QueryROI.Y', 'NOMIC.QueryROI.H', 'NOMIC.QueryROI.W')
			droi = dict([('NOMIC.DefROI.ROIID', ROIIDs[i]), ('NOMIC.DefROI.X', qroi['NOMIC.QueryROI.X']), ('NOMIC.DefROI.Y', qroi['NOMIC.QueryROI.Y'] - sign * ROI_nod), ('NOMIC.DefROI.H', qroi['NOMIC.QueryROI.H']), ('NOMIC.DefROI.W', qroi['NOMIC.QueryROI.W'])])
			pi.setINDI(droi)

		# Move beam 2 position
		settings['PLC.%sSettings.Beam2_y' % (pzt)] = beam2_y
		pi.setINDI(settings)
		
		#Set integration parameters back to 1 frame
		pi.setINDI("NOMIC.Command.text", "rawbg 1 autodispwhat %i obssequences" % (n_wait), timeout=50000, wait=True)
		time.sleep(sleep_ao)
		
		# Take frames immediately (background bias minimization)
		# Take frame while phase loop is open
		n_done = 0
		while n_done < n_null and not pi.getINDI("PLC.CloseLoop.Yes"):
			pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)
			n_done += n_wait 
	        
		# Go into continuous mode
	        pi.setINDI("NOMIC.Command.text", "1 obssequences 0 savedata")
        	time.sleep(sleep)
        	pi.setINDI("NOMIC.Command.text", "1 contacq", timeout=50000, wait=True) 
	
		# Ask for confirmation
		if raw_input("Confirm that phase loop is stable and run setpoint script. Press [ENTER] when done or [c] + [ENTER] to abort. ") == "c": quit()

# Move OPW
# pi.setINDI("Warm.NIL_OPW.command", "_home_", timeout=20, wait=True)  # Home not working as of Nov 2014
pi.setINDI("Warm.NIL_OPW.command",  "%i" % (opw_pos), wait=False)
		
# PHOTOMETRY SEQUENCE
if skip_phot < 1:
	#Nod one telescope
	pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY","LBTO.OffsetPointing.OffsetX", 0, "LBTO.OffsetPointing.OffsetY", (-1*sign*offy), "LBTO.OffsetPointing.Side", "right", "LBTO.OffsetPointing.Type", "REL", timeout=150, wait=False)
	
	#Set fits header (OBSTYPE=0 for photometry)
	pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=0;Comment=observation type")

	# Take background
	pi.setINDI("NOMIC.Command.text", "rawbg 1 autodispwhat 1 obssequences 0 savedata 1 contacq", timeout=50000, wait=True)
	
	#Now pause to recover AO
	wait4AOrunning()
	
	#Turn off contacq, save data, and turn off display
	pi.setINDI("NOMIC.Command.text", "0 contacq 0 autodispwhat %i obssequences %i savedata" % (n_phot, save), timeout=50000, wait=True)
	time.sleep(sleep+1.0)
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000,wait=True)	

	# SHORT BACKGROUND SEQUENCE
	#Set fits header (OBSTYPE=3 for background)
	pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=3;Comment=observation type")

	#Nod the telescope
	pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY","LBTO.OffsetPointing.OffsetX", 0, "LBTO.OffsetPointing.OffsetY", 5, "LBTO.OffsetPointing.Side", "both", "LBTO.OffsetPointing.Type", "REL", timeout=150, wait=False) 
	
	#Turn off contacq, save data, and turn off display. NOTE: This comment seems outdated, this is NOT what the next line is doing!
	pi.setINDI("NOMIC.Command.text", "rawbg 1 autodispwhat 1 obssequences 0 savedata 1 contacq", timeout=50000, wait=True)

	#Now pause to recover AO
	wait4AOrunning()
	
	#Turn off contacq, save data, and turn off display
	pi.setINDI("NOMIC.Command.text", "0 contacq 0 autodispwhat %i obssequences %i savedata" % (n_bckg, save), timeout=50000, wait=True)
	time.sleep(sleep+1.0)			
	pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)	

#Restore log information and turn off data saving
pi.setINDI("NOMIC.Command.text", "1 loglevel 0 savedata", wait=False)
