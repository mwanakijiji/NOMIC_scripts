PRO LIVE_OPD, DATE=date, DIAGNOSTIC=diagnostic, DISPLAY_CORRECTION=display_correction, FILE=file, NO_UNWRAP=no_unwrap, NO_SNR=no_snr, $   ; input keywords
              PLOT_SNR=plot_snr, PLOT_BODE=plot_bode, PLOT_DELAY=plot_delay, PLOT_TT=plot_tt, TIME_BIN=time_bin, WAV=wav,$                ; input keywords
              FRQ_OPD=frq_opd, PSD_OPD=psd_opd, $                                                                                         ; output keywords
              SAVE=save, INFO=info                                                                                                        ; input keywords

; PURPOSE:
;   Read FITS files obtained with LBTI/PHASECAM and plot OPD time series, histograms, FFT, PSD and cumulative non-sampled RMS.
;
; KEYWORDS
;   DATE       :  String vector with the information about the data to reduce. The format is 'yymmddhhmm', e.g. '1310190858'.
;              :  If not set, the code is running continuously on the last files
;   DIAGNOSTIC :  Display diagnostic plots (e.g., tip vs phase)
;   DISPLAY_CO :  Overplot OPD correction to measured OPD plot
;   FILE       :  String with the name of the PHASECam file to be processed (superseed DATE)
;   NO_UNWRAP  :  Set this keyword to prevent phase unwrapping
;   NO_SNR     :  Turn off SNR selection
;   PLOT_SNR   :  Plot SNR vs time
;   PLOT_BODE  :  Plot Bode plot
;   PLOT_DELAY :  Plot time interval between frames vs time
;   PLOT_TT    :  Set to plot tip/tilt
;   TIME_BIN   :  Last seconds to reduced (max 60s for now)
;   WAV        :  [m], the wavelength at which the data has been taken (2.2D-6 by defaults)
;   PSD_OPD    :  On output, the PSD of the OPD (in m^2/s)
;   FRQ_OPD    :  The corresponding frequency
;   SAVE       :  Save data (phase, top, tilt, OVMS acc) in an output txt file 
;   INFO       :  Set this keyword to print info to screen
;
; MODIFICATION HISTORY:
;   Version 1.0,  31-OCT-2013, by Denis Defrère, University of Arizona, ddefrere@email.arizona.edu
;   Version 1.1,  04-NOV-2013, added keyword 'DIAGNOSTIC'
;   Version 1.2,  06-NOV-2013, updated for irregular time spacing (naive SPLINE interpolation approach)
;   Version 1.3,  12-NOV-2013, added Hanning windowing to take care of the sharp edges
;   Version 1.4,  13-NOV-2013, updated for irregular time spacing (naive interpolation approach)
;   Version 1.5,  13-NOV-2013, implemented continuous loop
;   Version 1.6,  14-NOV-2013, added keyword TIME_BIN, SAVE,and NO_UNWRAP
;   Version 1.7,  18-NOV-2013, improved output plots and added keywords 'NO_SNR'
;   Version 1.8,  24-NOV-2013, added tip/tilt computation
;   Version 1.9,  21-DEC-2013, added SNR and Bode displays
;   Version 2.0,  26-DEC-2013, added keyword IMAGE_DISPLAY
;   Version 2.1,  08-MAR-2014, added keyword DISPLAY_CORRECTION
;   Version 2.2,  15-APR-2014, now read phasecam data in a separate new routine (READ_PHASECAM.pro)
;   Version 2.3,  02-MAY-2014, removed keyword "IMAGE_DISPLAY'. Now done in separate routine
;   Version 2.4,  06-MAY-2014, modified for fixed contrast bin approach
;   Version 2.5,  06-AUG-2014, added keyword FILE and PSD_OPD
;   Version 2.6,  15-SEP-2014, implemented various colors for different gains
;   Version 2.7,  03-OCT-2014, now read unwrapped phase from the files instead of computing it
;   Version 2.8,  09-FEB-2015, added keyword PLOT_DELAY
;   Version 2.9,  13-MAR-2015, improved notations
;   Version 3.0,  13-FEB-2016, adapted for OVMS+
;   Version 3.1,  16-FEB-2016, now plot the H-band phase
;   Version 3.2,  06-MAY-2016, added keyword PLOT_TT
;   
; Sanity checks
IF NOT KEYWORD_SET(INFO)     THEN info     = 1 ELSE info = 0
IF NOT KEYWORD_SET(TIME_BIN) THEN time_bin = 60

; Frequency domain for extrapolation and binning factor
frq_lim  = 2D+3
n_bin    = 10

; Initiate variables
loop_on   = 1               ; variable to controle the live display
rms_last1 = 0               ; init OPD rms of the last frames
rms_last2 = 0               ; same for beam 2
tim_last  = 0               ; init time stamps of the last frames  
time0     = SYSTIME(1)      ; initial time
fr_min    = 100             ; minimum number of frames required to compute FFTs

; Define result path
;result_path = '/root/idl/idl82/lib/nodrs/results/'
result_path = '/usr/local/exelis/idl84/lib/nodrs/results/'

; Prepare plotting
screen = GET_SCREEN_SIZE(RESOLUTION=resolution) ; Get screen size
WINDOW, 0, TITLE= 'Tip/tilt and OPD analysis plots', XPOS=0.4*screen[0], YPOS=0.2*screen[1], XSIZE=0.6*screen[0], YSIZE=0.95*screen[1], RETAIN=2
IF NOT KEYWORD_SET(DATE)   THEN WINDOW, 1, XPOS=0*screen[0], YPOS=0.65*screen[1], XSIZE=0.4*screen[0], YSIZE=0.35*screen[1], TITLE='RMS OPD over time', RETAIN=2
IF KEYWORD_SET(PLOT_SNR)   THEN WINDOW, 2, XPOS=0*screen[0], YPOS=0.65*screen[1], XSIZE=0.4*screen[0], YSIZE=0.85*screen[1], TITLE='SNR', RETAIN=2
IF KEYWORD_SET(PLOT_BODE)  THEN WINDOW, 3, XPOS=0*screen[0], YPOS=0.65*screen[1], XSIZE=0.4*screen[0], YSIZE=0.35*screen[1], TITLE='Bode TF amplitude', RETAIN=2
IF KEYWORD_SET(PLOT_BODE)  THEN WINDOW, 4, XPOS=0*screen[0], YPOS=0.30*screen[1], XSIZE=0.4*screen[0], YSIZE=0.35*screen[1], TITLE='Bode TF phase', RETAIN=2
IF KEYWORD_SET(PLOT_DELAY) THEN WINDOW, 5, XPOS=0*screen[0], YPOS=0.30*screen[1], XSIZE=0.4*screen[0], YSIZE=0.35*screen[1], TITLE='Time since last frame', RETAIN=2
IF KEYWORD_SET(PLOT_TT)    THEN WINDOW, 6, XPOS=0*screen[0], YPOS=0.30*screen[1], XSIZE=0.3*screen[0], YSIZE=0.40*screen[1], TITLE='Tip/tilt information', RETAIN=2

; Prepare continuous looping 
WHILE loop_on EQ 1 DO BEGIN
  
  ; Retrieve data path
  IF NOT KEYWORD_SET(FILE) THEN BEGIN
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
      ; Get current date
      systime = SYSTIME(/UTC)
      yymmdd  = STRING(STRMID(systime, 20, 4), FORMAT='(I04)') + '_' + STRING(MONTH_CNV(STRMID(systime, 4, 3)), FORMAT='(I02)') + '_' + STRING(STRMID(systime, 8, 2), FORMAT="(I02)")
      hh      = STRMID(systime, 11, 2)
      mm      = STRMID(systime, 14, 2)
      ss      = STRMID(systime, 17, 2)
      ; Get path
      data_path = '/home/lbti/PLC/data/PLC_' + yymmdd + '/PLC_' + yymmdd + 'T' + hh + '/PLC_' + yymmdd + 'T' + hh + '_' + mm + '/'
      IF NOT FILE_TEST(data_path) THEN GOTO, jump_loop;
      ; If shorter than time_bin, also read previous data
      IF FLOAT(ss) LT time_bin THEN data_path2 = '/home/lbti/PLC/data/PLC_' + yymmdd + '/PLC_' + yymmdd + 'T' + hh + '/PLC_' + yymmdd + 'T' + hh + '_' + STRING(LONG(mm)-1, FORMAT='(I02)') + '/' ELSE data_path2 = 0
    ENDELSE
    ; Check that the file exists
    IF NOT FILE_TEST(data_path) THEN MESSAGE, 'Data not found in :' + data_path
    ; Find the txt file
    txtfile = FILE_SEARCH(data_path, '*.txt')
    n_txt   = N_ELEMENTS(txtfile)
    IF n_txt GT 1 THEN MESSAGE, 'Too many txt file in the input directory!'
  ENDIF ELSE BEGIN
    loop_on = 0
    txtfile = file
  ENDELSE
  
  ; If a text file exists, read it instead of the fits files
  IF STRPOS(txtfile,'') NE -1 THEN data = READ_PHASECAM(txtfile, INFO=info) ELSE PRINT, 'Input txt file missing'
  
  ; If data_path2 is set, read also the previous file
  ;IF KEYWORD_SET(data_path2) THEN BEGIN
  ;  txtfile2 = FILE_SEARCH(data_path2, '*.txt')
  ;  n_txt    = N_ELEMENTS(txtfile)
  ;  IF n_txt GT 1 THEN MESSAGE, 'Too many txt file in the input directory!'
  ;  IF STRPOS(txtfile,'') NE -1 THEN data2 = READ_PHASECAM(txtfile, INFO=info)
  ;  ;data     = [data,data2]
  ;ENDIF

   ; Only process if more than fr_min frames 
   n_data = N_ELEMENTS(data.pcjd) 
   IF n_data LT fr_min THEN GOTO, jump_loop
  
  ; If time_bin is  set, only use the last time_bin data
  IF KEYWORD_SET(TIME_BIN) THEN BEGIN
    time_jd  = data.pcjd
    time     = (time_jd-time_jd[0])*24.*60.*60.
    idx_time = WHERE(time GE MAX(time)-time_bin, n_data)
    IF n_data LT fr_min THEN GOTO, jump_loop 
  ENDIF ELSE idx_time = INDGEN(n_data)
  
  ; If NO_SNR is not set, then only use good snr frames
  IF NOT KEYWORD_SET(NO_SNR) THEN BEGIN
    pcftok   = data.pcftok[idx_time]
    idx_snr  = idx_time[WHERE(pcftok EQ 1, n_data)]
    IF n_data LT fr_min THEN GOTO, jump_loop 
  ENDIF ELSE idx_snr = idx_time
  
  ; Reject open loop frames (not closed loop with gains = 0)
  idx_closed = idx_snr[WHERE(data.pcclosed[idx_snr] NE -1, COMPLEMENT=idx_open, n_data)]
  IF n_data GT fr_min THEN BEGIN
    time_jd  = data.pcjd[idx_closed]
    time     = (time_jd-time_jd[0])*24.*60.*60.
    pcimgdt  = data.pcimgdt[idx_closed]
    naxis1   = data.naxis1[idx_closed]
    closed   = data.pcclosed[idx_closed]
    pl_pgain = data.pcplpg[idx_closed]
    pl_dgain = data.pcpldg[idx_closed]
    pl_igain = data.pcplig[idx_closed]
    pcplsp   = data.pcplsp1[idx_closed]
    phase1    = data.pcftphs1[idx_closed]
    phase_un1 = data.pcunwph1[idx_closed]
    phase2   = data.pcftphs2[idx_closed]
    phase_un2 = data.pcunwph2[idx_closed]
    tip      = data.pcftmgx1[idx_closed]
    tilt     = data.pcftmgy1[idx_closed]
    pc_ttpg  = data.pcttpg[idx_closed]
    pc_ttig  = data.pcttig[idx_closed]
    pc_ttdg  = data.pcttdg[idx_closed]
    pcftok   = data.pcftok[idx_closed]
    pcplcorr = data.pcplcmd[idx_closed]
    pctipcmd = data.pctipcmd[idx_closed]
    pctltcmd = data.pctltcmd[idx_closed]
    snr      = data.pcmfsnr[idx_closed]
    pcovplv  = data.pcovplv[idx_closed]
    pcovtlv  = data.pcovtlv[idx_closed]
    pcovtpv  = data.pcovtpv[idx_closed]
    pcovplg  = data.pcovplg[idx_closed]
    pcovtlg  = data.pcovtlg[idx_closed]
    pcovtpg  = data.pcovtpg[idx_closed]
    pcovhzn  = data.pcovhzn[idx_closed]
    wav1     = data.pcb1lam[idx_closed]*1D-6
    wav2     = data.pcb2lam[idx_closed]*1D-6
  ENDIF ELSE GOTO, jump_loop 
           
  ; Unwrap the phase 
  IF KEYWORD_SET(NO_UNWRAP) THEN BEGIN
    phase_un1 = phase1
    phase_un2 = phase2 
  ENDIF
    
  ; Measure tip/tilt average and standard deviation
  n_fft = 0;0.5*naxis1[0]
  tt = SQRT((tip-0.5*n_fft)^2+(tilt-0.5*n_fft)^2)
  AVGSDV, tt, avg_tt, rms_tt
  tt = tt - avg_tt
  
  ; Compute histograms
  QUICK_HISTOGRAM, phase1, phase_dif1, hist1, hist_dif1  
  QUICK_HISTOGRAM, phase2, phase_dif2, hist2, hist_dif2
  QUICK_HISTOGRAM, tt, tt_dif, hist_tt, hist_dif_tt   
  
  ; Convert to OPD
  IF KEYWORD_SET(WAV) THEN wav1 = wav 
  opd1 = phase_un1*wav1*1D+6/360.        ; in um
  opd2 = phase_un2*wav2*1D+6/360.
  
  ; Compute OPD difference
  opd3 = opd2-opd1
  
  ; Convert correction to microns
  opd_cor = pcplcorr;*wav*1D+6/360.
  ;FOR i=1, n_data-1 DO opd_cor[i] += opd_cor[i-1]
  
  ; Measure OPD average and standard deviation
  AVGSDV, opd1, opd_avg1, opd_rms1
  AVGSDV, opd2, opd_avg2, opd_rms2
  AVGSDV, opd3, opd_avg3, opd_rms3
  rms_last1 = [rms_last1, opd_rms1]
  rms_last2 = [rms_last2, opd_rms2]
  tim_last  = [tim_last, SYSTIME(1)-time0]

  ; Compute FFT, PSD, etc.. of phase (if at least fr_min points)
  IF n_data GT fr_min THEN BEGIN
    ; Compute FFTs
    COMPUTE_PSD, time, opd1, FREQ=freq1, FRQ_EXT=frqc_ext1, FFT=fft_opd1, PSD=psd_opd1, CUM_RMS=cum_opd1, SLOPE=slope_opd1, FRQ_LIM=1D3, INFO=info
    COMPUTE_PSD, time, opd2, FREQ=freq2, FRQ_EXT=frqc_ext2, FFT=fft_opd2, PSD=psd_opd2, CUM_RMS=cum_opd2, SLOPE=slope_opd2, FRQ_LIM=1D3, INFO=info
    COMPUTE_PSD, time, opd3, FREQ=freq3, FRQ_EXT=frqc_ext3, FFT=fft_opd3, PSD=psd_opd3, CUM_RMS=cum_opd3, SLOPE=slope_opd3, FRQ_LIM=1D3, INFO=info
    COMPUTE_PSD, time, tt, FFT=fft_tt, PSD=psd_tt, CUM_RMS=cum_tt, SLOPE=slope_tt, FRQ_LIM=1D3, INFO=info
    fft_opd1 = ABS(fft_opd1)
    fft_opd2 = ABS(fft_opd2)
    fft_tt   = ABS(fft_tt)  
      
    ; Compute OPD>30Hz
    ;idx30     = WHERE(ABS(frqc_ext1-30) EQ MIN(ABS(frqc_ext1-30)), n_freq)
    ;IF n_freq GT 0 THEN opd_rms30 = cum_opd1[idx30] ELSE opd_rms30 = 0
    ;idx66     = WHERE(ABS(frqc_ext1-66) EQ MIN(ABS(frqc_ext1-66)), n_freq)
    ;IF n_freq GT 0 THEN opd_rms66 = cum_opd1[idx66] ELSE opd_rms66 = 0    
    opd_rms27_1 = SQRT((MAX(frqc_ext1)/N_ELEMENTS(frqc_ext1))*TOTAL(psd_opd1*(1-(SINC(frqc_ext1*0.027))^2)))
    opd_rms15_1 = SQRT((MAX(frqc_ext1)/N_ELEMENTS(frqc_ext1))*TOTAL(psd_opd1*(1-(SINC(frqc_ext1*0.015))^2)))
    opd_rms27_2 = SQRT((MAX(frqc_ext2)/N_ELEMENTS(frqc_ext2))*TOTAL(psd_opd2*(1-(SINC(frqc_ext2*0.027))^2)))
    opd_rms15_2 = SQRT((MAX(frqc_ext2)/N_ELEMENTS(frqc_ext2))*TOTAL(psd_opd2*(1-(SINC(frqc_ext2*0.015))^2)))
    
    ; Now process the CG measurements if they exist
    ; In some old data, they are replaced by the "threee regions" approach
    IF NOT TAG_EXIST(data, 'pclrc') THEN BEGIN
      ; Read data
      pccgerr  = data.pccgerr[idx_closed]
      ; Find bad values
      idx_nan  = WHERE(FINITE(pccgerr) NE 1, n_nan, COMPLEMENT=idx_ok)
      PRINT, 'Number of Nan in CG', n_nan
      ; Compute histogram
      QUICK_HISTOGRAM, pccgerr, hist_gerr, hist_dif_gerr 
      ; Compute FFTs
      COMPUTE_PSD, time, pccgerr, FREQ=freq_pccgerr, FFT=fft_pccgerr, PSD=psd_pccgerr, CUM_RMS=rms_pccgerr, SLOPE=slope_pccgerr, INFO=info
      fft_pccgerr = ABS(fft_pccgerr)
    ENDIF ELSE BEGIN
        ; Read data
        cr_left   = data.pclrc[idx_closed]
        cr_center = data.pccrc[idx_closed]
        cr_right  = data.pcrrc[idx_closed]
        cr_wrap   = data.pcpwrap[idx_closed]
        ; Compute histograms
        binsize     = (MAX(cr_left) - MIN(cr_left))/n_div
        hist_left   = HISTOGRAM(cr_left, BINSIZE=binsize, MAX=MAX(cr_left, /NaN), MIN=MIN(cr_left), LOCATIONS=bins_left)
        bins_left   = bins_left + 0.5*binsize
        binsize     = (MAX(cr_center) - MIN(cr_center))/n_div
        hist_center = HISTOGRAM(cr_center, BINSIZE=binsize, MAX=MAX(cr_center, /NaN), MIN=MIN(cr_center), LOCATIONS=bins_center)
        bins_center = bins_center + 0.5*binsize
        binsize     = (MAX(cr_right) - MIN(cr_right))/n_div
        hist_right  = HISTOGRAM(cr_right, BINSIZE=binsize, MAX=MAX(cr_right, /NaN), MIN=MIN(cr_right), LOCATIONS=bins_right)
        bins_right  = bins_right + 0.5*binsize
    ENDELSE
  ENDIF
   
  ; Print info to screen
  IF info GT 0 THEN BEGIN
    PRINT, ''
    PRINT, 'Initial number of frames             :', N_ELEMENTS(data.pcjd) 
    PRINT, 'Number of frames in time bin         :', N_ELEMENTS(idx_time) 
    PRINT, 'Number of frames after SNR selection :', N_ELEMENTS(idx_snr) 
    PRINT, 'Number of closed frames              :', N_ELEMENTS(idx_closed) 
    PRINT, 'Repetition frequencies [Hz]          :', 2.*MAX(freq1)
    PRINT, ''
    PRINT, 'OPD rms [um] (beam 1, beam 2)        : ', opd_rms1, opd_rms2
    PRINT, '  - OPD rms (>30Hz) [um]             : ', opd_rms27_1, opd_rms27_2
    PRINT, '  - OPD rms (>15Hz) [um]             : ', opd_rms15_1, opd_rms15_2
    PRINT, 'Tip/tilt rms    [mas]                : ', rms_tt
    IF n_data GT fr_min THEN BEGIN
      PRINT, 'Phase setpoint :', pcplsp[UNIQ(pcplsp)]
      PRINT, 'Phase gain :'
      PRINT, '         - P    :', pl_pgain[UNIQ(pl_pgain)]
      PRINT, '         - I    :', pl_igain[UNIQ(pl_dgain)]
      PRINT, '         - D    :', pl_dgain[UNIQ(pl_igain)]
      ;IF TAG_EXIST(data, 'pccgerr') THEN BEGIN
      ;  PRINT, 'Contrast gradient gain :'
      ;  PRINT, '         - P    :', pg_pgain[UNIQ(pg_pgain)]
      ;  PRINT, '         - I    :', pg_igain[UNIQ(pg_igain)]
      ;ENDIF
      PRINT, 'Tip/tilt gain :'
      PRINT, '         - P    :', pc_ttpg[UNIQ(pc_ttpg)]
      PRINT, '         - I    :', pc_ttig[UNIQ(pc_ttig)]
      PRINT, '         - D    :', pc_ttdg[UNIQ(pc_ttdg)]
    ENDIF
    ;tmp_dat  = MIN(ABS(REVERSE(frqc_ext)-0.5*freq), idx_frq)
    ;IF nc GT 1 THEN PRINT, 'Non-sampled vibrations at repetition frequency [um]     :', rms_cl[idx_frq]
    ;IF nc GT 1 THEN PRINT, 'Estimate of the noise-floor RMS over 1kHz bandpass [um] :', rms_noi
  ENDIF
  
  ; Start plotting 
  IF n_data GT fr_min THEN BEGIN
    
    ; Define min&max frequencies
    min_frq    = 0.01          & max_frq    = 1D+3
    fft_min    = 1D-6          & fft_max    = 1.
    fft_tt_min = 1D-6          & fft_tt_max = 1.
    psd_min    = 1D-2          & psd_max    = 1D8
    rms_min    = 0.            & rms_max    = 10
    
    ; Load color and init plot
    !P.Multi = [0, 3, 5, 0, 1]   ; Plot 15 graphs per window
    LOADCT, 13, /SILENT
    color = 250
    charsize = 2
    WSET, 0

    ; 3. Plot tip/tilt histogram
    ;  n_bin   = N_ELEMENTS(hist_tt)
    ;  bins    = (MIN(tt) + FINDGEN(n_bin)/(n_bin-1.) * (MAX(tt)-MIN(tt)))
    ;  PLOT, [0], [0], XTITLE='Tip/tilt measurements [pix]', YTITLE='Number of occurence', XRANGE=[MIN(tt),MAX(tt)], YRANGE=[0.,1.2*MAX(hist_tt)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    ;  OPLOT, [bins], [hist_tt], COLOR=color

    ; Top-left plot: CG vs time if exist (fixed contrast otherwise)
    ; IF TAG_EXIST(data, 'pccgerr') THEN BEGIN
    ;  PLOT, [0], [0], XTITLE='Elapsed time [s]', YTITLE='PCCGERR', XRANGE=[MIN(time),MAX(time)], YRANGE=[1.5*MIN(pccgerr)<0.5*MIN(pccgerr),1.5*MAX(pccgerr)>0.5*MAX(pccgerr)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    ;  IF n_data GT fr_min THEN OPLOT, time, pccgerr, COLOR=color
    ;ENDIF ELSE BEGIN
    ;   IF TAG_EXIST(data, 'pclrc') THEN BEGIN
    ;      PLOT, [0], [0], XTITLE='Elapsed time [s]', YTITLE='Contrast', XRANGE=[MIN(time),MAX(time)], YRANGE=[0.5*(MIN(cr_left)<MIN(cr_center)<MIN(cr_right)),1.5*(MAX(cr_left)>MAX(cr_center)>MAX(cr_right))], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    ;      IF n_data GT fr_min THEN BEGIN
    ;        OPLOT, time, cr_left,   COLOR=[120]
    ;        OPLOT, time, cr_center;, COLOR=[0]
    ;        OPLOT, time, cr_right,  COLOR=[220]
    ;      ENDIF
    ;   ENDIF
    ;ENDELSE
    
    ; BEAM 1
    ; Top left plot: OPD vs time
    opd = opd1 - MEAN(opd1)
    PLOT, [0], [0], XTITLE='Elapsed time [s]', YTITLE='OPD [um]', XRANGE=[MIN(time),MAX(time)], YRANGE=[1.5*MIN(opd),1.5*MAX(opd)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, time, opd, COLOR=color
    IF KEYWORD_SET(DISPLAY_CORRECTION) THEN OPLOT, time, opd_cor;-MEAN(opd_cor)
    ;XYOUTS, 2, 0.95*(MIN(opd)-MEAN(opd)), 'PCC closed', COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
    XYOUTS, time[5], 1.20*(MAX(opd)), 'RMS OPD = ' + STRING(opd_rms1, FORMAT='(F5.2)'), COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
    
    ; Second left plot: phase histogram
    n_bin   = N_ELEMENTS(hist1)
    bins    = (MIN(phase1) + FINDGEN(n_bin)/(n_bin-1.) * (MAX(phase1)-MIN(phase1)))
    PLOT, [0], [0], XTITLE='Phase measurements [deg]', YTITLE='Number of occurence', XRANGE=[-360.,+360.], YRANGE=[0.,1.2*MAX(hist1)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, [bins], [hist1], COLOR=color

    ; Third left plot: phase difference histogram
    n_bin   = N_ELEMENTS(hist_dif1)
    bins    = (MIN(phase_dif1) + FINDGEN(n_bin)/(n_bin-1.) * (MAX(phase_dif1)-MIN(phase_dif1)))
    PLOT, [0], [0], XTITLE='Phase difference [deg]', YTITLE='Number of occurence', XRANGE=[-360.,+360.], YRANGE=[0.,1.2*MAX(hist_dif1)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, [bins], [hist_dif1], COLOR=color
    
    ; Fourth left plot: phase PSD
    PLOT, freq1, psd_opd1, /XLOG, /YLOG, XTITLE='Frequency [Hz]', YTITLE='PSD [um!e2!n/Hz]', XRANGE=[min_frq,frq_lim], YRANGE=[0.5*psd_min,psd_max], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, freq1, psd_opd1, COLOR=color
    OPLOT, freq1, 10^(slope_opd1[1]*ALOG10(freq1)+slope_opd1[0]), LINESTYLE=1
    XYOUTS, 1.5*min_frq, 2.*psd_min, 'Slope closed : ' + STRING(slope_opd1[1], FORMAT='(F5.2)'), CHARSIZE=1.5, CHARTHICK=1.2
    
    ; Lower left plot: reverse cumulative plot
    PLOT, frqc_ext1, cum_opd1, /XLOG, XTITLE='Frequency [Hz]', YTITLE='Non-sampled vibrations [um]', XRANGE=[min_frq,frq_lim], YRANGE=[0.,1.5*MAX(cum_opd1)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, frqc_ext1, cum_opd1, COLOR=color
    ;IF nc GT 1 THEN XYOUTS, 1.5*min_frq, 0.0125, 'Non-sampled vibrations at loop frequency [um] : ' + STRING(rms_cl[idx_frq], FORMAT='(F5.2)'), COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
    LOADCT, 0, /SILENT 
    
    ; SAME PLOT FOR BEAM 2
    ; Top middle plot: OPD vs time
    opd_h = opd2 - MEAN(opd2)
    PLOT, [0], [0], XTITLE='Elapsed time [s]', YTITLE='OPD [um]', XRANGE=[MIN(time),MAX(time)], YRANGE=[1.5*MIN(opd_h),1.5*MAX(opd_h)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, time, opd_h, COLOR=color
    IF KEYWORD_SET(DISPLAY_CORRECTION) THEN OPLOT, time, opd_cor;-MEAN(opd_cor)
    ;XYOUTS, 2, 0.95*(MIN(opd2)-MEAN(opd2)), 'PCC closed', COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
    XYOUTS, time[5], 1.20*(MAX(opd)), 'RMS OPD = ' + STRING(opd_rms2, FORMAT='(F5.2)'), COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2

    ; Second middle plot: phase histogram
    n_bin   = N_ELEMENTS(hist2)
    bins    = (MIN(phase2) + FINDGEN(n_bin)/(n_bin-1.) * (MAX(phase2)-MIN(phase2)))
    PLOT, [0], [0], XTITLE='Phase measurements [deg]', YTITLE='Number of occurence', XRANGE=[-360.,+360.], YRANGE=[0.,1.2*MAX(hist2)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, [bins], [hist2], COLOR=color

    ; Third middle plot: phase difference histogram
    n_bin   = N_ELEMENTS(hist_dif2)
    bins    = (MIN(phase_dif2) + FINDGEN(n_bin)/(n_bin-1.) * (MAX(phase_dif2)-MIN(phase_dif2)))
    PLOT, [0], [0], XTITLE='Phase difference [deg]', YTITLE='Number of occurence', XRANGE=[-360.,+360.], YRANGE=[0.,1.2*MAX(hist_dif2)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, [bins], [hist_dif2], COLOR=color

    ; Fourth middle plot: phase PSD
    PLOT, freq2, psd_opd2, /XLOG, /YLOG, XTITLE='Frequency [Hz]', YTITLE='PSD [um!e2!n/Hz]', XRANGE=[min_frq,frq_lim], YRANGE=[0.5*psd_min,psd_max], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, freq2, psd_opd2, COLOR=color
    OPLOT, freq2, 10^(slope_opd2[1]*ALOG10(freq2)+slope_opd2[0]), LINESTYLE=1
    XYOUTS, 1.5*min_frq, 2.*psd_min, 'Slope closed : ' + STRING(slope_opd2[1], FORMAT='(F5.2)'), CHARSIZE=1.5, CHARTHICK=1.2

    ; Lower middle plot: reverse cumulative plot
    PLOT, frqc_ext2, cum_opd2, /XLOG, XTITLE='Frequency [Hz]', YTITLE='Non-sampled vibrations [um]', XRANGE=[min_frq,frq_lim], YRANGE=[0.0,1.5*MAX(cum_opd1)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, frqc_ext2, cum_opd2, COLOR=color
    ;IF nc GT 1 THEN XYOUTS, 1.5*min_frq, 0.0125, 'Non-sampled vibrations at loop frequency [um] : ' + STRING(rms_cl[idx_frq], FORMAT='(F5.2)'), COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
    LOADCT, 0, /SILENT
    
    ; PLOT CG
    IF NOT TAG_EXIST(data, 'pclrc') THEN BEGIN
      PLOT, freq_pccgerr, psd_pccgerr, /XLOG, /YLOG, XTITLE='Frequency [Hz]', YTITLE='PSD', XRANGE=[min_frq,frq_lim], YRANGE=[0.5*psd_min,psd_max], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      OPLOT, freq_pccgerr, psd_pccgerr, COLOR=color
    ENDIF ELSE BEGIN
      PLOT, [0], [0], XTITLE='Elapsed time [s]', YTITLE='Wrap?', XRANGE=[MIN(time),MAX(time)], YRANGE=[-2,2], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      OPLOT, time, cr_wrap,   COLOR=[250]
    ENDELSE
    
    ; Top middle plot: CG histogram
    IF NOT TAG_EXIST(data, 'pclrc') THEN BEGIN
      n_bin   = N_ELEMENTS(hist_gerr)
      IF n_bin GT 1 THEN bins = (MIN(pccgerr) + FINDGEN(n_bin)/(n_bin-1.) * (MAX(pccgerr)-MIN(pccgerr))) $
                    ELSE bins = [MEAN(pccgerr)]
      PLOT, [0], [0], XTITLE='PCCGERR', YTITLE='Number of occurence', XRANGE=[MIN(pccgerr),MAX(pccgerr)], YRANGE=[0.,1.2*MAX(hist_gerr)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      OPLOT, [bins], [hist_gerr], COLOR=color
      AVGSDV, pccgerr, avg, rms_pccgerr
      ;XYOUTS, bins[2], MAX(hist_gerr), 'RMS PCCGERR = ' + STRING(rms_pccgerr, FORMAT='(F5.2)'), COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
    ENDIF ELSE BEGIN
      IF TAG_EXIST(data, 'pclrc') THEN BEGIN
        PLOT, [0], [0], XTITLE='Contrast', YTITLE='Number of occurence', XRANGE=[MIN(bins_left)<MIN(bins_center)<MIN(bins_right),MAX(bins_left)>MAX(bins_center)>MAX(bins_right)], YRANGE=[0.,1.2*(MAX(hist_left)>MAX(hist_center)>MAX(hist_right))], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
        LOADCT, 1, /SILENT
        OPLOT, [bins_left], [hist_left], COLOR=[120]
        LOADCT, 13, /SILENT
        OPLOT, [bins_center], [hist_center];, COLOR=[90]
        OPLOT, [bins_right], [hist_right], COLOR=[220]
      ENDIF
    ENDELSE
    
    ; PLOTS FOR (BEAM1-BEAM2)
    ; Top left plot: OPD vs time
    opd_d = opd3 - MEAN(opd3)
    PLOT, [0], [0], XTITLE='Elapsed time [s]', YTITLE='OPD [um]', XRANGE=[MIN(time),MAX(time)], YRANGE=[1.5*MIN(opd_d),1.5*MAX(opd_d)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, time, opd_d, COLOR=color
    IF KEYWORD_SET(DISPLAY_CORRECTION) THEN OPLOT, time, opd_cor;-MEAN(opd_cor)
    ;XYOUTS, 2, 0.95*(MIN(opd_d)-MEAN(opd_d)), 'PCC closed', COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
    XYOUTS, time[5], 1.20*(MAX(opd)), 'RMS OPD = ' + STRING(opd_rms3, FORMAT='(F5.2)'), COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2

    ; Fourth left plot: phase PSD
    PLOT, freq3, psd_opd3, /XLOG, /YLOG, XTITLE='Frequency [Hz]', YTITLE='PSD [um!e2!n/Hz]', XRANGE=[min_frq,frq_lim], YRANGE=[0.5*psd_min,psd_max], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, freq3, psd_opd3, COLOR=color
    OPLOT, freq3, 10^(slope_opd3[1]*ALOG10(freq3)+slope_opd3[0]), LINESTYLE=1
    XYOUTS, 1.5*min_frq, 2.*psd_min, 'Slope closed : ' + STRING(slope_opd3[1], FORMAT='(F5.2)'), CHARSIZE=1.5, CHARTHICK=1.2

    ; Lower left plot: reverse cumulative plot
    PLOT, frqc_ext3, cum_opd3, /XLOG, XTITLE='Frequency [Hz]', YTITLE='Non-sampled vibrations [um]', XRANGE=[min_frq,frq_lim], YRANGE=[0.0,1.5*MAX(cum_opd1)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    OPLOT, frqc_ext3, cum_opd3, COLOR=color
    ;IF nc GT 1 THEN XYOUTS, 1.5*min_frq, 0.0125, 'Non-sampled vibrations at loop frequency [um] : ' + STRING(rms_cl[idx_frq], FORMAT='(F5.2)'), COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
    LOADCT, 0, /SILENT
                  
    ; Plot the evolution OPD RMS
    IF NOT KEYWORD_SET(date) THEN BEGIN
      !P.Multi  = [0, 1, 1, 0, 1]   ; Plot 4 graphs per window
      WSET, 1
      PLOT, tim_last[1:*], 1D+3*rms_last1[1:*], XTITLE='Elapsed time [s]', YTITLE='RMS OPD [nm]', XRANGE=[0.,MAX(tim_last)], YRANGE=[0.,1.5*MAX(rms_last1)*1D+3], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      LOADCT, 13, /SILENT
      OPLOT, tim_last[1:*], 1D+3*rms_last1[1:*], LINESTYLE=0, THICK=3, COLOR=90
      OPLOT, tim_last[1:*], 1D+3*rms_last2[1:*], LINESTYLE=0, THICK=3, COLOR=250
      LOADCT, 0, /SILENT
    ENDIF
    
    ; Plot tip/tilt
    IF KEYWORD_SET(PLOT_SNR) THEN BEGIN
      !P.Multi  = [0, 1, 4, 0, 1]   ; Plot 4 graphs per window
      WSET, 2
      PLOT, time, snr, XTITLE='Elapsed time [s]', YTITLE='SNR', XRANGE=[MIN(time),MAX(time)], YRANGE=[0.,1.5*MAX(snr)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      snr2 = 0.5*(snr+SHIFT(snr,1)) & snr2 = snr2[1:*]
      PLOT, phase_dif, snr2, XTITLE='phase difference [deg]', YTITLE='SNR', XRANGE=[-360.,360.], YRANGE=[0.,1.5*MAX(snr)], PSYM=1, XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      tt2  = 0.5*(tt+SHIFT(tt,1)) & tt2 = tt2[1:*]
      PLOT, phase, tt2, XTITLE='Phase [deg]', YTITLE='Tip-tilt [mas]', XRANGE=[-180.,180.], YRANGE=[1.5*MIN(tt2),1.5*MAX(tt2)], PSYM=1, XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      PLOT, phase_dif1, tt2, XTITLE='phase difference [deg]', YTITLE='Tip-tilt [mas]', XRANGE=[-360.,360.], YRANGE=[1.5*MIN(tt2),1.5*MAX(tt2)], PSYM=1, XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      LOADCT, 13, /SILENT
    ENDIF
    
    ; Plot Bode tranmsision
    IF KEYWORD_SET(PLOT_BODE) THEN BEGIN
      ; Find number of different gains for OPD and extract unique combinations
      gain_idx = ATTRIBUTE_ID(TRANSPOSE([[pl_pgain],[pl_dgain],[pl_igain]]))
      n_gain   = MAX(gain_idx)-MIN(gain_idx)+1
      
      ; Init plot
      !P.Multi  = [0, 1, 1, 0, 1]   
      color_bode = 100 + FIX(DINDGEN(n_gain)/(n_gain-1)*155)
      COMPUTE_PSD, time[1:*], phase_dif, FREQ=freq_dev, FRQ_EXT=frqc_dev, FFT=fft_dev, PSD=psd_dev, CUM_RMS=rms_dev, SLOPE=slope_dev, INFO=info
      fft_dev_amp = 20*ALOG10(ABS(fft_dev))   ; in dB
      fft_dev_pha = ATAN(Imaginary(fft_dev),Real_part(fft_dev))/!DTOR
      WSET, 3 & 
      PLOT, [min_frq], [0], /XLOG, XTITLE='Frequency [Hz]', YTITLE='Bode FFT amplitude [dB]', XRANGE=[0.1,0.5*max_frq], YRANGE=[-50.,10.], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      OPLOT, freq_dev, fft_dev_amp, COLOR=color   
      WSET, 4 
      PLOT, [min_frq], [0], /XLOG, XTITLE='Frequency [Hz]', YTITLE='Bode FFT phase [deg]', XRANGE=[0.1,0.5*max_frq], YRANGE=[-180.,+180.], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      OPLOT, freq_dev, fft_dev_pha, COLOR=color  

      ; Loop over the different gains
      !P.Multi  = [0, 1, 2, 0, 1]   ; Plot 4 graphs per window
      charthick = 3.0
      charsize  = 1.3
      color     = 90
      FOR i_g=0, n_gain-1 DO BEGIN
        ; Find frame index and extract data
        idx_fr = WHERE(gain_idx EQ i_g, n_fr)
        IF n_fr LT fr_min THEN GOTO, SKIP_GAIN
        time_jd0  = time_jd[idx_fr]
        time      = (time_jd0-time_jd0[0])*24.*60.*60.
        pl_pgain0 = pl_pgain[idx_fr]
        pl_dgain0 = pl_dgain[idx_fr]
        pl_igain0 = pl_igain[idx_fr]
        phase0    = phase[idx_fr]

        ; Compute Bode TF
        ;time_dif  = time -SHIFT(time,1)  & time_dif = time_dif[1:*]
        phase_dif = phase0-SHIFT(phase0,1) & phase_dif = phase_dif[1:*]
        phase_dev = phase_dif;;MEAN(time_dif)
        COMPUTE_PSD, time[1:*], phase_dev, FREQ=freq_dev, FRQ_EXT=frqc_dev, FFT=fft_dev, PSD=psd_dev, CUM_RMS=rms_dev, SLOPE=slope_dev, INFO=0 
        
        ; Plot
        filename = 'bode_date_kd-' + STRTRIM(STRING(ABS(pl_dgain0[0]), FORMAT='(F6.1)'),1) + '_kp-' + STRTRIM(STRING(ABS(pl_pgain0[0]), FORMAT='(F6.1)'),1) + '_ki-' + STRTRIM(STRING(ABS(pl_igain0[0]), FORMAT='(F6.1)'),1) + '.eps'
        PREP_PS & DEVICE, FILEN=filename, /ENCAPS, /COLOR, XSIZE=17.8, YSIZE=14.7, /TIMES 
        LOADCT, 0, /SILENT
        PLOT, [min_frq], [0], /XLOG, XTITLE='Frequency [Hz]', YTITLE='Bode magnitude [dB]', XRANGE=[0.1,0.5*max_frq], YRANGE=[-60.,20.], XSTYLE=1, YSTYLE=1, THICK=4.0, CHARSIZE=charsize 
        LOADCT, 13, /SILENT
        OPLOT, freq_dev, 20*ALOG10(ABS(fft_dev)), THICK=4.0, COLOR=color
        LOADCT, 0, /SILENT
        PLOT, [min_frq], [0], /XLOG, XTITLE='Frequency [Hz]', YTITLE='Bode phase [deg]', XRANGE=[0.1,0.5*max_frq], YRANGE=[-180.,180.], XSTYLE=1, YSTYLE=1, THICK=4.0, CHARSIZE=charsize
        LOADCT, 13, /SILENT
        OPLOT, freq_dev, ATAN(Imaginary(fft_dev),Real_part(fft_dev))/!DTOR, THICK=4.0, COLOR=color
        DEVICE, /CLOSE & END_PS  
        ; Skip point
        SKIP_GAIN:   
      ENDFOR
    ENDIF
    
    IF KEYWORD_SET(PLOT_DELAY) THEN BEGIN
      !P.Multi  = [0, 1, 1, 0, 1]   ; Plot 4 graphs per window
      WSET, 5
      PLOT, time, pcimgdt, XTITLE='Elapsed time [s]', YTITLE='Time since last frame [ms]', XRANGE=[MIN(time),MAX(time)], YRANGE=[0.,5.], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    ENDIF
    
    ; Plot SNR
    IF KEYWORD_SET(PLOT_TT) THEN BEGIN
      !P.Multi  = [0, 1, 2, 0, 1]   ; Plot 4 graphs per window
      WSET, 6
      PLOT, time, tip, XTITLE='Elapsed time [s]', YTITLE='Tip [mas]', XRANGE=[MIN(time),MAX(time)], YRANGE=[MIN(tip),MAX(tip)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
      PLOT, time, tilt, XTITLE='Elapsed time [s]', YTITLE='Tilt [mas]', XRANGE=[MIN(time),MAX(time)], YRANGE=[MIN(tilt),MAX(tilt)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
    ENDIF
  ENDIF ; End of the plot block

  jump_loop:
  IF n_data LT 20 THEN PRINT, 'Not enough data points for FFT computation'
  
  ; Add a wait command
  WAIT, 0.5*time_bin < 1
ENDWHILE

; Diagnostic plots
IF KEYWORD_SET(DIAGNOSTIC) THEN BEGIN
  !P.Multi  = [0, 1, 1, 0, 1]   
  WINDOW, 3, XSIZE=800, YSIZE=400, TITLE='Phase and unwraped phase'
  WSET, 3
  PLOT, time, phase*!Dpi/180, XTITLE='Elapsed time [s]', YTITLE='phase', XRANGE=[0.,MAX(time)], YRANGE=[MIN(phase_un),MAX(phase_un)], XSTYLE=1, YSTYLE=1, CHARSIZE=charsize
  LOADCT, 13, /SILENT
  OPLOT, time, phase_un, COLOR=90
  LOADCT, 0, /SILENT
  
  WINDOW, 4, TITLE= '', XSIZE=0.20*screen[0], YSIZE=screen[1], XPOS=0.0*screen[0], RETAIN=2
  WSET, 4
  PLOT, tip, phase, XTITLE='Tip', YTITLE='phase [deg]', XRANGE=[MIN(tip)-1,MAX(tip)+1], YRANGE=[MIN(phase),MAX(phase)], XSTYLE=1, YSTYLE=1, PSYM=2, SYMSIZE=0.1, CHARSIZE=charsize
  
  WINDOW, 5, TITLE= '', XSIZE=0.20*screen[0], YSIZE=screen[1], XPOS=0.2*screen[0], RETAIN=2
  WSET, 5
  PLOT, tilt, phase, XTITLE='Tilt', YTITLE='phase [deg]', XRANGE=[MIN(tilt)-1,MAX(tilt)+1], YRANGE=[MIN(phase),MAX(phase)], XSTYLE=1, YSTYLE=1, PSYM=2, SYMSIZE=0.1, CHARSIZE=charsize
  
  WINDOW, 6, TITLE= '', XSIZE=0.20*screen[0], YSIZE=screen[1], XPOS=0.4*screen[0], RETAIN=2
  WSET, 6
  tt = SQRT(tilt^2+tip^2)
  PLOT, tt, phase, XTITLE='Tilt', YTITLE='phase [deg]', XRANGE=[MIN(tt)-1,MAX(tt)+1], YRANGE=[MIN(phase),MAX(phase)], XSTYLE=1, YSTYLE=1, PSYM=2, SYMSIZE=0.1, CHARSIZE=charsize
END

; Plot OVMS results
IF n_data GT fr_min THEN BEGIN
  IF MAX(pcovplv) NE 0 THEN BEGIN
    ; Compute PSD
    COMPUTE_PSD, time, pcovplv, FREQ=freq, FRQ_EXT=frqc, FFT=fft_opd, PSD=psd_opd, CUM_RMS=rms_opd, SLOPE=slope_opd, INFO=0 
    
    ; Plot OPD
    !P.Multi  = [0, 1, 1, 0, 1]
    filename = result_path + date + '_OPD_'+ STRING(pcovhzn[0], FORMAT='(I0)') + 'ms.eps'  
    PREP_PS, /VERYBOLD & DEVICE, FILEN=filename, /ENCAPS, /COLOR, XSIZE=17.8, YSIZE=14.7, /TIMES
    LOADCT, 0, /SILENT
    PLOT, time, pcovplv, XTITLE='Elapsed time [s]', YTITLE='OPD [um]', XRANGE=[0,20], YRANGE=[MIN(pcovplv),MAX(pcovplv)], XSTYLE=1, YSTYLE=1
    LOADCT, 13, /SILENT
    OPLOT, time, pcplcorr, THICK=4.0, COLOR=90
    OPLOT, time, opd, THICK=4.0, COLOR=160
    OPLOT, time, pcovplv, THICK=4.0, COLOR=250
    LOADCT, 0, /SILENT
    DEVICE, /CLOSE & END_PS
  ENDIF
ENDIF

; Save data if requested
IF KEYWORD_SET(SAVE) THEN BEGIN
  ; Compute normalized quantities
  ;phase_norm = phase_un - MIN(phase_un) ;& phase_norm = phase_norm/MAX(phase_norm)
  ;phase_norm = pccgerr - MIN(pccgerr)   & phase_norm = phase_norm/MAX(phase_norm)
  ;tip_norm   = tip - MIN(tip)           ;& tip_norm   = tip_norm/MAX(tip_norm)
  ;tilt_norm  = tilt - MIN(tilt)         ;& tilt_norm  = tilt_norm/MAX(tilt_norm)
  log_file   = result_path + date + '.txt'
  OPENW, lun, log_file, /GET_LUN, WIDTH=800
  PRINTF,lun, 't0=' + STRING(time_jd[0], FORMAT='(F16.8)')
  PRINTF,lun, 'PHASECam PID gains : ', STRTRIM(STRING(ABS(pl_pgain[0]), FORMAT='(F6.1)'),1) + ' ' + STRTRIM(STRING(ABS(pl_igain[0]), FORMAT='(F6.1)'),1) + ' ' + STRTRIM(STRING(ABS(pl_dgain[0]), FORMAT='(F6.1)'),1)
  PRINTF,lun, 'OVMS gains         : ', STRTRIM(STRING(ABS(pcovplg[0]), FORMAT='(F6.1)'),1) + ' ' + STRTRIM(STRING(ABS(pcovtpg[0]), FORMAT='(F6.1)'),1) + ' ' + STRTRIM(STRING(ABS(pcovtlg[0]), FORMAT='(F6.1)'),1)
  PRINTF,lun, 'OVMS prediction horizon is ' + STRING(pcovhzn[0], FORMAT='(F3.1)') + ' ms'
  PRINTF,lun, 'time[s];opd[um];tip[mas];tilt[mas];OVMS_OPD[um];OVMS_tip[as];OVMS_tilt[mas]
  ;FOR i=0, N_ELEMENTS(phase_norm)-1 DO PRINTF,lun, time[i],';', phase_norm[i],';',tip_norm[i],';',tilt_norm[i]
  ;FOR i=0, N_ELEMENTS(opd)-1 DO PRINTF,lun, time[i]-time[0],';', opd[i],';',tip[i],';',tilt[i],';',pcovplv[i],';',pcovtpv[i],';',pcovtlv[i]
  FOR i=0, N_ELEMENTS(opd)-1 DO PRINTF,lun, time[i]-time[0],';', pcplcorr[i],';',pctipcmd[i],';',pctltcmd[i],';',pcovplv[i],';',pcovtpv[i],';',pcovtlv[i]
  CLOSE, lun
  FREE_LUN, lun
  ; Print info to screen
  PRINT, 'Data saved in ', log_file
ENDIF
END


; ------------------------------------------------------------------
; ------------------------------------------------------------------
; Test routine

PRO TEST_PHASE
  RESTORE, 'phasecam06.sav'
  opd1 = opd
  AVGSDV, opd1, avg1, rms1
  RESTORE, 'phasecam.sav'
  opd2 = opd
  AVGSDV, opd2, avg2, rms2
  
  n = N_ELEMENTS(opd)
  diff = DBLARR(n)
  FOR i=0, n-1 DO BEGIN
    AVGSDV, opd1 - SHIFT(opd2, i), avg, rms
    diff[i] = rms
  ENDFOR
  min = MIN(ABS(diff), idx_min)
  
  !P.Multi  = [0, 1, 3, 0, 1]
  charsize = 2
  color    = 255
  LOADCT, 32, /SILENT
  PLOT, [0], [0], TITLE='Output 1', XTITLE='Time [s]', YTITLE='OPD [um]', CHARSIZE=charsize, XRANGE=[MIN(time),MAX(time)], YRANGE=[MIN(opd1),1.5*MAX(opd1)], XSTYLE=1
  OPLOT, time, opd1, COLOR=color
  XYOUTS, MIN(time[3]), 1.4*MAX(opd1), 'OPD RMS = ' + STRING(rms1, FORMAT='(F5.3)') + ' um', COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
  PLOT, [0], [0], TITLE='Output 2', XTITLE='Time [s]', YTITLE='OPD [um]', CHARSIZE=charsize, XRANGE=[MIN(time),MAX(time)], YRANGE=[MIN(opd1),1.5*MAX(opd1)], XSTYLE=1
  OPLOT, time, SHIFT(opd2, idx_min), COLOR=color
  XYOUTS, MIN(time[3]), 1.4*MAX(opd1), 'OPD RMS = ' + STRING(rms2, FORMAT='(F5.3)') + ' um', COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
  PLOT, time, opd1-SHIFT(opd2, idx_min), XTITLE='Time [s]', YTITLE='OPD difference [um]', CHARSIZE=charsize, XRANGE=[MIN(time),MAX(time)], YRANGE=[MIN(opd1),1.5*MAX(opd1)], XSTYLE=1
  XYOUTS, MIN(time[3]), 1.4*MAX(opd1), 'OPD RMS = ' + STRING(diff[idx_min], FORMAT='(F5.3)') + ' um', COLOR=color, CHARSIZE=1.5, CHARTHICK=1.2
END
