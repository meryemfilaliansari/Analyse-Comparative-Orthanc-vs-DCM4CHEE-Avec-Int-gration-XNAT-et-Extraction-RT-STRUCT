# Installation

Guide complet d installation de la plateforme PACS Multi-Systemes.

## Prerequis Systeme

| Composant | Minimum | Recommande |
|-----------|---------|------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| Stockage | 100 GB SSD | 500 GB SSD |

## Logiciels Requis

- Docker Engine 24.0+
- Docker Compose 2.20+
- Git 2.30+

## Installation Rapide

### Etape 1: Cloner le Repository

```bash
git clone https://github.com/meryemfilaliansari/Orthanc-vs-DCM4CHEE-Avec-XNAT-et-Extraction-RT-STRUCT.git
cd Orthanc-vs-DCM4CHEE-Avec-XNAT-et-Extraction-RT-STRUCT
```

### Etape 2: Configuration

```bash
cp .env.example .env
```

Editez le fichier .env avec vos mots de passe securises.

### Etape 3: Demarrage

```bash
docker compose up -d
docker compose ps
```

## Acces aux Interfaces

| Service | URL | Identifiants |
|---------|-----|--------------|
| Dashboard | http://localhost:3000 | Public |
| Orthanc | http://localhost:8042 | admin/orthanc |
| DCM4CHEE | http://localhost:8080/dcm4chee-arc/ui2 | admin/admin |
| XNAT | http://localhost:8081 | admin/admin |
| OHIF Viewer | http://localhost:3001 | Public |
| Grafana | http://localhost:3002 | admin/admin |

## Verification

Verifiez que tous les conteneurs sont actifs:

```bash
docker compose ps
```

Tous les services doivent afficher "Up" ou "healthy".

## Troubleshooting

Si un service ne demarre pas, consultez les logs:

```bash
docker compose logs <service_name>
```

Consultez la page [Problemes Courants](../troubleshooting/common-issues.md) pour plus d aide.
