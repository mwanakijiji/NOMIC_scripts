PRO LIVE_DISPLAY, DATE=date, INFO=info, DELAY=delay, FILE_ID=file_id, MODEL=model, QUADRANT=quadrant, PAUSE_EACH=pause_each, PAUSE_WRAP=pause_wrap, PLOT_FFT=plot_fft, $
                  SKIP_NFILE=skip_nfile, WAV=wav, EPS=eps

; PURPOSE:
;   
;
; KEYWORDS
;   DATE       :  String vector with the information about the data to reduce. The format is 'yymmddhhmm', e.g. '1310190858'.
;              :  If not set, the code is running continuously on the last files
;   FILE_ID    :  Vector giving the file ID to be read (format = ss_nnnnnn)
;   QUADRANT   :  Set this keyword to extract a quadrant to display (1,2,3,or 4 starting from bottom left) instead of the beam itself
;   MODEL      :  Set this keyword to compute and plot the model of the pupil fringes
;   PAUSE_EACH :  Set this keyword to tell the code to pause after each frame
;   PAUSE_WRAP :  Set this keyword to tell the code to pause when it sees a wrap
;   PLOT_FFT   :  Set this keyword to plot the FFTs
;   WAV        :  Wavelength in microns (K band by default)
;   EPS        :  Set this keyword to produce output plots in EPS format.
;   INFO       :  Set this keyword to print info to screen
;
; MODIFICATION HISTORY:
;   Version 1.0,  02-MAY-2014, by Denis Defrère, University of Arizona, ddefrere@email.arizona.edu
;   Version 1.1,  22-MAY-2014, DD: added keywords DATE and PLOT_FFT
;   Version 1.2,  22-MAY-2014, DD: added keyword EPS to produce output plots in EPS format
;   Version 1.3,  01-OCT-2014, DD: added keyword WAV, MODEL, and SKIP_NFILE

; Keyword checks
IF NOT KEYWORD_SET(DELAY)    THEN delay     = 1
IF NOT KEYWORD_SET(QUADRANT) THEN quadrant  = 0
IF NOT KEYWORD_SET(WAV)      THEN wav       = 2.2D-6 ELSE wav *= 1D-6
IF KEYWORD_SET(EPS)          THEN plot_path = '/Volumes/nodrs/nodrs/results/phasecam/

; Running paramaters
loop_on = 1
n_pad   = 4         ; Beam padding factor (to improve resolution in Fourier space)
pix2m   = 0.5156    ; pupil pixel to m conversion factor
pix2tt  = 44.       ; Fourier pixel to tipt/tilt conversion factor (in mas)
col_tab = 0

; Print info to screen
PRINT,''
PRINT,'Now in continuous acquisition (ctrl-c to quit)'
PRINT,''
PRINT, "File ID, phase, unwrapped phase, phase difference, tip, and tilt :   "


; Init plot
screen  = GET_SCREEN_SIZE(RESOLUTION=resolution)
LOADCT, 0, /SILENT
fit     = 0.9*screen[1]/1200.
fit_eps = 20./1720.
zoom    = 5
IF KEYWORD_SET(MODEL) THEN PLOTXY, /INIT, INV=inv, NWINDOW=4, /COLOR, WINDOW=[50,50,700,650]*fit
PLOTXY, /INIT, INV=inv, NWINDOW=5, /COLOR, WINDOW=[50,650,700,1250]*fit
PLOTXY, /INIT, INV=inv, NWINDOW=6, /COLOR, WINDOW=[50,50,900,650]*fit
PLOTXY, /INIT, INV=inv, NWINDOW=7, /COLOR, WINDOW=[950,50,1800,650]*fit
IF KEYWORD_SET(PLOT_FFT) THEN PLOTXY, /INIT, INV=inv, NWINDOW=8, /COLOR, WINDOW=[750,700,1950,1300]*fit
IF KEYWORD_SET(PLOT_FFT) THEN PLOTXY, /INIT, INV=inv, NWINDOW=9, /COLOR, WINDOW=[750,300,1950,900]*fit
IF KEYWORD_SET(PLOT_FFT) THEN PLOTXY, /INIT, INV=inv, NWINDOW=10, /COLOR, WINDOW=[50,50,900,650]*fit

; Prepare continuous looping 
WHILE loop_on EQ 1 DO BEGIN

  ; Get current date
  ; Retrieve data path
  IF KEYWORD_SET(date) THEN BEGIN
    ; Stop the loop
    loop_on = 0
    ; Consitancy check
    IF STRLEN(date) NE 10 THEN MESSAGE, 'Invalid input string: must be composed of 10 digits (yymmddhhmm)'
    ; Get data path
    yymmdd    = '20' + STRMID(date, 0, 2) + '_' + STRMID(date, 2, 2) + '_' + STRMID(date, 4, 2)
    data_path = '/home/lbti/PLC/data/PLC_' + yymmdd + '/PLC_' + yymmdd + 'T' + STRMID(date, 6, 2) + '/PLC_' + yymmdd + 'T' + STRMID(date, 6, 2) + '_' + STRMID(date, 8, 2) + '/'
    IF NOT FILE_TEST(data_path) THEN MESSAGE, 'Data not found in :' + data_path
  ENDIF ELSE BEGIN
    systime = SYSTIME(/UTC)
    yymmdd  = STRING(STRMID(systime, 20, 4), FORMAT='(I02)') + '_' + STRING(MONTH_CNV(STRMID(systime, 4, 3)), FORMAT='(I02)') + '_' + STRING(STRMID(systime, 8, 2), FORMAT="(I02)")
    hh      = STRMID(systime, 11, 2)
    mm      = STRMID(systime, 14, 2)
    ss      = STRMID(systime, 17, 2)
    
    ; Get path
    data_path = '/home/lbti/PLC/data/PLC_' + yymmdd + '/PLC_' + yymmdd + 'T' + hh + '/PLC_' + yymmdd + 'T' + hh + '_' + mm + '/'
  ENDELSE
  
  ;data_path = '/Volumes/nodrs/data/LBTI/phasecam/PLC_2014_03_17/'
  ;loop_on = 0
  ;date = 0
  
  ; Get files
  IF KEYWORD_SET(FILE_ID) THEN BEGIN
    n_id      = N_ELEMENTS(file_id)
    img_files = 'junk'
    FOR i_i = 0, n_id-1 DO img_files = [img_files, FILE_SEARCH(data_path, '*' + file_id[i_i] + '*.fits')]
    img_files = img_files[1:*]
  ENDIF ELSE img_files = FILE_SEARCH(data_path, "*.fits")
  
  ; Number of files
  n_files   = N_ELEMENTS(img_files)
  IF n_files LT 2 THEN GOTO, jump_loop;

  ; Skip files if set
  IF KEYWORD_SET(SKIP_NFILE) THEN BEGIN
    img_files = img_files[skip_nfile:*] 
    n_files   = N_ELEMENTS(img_files)
    IF n_files LT 2 THEN GOTO, jump_loop;
  ENDIF
  
  ; Loop only if not live
  ; IF NOT KEYWORD_SET(DATE) THEN n_files = 1
  
  ; Open last image
  phase_plot = DBLARR(n_files)
  phase_wrap = DBLARR(n_files)
  phase_fft  = DBLARR(n_files)
  time_plot  = DBLARR(n_files)
  FOR i=0, n_files-1 DO BEGIN
    img_cur = READFITS(img_files[i], header, /SILENT)
    n_xpix  = N_ELEMENTS(img_cur[*,0])
    n_ypix  = N_ELEMENTS(img_cur[0,*])
    
    ; Read header
    time        = FXPAR(header, 'PCJD')
    pcimgdt     = FXPAR(header, 'PCIMGDT')   & IF i EQ 0 THEN time_plot[0] = 0 ELSE time_plot[i] = time_plot[i-1] + pcimgdt*0.001
    phase       = FXPAR(header, 'PCFTPHSA')  & phase_wrap[i] = phase
    phase_un    = FXPAR(header, 'PCUNWPHS')  & phase_plot[i] = phase_un
    tilt        = FXPAR(header, 'PCFTMAGX')
    tip         = FXPAR(header, 'PCFTMAGY')
    pcftok      = FXPAR(header, 'PCFTOK')
    pcplcorr    = FXPAR(header, 'PCPLCORR')
    pcbrad      = FXPAR(header, 'PCBRAD')
    pcb1x       = FXPAR(header, 'PCB1X')-1   ; -1 for 0-based here
    pcb1y       = FXPAR(header, 'PCB1Y')-1   ; -1 for 0-based here
    
    ; Print info to screen
    PRINT, pcbrad
    PRINT, STRMID(img_files[i], STRPOS(img_files[i], '.fits')-6, 6), phase, phase_un, phase_plot[i]-phase_plot[(i-1)>0], tilt, tip

    ; If old files, convert tip/tilt from pixels to mas
    ; 0.5 for one quadrant and another 0.5 for half of the quadrant
    ; IF time LT 2457734.0 THEN BEGIN
    ;  tilt = (tilt-0.25*n_xpix)*pix2tt
    ;  tip  = (tip-0.25*n_ypix)*pix2tt
    ;ENDIF
           
    ; Force model to given values
    ;phase = 0
    ;tilt  = 176
    ;tip   = 0
    
    ; Define zone limts
    zone_l = -FIX(0.5*FIX(853/tilt))
    zone_r = FIX(0.5*FIX(853/tilt)) 
    
    ; Extract quadrant
    IF KEYWORD_SET(QUADRANT) THEN BEGIN
      x_min = ((quadrant-1) MOD 2)*(0.5*n_xpix)  & n_xpix = 0.5*n_xpix
      y_min = FLOOR((quadrant-1)/2)*(0.5*n_ypix) & n_ypix = 0.5*n_ypix
      img_cur = TEMPORARY(img_cur[x_min:x_min+n_xpix-1,y_min:y_min+n_ypix-1])
    ENDIF ELSE BEGIN  
      x_min = FLOOR(pcb1x - pcbrad)  & n_xpix = 2*pcbrad
      y_min = FLOOR(pcb1y - pcbrad)  & n_ypix = 2*pcbrad
      img_cur = TEMPORARY(img_cur[x_min:x_min+n_xpix-1,y_min:y_min+n_ypix-1])
    ENDELSE
    
    ; Remove constant part of the image
    img_cur -= MEAN(img_cur)
    
    ; Establish coordinates
    n_pix   = n_xpix
    range   = [-1.,1]*pix2m*pcbrad
    x_coord = range[0] + DINDGEN(n_pix)/(n_pix-1)*(range[1]-range[0]) ; Detector x coordinates
    y_coord = x_coord
    
    ; Mask outside the beam size
    mask_r = pix2m*pcbrad
    DIST_CIRCLE, map, [n_xpix, n_ypix] 
    map  = MAX(SQRT(x_coord^2+y_coord^2))/MAX(map)*map
    mask = 0*img_cur
    mask[ WHERE(map LE mask_r, n_m, /NULL)] = 1
    img_cur = mask*img_cur
        
    ; Compute number of pixels in the beam per column
    pixcol  = TOTAL(mask,2) > 1

    ; Compute collapsed image
    img_c  = TOTAL(img_cur, 2)/pixcol
    img_c -= MIN(img_c)
    
    ; Compute OPD
    ;IF NOT KEYWORD_SET(NO_UNWRAP) THEN phase_un = UNWRAP(phase*!Dpi/180.) ELSE 
    ;phase_un = phase*!Dpi/180.; Radian
    opd      = phase_un*wav*1D+6/(2*!Dpi)
    
    ; Load color table
    LOADCT, col_tab, /SILENT
    
    ; Compute fringe envelope if set
    IF KEYWORD_SET(MODEL) THEN BEGIN
      model   = PUPIL_FRINGE(x_coord, y_coord, TILT=tilt, TIP=tip, OPD=opd, MASK=mask_r)
      model_c = TOTAL(model, 2)
      model_c -= MIN(model_c)
      model_c *= TOTAL(img_c)/TOTAL(model_c)
      
      ; Plot
      WSET, 4
      PLOTXY, CONGRID(model, zoom*n_xpix, zoom*n_ypix), /NEW, NWINDOW=nwindow, XRANGE=range, YRANGE=range, TITLE='', XTITLE='Pupil coordinates [m]', YTITLE='Pupil coordinates [m]', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
        CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[100,50,600,550]*fit;, INSET_UR='a.'
    ENDIF
      
    ; Plot PHASECAM images
    WSET, 5
    PLOTXY, CONGRID(img_cur, zoom*n_xpix, zoom*n_ypix), /NEW, NWINDOW=nwindow, XRANGE=range, YRANGE=range, TITLE='', XTITLE='Pupil coordinates [m]', YTITLE='Pupil coordinates [m]', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
            CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[100,50,600,550]*fit;, INSET_UR='a.'
    ;PLOTXY, model, /NEW, NWINDOW=nwindow, XRANGE=[0,n_xpix], YRANGE=[0,n_xpix], TITLE='', XTITLE='Pixels', YTITLE='Pixels', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
    ;  CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[100,600,600,1100]*fit;, INSET_UR='a.'
    ;PLOTXY, img_cur, /NEW, NWINDOW=nwindow, XRANGE=[0,n_xpix], YRANGE=[0,n_xpix], TITLE='', XTITLE='Pixels', YTITLE='Pixels', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
    ;        CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[100,50,600,550]*fit;, INSET_UR='a.'
 
    
    ; Plot residue  
    ;PLOTXY, CONGRID(img_cur, zoom*n_xpix, zoom*n_ypix), /NEW, NWINDOW=nwindow, XRANGE=[0,n_xpix], YRANGE=[0,n_xpix], TITLE='', XTITLE='Pixels', YTITLE='Pixels', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
    ;CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[100,50,600,550]*fit;, INSET_UR='a.'
    ; Overplot phase signal
  ;  phase_pix = -phase * 0.5 * pix360/!Dpi
  ;  PLOTXY, [20+phase_pix,20-phase_pix], [0, n_ypix], /NEW, NWINDOW=nwindow, XRANGE=[0,n_xpix], YRANGE=[0,n_xpix], COLOR=255, THICK=4, CHARSIZE=charsize, /NOERASE, /NODATA, WINDOW=[70,50,820,800]*fit
  ;  LOADCT, 13, /SILENT
  ;  FOR i=0, 30 DO BEGIN
  ;    pos = 30+phase_pix+i*pix360
  ;    IF pos LT n_xpix AND pos GT 0 THEN PLOTXY, [pos,pos], [0, n_ypix], COLOR=255, THICK=4, /ADD
  ;    IF pos LT n_xpix AND pos GT 0 THEN XYOUTS, pos, n_ypix-1, i, CHARSIZE=2, CHARTHICK=1.3
  ;  ENDFOR
  ;  LOADCT, 0, /SILENT
  
    ; Now phase signal
    IF i GT 1 THEN BEGIN
      WSET, 6  
      idx_plot  = WHERE(time_plot GE MAX(time_plot)-1 AND time_plot GT 0, /NULL) ; Only plot the last second
      time_cur  = time_plot[idx_plot]
      phase_cur = phase_plot[idx_plot]
      PLOTXY, time_cur, phase_cur, /NEW, NWINDOW=nwindow, TITLE='', XTITLE='Time [s]', YTITLE='Measured phase', XRANGE=[MIN(time_cur),MAX(time_cur)], YRANGE=[-360,360], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize,$
              WINDOW=[70,50,810,550]*fit, /NO_DATA
      LOADCT, 13, /SILENT
      PLOTXY, time_cur, phase_cur, SYMBOL=2, /ADD, COLOR=90 
      LOADCT, 0, /SILENT
    ENDIF
   
    ; Now plot collapsed signal
    WSET, 7
    PLOTXY, x_coord, img_c, /NEW, NWINDOW=nwindow, TITLE='', XTITLE='Pixels', YTITLE='Collapsed image', XRANGE=[MIN(x_coord),MAX(x_coord)], YRANGE=[0,1.5*MAX(img_c)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize,$
            WINDOW=[70,50,810,550]*fit, /NO_DATA
    PLOTXY, x_coord, img_c, /ADD, COLOR=0
    LOADCT, 13, /SILENT
    PLOTXY, x_coord, img_c, /ADD, COLOR=90
    PLOTXY, [zone_l,zone_l], [0,1000], /ADD, LINESTYLE=1
    PLOTXY, [zone_r,zone_r], [0,1000], /ADD, LINESTYLE=1
    LOADCT, 0, /SILENT
    
    ; Plot FFT
    IF KEYWORD_SET(PLOT_FFT) THEN BEGIN     
       ; Start with model image
       ; Beam padding to improve resolution in Fourier space
      img_new = DBLARR(n_pad*n_xpix,n_pad*n_ypix)                                                                                     ; create paded image of the good size
      img_new[0.5*(n_xpix*n_pad-n_xpix):0.5*(n_xpix*n_pad+n_xpix)-1,0.5*(n_ypix*n_pad-n_ypix):0.5*(n_ypix*n_pad+n_ypix)-1] = model  ; parse image
      
      ; Replace the outer part by the mean
      FOR i_x = 0, n_xpix*n_pad-1 DO BEGIN
        FOR i_y = 0, n_ypix*n_pad-1 DO BEGIN
          dd = SQRT((i_x-0.5*n_xpix*n_pad)^2 + (i_y-0.5*n_ypix*n_pad)^2)
          IF dd GT pcbrad THEN img_new[i_x,i_y]=0
        ENDFOR 
      ENDFOR
      
      ; Load color table
      LOADCT, col_tab, /SILENT
      
      ; Transform the image into the frequency domain and shift the zero-frequency location from (0,0) to
      ; the center of the data.
      img_tmp = SHIFT(img_new, 0.5*n_pad*n_xpix, 0.5*n_pad*n_ypix)
      mod_fft = FFT(img_tmp, /DOUBLE)
      mod_fft = SHIFT(mod_fft, 0.5*n_pad*n_xpix, 0.5*n_pad*n_ypix)
      ; Amplitude image
      amp_fft = ABS(mod_fft)
      ; Phase image
      pha_fft = ATAN(IMAGINARY(mod_fft),REAL_PART(mod_fft))/!DTOR
      ; Plot results
      WSET, 8
      PLOTXY, amp_fft, /NEW, NWINDOW=nwindow, XRANGE=[-1.,1.]*0.5*n_xpix*pix2tt, YRANGE=[-1.,1.]*0.5*n_ypix*pix2tt, TITLE='Fourier image (model)', XTITLE='Tilt [mas]', YTITLE='Tip [mas]', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
              CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[50,50,550,550]*fit;, INSET_UR='a.'
      PLOTXY, pha_fft, /NEW, NWINDOW=nwindow, XRANGE=[-1.,1.]*0.5*n_xpix*pix2tt, YRANGE=[-1.,1.]*0.5*n_ypix*pix2tt, TITLE='Fourier image (phasecam)', XTITLE='Tilt [mas]', YTITLE='Tip [mas]', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
             CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[650,50,1150,550]*fit;, INSET_UR='a.'
     
     ; Now, do the same for the actual image      
     ; Beam padding to improve resolution in Fourier space
     img_new = DBLARR(n_pad*n_xpix,n_pad*n_ypix)                                                                                     ; create paded image of the good size
     img_new[0.5*(n_xpix*n_pad-n_xpix):0.5*(n_xpix*n_pad+n_xpix)-1,0.5*(n_ypix*n_pad-n_ypix):0.5*(n_ypix*n_pad+n_ypix)-1] = img_cur  ; parse image

     ; Replace the outer part by the mean
     FOR i_x = 0, n_xpix*n_pad-1 DO BEGIN
       FOR i_y = 0, n_ypix*n_pad-1 DO BEGIN
         dd = SQRT((i_x-0.5*n_xpix*n_pad)^2 + (i_y-0.5*n_ypix*n_pad)^2)
         IF dd GT pcbrad THEN img_new[i_x,i_y]=0
       ENDFOR
     ENDFOR

     ; Transform the image into the frequency domain and shift the zero-frequency location from (0,0) to
     ; the center of the data.
     img_tmp = SHIFT(img_new, 0.5*n_pad*n_xpix, 0.5*n_pad*n_ypix)
     img_fft = FFT(img_tmp, /DOUBLE)
     img_fft = SHIFT(img_fft, 0.5*n_pad*n_xpix, 0.5*n_pad*n_ypix)
     ; Amplitude image
     amp_img = ABS(img_fft)
     ; Phase image
     pha_img = ATAN(IMAGINARY(img_fft),REAL_PART(img_fft))/!DTOR
     ; Find bright pixel
     idx_bri = WHERE(amp_img EQ MAX(amp_img))
     pos_bri = ARRAY_INDICES(amp_img, idx_bri[1])
     ; Define a box around it and compute centroid
     img_ex = amp_img[(pos_bri[0]-n_pad):(pos_bri[0]+n_pad), (pos_bri[1]-n_pad):(pos_bri[1]+n_pad)]
     cntrd, img_ex, n_pad, n_pad, xcen, ycen, 5
     ;i_pos   = WHERE(pos_bri GT 0.5*n_xpix)
     print, SIZE(pha_img)
     print, pos_bri[0]-n_pad+xcen, pos_bri[1]-n_pad+ycen
     phase_fft[i] = pha_img[ROUND(pos_bri[0]-n_pad+xcen), ROUND(pos_bri[1]-n_pad+ycen)]
     ;print, amp_img[idx_bri[i_pos]], pha_img[idx_bri[i_pos]]
     ; Define ranges
     xrange = [-1.,1.]*0.5*n_xpix*pix2tt
     yrange = [-1.,1.]*0.5*n_ypix*pix2tt
     ; Plot results
     WSET, 9
     PLOTXY, amp_img, /NEW, NWINDOW=nwindow, XRANGE=xrange, YRANGE=yrange, TITLE='Fourier image (model)', XTITLE='Tilt [mas]', YTITLE='Tip [mas]', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
       CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[50,50,550,550]*fit;, INSET_UR='a.'
     PLOTXY, pha_img, /NEW, NWINDOW=nwindow, XRANGE=[-1.,1.]*0.5*n_xpix*pix2tt, YRANGE=[-1.,1.]*0.5*n_ypix*pix2tt, TITLE='Fourier image (phasecam)', XTITLE='Tilt [mas]', YTITLE='Tip [mas]', GRID=0, THICK=3.0, XSTYLE=1, YSTYLE=1, $
       CHARTHICK=1.5, CHARSIZE=charsize, /NOERASE, WINDOW=[650,50,1150,550]*fit;, INSET_UR='a.'
     ;LOADCT, 13, /SILENT  
     ;PLOTXY, [xrange[0]+pos_bri[0]], [yrange[0]+pos_bri[1]],  COLOR=255, SYMBOL=3, /ADD
     ;LOADCT, 0, /SILENT
     
     IF i GT 1 THEN BEGIN
       WSET, 10
       PLOTXY, time_cur, phase_cur, /NEW, NWINDOW=nwindow, TITLE='', XTITLE='Time [s]', YTITLE='Measured raw phase', XRANGE=[MIN(time_cur),MAX(time_cur)], YRANGE=[-360,360], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize,$
               WINDOW=[70,50,810,550]*fit
       LOADCT, 13, /SILENT
       PLOTXY, time_cur, phase_wrap[idx_plot], SYMBOL=2, /ADD, COLOR=90 
       PLOTXY, time_cur, phase_fft[idx_plot], SYMBOL=2, /ADD, COLOR=150
       LOADCT, 0, /SILENT
     ENDIF
    ENDIF
    
    ; Jump point
    jump_loop:
    IF n_files LT 1 THEN PRINT, 'No image'
    
    ; Delay
    WAIT, delay
    
    ; Stop if PAUSE_EACH is set
    IF KEYWORD_SET(PAUSE_EACH) THEN STOP
    
    ; Pause if large jump
    IF i GT 0 AND KEYWORD_SET(PAUSE_WRAP) THEN IF ABS(phase_plot[i]-phase_plot[i-1]) GT 150 THEN STOP
  ENDFOR
ENDWHILE

; Finish plots
PLOTXY, /FIN
LOADCT, 0, /SILENT

IF KEYWORD_SET(EPS) THEN BEGIN
  ; Load color
  LOADCT, 0, /SILENT
  charthick = 4.8
  charsize  = 1.2
  ; Plot model
  PLOTXY, /INIT, INV=inv, /COLOR, /EPS, WINDOW=[0, 0,1100,1150]*fit_eps, FILENAME = plot_path + 'pupil_model.eps'
  PLOTXY, CONGRID(model, zoom*n_xpix, zoom*n_ypix), /NEW, NWINDOW=nwindow, XRANGE=range, YRANGE=range, TITLE='Camera image (model)', XTITLE='Pupil coordinates [m]', YTITLE='Pupil coordinates [m]', GRID=0, THICK=4.0, XSTYLE=1, YSTYLE=1, $
          CHARTHICK=charthick, CHARSIZE=charsize, /NOERASE, WINDOW=[150,150,1050,1050]*fiT_eps;, INSET_UR='a.'
  PLOTXY, /FIN
  ; Plot image
  PLOTXY, /INIT, INV=inv, /COLOR, /EPS, WINDOW=[0, 0,1100,1150]*fit_eps, FILENAME = plot_path + 'pupil_phasecam.eps'
  PLOTXY, CONGRID(img_cur, zoom*n_xpix, zoom*n_ypix), /NEW, NWINDOW=nwindow, XRANGE=range, YRANGE=range, TITLE='Camera image (phasecam)', XTITLE='Pupil coordinates [m]', YTITLE='Pupil coordinates [m]', GRID=0, THICK=4.0, XSTYLE=1, YSTYLE=1, $
          CHARTHICK=chartick, CHARSIZE=charsize, /NOERASE, WINDOW=[150,150,1050,1050]*fit_eps;, INSET_UR='a.'
  PLOTXY, /FIN

  ; Plot amplitude FFT
  PLOTXY, /INIT, INV=inv, /COLOR, /EPS, WINDOW=[0, 0,1150,1150]*fit_eps, FILENAME = plot_path + 'fft-amp_model.eps'
  PLOTXY, amp_fft, /NEW, NWINDOW=nwindow, XRANGE=[-1.,1.]*0.5*n_xpix*pix2tt, YRANGE=[-1.,1.]*0.5*n_ypix*pix2tt, TITLE='Fourier amplitude (model)', XTITLE='Tilt [mas]', YTITLE='Tip [mas]', GRID=0, THICK=4.0, XSTYLE=1, YSTYLE=1, $
    CHARTHICK=chartick, CHARSIZE=charsize, /NOERASE, WINDOW=[200,150,1050,1050]*fit_eps;, INSET_UR='a.'
  PLOTXY, /FIN
  ; Plot image
  PLOTXY, /INIT, INV=inv, /COLOR, /EPS, WINDOW=[0, 0,1150,1150]*fit_eps, FILENAME = plot_path + 'fft-amp_phasecam.eps'
  PLOTXY, amp_img, /NEW, NWINDOW=nwindow, XRANGE=[-1.,1.]*0.5*n_xpix*pix2tt, YRANGE=[-1.,1.]*0.5*n_ypix*pix2tt, TITLE='Fourier amplitude (phasecam)', XTITLE='Tilt [mas]', YTITLE='Tip [mas]', GRID=0, THICK=4.0, XSTYLE=1, YSTYLE=1, $
    CHARTHICK=chartick, CHARSIZE=charsize, /NOERASE, WINDOW=[200,150,1050,1050]*fit_eps;, INSET_UR='a.'
  PLOTXY, /FIN
  
  ; Plot phase FFT
  PLOTXY, /INIT, INV=inv, /COLOR, /EPS, WINDOW=[0, 0,1150,1150]*fit_eps, FILENAME = plot_path + 'fft-pha_model.eps'
  PLOTXY, pha_fft, /NEW, NWINDOW=nwindow, XRANGE=[-1.,1.]*0.5*n_xpix*pix2tt, YRANGE=[-1.,1.]*0.5*n_ypix*pix2tt, TITLE='Fourier phase (model)', XTITLE='Tilt [mas]', YTITLE='Tip [mas]', GRID=0, THICK=4.0, XSTYLE=1, YSTYLE=1, $
    CHARTHICK=chartick, CHARSIZE=charsize, /NOERASE, WINDOW=[200,150,1050,1050]*fit_eps;, INSET_UR='a.'
  PLOTXY, /FIN
  ; Plot image
  PLOTXY, /INIT, INV=inv, /COLOR, /EPS, WINDOW=[0, 0,1150,1150]*fit_eps, FILENAME = plot_path + 'fft-pha_phasecam.eps'
  PLOTXY, pha_img, /NEW, NWINDOW=nwindow, XRANGE=[-1.,1.]*0.5*n_xpix*pix2tt, YRANGE=[-1.,1.]*0.5*n_ypix*pix2tt, TITLE='Fourier phase (phasecam)', XTITLE='Tilt [mas]', YTITLE='Tip [mas]', GRID=0, THICK=4.0, XSTYLE=1, YSTYLE=1, $
    CHARTHICK=chartick, CHARSIZE=charsize, /NOERASE, WINDOW=[200,150,1050,1050]*fit_eps;, INSET_UR='a.'
  PLOTXY, /FIN
ENDIF


END