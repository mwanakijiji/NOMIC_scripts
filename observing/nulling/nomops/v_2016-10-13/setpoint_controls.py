from pyindi import * 
import numpy as np
import time
from matplotlib import use as mpl_use
import matplotlib.pyplot as plt
import warnings
from print_tools import *

pi = PyINDI()
mpl_use('tkagg')    # needed for interactive mode


# Ignore deprecation warnings
def fxn():
  warnings.warn('deprecated', DeprecationWarning)
with warnings.catch_warnings():
  warnings.simplefilter('ignore')
  fxn()

def find_setpoint(cfg):
  
  
  
  if cfg['pzt'] == 'UBC':
    forNAC = '0'
  else: # if cfg['pzt'] == 'NAC'
    forNAC = '1'
  
  # Start time counter
  t0 = time.time()
  
  #pi is an instance of PyINDI. Here we connect to the server
  pi=PyINDI(verbose=False)
  
  # Define ROI ID numbers
  ROIIDs = [3,2,1]
  
  # Set camera in safe state
  pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  # Turn ON continuous acquisition, save data if requested.
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  if cfg['nomic_setpoint_savedata'] == True:
    pi.setINDI('NOMIC.Command.text', '1 savedata', wait=True)
  
  # Initialize arrays
  null      = np.zeros((cfg['nomic_setpoint_img_stack']))
  setpoints = np.zeros((cfg['nomic_setpoint_n_scan']+1))
  null_tot  = np.zeros((cfg['nomic_setpoint_n_scan']))
  null_std  = np.zeros((cfg['nomic_setpoint_n_scan']))
  
  if (cfg['nomic_setpoint_output'] == 'screen') or (cfg['nomic_setpoint_output'] == 'both'):
    print('')
    print('  Initializing display.')
    # Init plot		NOTE: The following two lines take ~5 sec, needs optimization!!!!!
    plt.ion()  # Turn on interactive mode
    plt.figure(1)
    plt.ylabel('Mean flux at null [ADU]')
    plt.xlabel('Phase [degrees]')
    plt.title('Setpoint optimization')
    plt.draw()
  if (cfg['nomic_setpoint_output'] == 'file') or (cfg['nomic_setpoint_output'] == 'both'):
    print('')
    print('  Plotting to file.')
    plt.figure(1)
    plt.ylabel('Mean flux at null [ADU]')
    plt.xlabel('Phase [degrees]')
    plt.title('Setpoint optimization')
  
  # Get integration time and initial setpoint
  DIT  = pi.getINDI('NOMIC.CamInfo.IntTime') # get NOMIC integration time
  
  if cfg['pzt'] == 'UBC':
    setpoint_old = pi.getINDI('PLC.UBCSettings.PLSetpoint')
  else: # if cfg['pzt'] = 'NAC'
    setpoint_old = pi.getINDI('PLC.NACSettings.PLSetpoint')
  
  setpoint_current = setpoint_old # This parameter is used to keep track of the CURRENT setpoint during all offsets sent by the script.
  
  # 1. Find the best setpoint
  # *************************
  
  # Print info to screen
  print('')
  print('  OPTIMIZING SETPOINT')
  
  print('  Initial setpoint = %f degrees' % setpoint_old)
  
  # compute some values before the loop
  scan_step = np.sum(np.abs(cfg['nomic_setpoint_scan_range'])) / np.float(cfg['nomic_setpoint_n_scan'] - 1)     # step width of the OPD scan
  half_steps = (cfg['nomic_setpoint_n_scan'] - 1) / 2                                 # half of ( the number of steps - 1 )
  
  # Loop until offset is smaller than step width
  k = 0
  offset = 100000.0
  n_success = 0
  setpoints_fit = []
  
  if (cfg['pzt'] == 'UBC') and (not pi.getINDI('PLC.CloseLoop.Yes')): # Initial check if phase loop closed (can only be done on UBC)
    if raw_input('REQUEST: Phase loop open. Please close loop and press [ENTER] to continue or [c] + [ENTER] to abort. ') == 'c': quit()
  
  while n_success < cfg['nomic_setpoints_n_confirm'] + 1:
    k=k+1
    
    # loop over setpoints (scan)
    for i in range(0, cfg['nomic_setpoint_n_scan'] + 1):
      
      # compute setpoints to scan
      setpoints[i] = setpoint_old + np.float(i - half_steps) * scan_step
      setpoints[-1] = setpoint_old # Last scan step returns to center.
      
      # Set new setpoint
      while np.abs(setpoints[i] - setpoint_current) > cfg['nomic_setpoint_max_step']: # go small steps ...
        setpoint_current = setpoint_current + np.sign(setpoints[i] - setpoint_current) * cfg['nomic_setpoint_max_step']
        pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_current) + ';forNAC=' + forNAC)
      setpoint_current = setpoints[i] # go final step ...
      pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_current) + ';forNAC=' + forNAC)
      
      # Read RIOs
      if i < cfg['nomic_setpoint_n_scan']: # Ignore last step (back to center) for measurements.
        for j in range(cfg['nomic_setpoint_img_stack']):
          time_stats_0 = time.time()
          null[j] = pi.getINDI ('NOMIC.NullingStats.Mean3') - 0.5 * (pi.getINDI ('NOMIC.NullingStats.Mean1') + pi.getINDI ('NOMIC.NullingStats.Mean2'))
          time.sleep(np.max([0.0, t_int - (time.time() - time_stats_0)]))      # wait for 1 integration on nomic - time it took to get the stats (previous line), but not less then 0.0s
        
        # Compute mean value over stacked frames
        null_tot[i] = null.mean()
        null_std[i] = null.std()
    
    # Find new setpoint by parabola fit

    z = np.polyfit(setpoints[0:-1], null_tot, 2)    	# Numpy returns highest degree first
    
    setpoint_new = -0.5*z[1]/z[0]
    # if parabola has negative curvature of ir fit moves setpoint too far:
    if (z[0] < 0) or (setpoint_new < setpoints[0]) or (setpoint_new > setpoints[-2]):
      if null_tot[0] < null_tot[-1]:
        setpoint_new = setpoints[1]
      else:
        setpoint_new = setpoints[-3]
      offset = 10000000.0
    else:
      offset = np.abs(setpoint_old - setpoint_new)
    
    print('  Iteration %i -- min. flux %.2f max. flux %.2f -- new setpoint = %.1f' % (k,  np.min(null_tot), np.max(null_tot), setpoint_new))
    
    # Plot results
    if (cfg['nomic_setpoint_output'] == 'screen') or (cfg['nomic_setpoint_output'] == 'both'):
      null_range = null_tot.max() - null_tot.min()
      plot_range_x = [setpoints[0] - scan_step, setpoints[-2] + scan_step]
  
      # display measurements and fit
      xp = numpy.linspace(plot_range_x[0], plot_range_x[1], 30)
      p  = numpy.poly1d(z)
      plt.errorbar(setpoints[0:-1], null_tot, null_std, marker='o', linestyle='.')
      plt.plot(xp, p(xp), linestyle='-', color='black')
      plt.draw()
      time.sleep(0.001)
    if (cfg['nomic_setpoint_output'] == 'file') or (cfg['nomic_setpoint_output'] == 'both'):
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
      print('  Success: ', n_success)
    else:
      n_success = 0
      setpoints_fit = []
      print('  FAILED')
    
    # Pause for debugging
#    if raw_input('  Press [ENTER] to confirm or [c] + [ENTER] to abort. ') == 'c': quit()
    
    # Check for loop closed (can only be done on UBC)
    if (cfg['pzt'] == 'UBC') and (not pi.getINDI('PLC.CloseLoop.Yes')):
      n_success = 0
      if raw_input('REQUEST: Phase loop open. Please close loop and press [ENTER] to continue or [c] + [ENTER] to abort. ') == 'c': quit()
    else:
      setpoint_old = setpoint_new # Update setpoint scan center.
  
  # count time
  t1 = time.time()-t0
  
  # Print status
  print('  Time to optimize setpoint: %fs' % (t1))
  
  # Send determined setpoint
  setpoint_final = np.average(setpoints_fit)
  while np.abs(setpoint_final - setpoint_current) > cfg['nomic_setpoint_max_step']: # go small steps ...
    setpoint_current = setpoint_current + np.sign(setpoint_final - setpoint_current) * cfg['nomic_setpoint_max_step']
    pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_current) + ';forNAC=' + forNAC)
  setpoint_current = setpoint_final # go final step ...
  pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_current) + ';forNAC=' + forNAC)
  
  print('  New setpoint used: ', setpoint_final)


