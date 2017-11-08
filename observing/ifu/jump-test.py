#!/usr/bin/python

# testing jumping cursor

from pyindi import *         # import pyINDI
import time

pi     = PyINDI(verbose=False)

while True:
    f       = pi.getFITS("LMIRCAM.DisplayImage.File","LMIRCAM.GetDisplayImage.Now")
    time.sleep(1)
    print "ok"


