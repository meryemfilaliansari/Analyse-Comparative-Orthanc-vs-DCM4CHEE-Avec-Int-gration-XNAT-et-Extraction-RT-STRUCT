# 🔍 Détection des Viewers DICOM sur votre PC
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "🔍 DÉTECTION DES VIEWERS DICOM INSTALLÉS" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

$viewers = @()

# 1. 3D Slicer
Write-Host "`n🔬 Recherche de 3D Slicer..." -ForegroundColor Yellow
$slicerPaths = @(
    "C:\Program Files\Slicer*\Slicer.exe",
    "C:\Program Files (x86)\Slicer*\Slicer.exe",
    "$env:LOCALAPPDATA\NA-MIC\Slicer*\Slicer.exe"
)
foreach ($path in $slicerPaths) {
    $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "   ✅ 3D Slicer trouvé: $($found.FullName)" -ForegroundColor Green
        $viewers += @{Name="3D Slicer"; Path=$found.FullName; Found=$true}
        break
    }
}
if (-not $found) {
    Write-Host "   ❌ 3D Slicer non installé" -ForegroundColor Red
    Write-Host "   📥 Télécharger: https://www.slicer.org/" -ForegroundColor Gray
    $viewers += @{Name="3D Slicer"; Found=$false; Url="https://www.slicer.org/"}
}

# 2. Weasis
Write-Host "`n🌐 Recherche de Weasis..." -ForegroundColor Yellow
$weasisPaths = @(
    "C:\Program Files\Weasis\weasis.exe",
    "C:\Program Files (x86)\Weasis\weasis.exe",
    "$env:LOCALAPPDATA\Weasis\weasis.exe"
)
$found = $null
foreach ($path in $weasisPaths) {
    $found = Get-Item -Path $path -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "   ✅ Weasis trouvé: $($found.FullName)" -ForegroundColor Green
        $viewers += @{Name="Weasis"; Path=$found.FullName; Found=$true}
        break
    }
}
if (-not $found) {
    Write-Host "   ❌ Weasis non installé" -ForegroundColor Red
    Write-Host "   📥 Télécharger: https://nroduit.github.io/en/" -ForegroundColor Gray
    $viewers += @{Name="Weasis"; Found=$false; Url="https://nroduit.github.io/en/"}
}

# 3. RadiAnt
Write-Host "`n🪟 Recherche de RadiAnt..." -ForegroundColor Yellow
$radiantPaths = @(
    "C:\Program Files\RadiAnt DICOM Viewer\RadiAntViewer.exe",
    "C:\Program Files (x86)\RadiAnt DICOM Viewer\RadiAntViewer.exe"
)
$found = $null
foreach ($path in $radiantPaths) {
    $found = Get-Item -Path $path -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "   ✅ RadiAnt trouvé: $($found.FullName)" -ForegroundColor Green
        $viewers += @{Name="RadiAnt"; Path=$found.FullName; Found=$true}
        break
    }
}
if (-not $found) {
    Write-Host "   ❌ RadiAnt non installé" -ForegroundColor Red
    Write-Host "   📥 Télécharger: https://www.radiantviewer.com/" -ForegroundColor Gray
    $viewers += @{Name="RadiAnt"; Found=$false; Url="https://www.radiantviewer.com/"}
}

# 4. MicroDicom
Write-Host "`n🆓 Recherche de MicroDicom..." -ForegroundColor Yellow
$microdicomPaths = @(
    "C:\Program Files\MicroDicom\MicroDicom.exe",
    "C:\Program Files (x86)\MicroDicom\MicroDicom.exe"
)
$found = $null
foreach ($path in $microdicomPaths) {
    $found = Get-Item -Path $path -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "   ✅ MicroDicom trouvé: $($found.FullName)" -ForegroundColor Green
        $viewers += @{Name="MicroDicom"; Path=$found.FullName; Found=$true}
        break
    }
}
if (-not $found) {
    Write-Host "   ❌ MicroDicom non installé" -ForegroundColor Red
    Write-Host "   📥 Télécharger: http://www.microdicom.com/" -ForegroundColor Gray
    $viewers += @{Name="MicroDicom"; Found=$false; Url="http://www.microdicom.com/"}
}

# 5. Horos (Mac uniquement, mais on vérifie quand même)
Write-Host "`n🍎 Recherche de Horos..." -ForegroundColor Yellow
Write-Host "   ⚠️  Horos est uniquement pour macOS" -ForegroundColor Yellow

# Résumé
Write-Host "`n" + ("="*80) -ForegroundColor Cyan
Write-Host "📊 RÉSUMÉ" -ForegroundColor Cyan
Write-Host ("="*80) -ForegroundColor Cyan

$installed = ($viewers | Where-Object { $_.Found -eq $true }).Count
$notInstalled = ($viewers | Where-Object { $_.Found -eq $false }).Count

Write-Host "`n✅ Viewers installés: $installed" -ForegroundColor Green
Write-Host "❌ Viewers non installés: $notInstalled" -ForegroundColor Red

if ($installed -gt 0) {
    Write-Host "`n🎉 VIEWERS TROUVÉS:" -ForegroundColor Green
    foreach ($viewer in $viewers | Where-Object { $_.Found -eq $true }) {
        Write-Host "   • $($viewer.Name): $($viewer.Path)" -ForegroundColor Green
    }
    
    Write-Host "`n💡 COMMENT LES UTILISER:" -ForegroundColor Yellow
    Write-Host "   1. Ouvrir le viewer"
    Write-Host "   2. File → Import/Open DICOM"
    Write-Host "   3. Pointer vers: C:\Users\awati\Desktop\pacs\rt_diagnostic_output\rtstruct.dcm"
    Write-Host "   4. Charger aussi les images CT de Orthanc si disponibles"
}

if ($notInstalled -gt 0) {
    Write-Host "`n📥 VIEWERS RECOMMANDÉS (gratuits):" -ForegroundColor Yellow
    foreach ($viewer in $viewers | Where-Object { $_.Found -eq $false }) {
        if ($viewer.Url) {
            Write-Host "   • $($viewer.Name): $($viewer.Url)" -ForegroundColor Gray
        }
    }
}

# Solutions alternatives déjà disponibles
Write-Host "`n" + ("="*80) -ForegroundColor Cyan
Write-Host "✅ SOLUTIONS DÉJÀ DISPONIBLES (sans installation)" -ForegroundColor Green
Write-Host ("="*80) -ForegroundColor Cyan

Write-Host "`n1. 🌐 Interface Web Interactive (Recommandé!)" -ForegroundColor Green
Write-Host "   Fichier: rt_diagnostic_output\rtstruct_interactive.html"
Write-Host "   Commande: Start-Process 'rt_diagnostic_output\rtstruct_interactive.html'"

Write-Host "`n2. 🐍 Visualisation Python" -ForegroundColor Green
Write-Host "   Commande: python visualize_rtstruct.py"

Write-Host "`n3. 🏥 Orthanc Explorer" -ForegroundColor Green
Write-Host "   URL: http://localhost:8042/app/explorer.html"

Write-Host "`n4. 🖼️  Images PNG" -ForegroundColor Green
Write-Host "   Fichier: rt_diagnostic_output\rtstruct_visualization.png"

# Offrir d'ouvrir l'interface web
Write-Host "`n" + ("="*80) -ForegroundColor Cyan
Write-Host "🚀 ACTION RAPIDE" -ForegroundColor Cyan
Write-Host ("="*80) -ForegroundColor Cyan

$choice = Read-Host "`nVoulez-vous ouvrir l'interface web interactive? (o/n)"

if ($choice -eq 'o' -or $choice -eq 'O' -or $choice -eq 'oui' -or $choice -eq 'y') {
    Write-Host "`n✅ Ouverture de l'interface web..." -ForegroundColor Green
    Start-Process "rt_diagnostic_output\rtstruct_interactive.html"
    Write-Host "✅ Interface ouverte!" -ForegroundColor Green
} else {
    Write-Host "`nℹ️  Vous pouvez l'ouvrir manuellement:" -ForegroundColor Cyan
    Write-Host "   Start-Process 'rt_diagnostic_output\rtstruct_interactive.html'"
}

Write-Host "`n" + ("="*80) -ForegroundColor Cyan
Write-Host "✅ ANALYSE TERMINÉE" -ForegroundColor Green
Write-Host ("="*80) -ForegroundColor Cyan
