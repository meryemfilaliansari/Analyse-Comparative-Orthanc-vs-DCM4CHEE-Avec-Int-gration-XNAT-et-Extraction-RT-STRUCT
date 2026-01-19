# Reinit-Dcm4chee.ps1
# Réinitialisation complète de dcm4chee (containers, volumes, base PostgreSQL)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "REINITIALISATION COMPLETE DCM4CHEE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Arrêt et suppression des containers dcm4chee..." -ForegroundColor Yellow
docker-compose -f docker-compose-dcm4chee-stable.yml down -v

Write-Host "2. Suppression des volumes Docker (base, ldap, storage)..." -ForegroundColor Yellow
docker volume rm $(docker volume ls -q | Select-String "dcm4chee" | ForEach-Object { $_.ToString().Trim() }) 2>$null

Write-Host "3. Reconstruction et redémarrage de la stack dcm4chee..." -ForegroundColor Yellow
docker-compose -f docker-compose-dcm4chee-stable.yml up -d --build

Write-Host "4. Attente du démarrage complet (60s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

Write-Host "5. Vérification du statut des containers..." -ForegroundColor Cyan
docker ps -a | Select-String "dcm4chee"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "REINITIALISATION TERMINEE" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Testez à nouveau l'envoi DICOM avec storescu ou votre script."
