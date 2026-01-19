# Configuration

Guide de configuration avancee de la plateforme PACS.

## Fichier .env

Le fichier .env contient toutes les variables d environnement:

```env
# PostgreSQL
POSTGRES_PASSWORD=VotreMotDePasseSecurise123!
DATABASE_URL=postgresql://pacs_user:password@postgres:5432/pacs_db

# Orthanc
ORTHANC_USERNAME=admin
ORTHANC_PASSWORD=orthanc_secure_password

# DCM4CHEE
DCM4CHEE_ADMIN_PASSWORD=dcm4chee_admin_password
LDAP_ROOT_PASSWORD=ldap_root_password

# XNAT
XNAT_ADMIN_PASSWORD=xnat_admin_password

# Grafana
GF_SECURITY_ADMIN_PASSWORD=grafana_admin_password
```

## Configuration Orthanc

Le fichier orthanc.json configure le serveur Orthanc:

```json
{
  "Name": "Orthanc-Main",
  "DicomAet": "ORTHANC",
  "DicomPort": 4242,
  "HttpPort": 8042,
  "RemoteAccessAllowed": true,
  "AuthenticationEnabled": true,
  "RegisteredUsers": {
    "admin": "orthanc_secure_password"
  },
  "DicomModalities": {
    "DCM4CHEE": {
      "AET": "DCM4CHEE",
      "Host": "dcm4chee",
      "Port": 11112
    }
  }
}
```

## Configuration DCM4CHEE

DCM4CHEE utilise des fichiers XML pour la configuration.

Verifiez que les AE Titles sont correctement configures.

## Configuration XNAT

XNAT se configure via l interface web apres le premier demarrage.

1. Connectez-vous a http://localhost:8081
2. Acceptez les conditions d utilisation
3. Creez un projet
4. Configurez l anonymisation

## Securite en Production

En production, assurez-vous de:

- Changer TOUS les mots de passe par defaut
- Utiliser des mots de passe forts (16+ caracteres)
- Activer HTTPS avec certificats SSL
- Configurer un firewall

Pour plus de details, consultez la documentation complete.
