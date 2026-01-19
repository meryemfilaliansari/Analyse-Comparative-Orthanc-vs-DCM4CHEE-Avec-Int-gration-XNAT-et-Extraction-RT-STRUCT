# Script PowerShell pour télécharger des exemples DICOM CT + RT-STRUCT
# Utilise des datasets publics

Write-Host "`n" -NoNewline
Write-Host "Téléchargement d'exemples DICOM CT + RT-STRUCT" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Créer dossier de destination
$destFolder = ".\dicom_samples\rt_test"
New-Item -ItemType Directory -Force -Path $destFolder | Out-Null

Write-Host "Dossier: $destFolder" -ForegroundColor Green
Write-Host ""

# URLs d'exemples DICOM publics
$examples = @(
    @{
        Name = "Head-Neck Cancer RT-STRUCT (TCIA)"
        Url = "https://github.com/pydicom/pydicom/raw/main/src/pydicom/data/test_files/CT_small.dcm"
        Filename = "CT_small.dcm"
        Type = "CT"
    },
    @{
        Name = "RT-STRUCT Example (pydicom)"
        Url = "https://github.com/pydicom/pydicom/raw/main/src/pydicom/data/test_files/rtss.dcm"
        Filename = "rtss.dcm"
        Type = "RT-STRUCT"
    }
)

Write-Host "Sources des données:" -ForegroundColor Yellow
Write-Host "  - PyDICOM Test Files (Open Source)" -ForegroundColor White
Write-Host "  - Licence: MIT/Public Domain" -ForegroundColor White
Write-Host ""

foreach ($example in $examples) {
    Write-Host "[$($example.Type)] $($example.Name)" -ForegroundColor Cyan
    
    try {
        $destPath = Join-Path $destFolder $example.Filename
        
        # Télécharger
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $example.Url -OutFile $destPath -TimeoutSec 30
        $ProgressPreference = 'Continue'
        
        $fileSize = (Get-Item $destPath).Length / 1KB
        Write-Host "  OK: $($example.Filename) ($($fileSize.ToString('F2')) KB)" -ForegroundColor Green
        
    } catch {
        Write-Host "  ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "Téléchargement terminé!" -ForegroundColor Green
Write-Host ""
Write-Host "Fichiers dans: $destFolder" -ForegroundColor Cyan

# Lister les fichiers téléchargés
Get-ChildItem $destFolder -File | ForEach-Object {
    $size = $_.Length / 1KB
    Write-Host "  - $($_.Name) ($($size.ToString('F2')) KB)" -ForegroundColor White
}

Write-Host ""
Write-Host "PROCHAINES ÉTAPES:" -ForegroundColor Yellow
Write-Host "1. Allez sur http://localhost:8042" -ForegroundColor White
Write-Host "2. Cliquez Upload" -ForegroundColor White
Write-Host "3. Sélectionnez TOUS les fichiers .dcm du dossier" -ForegroundColor White
Write-Host "4. Attendez 10 secondes -> workflow automatique!" -ForegroundColor White
Write-Host ""
Write-Host "Alternative: Drag and drop des fichiers sur Orthanc" -ForegroundColor Cyan
Write-Host ""
