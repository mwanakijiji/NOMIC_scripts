FUNCTION PUPIL_FRINGE, x_coord, y_coord, WAV=wav, BANDWIDTH=bandwidth, OPD=opd, TILT=tilt, TIP=tip, MASK=mask, PLOT=plot

; Constants
m2r = 4.848136811D-9 

; Critical parameters
IF NOT KEYWORD_SET(WAV)       THEN wav       = 2.2D-6
IF NOT KEYWORD_SET(BANDWIDTH) THEN bandwidth = 0.4D-6
IF NOT KEYWORD_SET(TILT)      THEN tilt      = 0      ;mas
IF NOT KEYWORD_SET(TIP)       THEN tip       = 0      ;mas
IF NOT KEYWORD_SET(OPD)       THEN opd       = 0      

; Initate variable
n_x = N_ELEMENTS(x_coord)
n_y = N_ELEMENTS(y_coord)

; Create distance map
map = DBLARR(n_x,n_y)
FOR i_y = 0, n_y-1 DO map[*,i_y] = x_coord * TAN(tilt*m2r) + y_coord[i_y] * TAN(tip*m2r)

; Compute efficient OPD
opd_eff = map + opd
x       = bandwidth/wav^2*!Dpi*opd_eff
k       = 2D*!Dpi/wav
IF tilt NE 0 OR tip NE 0 THEN frg = SIN(x)/x*COS(k*opd_eff) ELSE frg = 1+INTARR(n_x,n_y)

; If set, add a mask to the output image
IF KEYWORD_SET(MASK) THEN BEGIN
  DIST_CIRCLE, map, [n_x, n_y] 
  map  = MAX(SQRT(x_coord^2+y_coord^2))/MAX(map)*map
  idx0 = WHERE(map GE mask, n_m)
  IF n_m GT 0 THEN frg[idx0] = 0;MEAN(frg)
ENDIF

; Plot if requested
IF KEYWORD_SET(PLOT) THEN BEGIN
  LOADCT, 3, /SILENT
  PLOTXY, frg
  LOADCT, 0, /SILENT
ENDIF

RETURN, frg
END

; Test routine
; ------------

PRO TEST_PUPILFRINGE
  n_pix   = 5D2
  range   = [-1.,1]*10.
  x_coord = range[0] + DINDGEN(n_pix)/(n_pix-1)*(range[1]-range[0]) ; Detector x coordinates
  y_coord = x_coord
  
  ; Generate random OPD
  n_opd = 100
  opd = RANDOMN(seed, n_opd)*1.0D-6
  FOR i_opd = 0, n_opd-1 DO BEGIN
    PLOTXY, PUPIL_FRINGE(x_coord, y_coord, TILT=160, TIP=160, MASK=4.125, OPD=opd[i_opd]), NWINDOW=1 
    WAIT, 0.1
  ENDFOR
END