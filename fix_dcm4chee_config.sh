#!/bin/bash
# Fix dcm4chee configuration - Problème pat_name NULL dans patient_id

echo "=========================================="
echo "FIX CONFIGURATION DCM4CHEE"
echo "Problème: pat_name NULL dans patient_id"
echo "=========================================="
echo ""

# 1. Vérification de la base de données
echo "1. VÉRIFICATION DU SCHÉMA DE LA BASE DE DONNÉES"
echo "------------------------------------------------"
echo "Inspection de la table patient_id..."
docker exec dcm4chee-db psql -U pacs -d pacsdb -c "\d patient_id" 2>&1

echo ""
echo "Vérification des contraintes NOT NULL:"
docker exec dcm4chee-db psql -U pacs -d pacsdb -c "SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = 'patient_id';" 2>&1

echo ""
echo "Contenu actuel de patient_id (devrait être vide):"
docker exec dcm4chee-db psql -U pacs -d pacsdb -c "SELECT * FROM patient_id LIMIT 10;" 2>&1

echo ""
echo ""
# 2. Vérification LDAP
echo "2. VÉRIFICATION DE LA CONFIGURATION LDAP"
echo "-----------------------------------------"
echo "Test de connexion LDAP..."
docker exec dcm4chee-ldap ldapsearch -x -H ldap://localhost:389 -D "cn=admin,dc=dcm4che,dc=org" -w admin -b "dc=dcm4che,dc=org" "(objectClass=*)" 2>&1 | head -20

echo ""
echo "Vérification de la configuration dcm4chee-arc dans LDAP:"
docker exec dcm4chee-ldap ldapsearch -x -H ldap://localhost:389 -D "cn=admin,dc=dcm4che,dc=org" -w admin -b "dicomDeviceName=dcm4chee-arc,cn=Devices,cn=DICOM Configuration,dc=dcm4che,dc=org" 2>&1 | grep -i "dn:\|dicomDeviceName\|dcmAttributeFilter"

echo ""
echo ""
# 3. Logs dcm4chee-arc lors du démarrage
echo "3. LOGS DE DÉMARRAGE DCM4CHEE-ARC"
echo "----------------------------------"
echo "Recherche d'erreurs de configuration..."
docker logs dcm4chee-arc 2>&1 | grep -i "error\|exception\|failed\|ldap" | tail -20

echo ""
echo ""
# 4. Variables d'environnement critiques
echo "4. VARIABLES D'ENVIRONNEMENT DCMCHEE-ARC"
echo "-----------------------------------------"
docker exec dcm4chee-arc env | grep -E "LDAP|DB|POSTGRES" | sort

echo ""
echo ""
# 5. Test de la contrainte problématique
echo "5. TEST DE LA CONTRAINTE PROBLÉMATIQUE"
echo "---------------------------------------"
echo "Tentative d'insertion manuelle avec pat_name NULL (devrait échouer):"
docker exec dcm4chee-db psql -U pacs -d pacsdb -c "INSERT INTO patient_id (pat_id) VALUES ('TEST_NULL');" 2>&1

echo ""
echo "Tentative d'insertion manuelle avec pat_name rempli (devrait réussir):"
docker exec dcm4chee-db psql -U pacs -d pacsdb -c "INSERT INTO patient_id (pat_id, pat_name) VALUES ('TEST_OK', 'TEST^NAME');" 2>&1

echo ""
echo "Vérification:"
docker exec dcm4chee-db psql -U pacs -d pacsdb -c "SELECT * FROM patient_id WHERE pat_id LIKE 'TEST%';" 2>&1

echo ""
echo "Nettoyage des tests:"
docker exec dcm4chee-db psql -U pacs -d pacsdb -c "DELETE FROM patient_id WHERE pat_id LIKE 'TEST%';" 2>&1

echo ""
echo ""
# 6. Recommandations
echo "=========================================="
echo "DIAGNOSTIC ET RECOMMANDATIONS"
echo "=========================================="
echo ""
echo "Le problème 'pat_name NULL' indique que dcm4chee n'arrive pas à"
echo "extraire PatientName du fichier DICOM pour l'insérer dans la DB."
echo ""
echo "Causes possibles:"
echo "  1. Configuration LDAP incomplète ou corrompue"
echo "  2. Mapping DICOM->DB manquant dans la configuration"
echo "  3. Bug de parsing du PatientName"
echo "  4. Schéma de base de données incompatible avec la version"
echo ""
echo "SOLUTIONS À ESSAYER:"
echo ""
echo "A. RÉINITIALISATION COMPLÈTE (recommandé):"
echo "   docker-compose down -v"
echo "   docker-compose up -d"
echo "   # Attendre 2-3 minutes que LDAP et DB soient complètement initialisés"
echo ""
echo "B. VÉRIFICATION DE LA SÉQUENCE DE DÉMARRAGE:"
echo "   Assurez-vous que dans docker-compose.yml:"
echo "   - dcm4chee-ldap démarre en premier"
echo "   - dcm4chee-db démarre après ldap"
echo "   - dcm4chee-arc démarre en dernier (depends_on: ldap, db)"
echo ""
echo "C. CONFIGURATION LDAP MANUELLE (si A et B échouent):"
echo "   Importez manuellement la configuration dcm4chee dans LDAP"
echo "   Documentation: https://github.com/dcm4che/dcm4chee-arc-light/wiki"
echo ""
echo "D. MODIFICATION DU SCHÉMA DB (dernier recours):"
echo "   Rendez pat_name nullable (non recommandé):"
echo "   docker exec dcm4chee-db psql -U pacs -d pacsdb -c 'ALTER TABLE patient_id ALTER COLUMN pat_name DROP NOT NULL;'"
echo ""
