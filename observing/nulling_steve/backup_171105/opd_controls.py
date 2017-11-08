from pyindi import * 
import numpy as np
from time import sleep
from print_tools import *

pi = PyINDI()

def offset_setpoint(inverse=False):
  """
  Offsets the OPD setpoint by +360 deg (in K band). If inverse=True is
  provided, this will undo anoffset sent before.
  
  Usage:
   >> offset_setpoint()
  """
  
  offset = 360.0
  if inverse:
    offset = -360.0
  
  setpoint_old = pi.getINDI('PLC.UBCSettings.PLSetpoint')
  pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_old + offset) + ';forNAC=0')

def opd_dither(cfg):
  """
  Initializes an OPD dither pattern. Uses the parameters
  'nomic_dither_opd_pattern', and 'nomic_dither_opd_ndits'
  of a configuration dictionary and gets the initial file
  number from the camera.
  
  Usage:
   >> opd_dither(cfg)
  """
  
  setpoint_new = pi.getINDI('PLC.UBCSettings.PLSetpoint')
  file_number = pi.getINDI('NOMIC.CamInfo.FIndex')  # Get initial file number
  offsets = np.array(cfg['nomic_dither_opd_pattern']) * 5.0 * 180.0 / np.pi   # input in rad at 11um, but commandet offsets in deg in K band
  pi.setINDI('NOMIC.EditFITS.Keyword=spdthpos;Value=0.0;Comment=setpoint dither position (offset from nominal setpoint) in rad')
  while True:
    for i_step in range(0, len(cfg['nomic_dither_opd_pattern'])):
      file_number = file_number + cfg['nomic_dither_opd_ndits'][i_step]
      try:
        pi.evalINDI ('"NOMIC.CamInfo.FIndex" >= %d' % file_number, timeout=900)   # wait for cfg['nomic_dither_opd_ndits'][i] new files to arrive
      except:
        info('OPD dither offset timed out (more than 15 min since last offset)')
        print('  or was interrupted.')
        print('  Make sure to restart OPD dither pattern.')
        return()
      setpoint_old = pi.getINDI('PLC.UBCSettings.PLSetpoint')   # ask for current setpoint
      if (setpoint_old - setpoint_new) > 2.9: # if expected setpoint is more than ~0.01 rad (at 11um) different from current setpoint
        info('Setpoint has changed between two dither positions.')
      setpoint_new = setpoint_old + offsets[i_step]             # determine new setpoint
      pi.setINDI('NOMIC.EditFITS.Keyword=spdthpos;Value=' + str(np.sum(offsets[:i_step+1])) + ';Comment=setpoint dither position (offset from nominal setpoint) in rad')
      pi.setINDI('PLC.PLSetpoint.PLSetpoint=' + str(setpoint_new) + ';forNAC=0')   # send a dither offset
