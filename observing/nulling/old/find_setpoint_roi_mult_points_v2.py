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
print('')
print('Importing libraries, setting up, initializing some things.')
import time
from pyindi import *
import numpy as np
#import numpy as flx      # obsolete
#import numpy as pixels   # obsolete
from matplotlib import use as mpl_use

#mpl_use('QT4Agg')
mpl_use('tkagg')    # needed for interactive mode

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
n_img    = 2          # number of images averaged for flux computation
srange   = [-360,360] # range of setpoints to scan around initial setpoint
wav      = 2.2        # Wavelength in m
src      = 'UBC'      # Set to NAC for NAC source testing (UBC otherwise)
n_points = 5          # number of OPD steps to go, use odd numbers only
plot     = 's'        # options for graphical output: 's' for screen, 'f' for file, 'b' for both, 'n' for none.
                      # The file will be saved as 'setpoint.eps' in the directory this script is located in.

# Define ROI ID numbers
pos1 = '3'  # on-source ROI
pos2 = '2'  # background ROI
pos3 = '1'  # background ROI

print('')
print('Getting the initial system parameters.')
#Get initial INDI values	NOTE: The following two lines take ~2 sec, could be optimized?
settings  = pi.getINDI('PLC.%sSettings.*' % (src))
t_int  = pi.getINDI('NOMIC.CamInfo.IntTime')

print('')
print('Setting up instrument and initializing some more arrays.')
#Make sure we are not saving data, turn ON continuous acquisition.
pi.setINDI("NOMIC.Command.text", "1 contacq 0 savedata", wait=True)

# Initiate arrays
null      = numpy.zeros((n_img))
null_tot  = numpy.zeros((n_points))
null_std  = numpy.zeros((n_points))
setpoints = numpy.zeros((n_points))

if (plot == 's') or (plot == 'b'):
  print('')
  print('Initializing display.')
  # Init plot		NOTE: The following two lines take ~5 sec, needs optimization!!!!!
  plt.ion()  # Turn on interactive mode
  plt.figure(1)
  plt.ylabel('Mean flux at null [ADU]')
  plt.xlabel('Phase [degrees]')
  plt.title('Setpoint optimization')
  plt.draw()
if (plot == 'f') or (plot == 'b'):
  print('')
  print('Plotting to file.')
  plt.figure(1)
  plt.ylabel('Mean flux at null [ADU]')
  plt.xlabel('Phase [degrees]')
  plt.title('Setpoint optimization')

# 1. Find the best setpoint
# *************************

# Print info to screen
print(' ')
print('OPTIMIZING SETPOINT')

# Get initial setpoint
setpoint0 = settings['PLC.%sSettings.PLSetpoint' % (src)]
#setpoint0 = 0.0
print('Initial setpoint = %f degrees' % setpoint0)

# compute some values before the loop
scan_step = np.sum(np.abs(srange)) / np.float(n_points - 1)     # step width of the OPD scan
half_steps = (n_points - 1) / 2                                 # half of ( the number of steps - 1 )

# Loop until offset is smaller than step width
k=0
offset = 100000.0
n_success = 0
setpoints_fit = []
#while (offset >= scan_step):
while n_success < 5:
  
  k=k+1
  
  # loop over setpoints (scan)
  for i in range(0, n_points):
    
    # compute setpoints to scan
    setpoints[i] = setpoint0 + np.float(i - half_steps) * scan_step
    
    # Set new setpoint
    settings['PLC.%sSettings.PLSetpoint' % (src)] = setpoints[i]
    pi.setINDI(settings)

    # Read RIOs
    for j in range(n_img):
      
      time_stats_0 = time.time()
      null[j] = pi.getINDI ('NOMIC.NullingStats.Mean3') - 0.5 * (pi.getINDI ('NOMIC.NullingStats.Mean1') + pi.getINDI ('NOMIC.NullingStats.Mean2'))
      
      time.sleep(np.max([0.0, t_int - (time.time() - time_stats_0)]))      # wait for 1 integration in nomic - time it took to get the stats (previous line), but not less then 0.0s
    
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
  if (plot == 's') or (plot == 'b'):
    null_range = null_tot.max() - null_tot.min()
    plot_range_x = [setpoints[0] - scan_step, setpoints[-1] + scan_step]

    # display measurements and fit
    xp = numpy.linspace(plot_range_x[0], plot_range_x[1], 30)
    p  = numpy.poly1d(z)
    plt.errorbar(setpoints, null_tot, null_std, marker='o', linestyle='.')
    plt.plot(xp, p(xp), linestyle='-', color='black')
    plt.draw()
    time.sleep(0.001)
  if (plot == 'f') or (plot == 'b'):
    null_range = null_tot.max() - null_tot.min()
    plot_range_x = [setpoints[0] - scan_step, setpoints[-1] + scan_step]
    xp = numpy.linspace(plot_range_x[0], plot_range_x[1], 30)
    p  = numpy.poly1d(z)
    plt.errorbar(setpoints, null_tot, null_std, marker='o', linestyle='.')
    plt.plot(xp, p(xp), linestyle='-', color='black')
    plt.savefig('setpoint.pdf')
    time.sleep(0.001)
  
  if offset <= scan_step:
    n_success = n_success + 1
    setpoints_fit.append(setpoint_new)
    print('Success: ', n_success)
  else:
    n_success = 0
    setpoints_fit = []
    print('FAILED')

# Start time counter
t1 = time.time()-t0

# Print status
print("Time to optimize setpoint: %fs" % (t1))
print(" ")

# Send determined setpoint
settings['PLC.%sSettings.PLSetpoint' % (src)] = np.average(setpoints_fit)
pi.setINDI(settings)

print('New setpoint used: ', setpoint0)

#Now pause 
raw_input("Press [ENTER] to confirm or [Ctrl] + [C] to abort.")
#input("Press 1")

