from pyindi import * 
import numpy as np
from print_tools import *
from time import sleep

pi = PyINDI()

def nod(cfg, nod_dir, move_tel=True, side='both'):
  """
  Nods the telescope and updates the position of the PHASECAM beams
  and the ROIs on the NOMIC display. Uses the parameters 'pzt',
  'opw_offset_nod', and 'phasecam_beam2_offset_nod' ofa configuration
  dictionary and the nod direction ('up' or 'down') as indicated when
  calling the function.
  
  Can also 'ignore' the telescopes, i.e., not move the telescope but
  everything else. This is useful to update all PHASECAM and NOMIC
  positions after a nod was done with the telescopes only (e.g., see
  below).
  
  Can also move one side only by indicating side='left' or side='right'
  when calling the function. This will ONLY move one side of the
  telescope and not move anything in PHASECAM or NOMIC.
  
  Usage:
   >> nod(hosts_std, 'up')
   >> nod(hosts_std, 'up', move_tel = False)
   >> nod(hosts_std, 'up', side='left')
  """
  
  print('')
  if (move_tel == True) and (side == 'both'):
    info('Nodding the telescope. Configuration parameters:')
  elif (move_tel == True) and (side != 'both'):
    info('Nodding the %s side only. Configuration parameters:' % (side))
  else:
    info('Doing a "nod" on PHASECAM and NOMIC only. Configuration parameters:')
  print('  nod_dir                   = ' + nod_dir)
  print('  nod_throw                 = ' + str(cfg['nod_throw']) + ' arcsec')
  if side == 'both':
    print('  pzt                       = ' + cfg['pzt'])
    print('  opw_offset_nod            = ' + str(cfg['opw_offset_nod']) + ' enc')
    print('  phasecam_beam2_offset_nod = ' + str(cfg['phasecam_beam2_offset_nod']) + ' pix')
  print('')
  
  if nod_dir == 'up':
    sign = 1
  elif nod_dir == 'down':
    sign = -1
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Take a background (and repeat to make sure it is a good one)
  # Set camera in safe state.
  pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  # Set up camera for integration.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  # Integrate.
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
  
  # Use background.
  pi.setINDI('NOMIC.Command.text', 'rawbg', timeout=50000, wait=True)
  
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  
  if side == 'both':
    #Get current NIL_OPW position
    opw_pos = pi.getINDI('Warm.NIL_OPW_status.PosNum', wait=False)
    
    #Get beam 2 Y position
    settings  = pi.getINDI('PLC.%sSettings.*' % (cfg['pzt']), wait=True)
    beam2_y   = settings['PLC.%sSettings.Beam2_y' % (cfg['pzt'])]
  
  # Open phase loop
  pi.setINDI('PLC.CloseLoop.Yes=Off')
  
  if side == 'both':
    # Move OPW
    pi.setINDI('Warm.NIL_OPW.command', '%i' % (opw_pos - sign * cfg['opw_offset_nod']), wait=False)
  
  if move_tel == True:
    # Nod the telescope side(s)
    pi.setINDI('LBTO.OffsetPointing.CoordSys', 'DETXY', 'LBTO.OffsetPointing.OffsetX', 0, 'LBTO.OffsetPointing.OffsetY', (sign * cfg['nod_throw']), 'LBTO.OffsetPointing.Side', side, 'LBTO.OffsetPointing.Type', 'REL', wait=False)
  
  if side == 'both':
    # Move beam 2 position
    settings['PLC.%sSettings.Beam2_y' % (cfg['pzt'])] = beam2_y + sign * cfg['phasecam_beam2_offset_nod']
    pi.setINDI(settings)
    
    # ROI info
    ROIIDs = [1,2,3]
    ROI_nod = np.int(cfg['nod_throw'] / 0.018)     # Nodding offset in pix
  
    # Move ROI positions
    for i in range(0, len(ROIIDs)):
      qroi = dict([('NOMIC.QueryROI.ROIID', ROIIDs[i]), ('NOMIC.QueryROI.X', 0.0), ('NOMIC.QueryROI.Y', 0.0), ('NOMIC.QueryROI.H', 0.0), ('NOMIC.QueryROI.W', 0.0)])
      pi.setINDI(qroi)
      qroi = pi.getINDI('NOMIC.QueryROI.ROIID', 'NOMIC.QueryROI.X', 'NOMIC.QueryROI.Y', 'NOMIC.QueryROI.H', 'NOMIC.QueryROI.W')
      droi = dict([('NOMIC.DefROI.ROIID', ROIIDs[i]), ('NOMIC.DefROI.X', qroi['NOMIC.QueryROI.X']), ('NOMIC.DefROI.Y', qroi['NOMIC.QueryROI.Y'] + sign * ROI_nod), ('NOMIC.DefROI.H', qroi['NOMIC.QueryROI.H']), ('NOMIC.DefROI.W', qroi['NOMIC.QueryROI.W'])])
      pi.setINDI(droi)
      
    
  print('')
  info('Nod finished.')
  print('')


def offset_background(cfg, off_dir):
  """
  Offsets the telescope pointing to take a background with the target
  outside the field of view. Uses the parameters '...', '...', and '...'
  of a configuration dictionary and the offset direction ('up' or 'down')
  as indicated when calling the function.
  
  Usage:
   >> offset_background(hosts_std, 'down')
  """
  
  print('')
  info('Offsetting the telescope. Configuration parameters:')
  print('  off_dir                   = ' + off_dir)
  print('  off_throw                 = ' + str(cfg['off_throw']) + ' arcsec')
  print('')
  
  if off_dir == 'up':
    sign = 1
  elif off_dir == 'down':
    sign = -1
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Take a background (and repeat to make sure it is a good one)
  # Set camera in safe state.
  pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  # Set up camera for integration.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  # Integrate.
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
  
  # Use background.
  pi.setINDI('NOMIC.Command.text', 'rawbg', timeout=50000, wait=True)
  
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  
  # Open phase loop
  pi.setINDI('PLC.CloseLoop.Yes=Off')
  
  # offset the telescope side(s)
  pi.setINDI('LBTO.OffsetPointing.CoordSys', 'DETXY', 'LBTO.OffsetPointing.OffsetX', 0, 'LBTO.OffsetPointing.OffsetY', (sign * cfg['off_throw']), 'LBTO.OffsetPointing.Side', 'both', 'LBTO.OffsetPointing.Type', 'REL', wait=False)
  
  # Wait for AO loop to be closed
  i = 0
  while not (pi.getINDI('LBTO.AOStatus.L_AOStatus') == 'AORunning') or not (pi.getINDI('LBTO.AOStatus.R_AOStatus') == 'AORunning'):
    i = i + 1
    if i < 10:
      print('  Waiting for AO loop(s) to close ...')
    if i == 10:
      print('  AO loop(s) still open, continue waiting quietly ...')
    sleep(1.0)
  print('AO loops closed.')
  
  print('')
  info('Offset finished.')
  print('')


