from pyindi import * 
import numpy as np
from time import sleep
pi = PyINDI()

def take_null(cfg):
  """
  Sets up NOMIC and takes null data. Uses the parameters 'save_nomic' and
  'nomic_nsequences_null' of a configuration dictionary and gets the
  integration time from the camere as set by the operator before.
  
  Usage:
   >> take_null(hosts_std)
  """
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Print status information.
  print('')
  print('INFO: Now collecting nulling data with NOMIC. Configuration parameters:')
  print('  save_nomic            = ' + np.str(cfg['save_nomic']))
  print('  nomic_nsequences_null = ' + np.str(cfg['nomic_nsequences_null']))
  print('  DIT                   = ' + np.str(DIT) + ' (as set by operator)')
  
  if cfg['save_nomic']:
    savedata = 1
  else:
    savedata = 0
  
  # Set fits header to nulling (obstype = 2).
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=2;Comment=observation type', wait=False)
  
  # Set camera in safe state.
  pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  # Display one frame.
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', wait=True)
  
  # Set up camera for integration.
  pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, cfg['nomic_nsequences_null']), wait=True)
  
  # Integrate
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
  
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  
  print('INFO: Integration finished.')
  print('')


def take_photometry(cfg):
  """
  Sets up NOMIC and takes photomatry data. Uses the parameters 'save_nomic'
  and 'nomic_nsequences_phot' of a configuration dictionary and gets the
  integration time from the camere as set by the operator before.
  
  Usage:
   >> take_photometry(hosts_std)
  """
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Print status information.
  print('')
  print('INFO: Now collecting photometry data with NOMIC. Configuration parameters:')
  print('  save_nomic            = ' + np.str(cfg['save_nomic']))
  print('  nomic_nsequences_phot = ' + np.str(cfg['nomic_nsequences_phot']))
  print('  DIT                   = ' + np.str(DIT) + ' (as set by operator)')
  
  if cfg['save_nomic']:
    savedata = 1
  else:
    savedata = 0
  
  # Set fits header to photometry (obstype = 0).
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=0;Comment=observation type', wait=False)
  
  # Set camera in safe state.
  pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  # Display one frame.
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', wait=True)
  
  # Set up camera for integration.
  pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, cfg['nomic_nsequences_phot']), wait=True)
  
  # Integrate
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
  
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', wait=True)
    
  print('INFO: Integration finished.')
  print('')


def take_background(cfg):
  """
  Sets up NOMIC and takes background data. Uses the parameters 'save_nomic'
  and 'nomic_nsequences_bkgd' of a configuration dictionary and gets the
  integration time from the camere as set by the operator before.
  
  Usage:
   >> take_background(hosts_std)
  """
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Print status information.
  print('')
  print('INFO: Now collecting background data with NOMIC. Configuration parameters:')
  print('  save_nomic            = ' + np.str(cfg['save_nomic']))
  print('  nomic_nsequences_bkgd = ' + np.str(cfg['nomic_nsequences_bkgd']))
  print('  DIT                   = ' + np.str(DIT) + ' (as set by operator)')
  
  if cfg['save_nomic']:
    savedata = 1
  else:
    savedata = 0
  
  # Set fits header to nulling (obstype = 2).
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=2;Comment=observation type', wait=False)
  
  # Set camera in safe state.
  pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  # Display one frame.
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', wait=True)
  
  # Set up camera for integration.
  pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, cfg['nomic_nsequences_bkgd']), wait=True)
  
  # Integrate
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
  
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', wait=True)
    
  print('INFO: Integration finished.')
  print('')


def wait_phase_loop(cfg, take_bkg = True):
  """
  Waits for the phase loop to be closed. Uses the parameters 'save_nomic',
  and 'nomic_nsequences_null', and 'nomic_nwait_phase_loop' of a configuration
  dictionary. Takes up to [nomic_nsequences_null] background frames in groups
  of [nomic_nwait_phase_loop] while waiting if 'take_bkg = True' (default).
  
  Usage:
   >> wait_phase_loop(hosts_std)
   >> wait_phase_loop(hosts_std, take_bkg = False)
  """
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Print status information.
  print('')
  if pi.getINDI('PLC.CloseLoop.Yes'):
    print('INFO: Phase loop closed, continuing.')
    return
  print('REQUEST: Please close phase loop.')
  if take_bkg == True:
    print('  Taking background frames in the mean time. Configuration parameters:')
    print('  save_nomic             = ' + np.str(cfg['save_nomic']))
    print('  nomic_nwait_phase_loop = ' + np.str(cfg['nomic_nwait_phase_loop']))
    print('  DIT                    = ' + np.str(DIT) + ' (as set by operator)')
  else:
    print('  *NOT* taking background frames in the mean time.')
  
  if cfg['save_nomic']:
    savedata = 1
  else:
    savedata = 0
  
  n_done = 0 
  if take_bkg == True:
    # Set camera in safe state.
    pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
    pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
    pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
    pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
    pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
    
    # Set up camera for integration.
    pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
    pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
    pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, cfg['nomic_nwait_phase_loop']), wait=True)
    
    while n_done < cfg['nomic_nsequences_null'] and not pi.getINDI('PLC.CloseLoop.Yes'):
      print('  Phase loop still open, taking %i background frames.' % (cfg['nomic_nwait_phase_loop']))
      sleep(0.3)
      pi.setINDI('NOMIC.Command.text', "go", timeout=50000, wait=True)
      n_done = n_done + cfg['nomic_nwait_phase_loop']
    
    # Set camera in continuous.
    pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
    pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
    pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
    sleep(0.3)
    pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
    
    if not pi.getINDI('PLC.CloseLoop.Yes'):
      print('')
      print('  Phase loop still open, but took enough background frames.')
      print('  Stoped taking background frames, still waiting.')
      print('')
      
  
  i = 0
  while not pi.getINDI('PLC.CloseLoop.Yes'):
    i = i + 1
    if i < 5:
      print('  Phase loop still open, waiting ...')
    if i == 5:
      print('  Phase loop still open, continue waiting quietly ...')
    sleep(1.0)
    
  print('INFO: Phase loop closed. %i background files taken.' % n_done)
  print('')


