from pyindi import * 
import numpy as np
from time import sleep
from multiprocessing import Process
from print_tools import *
from opd_controls import *

pi = PyINDI(verbose=False)

def take_darks(cfg):
  """
  Sets up NOMIC and takes darks. Uses the parameters 'save_nomic and
  'nomic_nomic_nsequences_dark' of a configuration dictionary and gets
  the integration time from the camera as set by the operator before.
  
  Usage:
  >> take_darks(hosts_std)
  """
  #Get initial FLAG
  f=pi.getFITS('NOMIC.DisplayImage.File', 'NOMIC.GetDisplayImage.Now')
  flag=f[0].header['FLAG']
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Print status information.
  print('')
  info('Now setting up NOMIC and taking darks. Configuration parameters:')
  print('  save_nomic            = ' + np.str(cfg['save_nomic']))
  print('  nomic_nsequences_dark = ' + np.str(cfg['nomic_nsequences_dark']))
  print('  DIT                   = ' + np.str(DIT) + ' (as set by operator)')
  
  if cfg['save_nomic']:
    savedata = 1
  else:
    savedata = 0
  
  n_sequ = cfg['nomic_nsequences_dark']
  # Set camera in safe state.
  pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
  pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  
  info('Moving in blank+tape.')
  #Set filters to flat
  pi.setINDI("Warm.NOMIC_FW2.command", "Blank+tape", timeout=20, wait=True)
  pi.setINDI("NOMIC.EditFITS.Keyword=FLAG;Value=DRK;Comment=SCI/CAL/DRK/FLT")
  
  # Set up camera for integration.
  pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, n_sequ), wait=True)
  
  info('Taking ' + np.str(n_sequ) + ' dark frames.')
  # Integrate
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
  
  info('Opening filter wheel 2.')
  #Open FW2
  pi.setINDI("Warm.NOMIC_FW2.command", "Open", timeout=20, wait=True)
  
  # Restore FLAG
  pi.setINDI("NOMIC.EditFITS.Keyword=FLAG;Value=%s;Comment=SCI/CAL/DRK/FLT" % ( flag ))
  
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  
  info('Integration finished.')
  print('')


def take_null(cfg):
  """
  Sets up NOMIC and takes null data. Uses the parameters 'save_nomic',
  'nomic_nsequences_null', 'nomic_dither_opd', 'nomic_dither_opd_pattern',
  'nomic_dither_opd_ndits', and 'nomic_dither_opd_off0' of a configuration
  dictionary and gets the integration time from the camere as set by the
  operator before.
  
  Usage:
   >> take_null(hosts_std)
  """
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Print status information.
  print('')
  info('Now collecting nulling data with NOMIC. Configuration parameters:')
  print('  save_nomic            = ' + np.str(cfg['save_nomic']))
  print('  nomic_nsequences_null = ' + np.str(cfg['nomic_nsequences_null']))
  print('  DIT                   = ' + np.str(DIT) + ' (as set by operator)')
  print('  OPD dither enabled?     ' + np.str(cfg['nomic_dither_opd']))
  
  if cfg['save_nomic']:
    savedata = 1
  else:
    savedata = 0
  
  # Set fits header to nulling (obstype = 2).
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=2;Comment=observation type', wait=False)
  
  # Start OPD dither pattern
  if cfg['nomic_dither_opd']:
    dither = Process(target=opd_dither, args=(cfg,))
    dither.start()
    sleep(0.3)
  
  # Integrate
  n_sequ = cfg['nomic_nsequences_null']
  file_number_start = pi.getINDI('NOMIC.CamInfo.FIndex')  # Get initial file number
  while True:
    try:
      # Set camera in safe state.
      pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
      pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
      
      # Set up camera for integration.
      pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
      pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
#      pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, n_sequ - 2), wait=True)
      pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, n_sequ), wait=True)
      
      # Integrate
      sleep(0.3)
      pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
      break
    except:
      file_number = pi.getINDI('NOMIC.CamInfo.FIndex')  # Get file number
      request('An error occured. Please recover error.')
      print('  When done, please enter the number of frames for this')
      print('  sequence you would still like to take.')
      print('  Enter 0 if you do not want to take additional frames')
      print('  or -1 to repeat the full sequence.')
      print('  We took ' + np.str(file_number - file_number_start) + ' files so far.')
      pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
      pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
      pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
      sleep(0.3)
      pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
      inp = int(raw_input())
      if inp == 0:
        info('Aborting sequence as requested.')
        break
      elif inp > 0:
        info('Taking ' + str(inp) + ' more frames.')
        n_sequ = inp        
      else:
        info('Restarting sequence as requested.')
        file_number_start = pi.getINDI('NOMIC.CamInfo.FIndex')  # Get initial file number
        if cfg['nomic_dither_opd']:
          dither.terminate()  # terminate and then restart dither pattern
          dither = Process(target=opd_dither, args=(cfg,))
          dither.start()
          sleep(0.3)
        continue
  
  if cfg['nomic_dither_opd']:
    dither.terminate()   # terminate dither pattern since we are done for this integration
  
#  # check phase loop
#  if not pi.getINDI('PLC.CloseLoop.Yes'):
#    request('Please close phase loop.')
#    while True:
#      sleep(0.5)
#      if pi.getINDI('PLC.CloseLoop.Yes'):
#        break
#  
#  # offsetting setpoint for star position integration
#  offset_setpoint()
#  
#  # set up camera for star position integration
#  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 2), wait=True)
#  
#  # Integrate
#  sleep(0.3)
#  pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
    
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  
  # Set obstype to 4 (undefined)
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=4;Comment=observation type', wait=False)
  
  info('Integration finished.')
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
  info('Now collecting photometry data with NOMIC. Configuration parameters:')
  print('  save_nomic            = ' + np.str(cfg['save_nomic']))
  print('  nomic_nsequences_phot = ' + np.str(cfg['nomic_nsequences_phot']))
  print('  DIT                   = ' + np.str(DIT) + ' (as set by operator)')
  
  if cfg['save_nomic']:
    savedata = 1
  else:
    savedata = 0
  
  # Set fits header to photometry (obstype = 0).
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=0;Comment=observation type', wait=False)
  
  n_sequ = cfg['nomic_nsequences_phot']
  while True:
    try:
      # Set camera in safe state.
      pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
      pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
      
      # Set up camera for integration.
      pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
      pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
      pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, n_sequ), wait=True)
      
      # Integrate
      sleep(0.3)
      pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
      break
    except:
      request('An error occured. Please recover error.')
      print('  When done, please enter the number of frames for this')
      print('  sequence you would still like to take.')
      print('  Enter 0 if you do not want to take additional frames')
      print('  or -1 to repeat the full sequence.')
      inp = int(raw_input())
      if inp == 0:
        info('Aborting sequence as requested.')
        break
      elif inp > 0:
        info('Taking ' + str(inp) + ' more frames.')
        n_sequ = inp        
      else:
        info('Restarting sequence as requested.')
        continue
  
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
    
  # Set obstype to 4 (undefined)
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=4;Comment=observation type', wait=False)
  
  info('Integration finished.')
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
  info('Now collecting background data with NOMIC. Configuration parameters:')
  print('  save_nomic            = ' + np.str(cfg['save_nomic']))
  print('  nomic_nsequences_bkgd = ' + np.str(cfg['nomic_nsequences_bkgd']))
  print('  DIT                   = ' + np.str(DIT) + ' (as set by operator)')
  
  if cfg['save_nomic']:
    savedata = 1
  else:
    savedata = 0
  
  # Set fits header to background (obstype = 3).
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=3;Comment=observation type', wait=False)
  
  n_sequ = cfg['nomic_nsequences_bkgd']
  while True:
    try:
      # Set camera in safe state.
      pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
      pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
      pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
      
      # Set up camera for integration.
      pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
      pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
      pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, n_sequ), wait=True)
      
      # Integrate
      sleep(0.3)
      pi.setINDI('NOMIC.Command.text', 'go', timeout=50000, wait=True)
      break
    except:
      request('An error occured. Please recover error.')
      print('  When done, please enter the number of frames for this')
      print('  sequence you would still like to take.')
      print('  Enter 0 if you do not want to take additional frames')
      print('  or -1 to repeat the full sequence.')
      inp = int(raw_input())
      if inp == 0:
        info('Aborting sequence as requested.')
        break
      elif inp > 0:
        info('Taking ' + str(inp) + ' more frames.')
        n_sequ = inp        
      else:
        info('Restarting sequence as requested.')
        continue
  
  # Set camera in continuous.
  pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
  pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
  pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
  sleep(0.3)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  
  # Set obstype to 4 (undefined)
  pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=4;Comment=observation type', wait=False)
  
  info('Integration finished.')
  print('')


def wait_AO_loop(cfg, take_bkg = True):
  """
  Waits for the AO loop to be closed. Uses the parameters 'save_nomic',
  and 'nomic_nsequences_null', and 'nomic_nwait_AO_loop' of a configuration
  dictionary. Takes up to [nomic_nsequences_null] background frames in groups
  of [nomic_nwait_AO_loop] while waiting if 'take_bkg = True' (default).
  
  Usage:
   >> wait_AO_loop(hosts_std)
   >> wait_AO_loop(hosts_std, take_bkg = False)
  """
  
  # Get DIT as set by operator.
  DIT = pi.getINDI('NOMIC.CamInfo.IntTime')
  
  # Print status information.
  print('')
  if (pi.getINDI('LBTO.AOStatus.L_AOStatus') == 'AORunning') and (pi.getINDI('LBTO.AOStatus.R_AOStatus') == 'AORunning'):
    info('AO loop closed, continuing.')
    return
  request('Please close AO loop.')
  if take_bkg == True:
    print('  Taking background frames in the mean time. Configuration parameters:')
    print('  save_nomic             = ' + np.str(cfg['save_nomic']))
    print('  nomic_nwait_AO_loop    = ' + np.str(cfg['nomic_nwait_AO_loop']))
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
    pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
    pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, cfg['nomic_nwait_AO_loop']), wait=True)
    
    while n_done < cfg['nomic_nsequences_null'] and not ((pi.getINDI('LBTO.AOStatus.L_AOStatus') == 'AORunning') and (pi.getINDI('LBTO.AOStatus.R_AOStatus') == 'AORunning')):
      print('  AO loop still open, taking %i background frames.' % (cfg['nomic_nwait_AO_loop']))
      sleep(0.3)
      pi.setINDI('NOMIC.Command.text', "go", timeout=50000, wait=True)
      n_done = n_done + cfg['nomic_nwait_AO_loop']
    
    # Set camera in continuous.
    pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
    pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
    pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
    sleep(0.3)
    pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
    
    if not ((pi.getINDI('LBTO.AOStatus.L_AOStatus') == 'AORunning') and (pi.getINDI('LBTO.AOStatus.R_AOStatus') == 'AORunning')):
      print('')
      print('  AO loop still open, but took enough background frames.')
      print('  Stoped taking background frames, still waiting.')
      print('')
      
  i = 0
  while not ((pi.getINDI('LBTO.AOStatus.L_AOStatus') == 'AORunning') and (pi.getINDI('LBTO.AOStatus.R_AOStatus') == 'AORunning')):
    i = i + 1
    if i < 5:
      print('  AO loop still open, waiting ...')
    if i == 5:
      print('  AO loop still open, continue waiting quietly ...')
    sleep(1.0)
    
  info('AO loop closed. %i background files taken.' % n_done)
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
    info('Phase loop closed, continuing.')
    return
  request('Please close phase loop.')
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
    # Set fits header to nulling (obstype = 2).
    pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=2;Comment=observation type', wait=False)

    # Set camera in safe state.
    pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
    pi.setINDI('NOMIC.Command.text', '0 savedata', wait=True)
    pi.setINDI('NOMIC.Command.text', '0 loglevel', wait=True)
    pi.setINDI('NOMIC.Command.text', '0 autodispwhat', wait=True)
    pi.setINDI('NOMIC.Command.text', '%f %i %i lbtintpar' % (DIT, 1, 1), wait=True)
    
    # Set up camera for integration.
    pi.setINDI('NOMIC.Command.text', '%i savedata' % savedata, wait=True)
    pi.setINDI('NOMIC.Command.text', '1 autodispwhat', wait=True)
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
    
    # Set obstype to 4 (undefined)
    pi.setINDI('NOMIC.EditFITS.Keyword=OBSTYPE;Value=4;Comment=observation type', wait=False)

  
  i = 0
  while not pi.getINDI('PLC.CloseLoop.Yes'):
    i = i + 1
    if i < 5:
      print('  Phase loop still open, waiting ...')
    if i == 5:
      print('  Phase loop still open, continue waiting quietly ...')
    sleep(1.0)
    
  info('Phase loop closed. %i background files taken.' % n_done)
  print('')


