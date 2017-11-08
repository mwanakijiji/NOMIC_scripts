#!/usr/bin/python
#Setpoint setting script
#
#
# !!!!! as of 2016, this script is obsolete and has been replaced !!!!
#
#
#DD-140207
#DD-141003 -- added PZT scan to first find the central fringe
#DD-141104 -- removed sleep commands to improve speed
#DD-150302 -- added wait statements for stability
#DD-150530 -- added option to use ROIs properties rather than current image
#DD-150603 -- now find null by polynomial fit (see find_setpoint_img.py for old approach)
#DD-150606 -- updated for NAC source testing

# Import libraries
from pyindi import *
import time
import numpy as flx
import numpy as pixels
import matplotlib 
matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
import warnings

# Ignore deprecation warnings
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()

# Start time counter
t0 = time.time()

#pi is an instance of PyINDI. Here we connect to the server
pi=PyINDI(verbose=False)

# Define running parameters
n_img    = 10         # number of images averaged for flux computation
n_stp    = 5          # number of iterations
srange   = [-180,180] # range of setpoints to scan around initial setpoint
wav      = 2.2        # Wavelength in m
src      = 'NAC'      # Set to NAC for NAC source testing (UBC otherwise)

#Get initial INDI values	
settings  = pi.getINDI('PLC.%sSettings.*' % (src))

#Make sure we are not saving data, turn off continuous acquisition, and turn coadd mode on (much faster than taking individual images)
pi.setINDI("NOMIC.Command.text", "1 contacq 0 savedata 1 autodispwhat", wait=True)

# Initiate arrays
null      = numpy.zeros((n_img))
null_tot  = numpy.zeros((2))
setpoints = numpy.zeros((2))

# Turn on interactive mode
plt.ion() 

# 1. Find the best setpoint
# *************************

# Print info to screen
print(' ') 
print('OPTIMIZING SETPOINT') 

# Get initial setpoint
setpoint0 = settings['PLC.%sSettings.PLSetpoint' % (src)] 
print('Initial setpoint = %f degrees' % setpoint0) 

# Loop over iteration steps
for i in range(n_stp):
	# Set new setpoint
	setpoints[0] = setpoint0 + srange[0]
	settings['PLC.%sSettings.PLSetpoint' % (src)] = setpoints[0]
	pi.setINDI(settings)
	
	# Read RIOs
	for j in range(n_img):
		rois    = pi.getKeys (device='NOMIC', prop='ROIStats', key='ID', nunique=3)
		null[j] = float(rois['3']['Mean'])-0.5*(float(rois['1']['Mean'])+float(rois['2']['Mean']))
	
	# Compute mean value over n_img images
	null_tot[0] = null.mean()
	
	# Repeat for other side of the range
	# Set new setpoint
	setpoints[1] = setpoint0 + srange[1]
	settings['PLC.%sSettings.PLSetpoint' % (src)] = setpoints[1]
	pi.setINDI(settings)
	
	# Read RIOs
	for j in range(n_img):
		rois    = pi.getKeys (device='NOMIC', prop='ROIStats', key='ID', nunique=3)
		null[j] = float(rois['3']['Mean'])-0.5*(float(rois['1']['Mean'])+float(rois['2']['Mean']))
	
	# Compute mean value over n_img images
	null_tot[1] = null.mean()
			
	# Find new setpont
	#setpoint0 = (((null_tot[i,0]*setpoints[i,1]**2-null_tot[i,1]*setpoints[i,0]**2)/(null_tot[i,1]-null_tot[i,0]))**2)**0.25
	#setpoint0 = (setpoints[1]/null_tot[1]**2+setpoints[0]/null_tot[0]**2)/(1.0/null_tot[1]**2+1.0/null_tot[0]**2)
	z = numpy.polyfit(setpoints, null_tot, 2)
	setpoints0 = -0.5*z[1]/z[0]

	# Set new setpoint
	print('Iteration %i -- flux %.2f %.2f -- new setpoint = %.1f' % (i+1,  null_tot[0], null_tot[1], setpoint0))
	settings['PLC.%sSettings.PLSetpoint' % (src)] = setpoint0
	pi.setINDI(settings)
	
	# Plot results
	plt.figure(1)
	plt.ylabel('Mean flux at null [ADU]')
	plt.xlabel('Phase [degrees]')
	plt.axis([-600,600,0,2*null_tot.max()])

	# display measurements AND FIT
	# plt.plot([setpoint0,setpoint0],[0,2*null_tot.max()], 'r--')
        # xp = numpy.linspace(-600, 600, 200)
	# p  = numpy.poly1d(z)
	plt.plot(setpoints, null_tot,'o-')
	plt.show()
	time.sleep(0.001)
		

# Start time counter
t1 = time.time()-t0

# Print status
print("Time to optimize setpoint: %fs" % (t1))
print(" ")

#Now pause 
input("Press 1")
