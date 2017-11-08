#!/usr/bin/python
# run_agpm_1T.py
#
# PURPOSE: 
# Python script to call QACITS.
# 
# INPUTS:
# 1. the detector integration time (AGPM-on)
# 2. the AGPM used ("L" for left, "R" for right). AGPM positions hard coded.
#
# PREREQUISITE:
# 1. IDL must be installed on the machine where the script is executed. So, lbti-ubc or lbti-housekeeper but no lbti-lmircam!
# 2. Python's idlpy module must be installed (see http://www.exelisvis.com/docs/PythonToIDL.html). It's installed by default for
# 	 IDL versions newer than 8.5. Otherwise, go to http://www.cacr.caltech.edu/~mmckerns/pyIDL.html and follow the steps. You might
#    have to create a symlink for the "libxpm" library if it has the version number in its name (usually under /usr/lib/, see 
#    .bashrc for how to set the paths).
# 3. PyQT4 (not install by default on lbti machines)           
# 
# MODIFICATION HISTORY:
# 151218 -- DD : first version for December 2015 run
# 151220 -- DD : now use pyIDL rather than subprocess to call IDL/QACITS (more flexible with arrays)
# 151222 -- DD : validated and updated after first on-sky testing
# 161007 -- DD : each telescope has now its own FITS keywords
# 161011 -- DD : adapted call of QACITS (now with integral gain) and updated for IFU observations
# 161012 -- DD : Convert images to LONG before passing them to IDL

# Import Python libraries
from pyindi import *         # import pyINDI
from pyIDL import idl        # import python to IDL bridge
import numpy as flx          
import numpy as pixels
import numpy as np
import matplotlib 
matplotlib.use('tkagg')    # needed for interactive mode
import matplotlib.pyplot as plt
import warnings
import time
#import subprocess

# Ignore deprecation warnings
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()
    
# 1. Retrieve parameters
# **********************

arg  = sys.argv
dit  = float(arg[1])
agpm = arg[2] 
pi   = PyINDI(verbose=False)
	
# 2. Define parameters and parse fits header
# ******************************************

aper    = 'L'    # We use the left aperture
spxl_w  = 0     # Spaxel width in pixels (0 for non-IFU observations)
period  = 10     # QACITS loop periods
n_img   = 1      #int(period/dit) 
display = 1      # Display QACITS plots
w       = 128     # in pixels, the width of the cropped image 
h       = 128     # in pixels, the height of the cropped image 
ld2as   = 0.092
nd      = 5
win_w   = 30      # Width in pixels of window for PSF fitting
ki      = [0,0]   # Integral gain
if agpm == 'L':
	x = 308.0     # x position of the AGPM1
	y = 425.0     # y position of the AGPM1
else:
	x = 861.2     # x position of the AGPM2
	y = 466.1     # y position of the AGPM2
	
# Parse fits header
pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "QACTPER;Value=" + str(period) + ";Comment=QACITS averaging period", wait=False)
pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "QACTND;Value=0;Comment=QACITS null depth", wait=False)
pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "QACTIP;Value=0;Comment=QACITS mean tilt", wait=False)
pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "QACTLT;Value=0;Comment=QACITS mean tip", wait=False)
pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "XCEN;Value=" + str(x) + ";Comment=X position of the Vortex center", wait=False)
pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "YCEN;Value=" + str(y) + ";Comment=Y position of the Vortex center", wait=False)
		

# 3. Read PSF file and compute flux
# *********************************
    
psf_file = '/home/observer/scripts_obs/observing/general/psf.fits'
hdulist  = pyfits.open(psf_file)
img_psf  = hdulist[0].data
img_psf  = img_psf.astype(long) # Convert to LONG
dit_psf  = hdulist[0].header['DIT']
x_psf    = float(hdulist[0].header['X'])
y_psf    = float(hdulist[0].header['Y'])
cxy_psf  = [x_psf,y_psf]
hdulist.close()

ri = idl()
ri.put('display',display)
ri.put('psf_img',img_psf)
ri.put('cxy_psf',cxy_psf)
ri.put('window_width',win_w)
ri.put('tint_psf',dit_psf)
ri.put('Flux',0)
ri.eval('run_qacits_lmircam_preprocessing, psf_img, tint_psf, Flux=Flux, cxy_psf = cxy_psf, window_width=window_width, boxwidth=boxwidth, n_sig=n_sig, display=display')
flux_psf=ri.get('Flux')
flux_psf=flux_psf*nd

print(" ")
print("RETRIEVING PSF FILE ")
print(" ")
print(" - Name  : /home/observer/scripts_obs/observing/general/psf.fits")
print(" - DIT   : %f " % dit_psf)
print(" - X_POS : %i " % x_psf)
print(" - Y_POS : %i " % y_psf)
print(" - flux  : %f " % flux_psf[0])
print(" ")

# 4. Run the control loop
# ***********************

# Print info to screen
print(' ') 
print('RUNNING QACITS NOW') 
print(' ') 

# Init timer
t0 = time.time() 

# Init plots
plt.figure(1)
plt.ion()  # Turn on interactive mode
plt.xlabel('Tilt [l/D]')
plt.ylabel('Tip [l/D]')
plt.title('Real-time tip/tilt estimates')
plt.draw()

plt.figure(2)
plt.ion()  # Turn on interactive mode
plt.xlabel('Iteration')
plt.ylabel('Null depth')
plt.title('Real-time null depth estimates')
plt.axis([0,10,0,20])
plt.draw()

# Prepare python to IDL bridge	
ri.put('tint_agpm',dit)
ri.put('flux',flux_psf)
ri.put('centerx',x)
ri.put('centery',y)
ri.put('null_depth',0)

# Init variables and run loop
tt_tot = [0.,0.]
nd_tot = 0.
i_all  = 0.
i_fr   = 1
while True:

	# Read last image
	f        = pi.getFITS("LMIRCAM.DisplayImage.File", "LMIRCAM.GetDisplayImage.Now")
	agpm_img = f[0].data
	agpm_img = agpm_img.astype(long) # Convert to LONG
	
	# Collapse image if IFU observations
	if spxl_w != 0:
		nx, ny   = agpm_img.shape
		nx       = nx - nx % spxl_w
		ny       = ny - ny % spxl_w
		agpm_img = agpm_img[0:nx,0:ny]
		nbin     = nx/spxl_w
		# img_crop = agpm_img[nx / 4: - nx / 4, ny / 4: - ny / 4]
		agpm_img.reshape([nbin, nx/nbin, nbin, nx/nbin]).mean(3).mean(1)
	
	# Extract ROI
	roi = pi.cutRegion(agpm_img,y-0.5*h,x-0.5*w,h,w)
	tam = agpm_img.shape

	# Prepare python to IDL bridge	
	ri.put('agpm_img',agpm_img)
	ri.put('integral_term',ki)

	# Call QACITS
	t2 = time.time()
	ri.eval('tt=run_qacits_lmircam(agpm_img = agpm_img, tint_agpm = tint_agpm, centerx = centerx, centery = centery, display=display, null_depth = null_depth, flux = flux, integral_term=integral_term)')
	t3 = time.time()-t2
	print("Time for one iteration of QACITS : %fs" % (t3))	

	# Get tipt/tilt, null depth, and integral term
	tt=ri.get('tt')
	nd=ri.get('null_depth')
	ki=ri.get('integral_term')
	
    	# Parse fits header
	pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "QACTND;Value=" + str(nd)    + ";Comment=QACITS null depth", wait=False)
	pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "QACTIP;Value=" + str(tt[0]) + ";Comment=QACITS mean tilt", wait=False)
	pi.setINDI("LMIRCAM.EditFITS.Keyword=" + str(aper) + "QACTLT;Value=" + str(tt[1]) + ";Comment=QACITS mean tip", wait=False)
	
	# Plot tip/tilt
	plt.figure(1)
	plt.scatter(tt[0], tt[1])
	plt.axis([-2,2,-2,2])
	plt.draw()
	time.sleep(0.001)
	plt.figure(2)
	plt.scatter(i_all, nd)
	plt.axis([0,100,0,30])
	plt.draw()
	time.sleep(0.001)
	
	# Compute sum
	tt_tot = [tt_tot[0] + tt[0], tt_tot[1] + tt[1]]
	nd_tot = nd_tot + nd
	
	# Sent tt commands to FPC if enough frames
	if i_fr == n_img:
		# Compute average and send command
		tt  = [tt_tot[0]/i_fr*ld2as,tt_tot[1]/i_fr*ld2as]
		nd  = nd/i_fr
		# Print info to screen and send opposite command!!!!
		print("Now sending tt command : %f %f" % ( -tt[0], -tt[1] ))		
		if aper == 'L':
			pi.setINDI('Acromag.FPC.Tip=%f;Tilt=%f;Piston=0;Mode=1' %(-tt[1],-tt[0] ), wait=True)	
		else:
			pi.setINDI('Acromag.SPC.Tip=%f;Tilt=%f;Piston=0;Mode=1' %( tt[0],tt[1] ), wait=True)	
		# Reset variables
		i_fr = 0
		tt_tot = [0.,0.]
		nd_tot = 0.
		
	# Increment counters
	i_fr = i_fr + 1
	i_all = i_all + 1
	
	# Print time
	t4 = time.time()-t2
	print("Time for full loop : %fs" % (t4))	

	# Pause
	#input()

# Print status
t1 = time.time()-t0
print("Time to run QACITS : %fs" % (t1))
print('')

# Start time counter
t1 = time.time()-t0

# Print status
print("Total script time: %fs" % (t1))
print(" ")
