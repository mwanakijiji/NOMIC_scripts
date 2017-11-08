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
from pyIDL import idl        # import python to IDL bridge
import numpy as np          
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
cxy_psf = [x,y]

# Declare function    
def wait4AORunning():
	while True:
		pi.setINDI("LBTO.Dictionary.Name=" + aper + "_AOStatus;Value=")
		status = pi.getINDI("LBTO.Dictionary.Value")
		time.sleep(0.05) 
		if status == "AORunning":
			break
# Init plots
plt.ion()  # Turn on interactive mode
plt.figure(1)
plt.xlabel('X coordinate')
plt.ylabel('Y coordinate')
plt.title('Input image')
plt.draw()

# File to read
psf_file = 'psf.fits'
			
# Check whether dome is open (double check)
hdulist = pyfits.open(psf_file)
img_psf = (hdulist[0].data)
img_psf = img_psf.astype(long)  # convert to long is mandatory for Python!!!!
cxy_psf = [x,y]
hdulist.close()

# Plot input image
# plt.imshow(img_psf)
# plt.show()

print np.amax(img_psf)
print np.amin(img_psf)

# Save current display as fits file
ri = idl()
ri.put('display',1)
ri.put('psf_img',img_psf)
ri.put('cxy_psf',cxy_psf)
ri.put('tint_psf',0)
ri.put('Flux',0)
ri.eval('run_qacits_lmircam_preprocessing, psf_img, tint_psf, Flux=Flux, cxy_psf = cxy_psf, display=display')
cxy_vcen=ri.get('cxy_psf')
print("Fitted vortex center : %f %f" % ( cxy_vcen[0], cxy_vcen[1] ))

# Start time counter
t1 = time.time()-t0

# Print status
print("Total script time: %fs" % (t1))
print(" ")

