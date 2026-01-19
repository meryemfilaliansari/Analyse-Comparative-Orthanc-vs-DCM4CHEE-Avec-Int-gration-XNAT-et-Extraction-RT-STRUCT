---
noteId: "68ec9aa1edb711f082ec11506d08b3ee"
tags: []

---

# 🔧 CONFIGURATION MANUELLE XNAT DANS ORTHANC

## 🎯 Objectif

Ajouter XNAT comme destination DICOM dans Orthanc Admin pour pouvoir envoyer des images.

---

## 📋 Méthode 1 : Via Interface Web Orthanc (FACILE)

### Étape 1 : Ouvrir Orthanc Explorer

1. **Navigateur** : http://localhost:8042
2. **Connexion** : admin / admin

### Étape 2 : Accéder aux Modalities

1. **En haut à droite**, cliquer sur l'icône **"Configuration"** (roue dentée)
2. **OU** : Aller dans le menu et chercher **"DICOM Modalities"**

### Étape 3 : Ajouter XNAT

1. **Cliquer** : "Add a DICOM modality"
2. **Remplir** :
   ```
   Symbolic name:  XNAT
   AET (AE Title): XNAT
   Host:           xnat
   Port:           8104
   Manufacturer:   Generic
   ```
3. **Cliquer "Add"**

### Étape 4 : Vérifier

1. **La modality "XNAT"** devrait apparaître dans la liste
2. **Tester** : Cliquer sur "Echo" à côté de XNAT
3. **Résultat** : Message "Success" ou "Echo successful"

---

## 📋 Méthode 2 : Via API REST (AVANCÉ)

### PowerShell

```powershell
# Ajouter modality XNAT
$body = @{
    "XNAT" = @("XNAT", "xnat", 8104)
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8042/modalities/XNAT" `
    -Method Put `
    -Body $body `
    -ContentType "application/json" `
    -Headers @{Authorization="Basic YWRtaW46YWRtaW4="}

# Vérifier
Invoke-RestMethod -Uri "http://localhost:8042/modalities" `
    -Headers @{Authorization="Basic YWRtaW46YWRtaW4="}
```

### Linux/Mac (curl)

```bash
# Ajouter XNAT
curl -X PUT http://localhost:8042/modalities/XNAT \
  -u admin:admin \
  -H "Content-Type: application/json" \
  -d '["XNAT", "xnat", 8104]'

# Vérifier
curl http://localhost:8042/modalities -u admin:admin
```

---

## 📋 Méthode 3 : Via Fichier de Configuration (PERMANENT)

### Créer `orthanc.json`

```json
{
  "Name": "Orthanc Admin",
  "RemoteAccessAllowed": true,
  "AuthenticationEnabled": true,
  "RegisteredUsers": {
    "admin": "admin"
  },
  "DicomModalities": {
    "XNAT": ["XNAT", "xnat", 8104],
    "ORTHANC_STUDENT": ["ORTHANC_ANON", "orthanc-anonymized", 4242]
  },
  "DicomAet": "ORTHANC_ADMIN",
  "DicomPort": 4242
}
```

### Monter dans Docker

Modifier `docker-compose.yml` pour monter ce fichier :

```yaml
orthanc-storage:
  image: orthancteam/orthanc:latest
  container_name: orthanc-admin
  volumes:
    - ./orthanc.json:/etc/orthanc/orthanc.json:ro
  # ... reste de la config
```

### Redémarrer

```powershell
docker-compose restart orthanc-storage
```

---

## ✅ Vérification

### Test 1 : Lister les modalities

**PowerShell** :
```powershell
curl http://localhost:8042/modalities -Headers @{Authorization="Basic YWRtaW46YWRtaW4="}
```

**Résultat attendu** :
```json
["XNAT"]
```

### Test 2 : DICOM Echo

**Interface Web** :
1. Orthanc → Configuration → DICOM Modalities
2. Cliquer "Echo" à côté de XNAT
3. ✅ "Success" apparaît

**PowerShell** :
```powershell
curl -X POST http://localhost:8042/modalities/XNAT/echo `
     -Headers @{Authorization="Basic YWRtaW46YWRtaW4="}
```

---

## 🚀 Utilisation

Une fois XNAT configuré :

### Envoyer une étude

**Via Interface Web** :
1. Ouvrir une étude dans Orthanc
2. Cliquer "Send to DICOM modality"
3. Sélectionner "XNAT"
4. Cliquer "Send"

**Via API** :
```powershell
# Récupérer ID d'une étude
$studies = curl http://localhost:8042/studies `
    -Headers @{Authorization="Basic YWRtaW46YWRtaW4="}

# Envoyer première étude vers XNAT
$studyId = ($studies.Content | ConvertFrom-Json)[0]

curl -X POST "http://localhost:8042/modalities/XNAT/store" `
     -Headers @{Authorization="Basic YWRtaW46YWRtaW4="} `
     -ContentType "application/json" `
     -Body "[`"$studyId`"]"
```

---

## 🔍 Dépannage

### ❌ Echo échoue : "Connection refused"

**Cause** : XNAT DICOM Receiver pas activé

**Solution** :
1. Ouvrir XNAT : http://localhost:8090
2. Administer → Site Administration → Plugin Settings
3. Activer DICOM Receiver
4. Configurer port 8104

### ❌ Echo échoue : "Unknown host"

**Cause** : Mauvais hostname

**Solution** :
- Utiliser `xnat` (nom du container)
- Pas `localhost` ou `127.0.0.1`

### ❌ Modality disparaît après redémarrage

**Cause** : Configuration non persistante

**Solution** :
- Utiliser fichier `orthanc.json` monté dans Docker
- OU reconfigurer via variables d'environnement

---

## 📝 Résumé

**Configuration minimale XNAT** :
- **Symbolic Name** : XNAT
- **AET** : XNAT
- **Host** : xnat
- **Port** : 8104

**Test** : Echo doit réussir

**Utilisation** : "Send to DICOM modality" → XNAT
