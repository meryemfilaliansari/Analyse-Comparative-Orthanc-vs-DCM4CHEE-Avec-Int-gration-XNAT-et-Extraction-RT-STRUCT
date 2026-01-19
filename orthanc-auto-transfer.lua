-- Orthanc Lua Script for Auto-Forwarding to DCM4CHEE
-- This script automatically sends received DICOM instances to DCM4CHEE

function OnStoredInstance(instanceId, tags, metadata, origin)
  -- Extract study information
  local studyInstanceUid = tags["StudyInstanceUID"]
  
  -- Log the received instance
  print("New instance received: " .. instanceId)
  print("Study UID: " .. studyInstanceUid)
  print("Origin: " .. tostring(origin))
  
  -- Forward the instance to DCM4CHEE modality
  local success, error = pcall(function()
    print("Forwarding instance to DCM4CHEE...")
    RestApiPost('/modalities/DCM4CHEE/store', instanceId)
    print("Successfully forwarded instance: " .. instanceId)
  end)
  
  if not success then
    print("ERROR: Failed to forward instance: " .. tostring(error))
  end
end

print("Orthanc Lua script loaded - Auto-forwarding to DCM4CHEE enabled")
