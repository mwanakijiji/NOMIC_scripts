#!/usr/bin/python
# Setpoint setting script

# ====================================================================================================
# Version history/change log
# ====================================================================================================
#DD-140207
#DD-141003 -- added PZT scan to first find the central fringe
#DD-141104 -- removed sleep commands to improve speed
#DD-150302 -- added wait statements for stability
#DD-150530 -- added option to use ROIs properties rather than current image
#DD-150603 -- now find null by polynomial fit (see find_setpoint_img.py for old approach)
#DD-150606 -- updated for NAC source testing
#DD-160212 -- updated for February 2016 run
#DD-160214 -- updated for fixed ROI numbers
# SE - 2016-03-05 -- Several changes: New way to read the ROIs fast, plot to screen, file, both, or none, 5 step single point scans + verification scans
# SE - 2016-03-06 -- New way implemented to read/write setpoints only, since they are now a separate indi property. Speeds up reading them.
# SE - 2016-03-22 -- Implemented maximum step width for the setpoint change.
# SE - 2016-04-21 -- Bug fix: Avoid too large changes of the scan center due to odd parabola fits
# SE - 2016-04-21 -- Bug fix: Now the script can actually be aborted at raw_input()
# SE - 2016-04-23 -- Check for loop closed implemented. Cleaned up several parameters.
# SE - 2016-04-23 -- Setpoint now always retrun to center of a scan when scan is done.
# SE - 2017-04-16 -- Updated to provide consistent screen prints to observing script.
# ====================================================================================================

from print_tools import *

# ====================================================================================================
# Define running parameters
# ====================================================================================================
n_img    = 3          # number of images averaged for flux computation
srange   = [-360,360] # range of setpoints to scan around initial setpoint
src      = 'UBC'      # Set to NAC for NAC source testing (UBC otherwise)
n_points = 5          # number of OPD steps to go, use odd numbers only
plot     = 'n'        # options for graphical output: 's' for screen, 'f' for file, 'b' for both, 'n' for none.
                      # The file will be saved as 'setpoint.eps' in the directory this script is located in.
save_data = 0         # Save data during setpoint optimization? 1 for Yes, 0 for No
max_step = 45         # Maximum single step with to change the setpoint, set to HUGE number for no constraint.
n_success_confirm = 1 # Number of successful setpoint confirmations required
# ====================================================================================================

print('')
info('Searching setpoint. Configuration parameters:')
print('  integrations per step     = ' + str(n_img))
print('  scan range per step       = ' + str(srange) + ' deg at H band.')
print('  number of scan steps      = ' + str(n_points))
print('  necessary successes       = ' + str(n_success_confirm + 1))
print('')

if src == 'UBC':
  forNAC = '0'
else: # if src == 'NAC'
  forNAC = '1'

# Import libraries
import time
from pyindi import *
import numpy as np
#import numpy as flx      # obsolete
#import numpy as pixels   # obsolete
from matplotlib import use as mpl_use

#pi is an instance of PyINDI. Here we connect to the server
pi=PyINDI(verbose=False)

print('')
if pi.getINDI("NOMIC.CamInfo.Go"):
  info('Camera is still integrating. Aborting.')
  quit()

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

# Define ROI ID numbers
pos1 = '3'  # on-source ROI
pos2 = '2'  # background ROI
pos3 = '1'  # background ROI

#Make sure we are not saving data, turn ON continuous acquisition.
pi.setINDI("NOMIC.Command.text", "1 contacq " + str(save_data) + " savedata", wait=True)

# Initiate arrays
null      = numpy.zeros((n_img))
setpoints = numpy.zeros((n_points+1))
null_tot  = numpy.zeros((n_points))
null_std  = numpy.zeros((n_points))

if (plot == 's') or (plot == 'b'):
  # Init plot		NOTE: The following two lines take ~5 sec, needs optimization!!!!!
  plt.ion()  # Turn on interactive mode
  plt.figure(1)
  plt.ylabel('Mean flux at null [ADU]')
  plt.xlabel('Phase [degrees]')
  plt.title('Setpoint optimization')
  plt.draw()
if (plot == 'f') or (plot == 'b'):
  plt.figure(1)
  plt.ylabel('Mean flux at null [ADU]')
  plt.xlabel('Phase [degrees]')
  plt.title('Setpoint optimization')

# Get integration time and initial setpoint

t_int  = pi.getINDI('NOMIC.CamInfo.IntTime') # get NOMIC integration time

# settings  = pi.getINDI('PLC.%sSettings.*' % (src)) # outdated
# settings  = pi.getINDI('PLC.PLSetpoint.*')
if src == 'UBC':
  setpoint_old = pi.getINDI('PLC.UBCSettings.PLSetpoint')
else: # if src = 'NAC'
  setpoint_old = pi.getINDI('PLC.NACSettings.PLSetpoint')

setpoint_current = setpoint_old # This parameter is used to keep track of the CURRENT setpoint during all offsets sent by the script.

# 1. Find the best setpoint
# *************************

# Print info to screen

info('Initial setpoint = %f degrees' % setpoint_old)

# compute some values before the loop
scan_step = np.sum(np.abs(srange)) / np.float(n_points - 1)     # step width of the OPD scan
half_steps = (n_points - 1) / 2                                 # half of ( the number of steps - 1 )

# Loop until offset is smaller than step width
k=0
offset = 100000.0
n_success = 0
setpoints_fit = []

if (src == 'UBC') and (not pi.getINDI("PLC.CloseLoop.Yes")): # Initial check if phase loop closed (can only be done on UBC)
    print "PHASE LOOP OPEN! Aborting."
    quit()

#while (offset >= scan_step):
while n_success < n_success_confirm + 1:  
  k=k+1
  
  # loop over setpoints (scan)
  for i in range(0, n_points + 1):
    
    # compute setpoints to scan
    setpoints[i] = setpoint_old + np.float(i - half_steps) * scan_step
    setpoints[-1] = setpoint_old # Last scan step returns to center.
    
    # Set new setpoint
    while np.abs(setpoints[i] - setpoint_current) > max_step: # go small steps ...
      setpoint_current = setpoint_current + np.sign(setpoints[i] - setpoint_current) * max_step
      pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_current) + ';forNAC=' + forNAC)
    setpoint_current = setpoints[i] # go final step ...
    pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_current) + ';forNAC=' + forNAC)
    
    # Read RIOs
    if i < n_points: # Ignore last step (back to center) for measurements.
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
  z = numpy.polyfit(setpoints[0:-1], null_tot, 2)    	# Numpy returns highest degree first
    
  setpoint_new = -0.5*z[1]/z[0]
  # if parabola has negative curvature of if fit moves setpoint too far:
  if (z[0] < 0) or (setpoint_new < setpoints[0]) or (setpoint_new > setpoints[-2]):
    if null_tot[0] < null_tot[-1]:
      setpoint_new = setpoints[1]
    else:
      setpoint_new = setpoints[-3]
    offset = 10000000.0
  else:
    offset = np.abs(setpoint_old - setpoint_new)
  
  # Plot results
  if (plot == 's') or (plot == 'b'):
    null_range = null_tot.max() - null_tot.min()
    plot_range_x = [setpoints[0] - scan_step, setpoints[-2] + scan_step]

    # display measurements and fit
    xp = numpy.linspace(plot_range_x[0], plot_range_x[1], 30)
    p  = numpy.poly1d(z)
    plt.errorbar(setpoints[0:-1], null_tot, null_std, marker='o', linestyle='.')
    plt.plot(xp, p(xp), linestyle='-', color='black')
    plt.draw()
    time.sleep(0.001)
  if (plot == 'f') or (plot == 'b'):
    null_range = null_tot.max() - null_tot.min()
    plot_range_x = [setpoints[0] - scan_step, setpoints[-2] + scan_step]
    xp = numpy.linspace(plot_range_x[0], plot_range_x[1], 30)
    p  = numpy.poly1d(z)
    plt.errorbar(setpoints[0:-1], null_tot, null_std, marker='o', linestyle='.')
    plt.plot(xp, p(xp), linestyle='-', color='black')
    plt.savefig('setpoint.pdf')
    time.sleep(0.001)
  
  if offset <= scan_step:
    n_success = n_success + 1
    setpoints_fit.append(setpoint_new)
    info('Iteration #' + str(k) + ' -- Success! :D')
    print('  New setpoint = %.1f.' % (setpoint_new))
  
  else:
    n_success = 0
    setpoints_fit = []
    info('Iteration #' + str(k) + ' -- FAILED! :(')
    print('  New setpoint = %.1f.' % (setpoint_new))
  
  # Pause for debugging
  # if raw_input("Press [ENTER] to confirm or [c] + [ENTER] to abort. ") == "c": quit()
  
  # Check for loop closed (can only be done on UBC)
  if (src == 'UBC') and (not pi.getINDI("PLC.CloseLoop.Yes")):
    info('PHASE LOOP OPEN! Aborting.')
    quit()
  else:
    setpoint_old = setpoint_new # Update setpoint scan center.

# count time
t1 = time.time()-t0

# Send determined setpoint
setpoint_final = np.average(setpoints_fit)
while np.abs(setpoint_final - setpoint_current) > max_step: # go small steps ...
  setpoint_current = setpoint_current + np.sign(setpoint_final - setpoint_current) * max_step
  pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_current) + ';forNAC=' + forNAC)
setpoint_current = setpoint_final # go final step ...
pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_current) + ';forNAC=' + forNAC)

info('Finished. New setpoint used: ' + str(setpoint_final))
print('')

#Now pause
#if raw_input("Press [ENTER] to confirm or [c] + [ENTER] to abort. ") == "c": quit()
#input("Press 1")

