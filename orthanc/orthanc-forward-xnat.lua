-- ============================================================================
-- Orthanc Lua Script: Auto-Forward to XNAT
-- ============================================================================
-- Ce script transfère automatiquement les études stables vers XNAT
-- pour anonymisation après 10 secondes de stabilité
-- ============================================================================

function OnStableSeries(seriesId, tags, metadata)
    print('Stable series detected: ' .. seriesId)
    
    -- Récupérer les informations de la série
    local seriesInfo = ParseJson(RestApiGet('/series/' .. seriesId))
    local studyId = seriesInfo['ParentStudy']
    
    print('Parent study: ' .. studyId)
    
    -- Récupérer les informations de l'étude
    local studyInfo = ParseJson(RestApiGet('/studies/' .. studyId))
    
    -- Afficher les tags DICOM
    print('PatientID: ' .. (tags['PatientID'] or 'N/A'))
    print('PatientName: ' .. (tags['PatientName'] or 'N/A'))
    print('StudyDescription: ' .. (tags['StudyDescription'] or 'N/A'))
    print('Modality: ' .. (tags['Modality'] or 'N/A'))
    
    -- Transférer vers XNAT via DICOM C-STORE
    print('Transferring to XNAT DICOM receiver...')
    
    local command = {}
    command['Level'] = 'Study'
    command['Resources'] = { studyId }
    
    -- Envoi vers le modality XNAT configuré
    local result = RestApiPost('/modalities/XNAT/store', DumpJson(command))
    
    print('Transfer result: ' .. result)
    print('Study sent to XNAT for anonymization')
    
    return true
end

function OnStableStudy(studyId, tags, metadata)
    print('Stable study detected: ' .. studyId)
    
    -- Alternative: Transférer toute l'étude d'un coup
    print('PatientID: ' .. (tags['PatientID'] or 'N/A'))
    print('PatientName: ' .. (tags['PatientName'] or 'N/A'))
    print('StudyDescription: ' .. (tags['StudyDescription'] or 'N/A'))
    
    print('Transferring entire study to XNAT...')
    
    local command = {}
    command['Level'] = 'Study'
    command['Resources'] = { studyId }
    
    local result = RestApiPost('/modalities/XNAT/store', DumpJson(command))
    
    print('Transfer completed: ' .. result)
    
    return true
end

-- Log au démarrage
print('==============================================')
print('XNAT Auto-Forward Script Loaded Successfully')
print('Stable Age: 10 seconds')
print('Target: XNAT DICOM Receiver (Port 8104)')
print('==============================================')
