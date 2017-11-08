print ""
print "#################################################################"
print "###                                                           ###"
print "###   NOMIC observing scripts loaded.                         ###"
print "###   Author & contact: Steve Ertel                           ###"
print "###                                                           ###"
print "###   This is a collection of scripts to operate LBTI/NOMIC.  ###"
print "###                                                           ###"
print "###   Requires the following packages available:              ###"
print "###     - numpy                                               ###"
print "###                                                           ###"
print "###   For a list of scripts available type:                   ###"
print "###   >> help(nomic_scripts)                                  ###"
print "###   For help on a script use the usual:                     ###"
print "###   >> help(script)                                         ###"
print "###                                                           ###"
print "###   Comments, bug reports and discussion are welcome.       ###"
print "###                                                           ###"
print "###   For up-to-data contact information of Steve Ertel,      ###"
print "###   see www.se-astro.org.                                   ###"
print "###                                                           ###"
print "###   Compatibility note: Created for Python 2.6              ###"
print "###                                                           ###"
print "#################################################################"
print ""

from pyindi import *
pi = PyINDI()

from config_tools import *
from camera_controls import *
from telescope_controls import *
from setpoint_controls import *
from print_tools import *
import config

