#!/usr/bin/python
#Bill's diagnostic script
#DD-141102 (based on Bill's request)

import time
from pyindi import * 

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=True)

#set filters to dark
pi.setINDI("Warm.NOMIC_FW2.command", "Blank+tape", timeout=20)

#turn on save data
pi.setINDI("NOMIC.Command.text", "1 savedata")

#now take Bill's diagnostic data
pi.setINDI("NOMIC.EditFITS.Keyword=FLAG;Value=DRK;Comment=SCI/CAL/DRK/FLT")    
pi.setINDI("NOMIC.Command.text", "0 contacq")
pi.setINDI("NOMIC.Command.text", "2 3 pagbw")
pi.setINDI("NOMIC.Command.text", '" Ch4-11_512x256"  subsectmap')
pi.setINDI("NOMIC.Command.text", "4095 paoffset")
time.sleep(1)
pi.setINDI("NOMIC.Command.text", "0 autodispwhat")
pi.setINDI("NOMIC.Command.text", "0 loglevel")
pi.setINDI("NOMIC.Command.text", "%f 1 500 lbtintpar 500 sleep" % (0.003), timeout=15)
pi.setINDI("NOMIC.Command.text", "go", timeout=50000, wait=True)

#turn off save data
pi.setINDI("NOMIC.Command.text", "0 savedata")
pi.setINDI("NOMIC.Command.text", "1 autodispwhat")
pi.setINDI("NOMIC.Command.text", "1 loglevel")

