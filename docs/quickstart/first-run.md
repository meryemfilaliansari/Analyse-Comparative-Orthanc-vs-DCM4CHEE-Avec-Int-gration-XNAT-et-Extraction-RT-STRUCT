# Premier Demarrage

Guide de verification et de tests apres l installation.

## Verification des Services

Verifiez que tous les services sont demarres:

```bash
cd C:\Users\awati\Desktop\pacs
docker compose ps
```

Tous les services doivent avoir le statut **Up**.

## Tests de Sante

### Orthanc
```bash
curl http://localhost:8042/system
```

### Dashboard
Ouvrez http://localhost:3000 - vous devriez voir le tableau de bord avec les statistiques.

### OHIF Viewer
Ouvrez http://localhost:3001 - le viewer DICOM doit s afficher.

## Premier Upload DICOM

### Via l Interface Web

1. Ouvrez http://localhost:3000
2. Cliquez sur "Upload DICOM"
3. Selectionnez un fichier .dcm
4. Verifiez que le fichier apparait dans Orthanc

### Via StoreSCU

```bash
storescu localhost 4242 -aec ORTHANC fichier.dcm
```

## Tests d Integration

### Transfert Orthanc vers DCM4CHEE

```bash
curl -X POST http://localhost:8042/modalities/DCM4CHEE/store \
  -d '{"Resources":["instance-id"]}'
```

### Verification dans DCM4CHEE

Connectez-vous a http://localhost:8082 et verifiez que l etude apparait.

## Tests d Extraction RT-STRUCT

Si vous avez des fichiers RT-STRUCT:

```bash
curl http://localhost:8000/api/extract-rt/instance-id
```

## Verification Grafana

1. Ouvrez http://localhost:3002
2. Connectez-vous (admin/grafana_admin_password)
3. Verifiez que les metriques s affichent dans le dashboard

## Problemes Courants

Si un service ne demarre pas, consultez les logs:

```bash
docker compose logs service-name
```

Pour plus de details, consultez [Common Issues](../troubleshooting/common-issues.md).
