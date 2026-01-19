# Guide du Dashboard

Guide complet d utilisation du dashboard de monitoring.

## Interface Principale

Le dashboard est accessible a http://localhost:3000.

## Sections du Dashboard

### 1. Panel de Statut

Affiche l etat de tous les services:
- Orthanc (vert = actif)
- DCM4CHEE (vert = actif)
- XNAT (vert = actif)
- RT-Extractor (vert = actif)

### 2. Cartes de Statistiques

Quatre cartes principales:

#### Total Studies
Nombre total d etudes DICOM dans Orthanc.

#### Total Series
Nombre total de series DICOM.

#### Total Instances
Nombre total d instances DICOM (images individuelles).

#### Storage Used
Espace disque utilise par les fichiers DICOM.

### 3. Graphiques

#### Graphique de Croissance
Montre l evolution du nombre d instances au fil du temps.

#### Graphique de Distribution
Distribution des etudes par modalite (CT, MR, US, etc.).

### 4. Feed d Activite

Liste des dernieres activites:
- Nouveaux uploads
- Transferts entre serveurs
- Extractions RT-STRUCT

### 5. Actions Rapides

Boutons d acces rapide:
- "Open OHIF Viewer" - Ouvre le viewer DICOM
- "Open Orthanc" - Interface Orthanc
- "Open DCM4CHEE" - Interface DCM4CHEE
- "Open XNAT" - Interface XNAT

## Modal d Upload

Cliquez sur "Upload DICOM" pour ouvrir le modal.

### Etapes d Upload
1. Cliquez sur la zone de drop ou selectionnez un fichier
2. Selectionnez un ou plusieurs fichiers .dcm
3. Cliquez sur "Upload to Orthanc"
4. Attendez la confirmation

### Formats Supportes
- .dcm (fichiers DICOM standard)
- Zip contenant plusieurs fichiers DICOM

## Integration API

Le dashboard communique avec l API FastAPI:

```javascript
// Exemple de requete
const response = await axios.get('http://localhost:8000/api/status');
```

## Actualisation Automatique

Le dashboard se rafraichit automatiquement toutes les 30 secondes pour afficher les dernieres donnees.

## Troubleshooting

Si le dashboard ne se charge pas:
1. Verifiez que le conteneur est actif: `docker compose ps`
2. Verifiez les logs: `docker compose logs dashboard`
3. Verifiez que le port 3000 n est pas utilise

Pour plus de details, voir [Common Issues](../troubleshooting/common-issues.md).
