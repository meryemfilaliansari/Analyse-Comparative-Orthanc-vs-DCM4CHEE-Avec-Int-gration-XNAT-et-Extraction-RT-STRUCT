#!/bin/bash
# Script de diagnostic complet pour dcm4chee

echo "=========================================="
echo "DIAGNOSTIC DCM4CHEE - RECHERCHE DE L'ERREUR 0x0110"
echo "=========================================="
echo ""

# 1. Liste tous les conteneurs

echo "--- Conteneurs Docker ---"
docker ps -a

echo ""

# 2. Logs récents dcm4chee-arc

echo "--- Derniers logs dcm4chee-arc ---"
docker logs dcm4chee-arc --tail 100

echo ""

# 3. Logs récents base de données dcm4chee-db

echo "--- Derniers logs dcm4chee-db ---"
docker logs dcm4chee-db --tail 100

echo ""

# 4. Contraintes sur la table patient_id

echo "--- Contraintes sur patient_id (PostgreSQL) ---"
docker exec dcm4chee-db psql -U postgres -d pacsdb -c "\d+ patient_id"

echo ""

# 5. Version dcm4chee

echo "--- Version dcm4chee ---"
docker exec dcm4chee-arc printenv | grep DCM4CHEE_VERSION

echo ""

# 6. Version PostgreSQL

echo "--- Version PostgreSQL ---"
docker exec dcm4chee-db psql -U postgres -c "SELECT version();"

echo ""

echo "Diagnostic terminé."
