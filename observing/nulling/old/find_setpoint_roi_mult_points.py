#!/usr/bin/python
#Setpoint setting script
#DD-140207
#DD-141003 -- added PZT scan to first find the central fringe
#DD-141104 -- removed sleep commands to improve speed
#DD-150302 -- added wait statements for stability
#DD-150530 -- added option to use ROIs properties rather than current image
#DD-150603 -- now find null by polynomial fit (see find_setpoint_img.py for old approach)
#DD-150606 -- updated for NAC source testing
#DD-160212 -- updated for February 2016 run
#DD-160214 -- updated for fixed ROI numbers

# Import libraries
from pyindi import *
import time
import numpy as np
import numpy as flx
import numpy as pixels
import matplotlib 
#matplotlib.use('QT4Agg')
matplotlib.use('tkagg')    # needed for interactive mode
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
srange   = [-360,360] # range of setpoints to scan around initial setpoint
wav      = 2.2        # Wavelength in m
src      = 'NAC'      # Set to NAC for NAC source testing (UBC otherwise)
n_points = 5          # number of OPD steps to go, use odd numbers only

# Define ROI ID numbers
pos1 = '3'  # on-source ROI
pos2 = '2'  # background ROI
pos3 = '1'  # background ROI

#Get initial INDI values	
settings  = pi.getINDI('PLC.%sSettings.*' % (src))
t_int  = pi.getINDI('NOMIC.CamInfo.IntTime')

#Make sure we are not saving data, turn off continuous acquisition, and turn coadd mode on (much faster than taking individual images)
pi.setINDI("NOMIC.Command.text", "1 contacq 0 savedata 1 autodispwhat", wait=True)

# Initiate arrays
null      = numpy.zeros((n_img))
null_tot  = numpy.zeros((n_points))
null_std  = numpy.zeros((n_points))
setpoints = numpy.zeros((n_points))

# Init plot
plt.ion()  # Turn on interactive mode
plt.figure(1)
plt.ylabel('Mean flux at null [ADU]')
plt.xlabel('Phase [degrees]')
plt.title('Setpoint optimization')
plt.draw()

# 1. Find the best setpoint
# *************************

# Print info to screen
print(' ') 
print('OPTIMIZING SETPOINT') 

# Get initial setpoint
setpoint0 = settings['PLC.%sSettings.PLSetpoint' % (src)] 
print('Initial setpoint = %f degrees' % setpoint0) 

# Loop until offset is smaller than step width
k=0
offset = 100000.0
#while (null_tot[0] >= null_tot[1] or null_tot[0] >= null_tot[2]):
while (offset >= np.sum(np.abs(srange)) / np.float(n_points - 1)):
  k=k+1
  
  # loop over setpoints (scan)
  for i in range(0, n_points):
    
    # compute setpoints to scan
    setpoints[i] = setpoint0 + (np.float(i) - np.float(n_points - 1) / 2.0) * np.sum(np.abs(srange)) / np.float(n_points - 1)
    
    # Set new setpoint
    settings['PLC.%sSettings.PLSetpoint' % (src)] = setpoints[i]
    pi.setINDI(settings)
    
    # Read RIOs
    for j in range(n_img):
      t0 = time.time()
      rois    = pi.getKeys (device='NOMIC', prop='ROIStats', key='ID')
      null[j] = float(rois[pos1]['Mean'])-0.5*(float(rois[pos2]['Mean'])+float(rois[pos3]['Mean']))
#      time.sleep(np.max([0.0, t_int-0.1]))      # wait for 1 integration in nomic - time of above 2 lines (estimated to be 100ms), but not less then 0.0s
      t1 = time.time()-t0
#      time.sleep(np.max([0.0, t_int-(t1-t0)]))
      print("Time for getKeys: %fs" % (t1))
    
    # Compute mean value over n_img images
    null_tot[i] = null.mean()
    null_std[i] = null.std()
    
  # Find new setpoint by parabola fit
  # If parabola has the wrong sign, use the smallest flux to define the setpoint. OItherwise, use the parabola.
  #setpoint0 = (((null_tot[i,0]*setpoints[i,1]**2-null_tot[i,1]*setpoints[i,0]**2)/(null_tot[i,1]-null_tot[i,0]))**2)**0.25
  #setpoint0 = (setpoints[1]/null_tot[1]**2+setpoints[0]/null_tot[0]**2)/(1.0/null_tot[1]**2+1.0/null_tot[0]**2)
  z = numpy.polyfit(setpoints, null_tot, 2)    	# Numpy returns highest degree first
  
  # if parabola has negative curvature:
  if z[0] < 0:
    if null_tot[0] < null_tot[-1]:
      setpoint_new = setpoints[0]
    else:
      setpoint_new = setpoints[-1]
    offset = 10000000.0
  else:
    setpoint_new = -0.5*z[1]/z[0]
    offset = np.abs(setpoint0 - setpoint_new)
  
  setpoint0 = setpoint_new
  print('Iteration %i -- min. flux %.2f max. flux %.2f -- new setpoint = %.1f' % (k,  np.min(null_tot), np.max(null_tot), setpoint0))
  
  # Plot results
  plt.figure(1)
  plt.axis([setpoints[0] - np.sum(np.abs(srange)) / np.float(n_points - 1), setpoints[-1] + np.sum(np.abs(srange)) / np.float(n_points - 1), -np.abs(null_tot.max()) / 5.0, np.abs(2*null_tot.max())])
  
  # display measurements AND FIT
  # plt.plot([setpoint0,setpoint0],[0,2*null_tot.max()], 'r--')
  xp = numpy.linspace(-500, 500, 200)
  p  = numpy.poly1d(z)
  # plt.plot(setpoints, null_tot,'o', xp, p(xp), '-')
  plt.errorbar(setpoints, null_tot, null_std, marker='o', linestyle='.')
  plt.plot(xp, p(xp), linestyle='-', color='black')
  plt.draw()
  # plt.show(block=False)
  time.sleep(0.001)

# Start time counter
t1 = time.time()-t0

# Print status
print("Time to optimize setpoint: %fs" % (t1))
print(" ")

#Now pause 
input("Press 1")

