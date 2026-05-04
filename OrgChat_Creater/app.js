/**
 * OrgChart Creator Pro - Enhanced Edition
 * Multi-chart management with drag-drop support
 */

class OrgChartApp {
    constructor() {
        // Multi-chart state
        this.charts = {}; // All saved charts
        this.currentChartId = null;
        this.currentChart = null;
        
        // Current chart state
        this.nodes = [];
        this.connections = [];
        this.selectedNode = null;
        this.selectedNodes = []; // Multi-select support
        this.contextNodeId = null;
        
        // UI State
        this.zoom = 1;
        this.history = [];
        this.historyIndex = -1;
        this.defaultColor = '#4F46E5';
        this.lineColor = '#6366F1'; // Default line color
        this.isDragging = false;
        this.dragNode = null;
        this.dragOffset = { x: 0, y: 0 };
        this.isPanning = false;
        this.hasUnsavedChanges = false;
        
        // Selection box state
        this.isSelecting = false;
        this.selectionStart = { x: 0, y: 0 };
        
        // Clipboard for copy/paste
        this.clipboard = null;
        
        // New feature states
        this.isDarkMode = localStorage.getItem('orgchart_darkmode') === 'true';
        this.gridSnapEnabled = false;
        this.gridSize = 40;
        this.minimapVisible = true;
        this.collapsedNodes = new Set();
        this.focusedNodeIndex = -1;
        this.csvData = null;
        
        // Constants
        this.NODE_WIDTH = 220;
        this.NODE_HEIGHT = 100;
        this.NODE_GAP_H = 60;
        this.NODE_GAP_V = 80;
        
        // Initialize
        this.init();
    }
    
    init() {
        this.cacheElements();
        this.bindEvents();
        this.loadChartsFromStorage();
        this.setupDragDropZones();
    }
    
    cacheElements() {
        this.elements = {
            // Modals
            welcomeModal: document.getElementById('welcomeModal'),
            personModal: document.getElementById('personModal'),
            newChartModal: document.getElementById('newChartModal'),
            
            // Sidebar
            sidebar: document.getElementById('sidebar'),
            savedChartsList: document.getElementById('savedChartsList'),
            chartCount: document.getElementById('chartCount'),
            
            // Forms
            companyForm: document.getElementById('companyForm'),
            personForm: document.getElementById('personForm'),
            newChartForm: document.getElementById('newChartForm'),
            
            // Inputs
            companyName: document.getElementById('companyName'),
            companyLogo: document.getElementById('companyLogo'),
            logoPreview: document.getElementById('logoPreview'),
            personPhoto: document.getElementById('personPhoto'),
            photoPreview: document.getElementById('photoPreview'),
            photoDropZone: document.getElementById('photoDropZone'),
            
            // Header
            headerLogo: document.getElementById('headerLogo'),
            headerCompanyName: document.getElementById('headerCompanyName'),
            chartStatus: document.getElementById('chartStatus'),
            
            // App
            app: document.getElementById('app'),
            canvas: document.getElementById('canvas'),
            canvasContainer: document.getElementById('canvasContainer'),
            orgChart: document.getElementById('orgChart'),
            connectionsSvg: document.getElementById('connectionsSvg'),
            emptyState: document.getElementById('emptyState'),
            nodeCount: document.getElementById('nodeCount'),
            
            // Context Menus
            contextMenu: document.getElementById('contextMenu'),
            chartContextMenu: document.getElementById('chartContextMenu'),
            
            // Export dropdown
            exportDropdown: document.getElementById('exportDropdown'),
            
            // Drag overlay
            dragOverlay: document.getElementById('dragOverlay'),
            
            // Buttons
            toggleSidebar: document.getElementById('toggleSidebar'),
            mobileMenuBtn: document.getElementById('mobileMenuBtn'),
            newChartBtn: document.getElementById('newChartBtn'),
            addRootBtn: document.getElementById('addRootBtn'),
            emptyAddBtn: document.getElementById('emptyAddBtn'),
            centerViewBtn: document.getElementById('centerViewBtn'),
            clearAllBtn: document.getElementById('clearAllBtn'),
            saveChartBtn: document.getElementById('saveChartBtn'),
            exportBtn: document.getElementById('exportBtn'),
            
            // Zoom
            zoomInBtn: document.getElementById('zoomInBtn'),
            zoomOutBtn: document.getElementById('zoomOutBtn'),
            fitScreenBtn: document.getElementById('fitScreenBtn'),
            zoomLevel: document.getElementById('zoomLevel'),
            
            // Undo/Redo
            undoBtn: document.getElementById('undoBtn'),
            redoBtn: document.getElementById('redoBtn'),
            
            // Color
            defaultColor: document.getElementById('defaultColor'),
            lineColor: document.getElementById('lineColor'),
            
            // Selection
            selectionBox: document.getElementById('selectionBox'),
            selectAllBtn: document.getElementById('selectAllBtn'),
            selectedCount: document.getElementById('selectedCount'),
            
            // Toast
            toastContainer: document.getElementById('toastContainer'),
            
            // New feature elements
            gridSnapBtn: document.getElementById('gridSnapBtn'),
            gridOverlay: document.getElementById('gridOverlay'),
            fitAllBtn: document.getElementById('fitAllBtn'),
            minimap: document.getElementById('minimap'),
            minimapContent: document.getElementById('minimapContent'),
            minimapViewport: document.getElementById('minimapViewport'),
            minimapToggle: document.getElementById('minimapToggle'),
            importCSVBtn: document.getElementById('importCSVBtn'),
            csvImportModal: document.getElementById('csvImportModal'),
            csvFileInput: document.getElementById('csvFileInput'),
            csvPreview: document.getElementById('csvPreview'),
            csvPreviewTable: document.getElementById('csvPreviewTable'),
            importCSVDataBtn: document.getElementById('importCSVDataBtn'),
            shortcutsModal: document.getElementById('shortcutsModal'),
            showSidebarBtn: document.getElementById('showSidebarBtn'),
            downloadSampleCSV: document.getElementById('downloadSampleCSV')
        };
    }
    
    bindEvents() {
        // Welcome form
        this.elements.companyForm.addEventListener('submit', (e) => this.handleCompanySubmit(e));
        this.elements.companyLogo.addEventListener('change', (e) => this.handleLogoUpload(e, 'logoPreview'));
        
        // Load saved charts button
        const loadSavedChartsBtn = document.getElementById('loadSavedChartsBtn');
        if (loadSavedChartsBtn) {
            loadSavedChartsBtn.addEventListener('click', () => this.openSavedChartsFromWelcome());
        }
        
        // New chart form
        this.elements.newChartForm.addEventListener('submit', (e) => this.handleNewChartSubmit(e));
        document.getElementById('newChartLogo').addEventListener('change', (e) => this.handleLogoUpload(e, 'newLogoPreview'));
        document.getElementById('closeNewChartModal').addEventListener('click', () => this.closeNewChartModal());
        document.getElementById('cancelNewChartBtn').addEventListener('click', () => this.closeNewChartModal());
        
        // Person Modal
        this.elements.personForm.addEventListener('submit', (e) => this.handlePersonSubmit(e));
        document.getElementById('closePersonModal').addEventListener('click', () => this.closePersonModal());
        document.getElementById('cancelPersonBtn').addEventListener('click', () => this.closePersonModal());
        document.getElementById('uploadPhotoBtn').addEventListener('click', () => this.elements.personPhoto.click());
        document.getElementById('removePhotoBtn').addEventListener('click', () => this.removePhoto());
        this.elements.personPhoto.addEventListener('change', (e) => this.handlePhotoUpload(e));
        
        // Color options
        document.querySelectorAll('.color-option').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectColor(e.target));
        });
        
        // Sidebar
        this.elements.toggleSidebar.addEventListener('click', () => this.toggleSidebar());
        this.elements.mobileMenuBtn.addEventListener('click', () => this.toggleSidebar());
        this.elements.newChartBtn.addEventListener('click', () => this.openNewChartModal());
        
        // Toolbar - Add Root Button (now in dropdown)
        if (this.elements.addRootBtn) {
            this.elements.addRootBtn.addEventListener('click', () => {
                document.getElementById('addPersonDropdown')?.classList.remove('show');
                this.openAddModal();
            });
        }
        this.elements.emptyAddBtn.addEventListener('click', () => this.openAddModal());
        this.elements.centerViewBtn.addEventListener('click', () => this.centerView());
        this.elements.clearAllBtn.addEventListener('click', () => this.clearAll());
        this.elements.saveChartBtn.addEventListener('click', () => this.saveCurrentChart());
        
        // Export dropdown
        this.elements.exportBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.elements.exportDropdown.classList.toggle('show');
        });
        document.getElementById('exportJSON').addEventListener('click', () => this.exportJSON());
        
        // Zoom
        this.elements.zoomInBtn.addEventListener('click', () => this.zoomIn());
        this.elements.zoomOutBtn.addEventListener('click', () => this.zoomOut());
        this.elements.fitScreenBtn.addEventListener('click', () => this.fitToScreen());
        
        // Toolbar zoom controls
        document.getElementById('toolbarZoomIn').addEventListener('click', () => this.zoomIn());
        document.getElementById('toolbarZoomOut').addEventListener('click', () => this.zoomOut());
        document.getElementById('toolbarFitScreen').addEventListener('click', () => this.fitToScreen());
        
        // Undo/Redo
        this.elements.undoBtn.addEventListener('click', () => this.undo());
        this.elements.redoBtn.addEventListener('click', () => this.redo());
        
        // Default Color
        this.elements.defaultColor.addEventListener('change', (e) => {
            this.defaultColor = e.target.value;
        });
        
        // Line Color
        if (this.elements.lineColor) {
            this.elements.lineColor.addEventListener('change', (e) => {
                this.lineColor = e.target.value;
                this.renderConnections();
            });
        }
        
        // Select All
        if (this.elements.selectAllBtn) {
            this.elements.selectAllBtn.addEventListener('click', () => this.selectAll());
        }
        
        // Context Menus
        document.getElementById('ctxAddLeft').addEventListener('click', () => this.addInDirection('left'));
        document.getElementById('ctxAddRight').addEventListener('click', () => this.addInDirection('right'));
        document.getElementById('ctxAddTop').addEventListener('click', () => this.addInDirection('top'));
        document.getElementById('ctxAddBottom').addEventListener('click', () => this.addInDirection('bottom'));
        document.getElementById('ctxLinkTo').addEventListener('click', () => this.startLinkingMode());
        document.getElementById('ctxEdit').addEventListener('click', () => this.editNode());
        document.getElementById('ctxDuplicate').addEventListener('click', () => this.duplicateNode());
        document.getElementById('ctxChangePhoto').addEventListener('click', () => this.changeNodePhoto());
        document.getElementById('ctxDelete').addEventListener('click', () => this.deleteNode());
        
        // Chart context menu
        document.getElementById('ctxChartOpen').addEventListener('click', () => this.openChartFromContext());
        document.getElementById('ctxChartRename').addEventListener('click', () => this.renameChartFromContext());
        document.getElementById('ctxChartDuplicate').addEventListener('click', () => this.duplicateChartFromContext());
        document.getElementById('ctxChartExport').addEventListener('click', () => this.exportChartFromContext());
        document.getElementById('ctxChartDelete').addEventListener('click', () => this.deleteChartFromContext());
        
        // Close menus on outside click
        document.addEventListener('click', (e) => {
            if (!this.elements.contextMenu.contains(e.target)) {
                this.hideContextMenu();
            }
            if (!this.elements.chartContextMenu.contains(e.target)) {
                this.hideChartContextMenu();
            }
            if (!this.elements.exportBtn.contains(e.target)) {
                this.elements.exportDropdown.classList.remove('show');
            }
            // Close Add Person dropdown
            const addPersonDropdownBtn = document.getElementById('addPersonDropdownBtn');
            const addPersonDropdown = document.getElementById('addPersonDropdown');
            if (addPersonDropdownBtn && addPersonDropdown && !addPersonDropdownBtn.contains(e.target) && !addPersonDropdown.contains(e.target)) {
                addPersonDropdown.classList.remove('show');
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // New feature event listeners
        this.bindNewFeatureEvents();
        
        // Canvas events
        this.setupCanvasEvents();
        
        // Double-click to add
        this.elements.canvasContainer.addEventListener('dblclick', (e) => {
            if (e.target === this.elements.canvas || e.target === this.elements.orgChart) {
                this.openAddModalAtPosition(e);
            }
        });
        
        // Global drag-drop for images
        this.setupGlobalDragDrop();
    }
    
    // ===== Drag & Drop Setup =====
    setupDragDropZones() {
        // Logo drop zone in welcome modal
        const logoDropZone = document.getElementById('logoDropZone');
        this.setupDropZone(logoDropZone, (file) => {
            this.loadImageFile(file, (dataUrl) => {
                this.elements.logoPreview.innerHTML = `<img src="${dataUrl}" alt="Logo">`;
            });
        });
        
        // New chart logo drop zone
        const newLogoDropZone = document.getElementById('newLogoDropZone');
        this.setupDropZone(newLogoDropZone, (file) => {
            this.loadImageFile(file, (dataUrl) => {
                document.getElementById('newLogoPreview').innerHTML = `<img src="${dataUrl}" alt="Logo">`;
            });
        });
        
        // Photo drop zone in person modal
        this.setupDropZone(this.elements.photoDropZone, (file) => {
            this.loadImageFile(file, (dataUrl) => {
                this.elements.photoPreview.innerHTML = `<img src="${dataUrl}" alt="Photo">`;
                document.getElementById('removePhotoBtn').style.display = '';
            });
        });
    }
    
    setupDropZone(element, onDrop) {
        if (!element) return;
        
        element.addEventListener('dragover', (e) => {
            e.preventDefault();
            element.classList.add('drag-over');
        });
        
        element.addEventListener('dragleave', () => {
            element.classList.remove('drag-over');
        });
        
        element.addEventListener('drop', (e) => {
            e.preventDefault();
            element.classList.remove('drag-over');
            
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                onDrop(file);
            }
        });
    }
    
    setupGlobalDragDrop() {
        let dragCounter = 0;
        
        document.addEventListener('dragenter', (e) => {
            if (e.dataTransfer.types.includes('Files')) {
                dragCounter++;
                if (this.selectedNode) {
                    this.elements.dragOverlay.classList.remove('hidden');
                }
            }
        });
        
        document.addEventListener('dragleave', () => {
            dragCounter--;
            if (dragCounter === 0) {
                this.elements.dragOverlay.classList.add('hidden');
            }
        });
        
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        document.addEventListener('drop', (e) => {
            e.preventDefault();
            dragCounter = 0;
            this.elements.dragOverlay.classList.add('hidden');
            
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/') && this.selectedNode) {
                this.loadImageFile(file, (dataUrl) => {
                    this.updateNodePhoto(this.selectedNode, dataUrl);
                });
            }
        });
    }
    
    loadImageFile(file, callback) {
        const reader = new FileReader();
        reader.onload = (e) => callback(e.target.result);
        reader.readAsDataURL(file);
    }
    
    // ===== Canvas Events =====
    setupCanvasEvents() {
        const container = this.elements.canvasContainer;
        
        container.addEventListener('wheel', (e) => {
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.1 : 0.1;
                this.setZoom(this.zoom + delta);
            }
        });
        
        container.addEventListener('mousedown', (e) => {
            // Middle click or left click on empty canvas = pan
            if (e.button === 1) {
                this.isPanning = true;
                container.style.cursor = 'grabbing';
                this.panStart = { x: e.clientX, y: e.clientY };
                this.scrollStart = { x: container.scrollLeft, y: container.scrollTop };
                e.preventDefault();
            }
            // Left click on canvas = start selection box
            else if (e.button === 0 && (e.target === this.elements.canvas || e.target === this.elements.orgChart)) {
                const rect = this.elements.canvas.getBoundingClientRect();
                this.isSelecting = true;
                this.selectionStart = {
                    x: (e.clientX - rect.left + container.scrollLeft) / this.zoom,
                    y: (e.clientY - rect.top + container.scrollTop) / this.zoom
                };
                
                // Clear selection if not holding Shift
                if (!e.shiftKey) {
                    this.clearSelection();
                }
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (this.isPanning) {
                const dx = e.clientX - this.panStart.x;
                const dy = e.clientY - this.panStart.y;
                container.scrollLeft = this.scrollStart.x - dx;
                container.scrollTop = this.scrollStart.y - dy;
            }
            
            if (this.isDragging && this.dragNode) {
                this.handleNodeDrag(e);
            }
            
            // Selection box drawing
            if (this.isSelecting) {
                this.updateSelectionBox(e);
            }
        });
        
        document.addEventListener('mouseup', (e) => {
            if (this.isPanning) {
                this.isPanning = false;
                container.style.cursor = '';
            }
            
            if (this.isDragging) {
                this.endNodeDrag();
            }
            
            // End selection box
            if (this.isSelecting) {
                this.finishSelection();
            }
        });
    }
    
    // ===== Selection Box Methods =====
    updateSelectionBox(e) {
        const container = this.elements.canvasContainer;
        const rect = this.elements.canvas.getBoundingClientRect();
        const currentX = (e.clientX - rect.left + container.scrollLeft) / this.zoom;
        const currentY = (e.clientY - rect.top + container.scrollTop) / this.zoom;
        
        const box = this.elements.selectionBox;
        const left = Math.min(this.selectionStart.x, currentX);
        const top = Math.min(this.selectionStart.y, currentY);
        const width = Math.abs(currentX - this.selectionStart.x);
        const height = Math.abs(currentY - this.selectionStart.y);
        
        box.style.left = left + 'px';
        box.style.top = top + 'px';
        box.style.width = width + 'px';
        box.style.height = height + 'px';
        box.classList.remove('hidden');
    }
    
    finishSelection() {
        const box = this.elements.selectionBox;
        const boxRect = {
            left: parseFloat(box.style.left) || 0,
            top: parseFloat(box.style.top) || 0,
            width: parseFloat(box.style.width) || 0,
            height: parseFloat(box.style.height) || 0
        };
        
        // Only select if box is big enough (not just a click)
        if (boxRect.width > 10 && boxRect.height > 10) {
            this.nodes.forEach(node => {
                const nodeRight = node.x + this.NODE_WIDTH;
                const nodeBottom = node.y + this.NODE_HEIGHT;
                
                // Check if node intersects with selection box
                if (node.x < boxRect.left + boxRect.width &&
                    nodeRight > boxRect.left &&
                    node.y < boxRect.top + boxRect.height &&
                    nodeBottom > boxRect.top) {
                    if (!this.selectedNodes.includes(node.id)) {
                        this.selectedNodes.push(node.id);
                    }
                }
            });
            this.render();
            this.updateSelectedCount();
        }
        
        box.classList.add('hidden');
        box.style.width = '0';
        box.style.height = '0';
        this.isSelecting = false;
    }
    
    clearSelection() {
        this.selectedNodes = [];
        this.selectedNode = null;
        this.updateSelectedCount();
    }
    
    selectAll() {
        this.selectedNodes = this.nodes.map(n => n.id);
        this.render();
        this.updateSelectedCount();
        this.showToast(`Selected ${this.selectedNodes.length} members`, 'info');
    }
    
    updateSelectedCount() {
        if (this.elements.selectedCount) {
            if (this.selectedNodes.length > 0) {
                this.elements.selectedCount.textContent = `| ${this.selectedNodes.length} selected`;
                this.elements.selectedCount.classList.remove('hidden');
            } else {
                this.elements.selectedCount.classList.add('hidden');
            }
        }
    }

    
    // ===== Company/Chart Setup =====
    handleCompanySubmit(e) {
        e.preventDefault();
        const name = this.elements.companyName.value.trim();
        const logoImg = this.elements.logoPreview.querySelector('img');
        
        this.createNewChart(name, logoImg ? logoImg.src : null);
        this.elements.welcomeModal.classList.remove('active');
        this.elements.app.classList.remove('hidden');
    }
    
    createNewChart(name, logo = null) {
        const chartId = 'chart_' + Date.now();
        const chart = {
            id: chartId,
            name: name,
            logo: logo,
            nodes: [],
            connections: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        
        this.charts[chartId] = chart;
        this.loadChart(chartId);
        this.saveChartsToStorage();
        this.renderSavedChartsList();
        this.showToast(`Created "${name}"`, 'success');
        
        return chartId;
    }
    
    loadChart(chartId) {
        if (this.hasUnsavedChanges && this.currentChartId) {
            this.saveCurrentChartData();
        }
        
        const chart = this.charts[chartId];
        if (!chart) return;
        
        this.currentChartId = chartId;
        this.currentChart = chart;
        this.nodes = JSON.parse(JSON.stringify(chart.nodes || []));
        this.connections = JSON.parse(JSON.stringify(chart.connections || []));
        
        // Update header
        this.elements.headerCompanyName.textContent = chart.name;
        if (chart.logo) {
            this.elements.headerLogo.src = chart.logo;
            this.elements.headerLogo.classList.remove('hidden');
        } else {
            this.elements.headerLogo.classList.add('hidden');
        }
        
        this.history = [];
        this.historyIndex = -1;
        this.hasUnsavedChanges = false;
        this.updateSaveStatus();
        
        this.render();
        this.updateEmptyState();
        this.renderSavedChartsList();
        this.addToHistory();
    }
    
    saveCurrentChart() {
        this.saveCurrentChartData();
        this.saveChartsToStorage();
        this.hasUnsavedChanges = false;
        this.updateSaveStatus();
    }
    
    // Auto-save with debounce
    autoSave() {
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
        }
        this.autoSaveTimeout = setTimeout(() => {
            this.saveCurrentChartData();
            this.saveChartsToStorage();
            this.hasUnsavedChanges = false;
            this.updateSaveStatus();
        }, 500);
    }
    
    saveCurrentChartData() {
        if (!this.currentChartId) return;
        
        this.charts[this.currentChartId] = {
            ...this.charts[this.currentChartId],
            nodes: JSON.parse(JSON.stringify(this.nodes)),
            connections: JSON.parse(JSON.stringify(this.connections)),
            updatedAt: new Date().toISOString()
        };
    }
    
    updateSaveStatus() {
        const status = this.elements.chartStatus;
        if (this.hasUnsavedChanges) {
            status.innerHTML = '<i class="fas fa-circle"></i> Saving...';
            status.classList.add('unsaved');
        } else {
            status.innerHTML = '<i class="fas fa-check-circle"></i> Saved';
            status.classList.remove('unsaved');
        }
    }
    
    markUnsaved() {
        this.hasUnsavedChanges = true;
        this.updateSaveStatus();
        this.autoSave(); // Auto-save after changes
    }
    
    // ===== New Chart Modal =====
    openNewChartModal() {
        document.getElementById('newChartName').value = '';
        document.getElementById('newLogoPreview').innerHTML = `
            <i class="fas fa-cloud-upload-alt"></i>
            <span>Click or drag to upload</span>
        `;
        this.elements.newChartModal.classList.add('active');
    }
    
    closeNewChartModal() {
        this.elements.newChartModal.classList.remove('active');
    }
    
    handleNewChartSubmit(e) {
        e.preventDefault();
        const name = document.getElementById('newChartName').value.trim();
        const logoImg = document.getElementById('newLogoPreview').querySelector('img');
        
        this.createNewChart(name, logoImg ? logoImg.src : null);
        this.closeNewChartModal();
    }
    
    // ===== Saved Charts List =====
    renderSavedChartsList() {
        const chartIds = Object.keys(this.charts);
        this.elements.chartCount.textContent = chartIds.length;
        
        if (chartIds.length === 0) {
            this.elements.savedChartsList.innerHTML = `
                <div class="empty-charts-msg">
                    <i class="fas fa-folder-open"></i>
                    <p>No saved charts yet</p>
                </div>
            `;
            return;
        }
        
        // Sort by updated date
        const sortedCharts = chartIds
            .map(id => this.charts[id])
            .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
        
        this.elements.savedChartsList.innerHTML = sortedCharts.map(chart => `
            <div class="chart-item ${chart.id === this.currentChartId ? 'active' : ''}" 
                 data-id="${chart.id}">
                <div class="chart-item-logo">
                    ${chart.logo 
                        ? `<img src="${chart.logo}" alt="${chart.name}">` 
                        : '<i class="fas fa-building"></i>'
                    }
                </div>
                <div class="chart-item-info">
                    <div class="chart-item-name">${this.escapeHtml(chart.name)}</div>
                    <div class="chart-item-meta">${chart.nodes?.length || 0} members</div>
                </div>
                <div class="chart-item-actions">
                    <button class="btn btn-icon btn-sm chart-menu-btn" data-id="${chart.id}">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        // Bind events
        this.elements.savedChartsList.querySelectorAll('.chart-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.chart-menu-btn')) {
                    this.loadChart(item.dataset.id);
                }
            });
        });
        
        this.elements.savedChartsList.querySelectorAll('.chart-menu-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.contextChartId = btn.dataset.id;
                this.showChartContextMenu(e.pageX, e.pageY);
            });
        });
    }
    
    // ===== Chart Context Menu =====
    showChartContextMenu(x, y) {
        const menu = this.elements.chartContextMenu;
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;
        menu.classList.remove('hidden');
    }
    
    hideChartContextMenu() {
        this.elements.chartContextMenu.classList.add('hidden');
    }
    
    openChartFromContext() {
        this.hideChartContextMenu();
        if (this.contextChartId) {
            this.loadChart(this.contextChartId);
        }
    }
    
    renameChartFromContext() {
        this.hideChartContextMenu();
        if (this.contextChartId) {
            const chart = this.charts[this.contextChartId];
            const newName = prompt('Enter new name:', chart.name);
            if (newName && newName.trim()) {
                chart.name = newName.trim();
                if (this.contextChartId === this.currentChartId) {
                    this.elements.headerCompanyName.textContent = newName.trim();
                }
                this.saveChartsToStorage();
                this.renderSavedChartsList();
                this.showToast('Chart renamed!', 'success');
            }
        }
    }
    
    duplicateChartFromContext() {
        this.hideChartContextMenu();
        if (this.contextChartId) {
            const chart = this.charts[this.contextChartId];
            const newId = this.createNewChart(chart.name + ' (Copy)', chart.logo);
            this.charts[newId].nodes = JSON.parse(JSON.stringify(chart.nodes || []));
            this.charts[newId].connections = JSON.parse(JSON.stringify(chart.connections || []));
            this.saveChartsToStorage();
            this.loadChart(newId);
        }
    }
    
    exportChartFromContext() {
        this.hideChartContextMenu();
        if (this.contextChartId) {
            const chart = this.charts[this.contextChartId];
            this.downloadJSON(chart, `${chart.name}_OrgChart.json`);
        }
    }
    
    deleteChartFromContext() {
        this.hideChartContextMenu();
        if (this.contextChartId) {
            const chart = this.charts[this.contextChartId];
            if (confirm(`Delete "${chart.name}"? This cannot be undone.`)) {
                delete this.charts[this.contextChartId];
                
                if (this.contextChartId === this.currentChartId) {
                    const remaining = Object.keys(this.charts);
                    if (remaining.length > 0) {
                        this.loadChart(remaining[0]);
                    } else {
                        this.currentChartId = null;
                        this.nodes = [];
                        this.connections = [];
                        this.render();
                        this.updateEmptyState();
                    }
                }
                
                this.saveChartsToStorage();
                this.renderSavedChartsList();
                this.showToast('Chart deleted!', 'success');
            }
        }
    }
    
    // ===== Person Modal =====
    openAddModal(sourceNodeId = null, direction = null) {
        document.getElementById('personModalTitle').textContent = 'Add New Member';
        document.getElementById('personSubmitText').textContent = 'Add Member';
        document.getElementById('personId').value = '';
        document.getElementById('sourceNodeId').value = sourceNodeId || '';
        document.getElementById('connectionDirection').value = direction || '';
        this.elements.personForm.reset();
        this.elements.photoPreview.innerHTML = '<i class="fas fa-user"></i>';
        document.getElementById('removePhotoBtn').style.display = 'none';
        
        document.querySelectorAll('.color-option').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.color === this.defaultColor);
        });
        
        this.elements.personModal.classList.add('active');
    }
    
    openAddModalAtPosition(e) {
        const rect = this.elements.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left + this.elements.canvasContainer.scrollLeft) / this.zoom;
        const y = (e.clientY - rect.top + this.elements.canvasContainer.scrollTop) / this.zoom;
        
        this.pendingPosition = { x: x - this.NODE_WIDTH / 2, y: y - this.NODE_HEIGHT / 2 };
        this.openAddModal();
    }
    
    openEditModal(node) {
        document.getElementById('personModalTitle').textContent = 'Edit Member';
        document.getElementById('personSubmitText').textContent = 'Save Changes';
        document.getElementById('personId').value = node.id;
        document.getElementById('sourceNodeId').value = '';
        document.getElementById('connectionDirection').value = '';
        document.getElementById('personName').value = node.name;
        document.getElementById('personDesignation').value = node.designation;
        document.getElementById('personPhone').value = node.phone || '';
        document.getElementById('personEmail').value = node.email || '';
        document.getElementById('personDepartment').value = node.department || '';
        document.getElementById('personLocation').value = node.location || '';
        
        if (node.photo) {
            this.elements.photoPreview.innerHTML = `<img src="${node.photo}" alt="${node.name}">`;
            document.getElementById('removePhotoBtn').style.display = '';
        } else {
            this.elements.photoPreview.innerHTML = '<i class="fas fa-user"></i>';
            document.getElementById('removePhotoBtn').style.display = 'none';
        }
        
        document.querySelectorAll('.color-option').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.color === node.color);
        });
        
        this.elements.personModal.classList.add('active');
    }
    
    closePersonModal() {
        this.elements.personModal.classList.remove('active');
        this.pendingPosition = null;
    }
    
    handleLogoUpload(e, previewId) {
        const file = e.target.files[0];
        if (file) {
            this.loadImageFile(file, (dataUrl) => {
                document.getElementById(previewId).innerHTML = `<img src="${dataUrl}" alt="Logo">`;
            });
        }
    }
    
    handlePhotoUpload(e) {
        const file = e.target.files[0];
        if (file) {
            this.loadImageFile(file, (dataUrl) => {
                this.elements.photoPreview.innerHTML = `<img src="${dataUrl}" alt="Photo">`;
                document.getElementById('removePhotoBtn').style.display = '';
            });
        }
    }
    
    removePhoto() {
        this.elements.photoPreview.innerHTML = '<i class="fas fa-user"></i>';
        document.getElementById('removePhotoBtn').style.display = 'none';
        this.elements.personPhoto.value = '';
    }
    
    selectColor(btn) {
        document.querySelectorAll('.color-option').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    
    handlePersonSubmit(e) {
        e.preventDefault();
        
        const personId = document.getElementById('personId').value;
        const sourceNodeId = document.getElementById('sourceNodeId').value;
        const direction = document.getElementById('connectionDirection').value;
        const photoImg = this.elements.photoPreview.querySelector('img');
        const activeColor = document.querySelector('.color-option.active');
        
        const personData = {
            name: document.getElementById('personName').value.trim(),
            designation: document.getElementById('personDesignation').value.trim(),
            phone: document.getElementById('personPhone').value.trim(),
            email: document.getElementById('personEmail').value.trim(),
            department: document.getElementById('personDepartment').value.trim(),
            location: document.getElementById('personLocation').value.trim(),
            photo: photoImg ? photoImg.src : null,
            color: activeColor ? activeColor.dataset.color : this.defaultColor
        };
        
        if (personId) {
            this.updateNode(personId, personData);
            this.showToast('Member updated!', 'success');
        } else {
            let position;
            
            if (this.pendingPosition) {
                position = this.pendingPosition;
            } else if (sourceNodeId && direction) {
                position = this.calculateNewPosition(sourceNodeId, direction);
            } else {
                position = this.getDefaultPosition();
            }
            
            const newNode = this.addNode(personData, position);
            
            if (sourceNodeId && direction) {
                this.addConnection(sourceNodeId, newNode.id, direction);
            }
            
            this.showToast('Member added!', 'success');
        }
        
        this.closePersonModal();
        this.addToHistory();
        this.markUnsaved();
    }
    
    // ===== Node Operations =====
    generateId() {
        return 'node_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    addNode(data, position) {
        const node = {
            id: this.generateId(),
            x: position.x,
            y: position.y,
            ...data
        };
        
        this.nodes.push(node);
        this.render();
        this.updateEmptyState();
        this.updateNodeCount();
        
        return node;
    }
    
    updateNode(id, data) {
        const index = this.nodes.findIndex(n => n.id === id);
        if (index !== -1) {
            this.nodes[index] = { ...this.nodes[index], ...data };
            this.render();
        }
    }
    
    updateNodePhoto(nodeId, photoUrl) {
        const node = this.findNode(nodeId);
        if (node) {
            node.photo = photoUrl;
            this.render();
            this.addToHistory();
            this.markUnsaved();
            this.showToast('Photo updated!', 'success');
        }
    }
    
    deleteNodeById(id) {
        this.nodes = this.nodes.filter(n => n.id !== id);
        this.connections = this.connections.filter(c => c.from !== id && c.to !== id);
        this.render();
        this.updateEmptyState();
        this.updateNodeCount();
        this.addToHistory();
        this.markUnsaved();
    }
    
    findNode(id) {
        return this.nodes.find(n => n.id === id);
    }
    
    getDefaultPosition() {
        if (this.nodes.length === 0) {
            return { x: 400, y: 200 };
        }
        
        const avgX = this.nodes.reduce((sum, n) => sum + n.x, 0) / this.nodes.length;
        const avgY = this.nodes.reduce((sum, n) => sum + n.y, 0) / this.nodes.length;
        
        return {
            x: avgX + (Math.random() - 0.5) * 200,
            y: avgY + this.NODE_HEIGHT + this.NODE_GAP_V
        };
    }
    
    calculateNewPosition(sourceId, direction) {
        const source = this.findNode(sourceId);
        if (!source) return this.getDefaultPosition();
        
        let x = source.x;
        let y = source.y;
        
        switch (direction) {
            case 'left': x = source.x - this.NODE_WIDTH - this.NODE_GAP_H; break;
            case 'right': x = source.x + this.NODE_WIDTH + this.NODE_GAP_H; break;
            case 'top': y = source.y - this.NODE_HEIGHT - this.NODE_GAP_V; break;
            case 'bottom': y = source.y + this.NODE_HEIGHT + this.NODE_GAP_V; break;
        }
        
        return this.adjustForOverlap({ x, y });
    }
    
    adjustForOverlap(position) {
        let adjusted = { ...position };
        let attempts = 0;
        
        while (attempts < 10 && this.checkOverlap(adjusted)) {
            adjusted.x += (Math.random() - 0.5) * 100;
            adjusted.y += 50;
            attempts++;
        }
        
        return adjusted;
    }
    
    checkOverlap(position) {
        return this.nodes.some(node => {
            const dx = Math.abs(node.x - position.x);
            const dy = Math.abs(node.y - position.y);
            return dx < this.NODE_WIDTH + 20 && dy < this.NODE_HEIGHT + 20;
        });
    }
    
    // ===== Connections =====
    addConnection(fromId, toId, direction) {
        const exists = this.connections.some(c => 
            (c.from === fromId && c.to === toId) || 
            (c.from === toId && c.to === fromId)
        );
        
        if (!exists) {
            this.connections.push({
                id: 'conn_' + Date.now(),
                from: fromId,
                to: toId,
                direction: direction
            });
            this.renderConnections();
        }
    }
    
    renderConnections() {
        const svg = this.elements.connectionsSvg;
        const color = this.lineColor || '#6366F1';
        
        // Add arrow marker definitions with custom color
        let markersHtml = `
            <defs>
                <marker id="arrowhead-custom" markerWidth="12" markerHeight="10" refX="6" refY="5" orient="auto" markerUnits="userSpaceOnUse">
                    <polygon points="0 0, 12 5, 0 10" fill="${color}"/>
                </marker>
            </defs>
        `;
        
        let pathsHtml = '';
        this.connections.forEach(conn => {
            const fromNode = this.findNode(conn.from);
            const toNode = this.findNode(conn.to);
            
            if (fromNode && toNode) {
                pathsHtml += this.createConnectionPath(fromNode, toNode, conn.direction, color);
            }
        });
        
        svg.innerHTML = markersHtml + pathsHtml;
    }
    
    createConnectionPath(from, to, direction, color) {
        const strokeColor = color || this.lineColor || '#6366F1';
        let startX, startY, endX, endY;

        // Determine start and end points based on direction
        switch (direction) {
            case 'bottom':
                startX = from.x + this.NODE_WIDTH / 2;
                startY = from.y + this.NODE_HEIGHT;
                endX = to.x + this.NODE_WIDTH / 2;
                endY = to.y;
                break;
            case 'top':
                startX = from.x + this.NODE_WIDTH / 2;
                startY = from.y;
                endX = to.x + this.NODE_WIDTH / 2;
                endY = to.y + this.NODE_HEIGHT;
                break;
            case 'right':
                startX = from.x + this.NODE_WIDTH;
                startY = from.y + this.NODE_HEIGHT / 2;
                endX = to.x;
                endY = to.y + this.NODE_HEIGHT / 2;
                break;
            case 'left':
                startX = from.x;
                startY = from.y + this.NODE_HEIGHT / 2;
                endX = to.x + this.NODE_WIDTH;
                endY = to.y + this.NODE_HEIGHT / 2;
                break;
            default: // Fallback
                startX = from.x + this.NODE_WIDTH / 2;
                startY = from.y + this.NODE_HEIGHT / 2;
                endX = to.x + this.NODE_WIDTH / 2;
                endY = to.y + this.NODE_HEIGHT / 2;
                break;
        }

        // Use a straight line path for simplicity and accuracy
        const pathData = `M ${startX} ${startY} L ${endX} ${endY}`;

        return `<path d="${pathData}" class="connection-path" stroke="${strokeColor}" marker-end="url(#arrowhead-custom)" />`;
    }
    

    // ===== Rendering =====
    render() {
        this.elements.orgChart.innerHTML = '';
        this.nodes.forEach(node => {
            const nodeEl = this.renderNode(node);
            this.elements.orgChart.appendChild(nodeEl);
        });
        this.renderConnections();
        this.updateMinimap();
    }
    
    renderNode(node) {
        const wrapper = document.createElement('div');
        wrapper.className = 'node-wrapper new';
        wrapper.dataset.nodeId = node.id;
        wrapper.style.left = node.x + 'px';
        wrapper.style.top = node.y + 'px';
        
        const isSelected = this.selectedNode === node.id || this.selectedNodes.includes(node.id);
        const reportCount = this.getReportCount(node.id);

        wrapper.innerHTML = `
            <div class="org-node ${isSelected ? 'selected' : ''}" tabindex="0" style="border-color: ${node.color || this.defaultColor}">
                ${reportCount > 0 ? `<span class="node-report-count">${reportCount}</span>` : ''}
                <div class="org-node-header" style="background-color: ${node.color || this.defaultColor}"></div>
                <div class="org-node-content">
                    <div class="org-node-photo" style="background-color: ${node.color || this.defaultColor}20">
                        ${node.photo 
                            ? `<img src="${node.photo}" alt="${node.name}">` 
                            : `<i class="fas fa-user" style="color: ${node.color || this.defaultColor}"></i>`
                        }
                    </div>
                    <div class="org-node-info">
                        <h4 class="org-node-name">${this.escapeHtml(node.name)}</h4>
                        <p class="org-node-designation">${this.escapeHtml(node.designation)}</p>
                    </div>
                </div>
                <div class="org-node-actions">
                    <button class="node-action-btn add-left" title="Add Left"><i class="fas fa-arrow-left"></i></button>
                    <button class="node-action-btn add-top" title="Add Above"><i class="fas fa-arrow-up"></i></button>
                    <button class="node-action-btn add-bottom" title="Add Below"><i class="fas fa-arrow-down"></i></button>
                    <button class="node-action-btn add-right" title="Add Right"><i class="fas fa-arrow-right"></i></button>
                </div>
            </div>
        `;
        
        // Bind events
        const nodeEl = wrapper.querySelector('.org-node');
        
        nodeEl.addEventListener('click', (e) => {
            if (!e.target.closest('.node-action-btn')) {
                this.handleNodeClick(node.id, e);
            }
        });
        
        nodeEl.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.contextNodeId = node.id;
            this.showContextMenu(e.pageX, e.pageY);
        });
        
        // Add buttons
        wrapper.querySelector('.add-left').addEventListener('click', (e) => {
            e.stopPropagation();
            this.openAddModal(node.id, 'left');
        });
        wrapper.querySelector('.add-top').addEventListener('click', (e) => {
            e.stopPropagation();
            this.openAddModal(node.id, 'top');
        });
        wrapper.querySelector('.add-bottom').addEventListener('click', (e) => {
            e.stopPropagation();
            this.openAddModal(node.id, 'bottom');
        });
        wrapper.querySelector('.add-right').addEventListener('click', (e) => {
            e.stopPropagation();
            this.openAddModal(node.id, 'right');
        });
        
        // Drag handling
        wrapper.addEventListener('mousedown', (e) => {
            if (e.button === 0 && !e.target.closest('.node-action-btn')) {
                this.startNodeDrag(e, node);
            }
        });
        
        return wrapper;
    }
    
    handleNodeClick(nodeId, e) {
        if (e.shiftKey || e.ctrlKey || e.metaKey) {
            // Multi-select: toggle selection
            const index = this.selectedNodes.indexOf(nodeId);
            if (index > -1) {
                this.selectedNodes.splice(index, 1);
            } else {
                this.selectedNodes.push(nodeId);
            }
        } else {
            // Single select: clear others and select this one
            this.selectedNodes = [nodeId];
        }
        this.selectedNode = nodeId;
        this.render();
        this.updateSelectedCount();
    }
    
    selectNode(nodeId) {
        this.selectedNodes = [nodeId];
        this.selectedNode = nodeId;
        this.render();
        this.updateSelectedCount();
    }
    
    // ===== Node Dragging =====
    startNodeDrag(e, node) {
        this.isDragging = true;
        this.dragNode = node;
        
        // If dragging a selected node, prepare to move all selected nodes
        if (this.selectedNodes.includes(node.id)) {
            this.dragStartPositions = {};
            this.selectedNodes.forEach(id => {
                const n = this.findNode(id);
                if (n) {
                    this.dragStartPositions[id] = { x: n.x, y: n.y };
                }
            });
        } else {
            // If dragging unselected node, select only this one
            this.selectedNodes = [node.id];
            this.dragStartPositions = { [node.id]: { x: node.x, y: node.y } };
        }
        
        const wrapper = e.currentTarget;
        this.dragOffset = {
            x: e.clientX - wrapper.getBoundingClientRect().left,
            y: e.clientY - wrapper.getBoundingClientRect().top
        };
        this.dragStartMouse = { x: e.clientX, y: e.clientY };
        wrapper.style.zIndex = '1000';
    }
    
    handleNodeDrag(e) {
        if (!this.isDragging || !this.dragNode) return;
        
        const rect = this.elements.canvas.getBoundingClientRect();
        const scrollLeft = this.elements.canvasContainer.scrollLeft;
        const scrollTop = this.elements.canvasContainer.scrollTop;
        
        // Calculate delta from start position
        const deltaX = (e.clientX - this.dragStartMouse.x) / this.zoom;
        const deltaY = (e.clientY - this.dragStartMouse.y) / this.zoom;
        
        // Snap to grid if enabled
        const snapSize = this.gridSnapEnabled ? this.gridSize : 1;
        const snappedDeltaX = Math.round(deltaX / snapSize) * snapSize;
        const snappedDeltaY = Math.round(deltaY / snapSize) * snapSize;
        
        // Move all selected nodes
        this.selectedNodes.forEach(id => {
            const node = this.findNode(id);
            const startPos = this.dragStartPositions[id];
            if (node && startPos) {
                node.x = Math.max(0, startPos.x + snappedDeltaX);
                node.y = Math.max(0, startPos.y + snappedDeltaY);
                
                // Update visual
                const wrapper = document.querySelector(`[data-node-id="${id}"]`);
                if (wrapper) {
                    wrapper.style.left = node.x + 'px';
                    wrapper.style.top = node.y + 'px';
                }
            }
        });
        
        this.renderConnections();
    }
    
    endNodeDrag() {
        if (this.isDragging && this.dragNode) {
            this.addToHistory();
            this.markUnsaved();
        }
        this.isDragging = false;
        this.dragNode = null;
        this.dragStartPositions = null;
        this.dragStartMouse = null;
    }
    
    // ===== Context Menu =====
    showContextMenu(x, y) {
        const menu = this.elements.contextMenu;
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;
        menu.classList.remove('hidden');
    }
    
    hideContextMenu() {
        this.elements.contextMenu.classList.add('hidden');
    }
    
    addInDirection(direction) {
        this.hideContextMenu();
        if (this.contextNodeId) {
            this.openAddModal(this.contextNodeId, direction);
        }
    }
    
    startLinkingMode() {
        this.hideContextMenu();
        this.showToast('Click on another node to create a link', 'info');
        // Simplified linking - could be expanded
    }
    
    editNode() {
        this.hideContextMenu();
        if (this.contextNodeId) {
            const node = this.findNode(this.contextNodeId);
            if (node) {
                this.openEditModal(node);
            }
        }
    }
    
    duplicateNode() {
        this.hideContextMenu();
        if (this.contextNodeId) {
            const node = this.findNode(this.contextNodeId);
            if (node) {
                const newNode = {
                    ...node,
                    id: this.generateId(),
                    x: node.x + 50,
                    y: node.y + 50,
                    name: node.name + ' (Copy)'
                };
                this.nodes.push(newNode);
                this.render();
                this.addToHistory();
                this.markUnsaved();
                this.showToast('Node duplicated!', 'success');
            }
        }
    }
    
    changeNodePhoto() {
        this.hideContextMenu();
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                this.loadImageFile(file, (dataUrl) => {
                    this.updateNodePhoto(this.contextNodeId, dataUrl);
                });
            }
        };
        input.click();
    }
    
    deleteNode() {
        this.hideContextMenu();
        if (this.contextNodeId) {
            if (confirm('Delete this member?')) {
                this.deleteNodeById(this.contextNodeId);
                this.showToast('Member deleted!', 'success');
            }
        }
    }
    
    // ===== Sidebar =====
    toggleSidebar() {
        this.elements.sidebar.classList.add('collapsed');
        const showBtn = document.getElementById('showSidebarBtn');
        if (showBtn) {
            showBtn.classList.add('visible');
        }
    }
    
    showSidebar() {
        this.elements.sidebar.classList.remove('collapsed');
        const showBtn = document.getElementById('showSidebarBtn');
        if (showBtn) {
            showBtn.classList.remove('visible');
        }
    }
    
    // ===== Sample CSV Download =====
    downloadSampleCSV() {
        const sampleCSV = `Name,Designation,Manager,Email,Phone,Department,Location
John Smith,CEO,,john@company.com,+1-555-0100,Executive,New York
Jane Doe,CTO,John Smith,jane@company.com,+1-555-0101,Engineering,San Francisco
Bob Wilson,VP Engineering,Jane Doe,bob@company.com,+1-555-0102,Engineering,Austin
Alice Brown,VP Product,John Smith,alice@company.com,+1-555-0103,Product,New York
Charlie Davis,Senior Engineer,Bob Wilson,charlie@company.com,+1-555-0104,Engineering,Austin
Diana Evans,Product Manager,Alice Brown,diana@company.com,+1-555-0105,Product,Remote
Frank Garcia,Engineer,Bob Wilson,frank@company.com,+1-555-0106,Engineering,San Francisco
Grace Harris,Designer,Alice Brown,grace@company.com,+1-555-0107,Design,New York`;
        
        const blob = new Blob([sampleCSV], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'orgchart_sample.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        this.showToast('Sample CSV downloaded!', 'success');
    }
    
    // ===== Keyboard Shortcuts =====
    handleKeyboard(e) {
        // Don't handle shortcuts when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        // Ctrl/Cmd + A = Select All
        if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
            e.preventDefault();
            this.selectAll();
        }
        // Ctrl/Cmd + Z = Undo
        if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
            e.preventDefault();
            this.undo();
        }
        // Ctrl/Cmd + Y or Ctrl/Cmd + Shift + Z = Redo
        if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
            e.preventDefault();
            this.redo();
        }
        // Ctrl/Cmd + S = Save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            this.saveCurrentChart();
            this.showToast('Chart saved!', 'success');
        }
        // Ctrl/Cmd + C = Copy selected nodes
        if ((e.ctrlKey || e.metaKey) && e.key === 'c' && this.selectedNodes.length > 0) {
            e.preventDefault();
            this.copySelectedNodes();
        }
        // Ctrl/Cmd + V = Paste
        if ((e.ctrlKey || e.metaKey) && e.key === 'v' && this.clipboard) {
            e.preventDefault();
            this.pasteNodes();
        }
        // Delete or Backspace = Delete selected
        if ((e.key === 'Delete' || e.key === 'Backspace') && this.selectedNodes.length > 0) {
            e.preventDefault();
            this.deleteSelectedNodes();
        }
        // Escape = Clear selection
        if (e.key === 'Escape') {
            this.clearSelection();
            this.hideContextMenu();
            this.hideChartContextMenu();
            this.clearSearch();
            this.render();
        }
        // Arrow keys for navigation
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
            e.preventDefault();
            this.navigateNodes(e.key);
        }
        // Enter to edit focused node
        if (e.key === 'Enter' && this.selectedNodes.length === 1) {
            e.preventDefault();
            this.editNode(this.selectedNodes[0]);
        }
        // G = Toggle grid
        if (e.key === 'g' || e.key === 'G') {
            this.toggleGridSnap();
        }
        // F = Fit all
        if (e.key === 'f' || e.key === 'F') {
            this.fitAllNodes();
        }
        // 0 = Reset zoom
        if (e.key === '0') {
            this.setZoom(1);
        }
        // + = Zoom in
        if (e.key === '+' || e.key === '=') {
            this.zoomIn();
        }
        // - = Zoom out
        if (e.key === '-') {
            this.zoomOut();
        }
        // ? = Show shortcuts
        if (e.key === '?') {
            this.showShortcutsModal();
        }
    }
    
    // ===== Copy/Paste =====
    copySelectedNodes() {
        this.clipboard = this.selectedNodes.map(id => {
            const node = this.findNode(id);
            return node ? { ...node } : null;
        }).filter(n => n);
        this.showToast(`Copied ${this.clipboard.length} node(s)`, 'info');
    }
    
    pasteNodes() {
        if (!this.clipboard || this.clipboard.length === 0) return;
        
        const offsetX = 50;
        const offsetY = 50;
        const newIds = [];
        
        this.clipboard.forEach(node => {
            const newNode = {
                ...node,
                id: this.generateId(),
                x: node.x + offsetX,
                y: node.y + offsetY,
                name: node.name + ' (Copy)'
            };
            this.nodes.push(newNode);
            newIds.push(newNode.id);
        });
        
        this.selectedNodes = newIds;
        this.render();
        this.addToHistory();
        this.markUnsaved();
        this.updateSelectedCount();
        this.showToast(`Pasted ${newIds.length} node(s)`, 'success');
    }
    
    deleteSelectedNodes() {
        if (this.selectedNodes.length === 0) return;
        
        const count = this.selectedNodes.length;
        if (confirm(`Delete ${count} selected member(s)?`)) {
            this.selectedNodes.forEach(id => {
                this.nodes = this.nodes.filter(n => n.id !== id);
                this.connections = this.connections.filter(c => c.from !== id && c.to !== id);
            });
            this.selectedNodes = [];
            this.selectedNode = null;
            this.render();
            this.updateEmptyState();
            this.updateNodeCount();
            this.updateSelectedCount();
            this.addToHistory();
            this.markUnsaved();
            this.showToast(`Deleted ${count} member(s)`, 'success');
        }
    }
    
    // ===== Zoom =====
    setZoom(level) {
        this.zoom = Math.max(0.25, Math.min(2, level));
        this.elements.canvas.style.transform = `scale(${this.zoom})`;
        const zoomText = Math.round(this.zoom * 100) + '%';
        this.elements.zoomLevel.textContent = zoomText;
        // Update toolbar zoom level too
        const toolbarZoomLevel = document.getElementById('toolbarZoomLevel');
        if (toolbarZoomLevel) toolbarZoomLevel.textContent = zoomText;
    }
    
    zoomIn() {
        this.setZoom(this.zoom + 0.1);
    }
    
    zoomOut() {
        this.setZoom(this.zoom - 0.1);
    }
    
    fitToScreen() {
        if (this.nodes.length === 0) {
            this.setZoom(1);
            return;
        }
        
        const containerRect = this.elements.canvasContainer.getBoundingClientRect();
        const minX = Math.min(...this.nodes.map(n => n.x));
        const maxX = Math.max(...this.nodes.map(n => n.x + this.NODE_WIDTH));
        const minY = Math.min(...this.nodes.map(n => n.y));
        const maxY = Math.max(...this.nodes.map(n => n.y + this.NODE_HEIGHT));
        
        const contentWidth = maxX - minX + 200;
        const contentHeight = maxY - minY + 200;
        
        const scaleX = containerRect.width / contentWidth;
        const scaleY = containerRect.height / contentHeight;
        
        this.setZoom(Math.min(scaleX, scaleY, 1));
        this.centerView();
    }
    
    centerView() {
        if (this.nodes.length === 0) return;
        
        const avgX = this.nodes.reduce((sum, n) => sum + n.x, 0) / this.nodes.length;
        const avgY = this.nodes.reduce((sum, n) => sum + n.y, 0) / this.nodes.length;
        
        const containerRect = this.elements.canvasContainer.getBoundingClientRect();
        const centerX = (avgX + this.NODE_WIDTH / 2) * this.zoom - containerRect.width / 2;
        const centerY = (avgY + this.NODE_HEIGHT / 2) * this.zoom - containerRect.height / 2;
        
        this.elements.canvasContainer.scrollLeft = Math.max(0, centerX);
        this.elements.canvasContainer.scrollTop = Math.max(0, centerY);
    }
    
    // ===== History (Undo/Redo) =====
    addToHistory() {
        // Remove any redo states
        this.history = this.history.slice(0, this.historyIndex + 1);
        
        // Add current state
        this.history.push({
            nodes: JSON.parse(JSON.stringify(this.nodes)),
            connections: JSON.parse(JSON.stringify(this.connections))
        });
        
        this.historyIndex = this.history.length - 1;
        
        // Limit history size
        if (this.history.length > 50) {
            this.history.shift();
            this.historyIndex--;
        }
        
        this.updateHistoryButtons();
    }
    
    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const state = this.history[this.historyIndex];
            this.nodes = JSON.parse(JSON.stringify(state.nodes));
            this.connections = JSON.parse(JSON.stringify(state.connections));
            this.render();
            this.updateHistoryButtons();
            this.markUnsaved();
        }
    }
    
    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            const state = this.history[this.historyIndex];
            this.nodes = JSON.parse(JSON.stringify(state.nodes));
            this.connections = JSON.parse(JSON.stringify(state.connections));
            this.render();
            this.updateHistoryButtons();
            this.markUnsaved();
        }
    }
    
    updateHistoryButtons() {
        this.elements.undoBtn.disabled = this.historyIndex <= 0;
        this.elements.redoBtn.disabled = this.historyIndex >= this.history.length - 1;
    }
    
    // ===== Clear All =====
    clearAll() {
        if (this.nodes.length === 0) return;
        
        if (confirm('Clear all members from this chart?')) {
            this.nodes = [];
            this.connections = [];
            this.selectedNode = null;
            this.render();
            this.updateEmptyState();
            this.updateNodeCount();
            this.addToHistory();
            this.markUnsaved();
            this.showToast('Chart cleared!', 'success');
        }
    }
    
    // ===== Export =====
    async exportAs(format) {
        this.elements.exportDropdown.classList.remove('show');
        
        if (this.nodes.length === 0) {
            this.showToast('Nothing to export!', 'warning');
            return;
        }
        
        this.showToast('Preparing export...', 'info');
        
        // Save current state
        const savedSelection = [...this.selectedNodes];
        const savedZoom = this.zoom;
        const savedScrollLeft = this.elements.canvasContainer.scrollLeft;
        const savedScrollTop = this.elements.canvasContainer.scrollTop;
        
        // Clear selection and reset zoom for clean export
        this.selectedNodes = [];
        this.setZoom(1);
        this.render();
        
        // Wait for render to complete
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Use html2canvas if available
        if (typeof html2canvas !== 'undefined') {
            try {
                // Calculate the bounding box including nodes AND connection endpoints
                const padding = 80; // Extra padding for arrows
                
                // Start with node bounds
                let minX = Math.min(...this.nodes.map(n => n.x));
                let minY = Math.min(...this.nodes.map(n => n.y));
                let maxX = Math.max(...this.nodes.map(n => n.x + this.NODE_WIDTH));
                let maxY = Math.max(...this.nodes.map(n => n.y + this.NODE_HEIGHT));
                
                // Expand bounds to include connection line endpoints
                this.connections.forEach(conn => {
                    const fromNode = this.findNode(conn.from);
                    const toNode = this.findNode(conn.to);
                    if (fromNode && toNode) {
                        // Calculate actual line endpoints based on direction
                        let startX, startY, endX, endY;
                        switch (conn.direction) {
                            case 'bottom':
                                startX = fromNode.x + this.NODE_WIDTH / 2;
                                startY = fromNode.y + this.NODE_HEIGHT;
                                endX = toNode.x + this.NODE_WIDTH / 2;
                                endY = toNode.y;
                                break;
                            case 'top':
                                startX = fromNode.x + this.NODE_WIDTH / 2;
                                startY = fromNode.y;
                                endX = toNode.x + this.NODE_WIDTH / 2;
                                endY = toNode.y + this.NODE_HEIGHT;
                                break;
                            case 'right':
                                startX = fromNode.x + this.NODE_WIDTH;
                                startY = fromNode.y + this.NODE_HEIGHT / 2;
                                endX = toNode.x;
                                endY = toNode.y + this.NODE_HEIGHT / 2;
                                break;
                            case 'left':
                                startX = fromNode.x;
                                startY = fromNode.y + this.NODE_HEIGHT / 2;
                                endX = toNode.x + this.NODE_WIDTH;
                                endY = toNode.y + this.NODE_HEIGHT / 2;
                                break;
                            default:
                                startX = fromNode.x + this.NODE_WIDTH / 2;
                                startY = fromNode.y + this.NODE_HEIGHT / 2;
                                endX = toNode.x + this.NODE_WIDTH / 2;
                                endY = toNode.y + this.NODE_HEIGHT / 2;
                        }
                        minX = Math.min(minX, startX, endX);
                        minY = Math.min(minY, startY, endY);
                        maxX = Math.max(maxX, startX, endX);
                        maxY = Math.max(maxY, startY, endY);
                    }
                });
                
                // Ensure minimum bounds don't go negative (minX/minY is the crop start)
                const cropX = Math.max(0, minX - padding);
                const cropY = Math.max(0, minY - padding);
                const cropWidth = (maxX + padding) - cropX;
                const cropHeight = (maxY + padding) - cropY;
                
                // Hide SVG temporarily since html2canvas doesn't render it well
                const svgElement = this.elements.connectionsSvg;
                const originalSvgDisplay = svgElement.style.display;
                svgElement.style.display = 'none';
                
                // Capture the nodes without SVG
                const fullCanvas = await html2canvas(this.elements.canvas, {
                    backgroundColor: '#F8FAFC',
                    scale: 2,
                    useCORS: true,
                    allowTaint: true,
                    logging: false
                });
                
                // Restore SVG
                svgElement.style.display = originalSvgDisplay;
                
                // Create final export canvas
                const exportCanvas = document.createElement('canvas');
                const scale = 2;
                exportCanvas.width = cropWidth * scale;
                exportCanvas.height = cropHeight * scale;
                const ctx = exportCanvas.getContext('2d');
                
                // Fill with background color
                ctx.fillStyle = '#F8FAFC';
                ctx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
                
                // Draw the cropped nodes FIRST (background layer)
                const sourceX = cropX * scale;
                const sourceY = cropY * scale;
                const sourceW = cropWidth * scale;
                const sourceH = cropHeight * scale;
                
                ctx.drawImage(
                    fullCanvas,
                    sourceX, sourceY, sourceW, sourceH,
                    0, 0, sourceW, sourceH
                );
                
                // Draw connections ON TOP of nodes
                ctx.strokeStyle = this.lineColor || '#6366F1';
                ctx.lineWidth = 2 * scale;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                
                this.connections.forEach(conn => {
                    const fromNode = this.findNode(conn.from);
                    const toNode = this.findNode(conn.to);
                    if (fromNode && toNode) {
                        let startX, startY, endX, endY;
                        switch (conn.direction) {
                            case 'bottom':
                                startX = fromNode.x + this.NODE_WIDTH / 2;
                                startY = fromNode.y + this.NODE_HEIGHT;
                                endX = toNode.x + this.NODE_WIDTH / 2;
                                endY = toNode.y;
                                break;
                            case 'top':
                                startX = fromNode.x + this.NODE_WIDTH / 2;
                                startY = fromNode.y;
                                endX = toNode.x + this.NODE_WIDTH / 2;
                                endY = toNode.y + this.NODE_HEIGHT;
                                break;
                            case 'right':
                                startX = fromNode.x + this.NODE_WIDTH;
                                startY = fromNode.y + this.NODE_HEIGHT / 2;
                                endX = toNode.x;
                                endY = toNode.y + this.NODE_HEIGHT / 2;
                                break;
                            case 'left':
                                startX = fromNode.x;
                                startY = fromNode.y + this.NODE_HEIGHT / 2;
                                endX = toNode.x + this.NODE_WIDTH;
                                endY = toNode.y + this.NODE_HEIGHT / 2;
                                break;
                            default:
                                startX = fromNode.x + this.NODE_WIDTH / 2;
                                startY = fromNode.y + this.NODE_HEIGHT / 2;
                                endX = toNode.x + this.NODE_WIDTH / 2;
                                endY = toNode.y + this.NODE_HEIGHT / 2;
                        }
                        
                        // Adjust coordinates relative to crop area
                        const adjStartX = (startX - cropX) * scale;
                        const adjStartY = (startY - cropY) * scale;
                        const adjEndX = (endX - cropX) * scale;
                        const adjEndY = (endY - cropY) * scale;
                        
                        // Draw line
                        ctx.beginPath();
                        ctx.moveTo(adjStartX, adjStartY);
                        ctx.lineTo(adjEndX, adjEndY);
                        ctx.stroke();
                        
                        // Draw arrow head
                        const angle = Math.atan2(adjEndY - adjStartY, adjEndX - adjStartX);
                        const arrowSize = 12 * scale;
                        ctx.fillStyle = this.lineColor || '#6366F1';
                        ctx.beginPath();
                        ctx.moveTo(adjEndX, adjEndY);
                        ctx.lineTo(
                            adjEndX - arrowSize * Math.cos(angle - Math.PI / 6),
                            adjEndY - arrowSize * Math.sin(angle - Math.PI / 6)
                        );
                        ctx.lineTo(
                            adjEndX - arrowSize * Math.cos(angle + Math.PI / 6),
                            adjEndY - arrowSize * Math.sin(angle + Math.PI / 6)
                        );
                        ctx.closePath();
                        ctx.fill();
                    }
                });
                
                const link = document.createElement('a');
                const chartName = this.currentChart?.name?.replace(/[^a-z0-9]/gi, '_') || 'orgchart';
                link.download = `${chartName}.${format}`;
                
                if (format === 'jpg' || format === 'jpeg') {
                    link.href = exportCanvas.toDataURL('image/jpeg', 0.95);
                } else {
                    link.href = exportCanvas.toDataURL('image/png');
                }
                
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                this.showToast(`Exported as ${format.toUpperCase()} successfully!`, 'success');
            } catch (err) {
                console.error('Export error:', err);
                this.showToast('Export failed: ' + err.message, 'error');
            }
        } else {
            this.showToast('Export library not loaded. Please refresh the page.', 'warning');
        }
        
        // Restore state
        this.selectedNodes = savedSelection;
        this.setZoom(savedZoom);
        this.elements.canvasContainer.scrollLeft = savedScrollLeft;
        this.elements.canvasContainer.scrollTop = savedScrollTop;
        this.render();
    }
    
    exportPDF() {
        this.elements.exportDropdown.classList.remove('show');
        this.showToast('PDF export requires jsPDF library', 'info');
        // Would implement with jsPDF library
    }
    
    exportJSON() {
        this.elements.exportDropdown.classList.remove('show');
        
        if (!this.currentChart) {
            this.showToast('No chart to export!', 'warning');
            return;
        }
        
        this.downloadJSON(this.currentChart, `${this.currentChart.name}_OrgChart.json`);
        this.showToast('JSON exported!', 'success');
    }
    
    downloadJSON(data, filename) {
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.download = filename;
        link.href = url;
        link.click();
        
        URL.revokeObjectURL(url);
    }
    
    importChart(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                
                if (data.id && data.name) {
                    // Single chart
                    const newId = 'chart_' + Date.now();
                    data.id = newId;
                    this.charts[newId] = data;
                    this.loadChart(newId);
                } else if (typeof data === 'object') {
                    // Multiple charts
                    Object.values(data).forEach(chart => {
                        if (chart.id && chart.name) {
                            const newId = 'chart_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
                            chart.id = newId;
                            this.charts[newId] = chart;
                        }
                    });
                    const firstId = Object.keys(this.charts)[0];
                    if (firstId) this.loadChart(firstId);
                }
                
                this.saveChartsToStorage();
                this.renderSavedChartsList();
                this.showToast('Chart imported!', 'success');
            } catch (err) {
                this.showToast('Invalid JSON file!', 'error');
            }
        };
        reader.readAsText(file);
        e.target.value = '';
    }
    
    exportAllCharts() {
        if (Object.keys(this.charts).length === 0) {
            this.showToast('No charts to export!', 'warning');
            return;
        }
        
        this.downloadJSON(this.charts, 'All_OrgCharts.json');
        this.showToast('All charts exported!', 'success');
    }
    
    clearAllData() {
        if (confirm('Delete ALL saved charts? This cannot be undone!')) {
            this.charts = {};
            this.currentChartId = null;
            this.currentChart = null;
            this.nodes = [];
            this.connections = [];
            localStorage.removeItem('orgChartPro_charts');
            this.render();
            this.updateEmptyState();
            this.renderSavedChartsList();
            this.showToast('All data cleared!', 'success');
        }
    }
    
    // ===== Storage =====
    saveChartsToStorage() {
        try {
            localStorage.setItem('orgChartPro_charts', JSON.stringify(this.charts));
        } catch (e) {
            console.warn('Could not save to localStorage:', e);
        }
    }
    
    loadChartsFromStorage() {
        try {
            const saved = localStorage.getItem('orgChartPro_charts');
            if (saved) {
                this.charts = JSON.parse(saved);
                this.renderSavedChartsList();
                
                // Update the saved charts hint on welcome page
                const chartCount = Object.keys(this.charts).length;
                const hint = document.getElementById('savedChartsHint');
                if (hint && chartCount > 0) {
                    hint.textContent = `You have ${chartCount} saved chart${chartCount > 1 ? 's' : ''}`;
                }
                
                // Auto-load the most recent chart
                const chartIds = Object.keys(this.charts);
                if (chartIds.length > 0) {
                    const sorted = chartIds
                        .map(id => this.charts[id])
                        .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
                    this.loadChart(sorted[0].id);
                    this.elements.welcomeModal.classList.remove('active');
                    this.elements.app.classList.remove('hidden');
                }
            }
        } catch (e) {
            console.warn('Could not load from localStorage:', e);
        }
    }
    
    openSavedChartsFromWelcome() {
        const chartIds = Object.keys(this.charts);
        if (chartIds.length === 0) {
            this.showToast('No saved charts found. Create a new chart first!', 'warning');
            return;
        }
        
        // Load the most recent chart
        const sorted = chartIds
            .map(id => this.charts[id])
            .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
        this.loadChart(sorted[0].id);
        this.elements.welcomeModal.classList.remove('active');
        this.elements.app.classList.remove('hidden');
    }
    
    // ===== UI Updates =====
    updateEmptyState() {
        if (this.nodes.length === 0) {
            this.elements.emptyState.classList.remove('hidden');
        } else {
            this.elements.emptyState.classList.add('hidden');
        }
    }
    
    updateNodeCount() {
        this.elements.nodeCount.textContent = this.nodes.length;
    }
    
    // ===== Toast Notifications =====
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'check-circle',
            error: 'times-circle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        
        toast.innerHTML = `
            <i class="fas fa-${icons[type] || 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        this.elements.toastContainer.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // ===== Utilities =====
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
    
    // ===== New Feature Methods =====
    
    bindNewFeatureEvents() {
        // Show sidebar button
        const showSidebarBtn = document.getElementById('showSidebarBtn');
        if (showSidebarBtn) {
            showSidebarBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showSidebar();
            });
        }
        
        // Import CSV from sidebar
        const importCSVBtn = document.getElementById('importCSVBtn');
        if (importCSVBtn) {
            importCSVBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openCSVModal();
            });
        }
        
        // Download sample CSV from sidebar
        const downloadSampleCSVSidebar = document.getElementById('downloadSampleCSVSidebar');
        if (downloadSampleCSVSidebar) {
            downloadSampleCSVSidebar.addEventListener('click', (e) => {
                e.stopPropagation();
                this.downloadSampleCSV();
            });
        }
        
        // Add Person dropdown
        const addPersonDropdownBtn = document.getElementById('addPersonDropdownBtn');
        const addPersonDropdown = document.getElementById('addPersonDropdown');
        if (addPersonDropdownBtn && addPersonDropdown) {
            addPersonDropdownBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                addPersonDropdown.classList.toggle('show');
            });
        }
        
        // Import CSV from toolbar dropdown
        const importCSVToolbarBtn = document.getElementById('importCSVToolbarBtn');
        if (importCSVToolbarBtn) {
            importCSVToolbarBtn.addEventListener('click', () => {
                addPersonDropdown?.classList.remove('show');
                this.openCSVModal();
            });
        }
        
        // Sample CSV download from toolbar dropdown
        const downloadSampleCSVToolbar = document.getElementById('downloadSampleCSVToolbar');
        if (downloadSampleCSVToolbar) {
            downloadSampleCSVToolbar.addEventListener('click', () => {
                addPersonDropdown?.classList.remove('show');
                this.downloadSampleCSV();
            });
        }
        
        // Sample CSV download from modal
        const downloadSampleCSVModal = document.getElementById('downloadSampleCSV');
        if (downloadSampleCSVModal) {
            downloadSampleCSVModal.addEventListener('click', (e) => {
                e.preventDefault();
                this.downloadSampleCSV();
            });
        }
        
        // Grid snap
        const gridSnapBtn = document.getElementById('gridSnapBtn');
        if (gridSnapBtn) {
            gridSnapBtn.addEventListener('click', () => this.toggleGridSnap());
        }
        
        // Fit all
        const fitAllBtn = document.getElementById('fitAllBtn');
        if (fitAllBtn) {
            fitAllBtn.addEventListener('click', () => this.fitAllNodes());
        }
        
        // Auto Layout
        const autoLayoutBtn = document.getElementById('autoLayoutBtn');
        if (autoLayoutBtn) {
            autoLayoutBtn.addEventListener('click', () => {
                this.autoLayoutHierarchy();
                this.fitAllNodes();
                this.addToHistory();
                this.showToast('Chart arranged hierarchically', 'success');
            });
        }
        
        // Minimap
        const minimapToggle = document.getElementById('minimapToggle');
        if (minimapToggle) {
            minimapToggle.addEventListener('click', () => this.toggleMinimap());
        }
        
        // CSV File Input
        const csvFileInput = document.getElementById('csvFileInput');
        if (csvFileInput) {
            csvFileInput.addEventListener('change', (e) => this.handleCSVFile(e));
        }
        
        // CSV Drop Zone drag and drop
        const csvDropZone = document.getElementById('csvDropZone');
        if (csvDropZone) {
            csvDropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                csvDropZone.classList.add('dragover');
            });
            csvDropZone.addEventListener('dragleave', () => {
                csvDropZone.classList.remove('dragover');
            });
            csvDropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                csvDropZone.classList.remove('dragover');
                const file = e.dataTransfer.files[0];
                if (file && file.name.endsWith('.csv')) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        this.parseCSV(event.target.result);
                    };
                    reader.readAsText(file);
                } else {
                    this.showToast('Please drop a CSV file', 'error');
                }
            });
        }
        
        document.getElementById('closeCSVModal')?.addEventListener('click', () => this.closeCSVModal());
        document.getElementById('cancelCSVBtn')?.addEventListener('click', () => this.closeCSVModal());
        document.getElementById('importCSVDataBtn')?.addEventListener('click', () => this.importCSVData());
        
        // Shortcuts modal
        document.getElementById('closeShortcutsModal')?.addEventListener('click', () => this.closeShortcutsModal());
        
        // Update minimap on scroll
        this.elements.canvasContainer?.addEventListener('scroll', () => this.updateMinimapViewport());
    }
    
    // Dark Mode
    toggleDarkMode() {
        this.isDarkMode = !this.isDarkMode;
        document.body.classList.toggle('dark-mode', this.isDarkMode);
        localStorage.setItem('orgchart_darkmode', this.isDarkMode);
        
        if (this.elements.themeToggle) {
            this.elements.themeToggle.innerHTML = this.isDarkMode ? 
                '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        }
        this.showToast(this.isDarkMode ? 'Dark mode enabled' : 'Light mode enabled', 'info');
    }
    
    // Search
    handleSearch(query) {
        query = query.toLowerCase().trim();
        
        document.querySelectorAll('.org-node').forEach(nodeEl => {
            const nodeId = nodeEl.closest('.node-wrapper')?.dataset.nodeId;
            const node = this.findNode(nodeId);
            
            if (!query) {
                nodeEl.classList.remove('search-match', 'search-dimmed');
                return;
            }
            
            const matches = node && (
                node.name.toLowerCase().includes(query) ||
                node.designation?.toLowerCase().includes(query) ||
                node.department?.toLowerCase().includes(query) ||
                node.email?.toLowerCase().includes(query)
            );
            
            nodeEl.classList.toggle('search-match', matches);
            nodeEl.classList.toggle('search-dimmed', !matches);
        });
    }
    
    clearSearch() {
        if (this.elements.searchInput) {
            this.elements.searchInput.value = '';
        }
        document.querySelectorAll('.org-node').forEach(nodeEl => {
            nodeEl.classList.remove('search-match', 'search-dimmed');
        });
    }
    
    // Grid Snap
    toggleGridSnap() {
        this.gridSnapEnabled = !this.gridSnapEnabled;
        this.elements.gridSnapBtn?.classList.toggle('active', this.gridSnapEnabled);
        this.elements.gridOverlay?.classList.toggle('hidden', !this.gridSnapEnabled);
        this.showToast(this.gridSnapEnabled ? 'Grid snap enabled' : 'Grid snap disabled', 'info');
    }
    
    snapToGrid(value) {
        if (!this.gridSnapEnabled) return value;
        return Math.round(value / this.gridSize) * this.gridSize;
    }
    
    // Fit All Nodes
    fitAllNodes() {
        if (this.nodes.length === 0) return;
        
        const padding = 100;
        const minX = Math.min(...this.nodes.map(n => n.x));
        const minY = Math.min(...this.nodes.map(n => n.y));
        const maxX = Math.max(...this.nodes.map(n => n.x + this.NODE_WIDTH));
        const maxY = Math.max(...this.nodes.map(n => n.y + this.NODE_HEIGHT));
        
        const contentWidth = maxX - minX + padding * 2;
        const contentHeight = maxY - minY + padding * 2;
        
        const containerRect = this.elements.canvasContainer.getBoundingClientRect();
        const scaleX = containerRect.width / contentWidth;
        const scaleY = containerRect.height / contentHeight;
        const newZoom = Math.min(scaleX, scaleY, 1);
        
        this.setZoom(newZoom);
        
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        
        this.elements.canvasContainer.scrollLeft = centerX * this.zoom - containerRect.width / 2;
        this.elements.canvasContainer.scrollTop = centerY * this.zoom - containerRect.height / 2;
        
        this.showToast('Fit all nodes to view', 'info');
    }
    
    // Auto Layout - Hierarchical Tree Layout
    autoLayoutHierarchy() {
        if (this.nodes.length === 0) return;
        
        const HORIZONTAL_SPACING = 280;
        const VERTICAL_SPACING = 180;
        const START_X = 400;
        const START_Y = 100;
        
        // Build parent-child relationships
        const childrenMap = new Map(); // parentId -> [childIds]
        const parentMap = new Map();   // childId -> parentId
        
        this.connections.forEach(conn => {
            const parentId = conn.from;
            const childId = conn.to;
            
            if (!childrenMap.has(parentId)) {
                childrenMap.set(parentId, []);
            }
            childrenMap.get(parentId).push(childId);
            parentMap.set(childId, parentId);
        });
        
        // Find root nodes (nodes with no parent)
        const rootNodes = this.nodes.filter(n => !parentMap.has(n.id));
        
        // If no root nodes found (circular refs), use all nodes
        if (rootNodes.length === 0) {
            rootNodes.push(...this.nodes);
        }
        
        // Calculate subtree widths
        const getSubtreeWidth = (nodeId) => {
            const children = childrenMap.get(nodeId) || [];
            if (children.length === 0) return 1;
            return children.reduce((sum, childId) => sum + getSubtreeWidth(childId), 0);
        };
        
        // Position nodes recursively
        const positionNode = (nodeId, x, y, availableWidth) => {
            const node = this.findNode(nodeId);
            if (!node) return;
            
            node.x = x + (availableWidth * HORIZONTAL_SPACING - this.NODE_WIDTH) / 2;
            node.y = y;
            
            const children = childrenMap.get(nodeId) || [];
            if (children.length === 0) return;
            
            // Calculate positions for children
            const totalChildWidth = children.reduce((sum, childId) => sum + getSubtreeWidth(childId), 0);
            let childX = x + (availableWidth - totalChildWidth) * HORIZONTAL_SPACING / 2;
            
            children.forEach(childId => {
                const childWidth = getSubtreeWidth(childId);
                positionNode(childId, childX, y + VERTICAL_SPACING, childWidth);
                childX += childWidth * HORIZONTAL_SPACING;
            });
        };
        
        // Position all root nodes side by side
        let currentX = START_X;
        rootNodes.forEach(rootNode => {
            const width = getSubtreeWidth(rootNode.id);
            positionNode(rootNode.id, currentX, START_Y, width);
            currentX += width * HORIZONTAL_SPACING + HORIZONTAL_SPACING;
        });
        
        // Center the entire layout
        const minX = Math.min(...this.nodes.map(n => n.x));
        const maxX = Math.max(...this.nodes.map(n => n.x));
        const containerWidth = this.elements.canvasContainer.clientWidth;
        const offsetX = (containerWidth / 2) - ((maxX + minX) / 2);
        
        if (offsetX > 0) {
            this.nodes.forEach(n => n.x += offsetX / 2);
        }
        
        this.render();
    }
    
    // Minimap
    toggleMinimap() {
        this.minimapVisible = !this.minimapVisible;
        this.elements.minimapContent?.classList.toggle('collapsed', !this.minimapVisible);
        if (this.elements.minimapToggle) {
            this.elements.minimapToggle.innerHTML = this.minimapVisible ? 
                '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
        }
    }
    
    updateMinimap() {
        if (!this.elements.minimapContent || this.nodes.length === 0) return;
        
        const padding = 20;
        const minX = Math.min(...this.nodes.map(n => n.x));
        const minY = Math.min(...this.nodes.map(n => n.y));
        const maxX = Math.max(...this.nodes.map(n => n.x + this.NODE_WIDTH));
        const maxY = Math.max(...this.nodes.map(n => n.y + this.NODE_HEIGHT));
        
        const contentWidth = maxX - minX + padding * 2;
        const contentHeight = maxY - minY + padding * 2;
        
        const minimapWidth = 200;
        const minimapHeight = 120;
        const scale = Math.min(minimapWidth / contentWidth, minimapHeight / contentHeight);
        
        // Clear and redraw nodes
        const nodesHtml = this.nodes.map(node => {
            const x = (node.x - minX + padding) * scale;
            const y = (node.y - minY + padding) * scale;
            const w = this.NODE_WIDTH * scale;
            const h = this.NODE_HEIGHT * scale;
            return `<div class="minimap-node" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;"></div>`;
        }).join('');
        
        this.elements.minimapContent.innerHTML = nodesHtml + '<div class="minimap-viewport" id="minimapViewport"></div>';
        this.elements.minimapViewport = document.getElementById('minimapViewport');
        
        // Store for viewport calculation
        this._minimapScale = scale;
        this._minimapOffset = { x: minX - padding, y: minY - padding };
        
        this.updateMinimapViewport();
    }
    
    updateMinimapViewport() {
        if (!this.elements.minimapViewport || !this._minimapScale) return;
        
        const container = this.elements.canvasContainer;
        const scale = this._minimapScale;
        const offset = this._minimapOffset;
        
        const viewX = (container.scrollLeft / this.zoom - offset.x) * scale;
        const viewY = (container.scrollTop / this.zoom - offset.y) * scale;
        const viewW = (container.clientWidth / this.zoom) * scale;
        const viewH = (container.clientHeight / this.zoom) * scale;
        
        this.elements.minimapViewport.style.left = `${viewX}px`;
        this.elements.minimapViewport.style.top = `${viewY}px`;
        this.elements.minimapViewport.style.width = `${viewW}px`;
        this.elements.minimapViewport.style.height = `${viewH}px`;
    }
    
    // CSV Import
    openCSVModal() {
        this.elements.csvImportModal?.classList.add('active');
        this.csvData = null;
        if (this.elements.csvPreview) {
            this.elements.csvPreview.classList.add('hidden');
        }
        if (this.elements.importCSVDataBtn) {
            this.elements.importCSVDataBtn.disabled = true;
        }
        if (this.elements.csvFileInput) {
            this.elements.csvFileInput.value = '';
        }
    }
    
    closeCSVModal() {
        this.elements.csvImportModal?.classList.remove('active');
        this.csvData = null;
    }
    
    handleCSVFile(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            this.parseCSV(event.target.result);
        };
        reader.readAsText(file);
    }
    
    parseCSV(content) {
        const lines = content.split('\n').filter(line => line.trim());
        if (lines.length < 2) {
            this.showToast('CSV must have headers and at least one data row', 'error');
            return;
        }
        
        // Parse headers, filter out empty ones (handles trailing commas)
        const headers = lines[0].split(',').map(h => h.trim().toLowerCase()).filter(h => h);
        const data = [];
        
        for (let i = 1; i < lines.length; i++) {
            const values = this.parseCSVLine(lines[i]);
            const row = {};
            headers.forEach((h, idx) => {
                row[h] = values[idx]?.trim() || '';
            });
            // Only add row if it has a name
            if (row.name || row.fullname || row['full name']) {
                data.push(row);
            }
        }
        
        this.csvData = data;
        this.showCSVPreview(headers, data.slice(0, 5));
        
        if (this.elements.importCSVDataBtn) {
            this.elements.importCSVDataBtn.disabled = false;
        }
    }
    
    parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current);
                current = '';
            } else {
                current += char;
            }
        }
        result.push(current);
        return result;
    }
    
    showCSVPreview(headers, data) {
        if (!this.elements.csvPreviewTable) return;
        
        let html = '<thead><tr>';
        headers.forEach(h => {
            html += `<th>${this.escapeHtml(h)}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        data.forEach(row => {
            html += '<tr>';
            headers.forEach(h => {
                html += `<td>${this.escapeHtml(row[h] || '')}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody>';
        
        this.elements.csvPreviewTable.innerHTML = html;
        this.elements.csvPreview?.classList.remove('hidden');
    }
    
    importCSVData() {
        if (!this.csvData || this.csvData.length === 0) return;
        
        const nodeMap = new Map();
        
        // First pass: create all nodes (position will be set by autoLayout)
        this.csvData.forEach((row, idx) => {
            const name = row.name || row.fullname || row['full name'] || `Person ${idx + 1}`;
            const node = {
                id: this.generateId(),
                x: 400,
                y: 200,
                name: name,
                designation: row.designation || row.title || row.role || '',
                email: row.email || '',
                phone: row.phone || row.telephone || '',
                department: row.department || row.dept || '',
                location: row.location || row.office || '',
                photo: null,
                color: this.defaultColor
            };
            this.nodes.push(node);
            nodeMap.set(name.toLowerCase().trim(), node.id);
        });
        
        // Second pass: create connections based on manager field
        // Skip self-references (someone reporting to themselves)
        this.csvData.forEach(row => {
            const name = (row.name || row.fullname || row['full name'] || '').toLowerCase().trim();
            const managerName = (row.manager || row.reportsto || row['reports to'] || '').toLowerCase().trim();
            
            // Skip if no manager, same as self, or manager not found
            if (managerName && name !== managerName && nodeMap.has(name) && nodeMap.has(managerName)) {
                this.connections.push({
                    id: 'conn_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
                    from: nodeMap.get(managerName),
                    to: nodeMap.get(name),
                    direction: 'bottom'
                });
            }
        });
        
        // Apply hierarchical layout
        this.autoLayoutHierarchy();
        this.updateEmptyState();
        this.addToHistory();
        this.closeCSVModal();
        this.fitAllNodes();
        this.showToast(`Imported ${this.csvData.length} people from CSV`, 'success');
    }
    
    // Keyboard Navigation
    navigateNodes(direction) {
        if (this.nodes.length === 0) return;
        
        let currentNode = null;
        if (this.selectedNodes.length > 0) {
            currentNode = this.findNode(this.selectedNodes[0]);
        }
        
        if (!currentNode) {
            // Select first node
            this.selectedNodes = [this.nodes[0].id];
            this.render();
            return;
        }
        
        // Find closest node in the direction
        let bestNode = null;
        let bestDistance = Infinity;
        
        this.nodes.forEach(node => {
            if (node.id === currentNode.id) return;
            
            const dx = node.x - currentNode.x;
            const dy = node.y - currentNode.y;
            
            let isInDirection = false;
            let distance = 0;
            
            switch (direction) {
                case 'ArrowUp':
                    isInDirection = dy < -20;
                    distance = Math.abs(dy) + Math.abs(dx) * 0.5;
                    break;
                case 'ArrowDown':
                    isInDirection = dy > 20;
                    distance = Math.abs(dy) + Math.abs(dx) * 0.5;
                    break;
                case 'ArrowLeft':
                    isInDirection = dx < -20;
                    distance = Math.abs(dx) + Math.abs(dy) * 0.5;
                    break;
                case 'ArrowRight':
                    isInDirection = dx > 20;
                    distance = Math.abs(dx) + Math.abs(dy) * 0.5;
                    break;
            }
            
            if (isInDirection && distance < bestDistance) {
                bestDistance = distance;
                bestNode = node;
            }
        });
        
        if (bestNode) {
            this.selectedNodes = [bestNode.id];
            this.render();
            this.scrollNodeIntoView(bestNode);
        }
    }
    
    scrollNodeIntoView(node) {
        const container = this.elements.canvasContainer;
        const nodeX = node.x * this.zoom;
        const nodeY = node.y * this.zoom;
        
        const viewLeft = container.scrollLeft;
        const viewTop = container.scrollTop;
        const viewRight = viewLeft + container.clientWidth;
        const viewBottom = viewTop + container.clientHeight;
        
        const padding = 50;
        
        if (nodeX < viewLeft + padding) {
            container.scrollLeft = nodeX - padding;
        } else if (nodeX + this.NODE_WIDTH * this.zoom > viewRight - padding) {
            container.scrollLeft = nodeX + this.NODE_WIDTH * this.zoom - container.clientWidth + padding;
        }
        
        if (nodeY < viewTop + padding) {
            container.scrollTop = nodeY - padding;
        } else if (nodeY + this.NODE_HEIGHT * this.zoom > viewBottom - padding) {
            container.scrollTop = nodeY + this.NODE_HEIGHT * this.zoom - container.clientHeight + padding;
        }
    }
    
    // Get report count for a node
    getReportCount(nodeId) {
        return this.connections.filter(c => c.from === nodeId && c.direction === 'bottom').length;
    }
    
    // Show shortcuts modal
    showShortcutsModal() {
        this.elements.shortcutsModal?.classList.add('active');
    }
    
    closeShortcutsModal() {
        this.elements.shortcutsModal?.classList.remove('active');
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.app = new OrgChartApp();
});
