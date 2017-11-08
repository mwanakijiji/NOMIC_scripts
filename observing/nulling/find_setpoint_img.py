#!/usr/bin/python
#Setpoint setting script
#DD-140207
#DD-141003 -- added PZT scan to first find the central fringe
#DD-141104 -- removed sleep commands to improve speed
#DD-150302 -- added wait statements for stability
#DD-150302 -- added option to use ROIs properties rather than current image

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
n_img    = 1      # number of images averaged for flux computation
n_stp    = 20       # number of iterations to find the null
wav      = 2.2     # Wavelength in m
no_jump  = 1       # Turn on/off pupil PZT jumps (this assumes we are in the right fringe)
use_roi  = 1       # set to non 0 to use ROIs INDI properties rather than reading the current image

# Parameters defining the beam position (only if use_roi = 0)
x        = 45      # x position of the star
y        = 76      # y position of the star
w        = 20      # in pixels, the width of the cropped image (around the null)
h        = w       # in pixels, the height of the cropped image (around the null)

# define opd steps (degrees)
opd_step = wav
opd2deg  = 360/wav

#Get initial INDI values	
settings  = pi.getINDI('PLC.UBCSettings.*')

#Make sure we are not saving data, utrn off continuous acquisition, and turn coadd mode on (much faster than taking individual images)
if use_roi != 0: 	
	pi.setINDI("NOMIC.Command.text", "1 contacq 0 savedata 1 autodispwhat", wait=True)
else:
	pi.setINDI("NOMIC.Command.text", "0 contacq 0 savedata 5 autodispwhat", wait=True)

# Initiate arrays
avg          = numpy.zeros((n_stp,2))
setpoints    = numpy.zeros((n_stp,2))
rel_opd      = [-opd_step,opd_step]

# Turn on interactive mode
plt.ion() 

# 1. Find the best setpoint
# *************************

# Print info to screen
print(' ') 
print('OPTIMIZING SETPOINT') 

# Get initial setpoint
setpoint0 = settings['PLC.UBCSettings.PLSetpoint'] 
print('Initial setpoint = %f degrees' % setpoint0) 

# Loop over iteration steps
for i in range(n_stp):
	# Loop over the two setpoint offsets
	for j in range(2):
		#Jump PZT pupil by rel_opd (mode=1 for relative moves) or change setpoint if no_jump is set
		setpoints[i,j] = setpoint0 + rel_opd[j]*opd2deg
		if no_jump == 0: 	
			pi.setINDI('Acromag.Pupil.Tip=0;Tilt=0;Piston=%d;Mode=1' %(rel_opd[j]))
		else:
			settings['PLC.UBCSettings.PLSetpoint'] = setpoints[i,j]
		
		# Read current displayed image or ROI properties
		if use_roi == 0: 
			# Take data
			pi.setINDI("NOMIC.Command.text", "0.015 1 %d lbtintpar" % (n_img), timeout=15, wait=True)			
			pi.setINDI("NOMIC.Command.text", "go", timeout=15, wait=True)
			
			# Read image
			f      = pi.getFITS("NOMIC.DisplayImage.File", "NOMIC.GetDisplayImage.Now")
			pixels = f[0].data

			# Extract background regions up and down
			roi_up = pi.cutRegion(pixels,y+0.5*h,x-0.5*w,h,w)
			roi_dw = pi.cutRegion(pixels,y-1.5*h,x-0.5*w,h,w)
		
			# Extract sub-array
			roi = pi.cutRegion(pixels,y-0.5*h,x-0.5*w,h,w)		
			tam = roi.shape
			
			# Prepare display	
			plt.figure(1)	
			plt.xlabel('x pixels')
			plt.ylabel('y pixels')
			plt.title('Step %d/%d' % (i+1,n_stp))
			plt.ylim([0, tam[0]])
			plt.xlim([0, tam[1]])
			
			# display scaled sub array
			plt.imshow(roi)
			plt.draw()
			time.sleep(0.001)
			
			# Compute total flux (iteration i, side j)
			avg[i,j] = roi.mean()-0.5*(roi_up.mean()+roi_dw.mean())
			#print('Flux AVG = %d %d' % avg[0] avg[1]) 
		else:
			rois = pi.getKeys (device='NOMIC', prop='ROIStats', key='ID', nunique=3)
			avg[i,j] = float(rois['3']['Mean'])-0.5*(float(rois['1']['Mean'])+float(rois['2']['Mean']))
			print('Flux at null = %f degrees' % avg[i,j]) 
		
		#Jump PZT back to initial value or change setpoint
		if no_jump == 0: 	
			pi.setINDI('Acromag.Pupil.Tip=0;Tilt=0;Piston=%d;Mode=1' %(-rel_opd[j]))
		else:
			settings['PLC.UBCSettings.PLSetpoint'] = setpoint0	

	# Plot results
	plt.figure(2)
	plt.ylabel('Mean flux at null [ADU]')
	plt.xlabel('Phase [degrees]')
	plt.axis([-600,600,0,2*avg.max()])

	# display scaled sub array
	plt.plot([setpoint0,setpoint0],[0,16000], 'r--')
	plt.plot([setpoints[i,0],setpoints[i,1]], [avg[i,0],avg[i,1]],'o-')
	
	plt.draw()
	time.sleep(0.001)
		
	# Compute and apply new absolute setpoint or PZT position
	deg_offset   = (1/abs(avg[i,0])*setpoints[i,0] + 1/abs(avg[i,1])*setpoints[i,1])/(1/abs(avg[i,0])+1/abs(avg[i,1]))

	# If absolute change more than 180 degrees, jump by 2.2 microns and repeat
	if abs(deg_offset) >= 180 and no_jump == 0:
		if deg_offset > 0:
			pi.setINDI('Acromag.Pupil.Tip=0;Tilt=0;Piston=%d;Mode=1' %(wav))
			print('Iteration %i -- Not the central fringe => Jump by +360deg' %(i+1))
		else:
			pi.setINDI('Acromag.Pupil.Tip=0;Tilt=0;Piston=%d;Mode=1' %(-wav))
			print('Iteration %i -- Not the central fringe => Jump by -360deg' %(i+1))
	else:
		new_setpoint = setpoint0 + deg_offset
		setpoint0    = new_setpoint
		print('Iteration %i -- flux %.2f %.2f -- new setpoint = %.1f' % (i+1, avg[i,0], avg[i,1], new_setpoint))
		settings['PLC.UBCSettings.PLSetpoint'] = new_setpoint
		pi.setINDI(settings)
	
	# Compute new setpoint step
	# setpoint_step *= abs((avg[1]-avg[0])/(avg[1]+avg[1]))
	# rel_setpoint = [-setpoint_step,+setpoint_step]

#Turn coadd mode off
pi.setINDI("NOMIC.Command.text", "1 autodispwhat")

# Start time counter
t1 = time.time()-t0

# Print status
print("Time to optimize setpoint: %fs" % (t1))
print(" ")

#Now pause 
input("Press 1")
