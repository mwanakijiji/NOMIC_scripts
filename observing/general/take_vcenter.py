#!/usr/bin:wq/python
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
from pyIDL import idl        # import python to IDL bridge
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
cxy_psf = [x,y]

# Declare function    
def wait4AORunning():
	while True:
		pi.setINDI("LBTO.Dictionary.Name=" + aper + "_AOStatus;Value=")
		status = pi.getINDI("LBTO.Dictionary.Value")
		time.sleep(0.05) 
		if status == "AORunning":
			break


# Stop continuous acquisition if running
pi.setINDI("LMIRCAM.Command.text","0 contacq")   

# Set integration time
# pi.setINDI("LMIRCAM.Command.text", "%f %i %i lbtintpar" % (dit, n_coadd, n_img), timeout=100, wait=True)	

# Save
pi.setINDI("LMIRCAM.Command.text","1 savedata")

#  Turn on display
#pi.setINDI("LMIRCAM.Command.text", "1 autodispwhat", wait=True)

# Mark data as PSF
pi.setINDI("LMIRCAM.EditFITS.Keyword=FLAG;Value=SKY;Comment=frame type", wait=False)

# Take a frames						
pi.setINDI("LMIRCAM.Command.text", "go", timeout=3000, wait=True)

# Get last displayed frame
f   = pi.getFITS("LMIRCAM.DisplayImage.File", "LMIRCAM.GetDisplayImage.Now")
img = f[0].data
img = img.astype(long) # Convert to LONG

# Save current display as fits file
ri = idl()
ri.put('display',1)
ri.put('psf_img',img)
ri.put('cxy_psf',cxy_psf)
ri.put('window_width',20)
ri.put('tint_psf',0)
ri.put('Flux',0)
ri.eval('run_qacits_lmircam_preprocessing, psf_img, tint_psf, Flux=Flux, cxy_psf = cxy_psf, window_width=window_width, boxwidth=boxwidth, n_sig=n_sig, display=display, /sigmafilter')
cxy_vcen=ri.get('cxy_psf')
print cxy_vcen
print("Fitted vortex center : %f %f" % ( cxy_vcen[0], cxy_vcen[1] ))

# Start time counter
t1 = time.time()-t0

# Print status
print("Total script time: %fs" % (t1))
print(" ")
