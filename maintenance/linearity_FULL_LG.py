#!/usr/bin/python
#Darks/flats/linearity script
#DD-130617

from pyindi import * 

#pi is an instance of PyINDI. Here we connect to the lmircam server
pi=PyINDI(verbose=True)

#turn on save data
pi.setINDI("NOMIC.Command.text", "1 savedata")

#set filters to dark
#pi.setINDI("Warm.NOMIC_FW1.command", "Nprime", timeout=20)

#save frames
for j in range(40):
	print float(j+1)*0.027
	pi.setINDI("NOMIC.Command.text", "%f 1 10 lbtintpar 500 sleep" % ((j+1)*0.027), timeout=15)
	pi.setINDI("NOMIC.Command.text", "go", timeout=15)
	
#set filters to flat
pi.setINDI("Warm.NOMIC_FW2.command", "Home", timeout=20)

#save frames
for j in range(40):
	print float(j+1)*0.027
	pi.setINDI("NOMIC.Command.text", "%f 1 10 lbtintpar 500 sleep" % ((j+1)*0.027), timeout=15)
	pi.setINDI("NOMIC.Command.text", "go", timeout=15)

#turn off save data
pi.setINDI("NOMIC.Command.text", "0 savedata")
