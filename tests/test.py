from pyindi import * 
from time import sleep
from time import gmtime, strftime

pi = PyINDI()

while True:
  print strftime("%Y-%m-%d %H:%M:%S", gmtime())
  pi.setINDI('NOMIC.Command.text', '0 contacq', wait=True)
  pi.setINDI('NOMIC.Command.text', 'rawbg', timeout=50000, wait=True)
  pi.setINDI('NOMIC.Command.text', '1 contacq', wait=True)
  sleep(5)
