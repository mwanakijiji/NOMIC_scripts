#!/usr/bin/python
#Optimize nulling sequence paramaters
#DD-160217

# Define default parameters
epadu  = 145       # electrons per ADU
qe     = 0.4       # quantum efficiency
ron_e  = 450       # readout noise in electrons
ron_ph = ron_e/qe  # readout noise in photon

# Input parameters
aper   = 8         # aperture radius in pixels
dit    = 0.060     # integration time
bckg   = 5000      # background per pixel (ADU/dit)
flx_jy = 6         # stellar flux in Jansky
null   = 0.001     # desired null accuracy

# Convert Jansky to ph/read
jy2adu = 0.5*(52242+60735)*dit # Feb 2015 measurement
jy2ph  = jy2adu*epadu/qe

# Compute background in photons per dit
bckg_p = bckg*epadu/qe*3.14*aper**2

# Compute constructive stellar flux in photon
flx_p  = flx_jy*jy2ph 

# Compute noise
noi_p = (ron_ph**2+bckg_p)**0.5  # in photons
noi_a = (noi_p*qe/epadu) # in ADU

# Compute number of frames required to reach a given null
n_fr = (noi_p/(flx_p*null))**2

# Compute background null
bckg_null = bckg_p**0.5/flx_p

# Print info to screen
# For info, we measured a background RMS of 0.6% relative to beta Leo in February 2015 (dit = 0.060s)
print('Estimated noise [ADU/read] : %f ' % noi_a)
print('Background null : %f ' % bckg_null)
print('Number of null frames to reach null accuracy : %f ' % n_fr)

# Now compute number of frames for photometry
null_d = 0.01
n_fr   = (null_d/null*noi_p/flx_p)**2
print('Number of photometric frames to reach null accuracy : %f ' % n_fr)