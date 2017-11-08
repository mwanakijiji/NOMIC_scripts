FUNCTION READ_PHASECAM, file, INFO=info

  ; PURPOSE:
  ;   Read the phasecam txt file and return a structure with the corresponding data
  ; 
  ; INPUT:
  ;   file       :  The phasecam txt file to be read.
  ; 
  ; KEYWORDS
  ;   INFO       :  Set this keyword to print info to screen
  ;
  ; MODIFICATION HISTORY:
  ;   Version 1.0,  16-APR-2014, by Denis Defrère, University of Arizona, ddefrere@email.arizona.edu
  ;   Version 1.1,  05-MAY-2014, Modified for new version of the file
  ;   Version 1.2,  31-AUG-2014, Now can read any version of the files without pre-parsing the column names
  ;   Version 1.3,  14-FEB-2016, Updated for February 2016 run
  ;   Version 1.4,  26-MAR-2016, Now handles column nmaes with a trhee digit ID number!

; Keyword check
IF NOT KEYWORD_SET(info) THEN info = 0 

; Retrieve the date of the file
file_data = FILE_INFO(file)
file_date = file_data.ctime        ; this is the number of seconds since 1-1-1970 according to IDL manual

; Read header and create template
header = STRARR(1)
OPENR, lun, file, /GET_LUN
READF, lun, header
FREE_LUN, lun
header = STRSPLIT(header, ',', /EXTRACT, /PRESERVE_NULL) ; Extract to array

; Remove number in front of the field name
n_fields  = N_ELEMENTS(header)
header[0] = STRMID(header[0], 4)
FOR i_f = 1, n_fields-1 DO header[i_f] = STRMID(header[i_f], 2+(i_f GT 8)+(i_f GT 98))  ; i_f = 8 means ID number 9

; Create template
tmpl = {VERSION:1,DATASTART:1,DELIMITER:',',MISSINGVALUE:'Nan',COMMENTSYMBOL:'#',FIELDCOUNT:n_fields,FIELDTYPES:LONARR(n_fields),FIELDNAMES:STRARR(n_fields),FIELDLOCATIONS:LONARR(n_fields),FIELDGROUPS:LONARR(n_fields)}
tmpl.fieldtypes  = 5+INTARR(n_fields)                      
tmpl.fieldgroups = INDGEN(n_fields)           
tmpl.fieldnames  = header

; Read the file
IF info GT 0 THEN PRINT, 'Reading summary text file : ' + file
data = READ_ASCII(file, TEMPLATE=tmpl)

; ALL commands below are for backward compatibility
n_data = N_ELEMENTS(data.pcjd[0])

;IF NOT TAG_EXIST(data, 'pccgig')   THEN data = STRUCT_ADDTAGS(REPLICATE({pccgig:0.}, n_data), data)  ; obsolete
;IF NOT TAG_EXIST(data, 'pccgpg')   THEN data = STRUCT_ADDTAGS(REPLICATE({pccgpg:0.}, n_data), data)  ; obsolete
IF NOT TAG_EXIST(data, 'pccgerr')  THEN data = STRUCT_ADDTAGS(REPLICATE({pccgerr:0.}, n_data), data)
IF NOT TAG_EXIST(data, 'pcplig')   THEN data = STRUCT_ADDTAGS(REPLICATE({pcplig:0.}, n_data), data)
IF NOT TAG_EXIST(data, 'pcpldg')   THEN data = STRUCT_ADDTAGS(REPLICATE({pcpldg:0.}, n_data), data)

; As of 2016, we use two beams and the phase keywrods have now new names (e.g., pcftphsa became pcftphs1 and new pcftphs2 keyword) 
IF NOT TAG_EXIST(data, 'pcplsp1')  THEN BEGIN
  ; Create missing tags
  data = STRUCT_ADDTAGS(REPLICATE({pcplsp1:0.}, n_data), data)   
  data = STRUCT_ADDTAGS(REPLICATE({pcftphs1:0.}, n_data), data)   
  data = STRUCT_ADDTAGS(REPLICATE({pcunwph1:0.}, n_data), data)  
  data = STRUCT_ADDTAGS(REPLICATE({pcunpmn1:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcunpsd1:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcftmgx1:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcftmgy1:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcplsp2:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcftphs2:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcunwph2:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcunpmn2:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcunpsd2:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcftmgx2:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcftmgy2:0.}, n_data), data)         
  ; Parse new tags with data stored in old tags (only one beam before so beam 2 tags stay at zero)
  data.pcplsp1  = data.pcplsp 
  data.pcftphs1 = data.pcftphsa
  IF NOT TAG_EXIST(data, 'pcunwphs') THEN data.pcunwph1 = UNWRAP(data.pcftphs1/!DTOR)*!DTOR ELSE data.pcunwph1 = data.pcunwphs
  data.pcftmgx1 = data.pcftmagx 
  data.pcftmgy1 = data.pcftmagy
ENDIF

; SNR was not saved in old versions
IF NOT TAG_EXIST(data, 'pcmfsnr') THEN BEGIN
  data         = STRUCT_ADDTAGS(REPLICATE({pcmfsnr:0.}, n_data), data)
  data.pcmfsnr = data.pcftmags/data.pcftmagn
ENDIF

; OVMS tags (exist only for on-sky data, not NAC source)
IF NOT TAG_EXIST(data, 'pcovplv') THEN BEGIN
  ; Create missing tags
  data = STRUCT_ADDTAGS(REPLICATE({pcovplv:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcovok:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcovage:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcovplg:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcovtpv:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcovtpg:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcovtlg:0.}, n_data), data)
  data = STRUCT_ADDTAGS(REPLICATE({pcovtlv:0.}, n_data), data)
ENDIF
IF NOT TAG_EXIST(data, 'pcovhzn') THEN data = STRUCT_ADDTAGS(REPLICATE({pcovhzn:0.}, n_data), data)  ; this one was added later

; Wavelength
IF NOT TAG_EXIST(data, 'pcb1lam') THEN data = STRUCT_ADDTAGS(REPLICATE({pcb1lam:2.18}, n_data), data) 
IF NOT TAG_EXIST(data, 'pcb2lam') THEN data = STRUCT_ADDTAGS(REPLICATE({pcb2lam:1.65}, n_data), data)  
  
RETURN, data
END
