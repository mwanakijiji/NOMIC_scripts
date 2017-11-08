FUNCTION READ_OVMSDATA, file
  
  file_id   = H5F_OPEN(file)
  ovms_data = H5D_OPEN(file_id, '/internal_system_monitor_01')
  ;attribute = H5A_OPEN_NAME(ovms_data, 'Units');
  ;units     = H5A_READ(attribute, 'Units');
  ovms      = H5D_Read(ovms_data)
  
  ; Close
  H5D_CLOSE, ovms_data
  H5F_CLOSE, file_id
  
  RETURN, ovms
END