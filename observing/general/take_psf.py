#!/usr/bin/python
# take_psf.py
#
# PURPOSE: 
# Basic script to take PSF data.
# The script also saves a "psf.fits" file on the local machine for later use (e.g., with QACITS).   
#
# INPUTS
# Three arguments giving the (1) the X position of the PSF, (2) the Y position of the PSF, and (3) an argument to take data (if = 1)       
# 
# MODIFICATION HISTORY:
# 151218 -- DD : first version for December 2015 run

# Import Python libraries
from pyindi import *         # import pyINDI
import numpy as flx          
import numpy as pixels
import matplotlib 
matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
import warnings
import time
import sys

# Start time counter
t0 = time.time() 

# Ignore deprecation warnings
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()
        
#pi is an instance of PyINDI. Here we connect to the INDI server
pi=PyINDI(verbose=False)

# Retrieve input paramaters
arg = sys.argv
x   = int(arg[1])
y   = int(arg[2])
z   = int(arg[3])

# Declare paramaters
aper    = 'L'     # Define which aperture is used (L for left, R for right)
dit     = 0.290   # Detector integration time in s 
n_coadd = 1       # Number of coadds
n_img   = 10      # Number of images per nod (0 to use the GUI value)
offx    = 2       # Nodding offset in X direction
offy    = 0       # Nodding offset in Y direction
test    = 0       # No AO interaction

# Declare function    
def wait4AORunning():
	while True:
		pi.setINDI("LBTO.Dictionary.Name=" + aper + "_AOStatus;Value=")
		status = pi.getINDI("LBTO.Dictionary.Value")
		time.sleep(0.05) 
		if status == "AORunning":
			break

# Get last displayed frame
f   = pi.getFITS("LMIRCAM.DisplayImage.File", "LMIRCAM.GetDisplayImage.Now")
img = f[0].data

# Save current display as fits file
hdu      = pyfits.PrimaryHDU()
hdu.data = img
hdu.header['DIT'] = dit*n_coadd
hdu.header['X']   = x
hdu.header['Y']   = y
hdu.writeto('/home/observer/scripts_obs/observing/general/psf.fits', clobber=True)

print("PSF file saved under /home/observer/scripts_obs/observing/general/psf.fits")
print(" ")

# RUN PSF sequence if requested
if z == 1:
			
	# Check whether dome is open (double check)
	shut = pi.getINDI("LBTO.Status." + aper + "_Shutter")
	if shut == 0:
		test = 1
	
	# Stop continuous acquisition if running
	pi.setINDI("LMIRCAM.Command.text","0 contacq")   

	# Set integration time
	pi.setINDI("LMIRCAM.Command.text", "%f %i %i lbtintpar" % (dit, n_coadd, n_img), timeout=100, wait=True)	

	# Save
	pi.setINDI("LMIRCAM.Command.text","1 savedata")

	#  Turn on display
	# pi.setINDI("LMIRCAM.Command.text", "1 autodispwhat", wait=True)

	# Mark data as PSF
	pi.setINDI("LMIRCAM.EditFITS.Keyword=FLAG;Value=PSF;Comment=frame type", wait=False)
	
	# Take a frames						
	pi.setINDI("LMIRCAM.Command.text", "go", timeout=3000, wait=True)

	# Use as background
	pi.setINDI("LMIRCAM.Command.text","rawbg",timeout=300,wait=True)

	# Nod the telescope to take the PSF and wait for AO
	if test != 1:
		pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY", "LBTO.OffsetPointing.OffsetX", offx, "LBTO.OffsetPointing.OffsetY", offy, "LBTO.OffsetPointing.Side", "left", "LBTO.OffsetPointing.Type", "REL", timeout=150, Wait=False)
		wait4AORunning()

	# Take a frames						
	pi.setINDI("LMIRCAM.Command.text", "go", timeout=3000, wait=True)
			   
	# Nod back the telescope 
	if test != 1:
		pi.setINDI("LBTO.OffsetPointing.CoordSys", "DETXY", "LBTO.OffsetPointing.OffsetX", -offx, "LBTO.OffsetPointing.OffsetY", -offy, "LBTO.OffsetPointing.Side", "left", "LBTO.OffsetPointing.Type", "REL", timeout=150, Wait=False)

# Start time counter
t1 = time.time()-t0

# Print status
print("Total script time: %fs" % (t1))
print(" ")

