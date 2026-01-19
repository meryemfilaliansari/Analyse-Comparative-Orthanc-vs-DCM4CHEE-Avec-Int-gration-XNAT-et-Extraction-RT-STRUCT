# Problemes Courants

Solutions aux problemes frequemment rencontres.

## Problemes d Installation

### Erreur: Port deja utilise

**Symptome**: `Bind for 0.0.0.0:8042 failed: port is already allocated`

**Solution**:
```bash
# Trouver le processus utilisant le port
netstat -ano | findstr :8042

# Arreter le processus ou modifier le port dans docker-compose.yml
```

### Erreur: Docker Compose non trouve

**Symptome**: `docker-compose: command not found`

**Solution**:
```bash
# Utiliser docker compose (sans tiret)
docker compose up -d

# Ou installer docker-compose
pip install docker-compose
```

## Problemes de Services

### Orthanc ne demarre pas

**Solution**:
```bash
# Verifier les logs
docker compose logs orthanc

# Supprimer le conteneur et recreer
docker compose down
docker compose up -d orthanc
```

### DCM4CHEE LDAP erreur

**Symptome**: `LDAP authentication failed`

**Solution**:
1. Verifiez le mot de passe LDAP dans .env
2. Reinitialiser LDAP: `docker compose restart ldap`
3. Verifiez ldap-init-simple.ldif

### XNAT ne se charge pas

**Solution**:
```bash
# XNAT prend plusieurs minutes au premier demarrage
docker compose logs xnat

# Attendre que le message "XNAT is ready" apparaisse
```

## Problemes DICOM

### Upload DICOM echoue

**Causes possibles**:
1. Fichier DICOM corrompu
2. AE Title incorrect
3. Ports non ouverts

**Solutions**:
```bash
# Verifier que le fichier est valide
dcmdump fichier.dcm

# Tester la connexion
echoscu localhost 4242 -aec ORTHANC

# Verifier les logs Orthanc
docker compose logs orthanc | grep -i error
```

### Transfert Orthanc vers DCM4CHEE echoue

**Solution**:
1. Verifiez que DCM4CHEE est actif
2. Verifiez l AE Title dans orthanc.json
3. Verifiez la configuration DCM4CHEE

## Problemes de Base de Donnees

### PostgreSQL erreur de connexion

**Symptome**: `could not connect to server`

**Solution**:
```bash
# Verifier que PostgreSQL est actif
docker compose ps postgres

# Recreer la base de donnees
docker compose down postgres
docker volume rm pacs_postgres_data
docker compose up -d postgres
```

### MySQL erreur DCM4CHEE

**Solution**:
```bash
# Verifier les logs MySQL
docker compose logs mysql

# Verifier les credentials dans .env
```

## Problemes de Performance

### Dashboard lent

**Causes**: Trop d instances DICOM, requetes lentes

**Solutions**:
- Limiter le nombre d instances affichees
- Optimiser les index PostgreSQL
- Augmenter les ressources Docker

### Orthanc lent

**Solutions**:
```bash
# Augmenter la memoire
docker update --memory=4g orthanc

# Nettoyer les anciennes instances
curl -X DELETE http://localhost:8042/instances/old-instance-id
```

## Problemes de Reseau

### Services ne se voient pas

**Solution**:
```bash
# Verifier le reseau Docker
docker network inspect pacs_network

# Recreer le reseau
docker compose down
docker network prune
docker compose up -d
```

### CORS erreur dans le browser

**Solution**: Ajouter les headers CORS dans la configuration Orthanc.

## Commandes de Diagnostic

### Verifier tous les services
```bash
docker compose ps
```

### Verifier les logs en temps reel
```bash
docker compose logs -f
```

### Verifier l espace disque
```bash
docker system df
```

### Nettoyer Docker
```bash
docker system prune -a
```

## Support Avance

Pour des problemes complexes, collectez les informations suivantes:
1. `docker compose ps > status.txt`
2. `docker compose logs > logs.txt`
3. Version Docker: `docker --version`
4. Systeme d exploitation

Pour plus d informations, consultez la [documentation complete](../index.md).
