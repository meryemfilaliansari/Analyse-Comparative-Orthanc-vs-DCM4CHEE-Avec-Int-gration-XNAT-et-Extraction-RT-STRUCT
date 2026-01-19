# Fix-LdapPassword.ps1
# Correction du mot de passe LDAP pour permettre la connexion

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "FIX LDAP - CORRECTION DU MOT DE PASSE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Probleme detecte:" -ForegroundColor Yellow
Write-Host "  LDAP_ROOTPASS dans docker-compose = 'secret'" -ForegroundColor White
Write-Host "  Mais les scripts essaient de se connecter avec 'admin'" -ForegroundColor White
Write-Host ""

Write-Host "1. Test avec le bon mot de passe (secret)..." -ForegroundColor Cyan
docker exec dcm4chee-ldap ldapsearch -x -H ldap://localhost:389 -D 'cn=admin,dc=dcm4che,dc=org' -w secret -b 'dc=dcm4che,dc=org' '(objectClass=*)' 2>&1 | Select-Object -First 10

Write-Host ""
Write-Host "2. Verification de la configuration dcm4chee-arc dans LDAP..." -ForegroundColor Cyan
$ldapResult = docker exec dcm4chee-ldap ldapsearch -x -H ldap://localhost:389 -D 'cn=admin,dc=dcm4che,dc=org' -w secret -b 'dicomDeviceName=dcm4chee-arc,cn=Devices,cn=DICOM Configuration,dc=dcm4che,dc=org' 2>&1

if ($ldapResult -match "numEntries: [1-9]") {
    Write-Host "OK Configuration dcm4chee-arc trouvee dans LDAP" -ForegroundColor Green
    $ldapResult | Select-Object -First 30
} else {
    Write-Host "NON Configuration dcm4chee-arc NON trouvee dans LDAP" -ForegroundColor Red
    Write-Host ""
    Write-Host "CAUSE DU PROBLEME:" -ForegroundColor Yellow
    Write-Host "  dcm4chee-arc n'a pas pu charger sa configuration depuis LDAP" -ForegroundColor White
    Write-Host "  a cause de l'erreur d'authentification au demarrage." -ForegroundColor White
    Write-Host ""
    Write-Host "SOLUTION:" -ForegroundColor Green
    Write-Host "  Redemarrer dcm4chee-arc pour qu'il charge la configuration LDAP:" -ForegroundColor White
    Write-Host ""
    Write-Host "  docker restart dcm4chee-arc" -ForegroundColor Cyan
    Write-Host ""
    $restart = Read-Host "Voulez-vous redemarrer dcm4chee-arc maintenant? (oui/non)"
    if ($restart -eq "oui") {
        Write-Host ""
        Write-Host "Redemarrage de dcm4chee-arc..." -ForegroundColor Yellow
        docker restart dcm4chee-arc
        Write-Host "Attente de 60 secondes pour le redemarrage complet..." -ForegroundColor Yellow
        Start-Sleep -Seconds 60
        Write-Host ""
        Write-Host "Verification des logs apres redemarrage..." -ForegroundColor Cyan
        docker logs dcm4chee-arc --tail 30 2>&1 | Select-String -Pattern "error|exception|started|deployed" -CaseSensitive:$false
        Write-Host ""
        Write-Host "Nouvelle verification de la configuration LDAP..." -ForegroundColor Cyan
        docker exec dcm4chee-ldap ldapsearch -x -H ldap://localhost:389 -D 'cn=admin,dc=dcm4che,dc=org' -w secret -b 'dicomDeviceName=dcm4chee-arc,cn=Devices,cn=DICOM Configuration,dc=dcm4che,dc=org' 2>&1 | Select-Object -First 20
    }
}

Write-Host ""
Write-Host "3. Verification de la sequence pk dans PostgreSQL..." -ForegroundColor Cyan
docker exec dcm4chee-db psql -U pacs -d pacsdb -c "SELECT * FROM pg_sequences WHERE schemaname = 'public' AND sequencename LIKE '%patient%';"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "RESUME" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Si la configuration dcm4chee-arc est trouvee dans LDAP:" -ForegroundColor White
Write-Host "  OK Testez l'envoi DICOM:" -ForegroundColor Green
Write-Host "    storescu -v -aec DCM4CHEE -aet TEST localhost 11112 ultra_minimal.dcm" -ForegroundColor Cyan
Write-Host ""
Write-Host "Si la configuration n'est toujours pas trouvee:" -ForegroundColor White
Write-Host "  ATTENTION Reinitialisation complete necessaire:" -ForegroundColor Yellow
Write-Host "    .\\Reinit-Dcm4chee.ps1" -ForegroundColor Cyan
Write-Host ""