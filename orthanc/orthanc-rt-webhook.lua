-- orthanc-rt-webhook.lua
-- Script Lua pour Orthanc Admin
-- Détecte les RT-STRUCT et déclenche le workflow automatique

function OnStoredInstance(instanceId, tags, metadata, origin)
   -- Obtenir la modalité
   local modality = tags["Modality"]
   
   -- Si c'est un RT-STRUCT, on log
   if modality == "RTSTRUCT" then
      print("RT-STRUCT détecté: " .. instanceId)
      print("SOPInstanceUID: " .. tags["SOPInstanceUID"])
      
      -- Obtenir l'étude parente
      local studyId = tags["StudyInstanceUID"]
      print("StudyInstanceUID: " .. studyId)
   end
end

function OnStableStudy(studyId, tags, metadata)
   print("Étude stable: " .. studyId)
   
   -- Récupérer toutes les séries de l'étude
   local study = ParseJson(RestApiGet("/studies/" .. studyId))
   
   local hasRTStruct = false
   local hasCT = false
   
   -- Vérifier la présence de RT-STRUCT et CT
   for i, seriesId in pairs(study["Series"]) do
      local series = ParseJson(RestApiGet("/series/" .. seriesId))
      local modality = series["MainDicomTags"]["Modality"]
      
      if modality == "RTSTRUCT" then
         hasRTStruct = true
      end
      
      if modality == "CT" then
         hasCT = true
      end
   end
   
   -- Si on a CT + RT-STRUCT, déclencher le webhook
   if hasRTStruct and hasCT then
      print("CT + RT-STRUCT détectés dans l'étude " .. studyId)
      print("Déclenchement du workflow automatique...")
      
      -- Appel webhook orchestrator
      local payload = {}
      payload["ID"] = studyId
      payload["Type"] = "StableStudy"
      
      local success, response = pcall(function()
         return HttpPost(
            "http://rt-workflow-orchestrator:5000/webhook/orthanc/stable-study",
            DumpJson(payload, true),
            { ["Content-Type"] = "application/json" }
         )
      end)
      
      if success then
         print("✅ Webhook envoyé avec succès: " .. response)
      else
         print("❌ Erreur webhook: " .. tostring(response))
      end
   end
end
