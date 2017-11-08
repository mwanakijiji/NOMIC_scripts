#!/usr/bin/python
#Script to take darks with NOMIC
#DD-160414: basic scripts to take darks (must be run at the beginning of each nulling pointing)

# import Python libraries
from pyindi import * 
import os 
import time

# number of dark frames to take
n_drk = 500

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=False)

#Get initial FLAG  
f=pi.getFITS("NOMIC.DisplayImage.File", "NOMIC.GetDisplayImage.Now")
flag=f[0].header['FLAG']

#Set integration parameters
pi.setINDI("NOMIC.Command.text", "0 contacq 0 loglevel 1 savedata %i obssequences" % (n_drk), wait=True)

#Set filters to flat
pi.setINDI("Warm.NOMIC_FW2.command", "Blank+tape", timeout=20, wait=True)
pi.setINDI("NOMIC.EditFITS.Keyword=FLAG;Value=DRK;Comment=SCI/CAL/DRK/FLT")

# Take data
pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)

#Open FW2
pi.setINDI("Warm.NOMIC_FW2.command", "Open", timeout=20, wait=True)

# Restore FLAG
pi.setINDI("NOMIC.EditFITS.Keyword=FLAG;Value=%s;Comment=SCI/CAL/DRK/FLT" % ( flag ))

#Restore log information and turn off data saving
pi.setINDI("NOMIC.Command.text", "1 loglevel 0 savedata", wait=False)
