PRO QUICK_HISTOGRAM, phase, phase_dif, hist, hist_dif

; PURPOSE:
;   Read and process phase measurements 
;   
; INPUTS
;   phase  
;
; KEYWORDS
;
; MODIFICATION HISTORY:
;   Version 1.0,  12-FEB-2016, by Denis Defrère, University of Arizona, ddefrere@email.arizona.edu

; 1. Compute histograms of phase
n_div   = SQRT(N_ELEMENTS(phase))
binsize = (MAX(phase) - MIN(phase))/n_div
IF MAX(phase) NE MIN(phase) THEN BEGIN
  hist = HISTOGRAM(phase, BINSIZE=binsize, MAX=MAX(phase), MIN=MIN(phase))
ENDIF ELSE hist = N_ELEMENTS(phase)

; 2. Same for phase difference
phase_dif = phase-SHIFT(phase,1) & phase_dif = phase_dif[1:*]
binsize   = (MAX(phase_dif) - MIN(phase_dif))/n_div
IF MAX(phase_dif) NE MIN(phase_dif) THEN BEGIN
  hist_dif  = HISTOGRAM(phase_dif, BINSIZE=binsize, MAX=MAX(phase_dif), MIN=MIN(phase_dif))
ENDIF ELSE hist_dif = N_ELEMENTS(phase_dif)




END