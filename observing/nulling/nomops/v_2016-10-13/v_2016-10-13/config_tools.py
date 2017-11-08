from pyindi import *
pi = PyINDI()

def custom_cfg(cfg_in):
  """
  Makes a deep copy of a configuration dictionary (or any dictionary)
  so that the copy can be modified without modifying the original along
  with it.
  
  Usage:
   >> import config
   >> my_cfg = custom_cfg(config.hosts_std)
  """
  cfg_out = {}; cfg_out.update(cfg_in)
  return cfg_out

def disp(cfg_in):
  """
  Prints the content of a configuration dictionary (or any dictionary)
  to a console using the PyINDI ppD function.
  
  Usage:
   >> import config
   >> disp(config.hosts_std)
  """
  pi.ppD(cfg_in)


