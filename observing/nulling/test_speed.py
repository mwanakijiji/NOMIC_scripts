#!/usr/bin/python
#test speed script
#DD-130916

from pyindi import * 
import os 
import time

# Init time counter 
t0 = time.time()

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=False)

# Running parameters
n_nod     = 4   # Number of nod pairs before the photometry
offy      = 2.3 # Nodding y offset in arcsec
sign      = 1   # Nodding direction (-1 for up -> down, 1 for down -> up) 
save      = 0   # Whether to save (=1) or not (=0)
skip_phot = 0   # 1 to skip the photometry
       
#Running parameters NOMIC
dit_n1  = 0.060
n_coadd = 1
n_null1 = 10

#Running parameters LMIRCAM
dit_l   = 0.029       # 0 to turn off LMIRCAM data acquisition
n_spec  = 2

#Set fits header to nulling (obstype = 2) and spectro (obstype = 1)
pi.setINDI("NOMIC.EditFITS.Keyword=OBSTYPE;Value=2;Comment=observation type", wait=False)
if dit_l > 0:
	pi.setINDI("LMIRCAM.EditFITS.Keyword=OBSTYPE;Value=8;Comment=observation type", wait=False)

#Get current NIL_OPW position
opw_pos = pi.getINDI("Warm.NIL_OPW_status.PosNum", wait=False)
	
# NULL SEQUENCE (Nod down)
#Turn off log, contacq, save data, and turn off display (for speed)
pi.setINDI("NOMIC.Command.text", "0 loglevel 0 contacq %i savedata 0 autodispwhat %f %i %i lbtintpar go" % (save,dit_n1, n_coadd, n_null1), wait=False)
if dit_l > 0:
	pi.setINDI("LMIRCAM.Command.text", "0 loglevel 0 contacq %i savedata %f %i %i lbtintpar" % (save,dit_l, n_coadd, n_spec), wait=False)
	pi.setINDI("LMIRCAM.Command.text", "go", timeout=500, wait=False)

print time.time()-t0

#Restore log information
pi.setINDI("NOMIC.Command.text", "1 loglevel", wait=False)
if dit_l > 0:
	pi.setINDI("LMIRCAM.Command.text", "1 loglevel", wait=False)
	
#turn off save data
pi.setINDI("NOMIC.Command.text", "0 savedata", wait=False)
if dit_l > 0:
	pi.setINDI("LMIRCAM.Command.text", "0 savedata", wait=False)
