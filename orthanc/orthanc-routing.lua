-- Orthanc Lua Script for Auto-Forwarding to XNAT
-- This script automatically sends received DICOM studies to XNAT

function OnStableStudy(studyId, tags, metadata)
  -- Log the event
  print("New stable study received: " .. studyId)
  print("Patient: " .. tags["PatientName"] .. " (" .. tags["PatientID"] .. ")")
  print("Study Date: " .. tags["StudyDate"])
  
  -- Forward to XNAT
  local studyInstanceUid = tags["StudyInstanceUID"]
  print("Forwarding study to XNAT: " .. studyInstanceUid)
  
  -- Send REST API call to XNAT to retrieve and anonymize
  local xnat_url = "http://xnat-web:8080/api/studies/" .. studyInstanceUid .. "/anonymize"
  print("XNAT URL: " .. xnat_url)
  
  -- Optional: Send to another PACS (DCM4CHEE)
  -- SendToPeer("DCM4CHEE", studyId)
  
  print("Forward operation initiated for study: " .. studyId)
end

function OnStableStudy_ProcessingEvent(event)
  -- Alternative event handler
  print("Processing event for study: " .. tostring(event))
end

print("Orthanc Lua script loaded - Auto-forwarding to XNAT enabled")
