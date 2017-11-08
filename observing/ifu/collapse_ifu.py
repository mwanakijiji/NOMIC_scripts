#!/usr/bin/python
# collapse_ifu.py
#
# PURPOSE: 
# Collapse an IFU image into a "regular" image
# 
# INPUTS:
#
# MODIFICATION HISTORY:
# 161007 -- DD : first basic version

# Import Python libraries
from pyindi import *         # import pyINDI
import numpy as img          
import numpy as np
import matplotlib 
matplotlib.use('tkagg')        # needed for interactive mode
#matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
import time

# Runnig parameters   
test   = 0
spxl_w = 20
pi     = PyINDI(verbose=False)

# Init plots
plt.figure(1)
plt.ion()  # Turn on interactive mode
plt.xlabel('X coordinates')
plt.ylabel('Y coordinates')
plt.title('Input image')
plt.draw()

#plt.figure(2)
plt.ion()  # Turn on interactive mode
plt.xlabel('X coordinates')
plt.ylabel('Y coordinates')
plt.title('Output image')
plt.draw()
 
# Read image
ni=0
while True:
	if test == 1:
		ifu_file = 'ifu_test.fits'
		hdulist  = pyfits.open(ifu_file)
		img_ifu  = hdulist[0].data
		hdulist.close()
	else:
		# Read last image
		f       = pi.getFITS("NOMIC.DisplayImage.File","NOMIC.GetDisplayImage.Now")
		img_ifu = f[0].data
		
	img_ifu  = img_ifu.astype(long) # Convert to LONG
	nx       = np.size(img_ifu, 0)
	ny       = np.size(img_ifu, 1)
	nx       = nx - nx % spxl_w
	ny       = ny - ny % spxl_w
	img_ifu  = img_ifu[0:nx,0:ny]
	Nbig     = nx
	Nsmall   = nx/spxl_w

	# Plot input image
	plt.figure(1)
	if ni != 0:
		plt.clf()
	plt.imshow(img_ifu, interpolation="nearest", origin="lower", cmap="hot")	
	plt.draw()	
	time.sleep(0.001)

	# Rebin image
	img_bin = img_ifu.reshape([Nsmall, Nbig/Nsmall, Nsmall, Nbig/Nsmall]).mean(3).mean(1)
	plt.figure(2)
	if ni != 0:
		plt.clf()	
	plt.imshow(img_bin, interpolation="nearest", origin="lower", cmap="hot")	
	plt.draw()
	time.sleep(0.001)
	ni = ni+1
	print ni
