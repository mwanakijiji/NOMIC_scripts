from pyindi import *
pi = PyINDI()
import numpy as np
from time import sleep

def take_null(cfg):
  """
  Sets up NOMIC and takes null data. Uses the parameters 'save_nomic' and
  'nomic_nsequences_null' of a configuration dictionary and gets the
  integration time from the camere as set by the operator before.
  """
  
  # Get DIT set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Print status information.
  print('')
  print('INFO: Now collecting nulling data with NOMIC. Configuration parameters:')
  print('  save_nomic = ' + np.str(cfg['save_nomic']))
  print('  nomic_nsequences_null = ' + np.str(cfg['nomic_nsequences_null']))
  print('  DIT = ' + np.str(DIT) + ' (as set by operator)')
  print('')
  
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
  
  # Display one frame.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', wait=True)

