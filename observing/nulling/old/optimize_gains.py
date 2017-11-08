#!/usr/bin/python
#Setpoint setting script
#DD-140207

from pyindi import *
import numpy as flx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=False)

# Define running parameters
n_img    = 50      # number of images averaged for flux computation
n_stp    = 5       # number of iterations to find the null
r        = 54     # x position of the star
c        = 81      # y position of the star
w        = 20      # in pixels, the width of the cropped image (around the null)
h        = 20      # in pixels, the height of the cropped image (around the null)
gain_stp = 50
gain_stp2 = 0.1

#Get initial INDI values
#pi.setINDI("Ubcs.SPC_TRANS.command=5")		
settings  = pi.getINDI('PLC.UBCSettings.*')

#Make sure we are not saving data 
pi.setINDI("NOMIC.Command.text", "0 savedata")

# Initiate arrays
flx          = numpy.zeros(n_img)
avg          = numpy.zeros(2)
rms          = numpy.zeros(2)
		
# Optimize gain
# **************

# Print info to screen
print('  ')
print('OPTIMIZING THE GRADIENT GAIN')

# Get initial gradient gain
cggain = settings['PLC.UBCSettings.CGPGain'] 
print('Initial gradient gain = %d' % cggain)

# Get initial setpoint
setpoint0 = settings['PLC.UBCSettings.CGSetpoint'] 
print('Initial setpoint = %f' % setpoint0) 

# Go to constructive interference
print('Going to constructive interference')
settings['PLC.UBCSettings.CGSetpoint'] = setpoint0 + setpoint_step 

# Run it at the current gain to find current RMS
# Loop over images and compute flux
for k in range(n_img):
	# Take data (assumed that we are at null in the bottom chop position when executing the script)
	pi.setINDI("NOMIC.Command.text", "go", timeout=15)

	# Read current displayed image
	f      = pi.getFITS("NOMIC.DisplayImage.File", "NOMIC.GetDisplayImage.Now")
	pixels = f[0].data

 	# Extract background region
	roi2 = pi.cutRegion(pixels,r+0.5*h,c-0.5*w,h,w)

	# Extract sub-array
	roi = pi.cutRegion(pixels,r-0.5*h,c-0.5*w,h,w)
	i#mgplot = plt.imshow(roi)

	# Compute total flux over the extracted region
	flx[k] = roi.sum()-roi2.sum()

	# Compute total flux over the extracted region
	flx[k] = roi.sum()

# Compute mean and rms of flux
avg_now = flx.mean()		
rms_now = flx.std()	
print('  - Gradient gain %d -- Flux AVG = %d and RMS = %d' % (cggain,avg_now,rms_now))

# Now loop over the gradient gain directions
sign    = [1,-1]
for i in range(2):
	rms_prev = pow(10,6)
	while rms_now < rms_prev:
		# rms_prev becomes rms_now
		rms_prev = rms_now
	
		# Increase gain
		cggain += sign[i]*gain_stp
		settings['PLC.UBCSettings.CGPGain'] = cggain
		pi.setINDI(settings)
	
		# Loop over images and compute flux
		for k in range(n_img):
			# Take data (assumed that we are at null in the bottom chop position when executing the script)
			pi.setINDI("NOMIC.Command.text", "go", timeout=15)

			# Read current displayed image
			f      = pi.getFITS("NOMIC.DisplayImage.File", "NOMIC.GetDisplayImage.Now")
			pixels = f[0].data

			 # Extract background region
			roi2 = pi.cutRegion(pixels,r+0.5*h,c-0.5*w,h,w)
			
			# Extract sub-array
			roi = pi.cutRegion(pixels,r-0.5*h,c-0.5*w,h,w)
			i#mgplot = plt.imshow(roi)
		
			# Compute total flux over the extracted region
			flx[k] = roi.sum()-roi2.sum()

		# Compute mean and rms of flux
		avg_now = flx.mean()		
		rms_now = flx.std()	
		print('  - Gradient gain %d -- Flux AVG = %d and RMS = %d' % (cggain,avg_now,rms_now))

# Correct for last step
cggain = cggain + gain_stp
settings['PLC.UBCSettings.CGPGain'] = cggain
pi.setINDI(settings)
print('Final gradient gain = %d' % cggain)
print('  ')

# Going back to null
print('Going back to destructive interference')
settings['PLC.UBCSettings.CGSetpoint'] = setpoint0
