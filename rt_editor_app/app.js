// RT-STRUCT Editor Pro - Application JavaScript
// Configuration
const CONFIG = {
    orthancUrl: '/api/orthanc',
    rtUtilsUrl: '/api/rt',
    itkVtkUrl: '/api',
    orchestratorUrl: '/api/workflow'
};

// Application State
const state = {
    currentStudy: null,
    currentSeries: null,
    rois: [],
    workflowSteps: ['pending', 'pending', 'pending', 'pending', 'pending'],
    viewer: null,
    scene3d: null,
    currentTool: 'zoom'
};

// Initialize application
document.addEventListener('DOMContentLoaded', init);

function init() {
    console.log('🚀 Initializing RT-STRUCT Editor Pro...');
    
    // Setup upload zone
    setupUploadZone();
    
    // Setup viewer tabs
    setupViewerTabs();
    
    // Setup tools
    setupTools();
    
    // Load studies from Orthanc
    loadOrthancStudies();
    
    // Setup action buttons
    setupActionButtons();
    
    // Initialize Cornerstone
    initializeCornerstone();
    
    console.log('✅ Application initialized');
}

// ============================================================================
// Upload & File Handling
// ============================================================================

function setupUploadZone() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    uploadZone.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
    
    // Drag & Drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
}

async function handleFiles(files) {
    if (!files.length) return;
    
    showLoading('Upload des fichiers DICOM...');
    updateProgress(0);
    
    try {
        // Upload to Orthanc
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            await uploadToOrthanc(file);
            updateProgress(((i + 1) / files.length) * 100);
        }
        
        hideLoading();
        updateWorkflowStep(0, 'completed');
        
        // Reload studies
        await loadOrthancStudies();
        
        showNotification('✅ Fichiers uploadés avec succès!');
    } catch (error) {
        hideLoading();
        showNotification('❌ Erreur upload: ' + error.message, 'error');
    }
}

async function uploadToOrthanc(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) throw new Error('Upload failed');
    return await response.json();
}

// ============================================================================
// Orthanc Studies Management
// ============================================================================

async function loadOrthancStudies() {
    try {
        const response = await fetch('/api/studies');
        const studyIds = await response.json();
        
        const studyList = document.getElementById('studyList');
        studyList.innerHTML = '';
        
        for (const studyId of studyIds.slice(0, 20)) {
            const study = await fetch(`/api/studies/${studyId}`).then(r => r.json());
            const studyItem = createStudyItem(studyId, study);
            studyList.appendChild(studyItem);
        }
    } catch (error) {
        console.error('Error loading studies:', error);
    }
}

function createStudyItem(studyId, study) {
    const li = document.createElement('li');
    li.className = 'study-item';
    li.dataset.studyId = studyId;
    
    const patientName = study.PatientMainDicomTags?.PatientName || 'Unknown';
    const studyDate = study.MainDicomTags?.StudyDate || 'N/A';
    
    li.innerHTML = `
        <div class="patient-name">${patientName}</div>
        <div class="study-date">${formatDate(studyDate)}</div>
    `;
    
    li.addEventListener('click', () => selectStudy(studyId, study));
    
    return li;
}

async function selectStudy(studyId, study) {
    console.log('📂 Loading study:', studyId);
    
    // Update UI
    document.querySelectorAll('.study-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.study-item').classList.add('active');
    
    state.currentStudy = studyId;
    
    showLoading('Chargement de l\'étude...');
    
    try {
        // Find CT series and RT-STRUCT
        const series = study.Series || [];
        let ctSeries = null;
        let rtstructSeries = null;
        
        for (const seriesId of series) {
            const seriesInfo = await fetch(`/api/series/${seriesId}`).then(r => r.json());
            const modality = seriesInfo.MainDicomTags?.Modality;
            
            if (modality === 'CT') ctSeries = seriesId;
            if (modality === 'RTSTRUCT') rtstructSeries = seriesId;
        }
        
        if (ctSeries) {
            await loadCTSeries(ctSeries);
        }
        
        if (rtstructSeries) {
            await loadRTStruct(rtstructSeries);
        }
        
        hideLoading();
        
        if (ctSeries && rtstructSeries) {
            document.getElementById('btnProcess').disabled = false;
            showNotification('✅ CT + RT-STRUCT détectés!');
        }
    } catch (error) {
        hideLoading();
        showNotification('❌ Erreur chargement: ' + error.message, 'error');
    }
}

async function loadCTSeries(seriesId) {
    console.log('📊 Loading CT series:', seriesId);
    state.currentSeries = seriesId;
    
    const seriesInfo = await fetch(`/api/series/${seriesId}`).then(r => r.json());
    const instances = seriesInfo.Instances || [];
    
    if (instances.length > 0) {
        const imageIds = instances.map(id => 
            `wadouri:/api/orthanc/instances/${id}/file`
        );
        
        loadImagesInViewer(imageIds);
    }
}

async function loadRTStruct(seriesId) {
    console.log('🎯 Loading RT-STRUCT:', seriesId);
    
    try {
        // Get RT-STRUCT instance
        const seriesInfo = await fetch(`/api/series/${seriesId}`).then(r => r.json());
        const instanceId = seriesInfo.Instances[0];
        
        // Call RT-Utils service to extract ROIs
        const response = await fetch('/api/rt/extract-rois', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rtstruct_uid: instanceId })
        });
        
        const data = await response.json();
        
        if (data.rois) {
            state.rois = data.rois;
            displayROIList(data.rois);
        }
    } catch (error) {
        console.error('Error loading RT-STRUCT:', error);
    }
}

function displayROIList(rois) {
    const roiListContainer = document.getElementById('roiListContainer');
    const roiList = document.getElementById('roiList');
    
    roiListContainer.querySelector('.empty-state')?.classList.add('hidden');
    roiList.classList.remove('hidden');
    roiList.innerHTML = '';
    
    rois.forEach((roi, index) => {
        const li = document.createElement('li');
        li.className = 'roi-item';
        
        const color = generateColor(index);
        
        li.innerHTML = `
            <div class="roi-color" style="background: ${color};"></div>
            <div class="roi-info">
                <div class="roi-name">${roi.name}</div>
                <div class="roi-volume">${roi.volume ? roi.volume.toFixed(2) + ' cm³' : 'N/A'}</div>
            </div>
            <div class="roi-actions">
                <button class="roi-btn" onclick="editROI(${index})">✏️</button>
                <button class="roi-btn" onclick="toggleROI(${index})">👁️</button>
            </div>
        `;
        
        roiList.appendChild(li);
    });
}

// ============================================================================
// Cornerstone Viewer
// ============================================================================

function initializeCornerstone() {
    cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
    cornerstoneWADOImageLoader.external.dicomParser = dicomParser;
    
    cornerstoneWADOImageLoader.configure({
        useWebWorkers: true,
    });
}

function loadImagesInViewer(imageIds) {
    const element = document.getElementById('dicomViewer');
    cornerstone.enable(element);
    
    if (imageIds.length > 0) {
        cornerstone.loadAndCacheImage(imageIds[0]).then(image => {
            cornerstone.displayImage(element, image);
            
            // Setup slice navigation
            if (imageIds.length > 1) {
                setupSliceNavigation(element, imageIds);
            }
        });
    }
    
    state.viewer = { element, imageIds };
}

function setupSliceNavigation(element, imageIds) {
    const sliceNav = document.getElementById('sliceNav');
    const sliceSlider = document.getElementById('sliceSlider');
    const currentSliceSpan = document.getElementById('currentSlice');
    const totalSlicesSpan = document.getElementById('totalSlices');
    
    sliceNav.classList.remove('hidden');
    sliceSlider.max = imageIds.length;
    totalSlicesSpan.textContent = imageIds.length;
    
    sliceSlider.addEventListener('input', (e) => {
        const sliceIndex = parseInt(e.target.value) - 1;
        currentSliceSpan.textContent = e.target.value;
        
        cornerstone.loadAndCacheImage(imageIds[sliceIndex]).then(image => {
            cornerstone.displayImage(element, image);
        });
    });
}

// ============================================================================
// Viewer Tabs & Tools
// ============================================================================

function setupViewerTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const view = tab.dataset.view;
            switchView(view);
        });
    });
}

function switchView(view) {
    const dicomViewer = document.getElementById('dicomViewer');
    const viewer3d = document.getElementById('viewer3d');
    
    if (view === '2d' || view === 'mpr') {
        dicomViewer.style.display = 'block';
        viewer3d.style.display = 'none';
    } else if (view === '3d') {
        dicomViewer.style.display = 'none';
        viewer3d.style.display = 'block';
        if (!state.scene3d) initialize3DViewer();
    }
}

function setupTools() {
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const tool = btn.dataset.tool;
            activateTool(tool);
        });
    });
}

function activateTool(tool) {
    state.currentTool = tool;
    console.log('🔧 Tool activated:', tool);
    // Implementation depends on Cornerstone tools
}

function initialize3DViewer() {
    const container = document.getElementById('viewer3d');
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);
    
    camera.position.z = 5;
    
    // Add lights
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(1, 1, 1);
    scene.add(light);
    
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);
    
    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();
    
    state.scene3d = { scene, camera, renderer };
}

// ============================================================================
// Workflow Processing
// ============================================================================

function setupActionButtons() {
    document.getElementById('btnProcess').addEventListener('click', processWorkflow);
    document.getElementById('btnExport').addEventListener('click', exportDICOMSEG);
    document.getElementById('btnReset').addEventListener('click', resetApplication);
}

async function processWorkflow() {
    console.log('⚙️ Starting workflow...');
    
    showLoading('Traitement en cours...');
    
    try {
        // Step 1: Already done (import)
        updateWorkflowStep(0, 'completed');
        
        // Step 2: Voxelization
        updateWorkflowStep(1, 'active');
        updateProgress(20);
        await voxelizeRTStruct();
        updateWorkflowStep(1, 'completed');
        
        // Step 3: Skip editing (optional)
        updateWorkflowStep(2, 'completed');
        updateProgress(50);
        
        // Step 4: Post-processing
        updateWorkflowStep(3, 'active');
        await postProcessing();
        updateWorkflowStep(3, 'completed');
        updateProgress(80);
        
        // Step 5: Generate DICOM-SEG
        updateWorkflowStep(4, 'active');
        await generateDICOMSEG();
        updateWorkflowStep(4, 'completed');
        updateProgress(100);
        
        hideLoading();
        document.getElementById('btnExport').disabled = false;
        showNotification('✅ Workflow terminé avec succès!');
    } catch (error) {
        hideLoading();
        showNotification('❌ Erreur workflow: ' + error.message, 'error');
    }
}

async function voxelizeRTStruct() {
    console.log('🔄 Voxelization...');
    await sleep(2000); // Simulation
}

async function postProcessing() {
    console.log('🔧 Post-processing...');
    await sleep(2000); // Simulation
}

async function generateDICOMSEG() {
    console.log('💾 Generating DICOM-SEG...');
    await sleep(2000); // Simulation
}

async function exportDICOMSEG() {
    showNotification('📥 Export DICOM-SEG...');
    // Implementation: download from Orthanc
}

function resetApplication() {
    if (confirm('Réinitialiser l\'application?')) {
        location.reload();
    }
}

// ============================================================================
// Workflow Status Management
// ============================================================================

function updateWorkflowStep(stepIndex, status) {
    const steps = document.querySelectorAll('.workflow-step');
    const step = steps[stepIndex];
    
    step.classList.remove('pending', 'active', 'completed');
    step.classList.add(status);
    
    state.workflowSteps[stepIndex] = status;
}

// ============================================================================
// UI Helpers
// ============================================================================

function showLoading(text = 'Chargement...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    
    loadingText.textContent = text;
    overlay.classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

function updateProgress(percent) {
    document.getElementById('progressFill').style.width = percent + '%';
}

function showNotification(message, type = 'success') {
    alert(message); // Simple for now, can be replaced with better notification system
}

// ============================================================================
// Utility Functions
// ============================================================================

function formatDate(dateStr) {
    if (!dateStr || dateStr === 'N/A') return 'N/A';
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${day}/${month}/${year}`;
}

function generateColor(index) {
    const colors = [
        '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24',
        '#6c5ce7', '#00b894', '#fdcb6e', '#e17055',
        '#74b9ff', '#a29bfe', '#fd79a8', '#fab1a0'
    ];
    return colors[index % colors.length];
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ROI Actions (global for inline onclick)
window.editROI = function(index) {
    console.log('✏️ Edit ROI:', index);
    showNotification('Fonction d\'édition en développement');
};

window.toggleROI = function(index) {
    console.log('👁️ Toggle ROI:', index);
    showNotification('Visibilité ROI basculée');
};

console.log('📦 RT-STRUCT Editor Pro loaded');
