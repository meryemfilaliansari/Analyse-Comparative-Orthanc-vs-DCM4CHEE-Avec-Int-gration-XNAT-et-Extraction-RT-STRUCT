
# ==============================================================================
# Script de Deploiement XNAT avec Protection Admin
# ==============================================================================

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "  AJOUT XNAT au Portail PACS - Admin Uniquement" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""

# Verifier Docker
Write-Host "[1/7] Verification Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "  OK Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERREUR Docker non installe!" -ForegroundColor Red
    exit 1
}

# Arreter les services existants
Write-Host "`n[2/7] Arret des services existants..." -ForegroundColor Cyan
docker-compose down 2>$null
Write-Host "  OK Services arretes" -ForegroundColor Green

# Creer le fichier .htpasswd pour admin si n'existe pas
Write-Host "`n[3/7] Configuration acces admin XNAT..." -ForegroundColor Cyan
if (-not (Test-Path ".htpasswd_admin")) {
    Write-Host "  Creation du fichier d'authentification admin..." -ForegroundColor Yellow
    # Hash simple pour admin:admin
    "admin:`$apr1`$`$xnat`$`$admin" | Out-File -FilePath ".htpasswd_admin" -Encoding ASCII
    Write-Host "  OK Fichier .htpasswd_admin cree (admin/admin)" -ForegroundColor Green
} else {
    Write-Host "  Fichier .htpasswd_admin existe deja" -ForegroundColor Gray
}

# Nettoyer les anciens builds XNAT si existants
Write-Host "`n[4/7] Nettoyage..." -ForegroundColor Cyan
if (Test-Path "xnat-build") {
    Remove-Item -Recurse -Force "xnat-build" 2>$null
    Write-Host "  OK Ancien build XNAT supprime" -ForegroundColor Green
}

# Verifier la configuration Nginx
Write-Host "`n[5/7] Verification configuration Nginx..." -ForegroundColor Cyan
if (Test-Path "nginx\conf.d\default.conf") {
    Write-Host "  OK Configuration Nginx trouvee" -ForegroundColor Green
} else {
    Write-Host "  ERREUR Configuration Nginx manquante!" -ForegroundColor Red
    exit 1
}

# Demarrer les services
Write-Host "`n[6/7] Demarrage des services..." -ForegroundColor Cyan
Write-Host "  Cela peut prendre 3-5 minutes pour XNAT..." -ForegroundColor Yellow
Write-Host ""

docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK Services demarres" -ForegroundColor Green
} else {
    Write-Host "  ERREUR au demarrage" -ForegroundColor Red
    exit 1
}

# Attendre l'initialisation
Write-Host "`n[7/7] Attente initialisation (90 secondes)..." -ForegroundColor Cyan
$seconds = 90
for ($i = 1; $i -le $seconds; $i++) {
    $percent = [math]::Round(($i / $seconds) * 100)
    Write-Progress -Activity "Initialisation des services" -Status "$percent% Complete" -PercentComplete $percent
    Start-Sleep -Seconds 1
}
Write-Progress -Activity "Initialisation des services" -Completed

# Verifier l'etat des services
Write-Host "`n" -NoNewline
Write-Host "=" -ForegroundColor Green -NoNewline
Write-Host ("=" * 78) -ForegroundColor Green
Write-Host "  STATUT DES SERVICES" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Green -NoNewline
Write-Host ("=" * 78) -ForegroundColor Green
Write-Host ""

docker-compose ps

# Test de connectivite
Write-Host "`n" -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "  TEST DE CONNECTIVITE" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""

$services = @(
    @{Name="PostgreSQL (DCM4CHEE)"; Url="http://localhost:5432"},
    @{Name="PostgreSQL (XNAT)    "; Port=5433},
    @{Name="DCM4CHEE             "; Url="http://localhost:8080/dcm4chee-arc/ui2/"},
    @{Name="XNAT Direct          "; Url="http://localhost:8090/"},
    @{Name="Nginx Gateway        "; Url="http://localhost:8001/health"}
)

foreach ($service in $services) {
    if ($service.Url) {
        try {
            $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            Write-Host "  OK $($service.Name)" -ForegroundColor Green
        } catch {
            Write-Host "  En attente $($service.Name) (en cours d'initialisation...)" -ForegroundColor Yellow
        }
    } elseif ($service.Port) {
        Write-Host "  Info $($service.Name) (Port $($service.Port))" -ForegroundColor Gray
    }
}

# Afficher les URLs d'acces
Write-Host "`n" -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "  URLS D'ACCES" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""
Write-Host "  PORTAIL PRINCIPAL" -ForegroundColor White
Write-Host "     http://localhost:8001" -ForegroundColor Green
Write-Host ""
Write-Host "  SERVICES ADMIN (via portail)" -ForegroundColor White
Write-Host "     DCM4CHEE        : http://localhost:8001/dcm4chee/" -ForegroundColor Cyan
Write-Host "     XNAT (PROTEGE)  : http://localhost:8001/xnat/" -ForegroundColor Cyan
Write-Host "                       Demande login admin" -ForegroundColor Yellow
Write-Host ""
Write-Host "  ACCES DIRECT (sans portail)" -ForegroundColor White
Write-Host "     DCM4CHEE        : http://localhost:8080/dcm4chee-arc/ui2/" -ForegroundColor Gray
Write-Host "     XNAT            : http://localhost:8090/" -ForegroundColor Gray
Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 78) -ForegroundColor Cyan

# Instructions XNAT
Write-Host "`n" -NoNewline
Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("=" * 78) -ForegroundColor Yellow
Write-Host "  CONFIGURATION XNAT (Premiere fois)" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("=" * 78) -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Acceder a XNAT via le portail:" -ForegroundColor White
Write-Host "     http://localhost:8001/xnat/" -ForegroundColor Cyan
Write-Host "     Entrez le login admin Nginx (admin/admin)" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Configuration initiale XNAT:" -ForegroundColor White
Write-Host "     Login XNAT: admin / admin (par defaut)" -ForegroundColor Gray
Write-Host "     Suivre assistant de configuration" -ForegroundColor Gray
Write-Host "     Site URL: http://localhost:8001/xnat/" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Creer le projet anonymisation:" -ForegroundColor White
Write-Host "     Nom: Formation_Radiologie_2024" -ForegroundColor Gray
Write-Host "     Type: Private" -ForegroundColor Gray
Write-Host ""
Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("=" * 78) -ForegroundColor Yellow

# Logs utiles
Write-Host "`n" -NoNewline
Write-Host "COMMANDES UTILES:" -ForegroundColor Cyan
Write-Host "  Logs XNAT            : " -NoNewline
Write-Host "docker logs xnat-web -f" -ForegroundColor White
Write-Host "  Logs DCM4CHEE        : " -NoNewline
Write-Host "docker logs dcm4chee -f" -ForegroundColor White
Write-Host "  Logs Nginx           : " -NoNewline
Write-Host "docker logs nginx -f" -ForegroundColor White
Write-Host "  Statut services      : " -NoNewline
Write-Host "docker-compose ps" -ForegroundColor White
Write-Host "  Arreter              : " -NoNewline
Write-Host "docker-compose down" -ForegroundColor White
Write-Host ""

Write-Host "OK Deploiement XNAT termine!" -ForegroundColor Green
Write-Host ""
Write-Host "ATTENTION XNAT peut prendre 2-3 minutes supplementaires pour initialiser." -ForegroundColor Yellow
Write-Host "Suivez les logs: docker logs xnat-web -f" -ForegroundColor Gray
Write-Host ""
