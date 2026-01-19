# Microservices

Details techniques de chaque microservice.

## Dashboard React (Port 3000)

### Technologies
- React 18
- Vite
- Recharts pour les graphiques
- Axios pour les requetes API

### Fonctionnalites
- Affichage des statistiques en temps reel
- Upload de fichiers DICOM
- Visualisation des etudes
- Acces rapide aux autres services

### Configuration Docker
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

## OHIF Viewer (Port 3001)

### Technologies
- React
- Cornerstone.js pour le rendu DICOM
- DICOMweb protocol

### Integration
Se connecte a Orthanc via DICOMweb QIDO-RS et WADO-RS.

Configuration dans app-config.js pour pointer vers Orthanc.

## Backend FastAPI (Port 8000)

### Endpoints Principaux

#### GET /api/status
Retourne l etat de tous les services.

#### POST /api/upload
Upload un fichier DICOM vers Orthanc.

#### GET /api/extract-rt/{instance_id}
Extrait les contours d un fichier RT-STRUCT.

### Dependencies
- FastAPI
- httpx pour les requetes asynchrones
- python-multipart pour l upload

## Orthanc PACS (Port 8042)

### Caracteristiques
- Serveur DICOM complet
- Support DICOMweb
- API REST complete
- Stockage PostgreSQL

### Plugins
- DICOMweb
- PostgreSQL
- Python (pour scripts d automatisation)

### Configuration
Voir orthanc.json pour la configuration complete.

## DCM4CHEE Archive (Port 8082)

### Caracteristiques
- Archive DICOM entreprise
- Interface web complete
- Support HL7 et DICOM
- Stockage MySQL

### Acces
- Interface: http://localhost:8082/dcm4chee-arc/ui2
- Username: admin
- Password: dcm4chee_admin_password

## XNAT Platform (Port 8081)

### Caracteristiques
- Plateforme de gestion d imagerie
- Anonymisation avancee
- Gestion de projets
- API REST complete

### Configuration
Se fait via l interface web apres le premier demarrage.

## RT-STRUCT Extractor (Port 8000)

### Technologies
- Python 3.11
- rt-utils pour l analyse RT-STRUCT
- pydicom pour la manipulation DICOM

### Fonctionnalites
- Extraction des contours
- Analyse des structures
- Export en JSON

## Grafana (Port 3002)

### Dashboards
- Metriques Orthanc
- Metriques DCM4CHEE
- Statistiques d utilisation

### Datasources
- Prometheus
- PostgreSQL

## Prometheus (Port 9090)

### Metrics Collected
- Nombre d instances DICOM
- Espace disque utilise
- Temps de reponse API
- Nombre de requetes

Pour plus de details sur l architecture globale, voir [Overview](overview.md).
