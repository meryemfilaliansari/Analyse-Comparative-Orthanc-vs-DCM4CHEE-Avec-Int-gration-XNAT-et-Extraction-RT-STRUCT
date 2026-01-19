#!/bin/bash
# Active les logs DEBUG dans dcm4chee pour diagnostiquer le problème 0x0110

DCM4CHEE_CONTAINER=$(docker ps --filter "name=dcm4chee-arc" --format "{{.Names}}" | head -n 1)

if [ -z "$DCM4CHEE_CONTAINER" ]; then
    echo "Erreur: Conteneur dcm4chee-arc introuvable."
    exit 1
fi

echo "Activation du mode DEBUG sur $DCM4CHEE_CONTAINER..."

docker exec "$DCM4CHEE_CONTAINER" bash -c 'sed -i "s/rootLogger.level=INFO/rootLogger.level=DEBUG/" /opt/wildfly/standalone/configuration/log4j2.properties && supervisorctl restart wildfly'

echo "DEBUG activé. Redémarrage du service wildfly."
