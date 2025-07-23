// main.js - Enhanced JavaScript for WordPress Engineer GUI

// Global error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript Error:', event.error);
    console.error('Error details:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
    });
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled Promise Rejection:', event.reason);
});

// Global app state
window.WordPressEngineer = {
    currentProject: null,
    darkMode: localStorage.getItem('darkMode') === 'true',
    notifications: [],
    activeConnections: 0
};

// Initialize the application
document.addEventListener("DOMContentLoaded", function() {
    console.log("WordPress Engineer GUI loaded.");
    
    try {
        // Initialize components
        initializeRealtimeUpdates();
        initializeKeyboardShortcuts();
        initializeTooltips();
        initializeProgressTracking();
        initializeCodeEditor();
        // initializeFileManager(); // Handled by Alpine.js appData
        // initializeTerminal();   // Handled by Alpine.js appData
        
        // Start real-time data updates
        startRealtimeUpdates();
        
        // Initialize charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            initializeCharts();
        } else {
            console.warn("Chart.js not loaded - charts will not be available");
        }
        
        console.log("WordPress Engineer GUI initialized successfully");
        
    } catch (error) {
        console.error("Error initializing WordPress Engineer GUI:", error);
        // Show user-friendly error message
        if (window.WordPressEngineer && window.WordPressEngineer.showNotification) {
            window.WordPressEngineer.showNotification("Initialization error. Check console for details.", "error");
        } else {
            alert("An error occurred during initialization. Check console for details.");
        }
    }
});

// Real-time Updates
function initializeRealtimeUpdates() {
    // Simulate real-time connection
    window.WordPressEngineer.connection = {
        status: 'connected',
        lastUpdate: new Date(),
        reconnectAttempts: 0
    };
}

function startRealtimeUpdates() {
    // Update connection status indicator
    setInterval(() => {
        updateConnectionStatus();
        // updateStats(); // Stats are now loaded via API in appData
    }, 5000);
    
    // Simulate incoming notifications
    setTimeout(() => {
        window.WordPressEngineer.showNotification('Welcome to WordPress Engineer!', 'success');
    }, 1000);
}

function updateConnectionStatus() {
    const statusElement = document.querySelector('.connection-status');
    if (statusElement) {
        statusElement.className = 'connection-status w-3 h-3 rounded-full status-online';
    }
}

// updateStats removed as it's now handled by appData.analytics.loadAnalytics()

function animateCounter(element, target) {
    const start = parseInt(element.textContent.replace(/,/g, '')) || 0;
    const increment = (target - start) / 20;
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current).toLocaleString();
    }, 50);
}

// Keyboard Shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openQuickSearch();
        }
        
        // Ctrl/Cmd + / for help
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showKeyboardShortcuts();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            closeModals();
        }
    });
}

function openQuickSearch() {
    window.WordPressEngineer.showNotification('Quick search (Ctrl+K)', 'info', 2000);
    // Implementation for quick search modal
}

function showKeyboardShortcuts() {
    const shortcuts = [
        'Ctrl+K - Quick Search',
        'Ctrl+/ - Show Shortcuts',
        'Esc - Close Modal',
        'Ctrl+N - New Project',
        'Ctrl+S - Save Current'
    ];
    
    window.WordPressEngineer.showNotification(
        `Keyboard Shortcuts:<br>${shortcuts.join('<br>')}`, 
        'info', 
        8000
    );
}

function closeModals() {
    // Close any open modals or overlays
    const modals = document.querySelectorAll('.modal-overlay');
    modals.forEach(modal => modal.remove());
}

// Tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip-popup absolute z-50 px-2 py-1 text-sm bg-gray-900 text-white rounded shadow-lg pointer-events-none';
    tooltip.textContent = e.target.getAttribute('data-tooltip');
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    
    e.target._tooltip = tooltip;
}

function hideTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        delete e.target._tooltip;
    }
}

// Progress Tracking
function initializeProgressTracking() {
    window.WordPressEngineer.trackProgress = function(operation, progress) {
        const progressBar = document.querySelector('.global-progress');
        if (progressBar) {
            progressBar.style.width = progress + '%';
            if (progress >= 100) {
                setTimeout(() => {
                    progressBar.style.width = '0%';
                }, 1000);
            }
        }
    };
}

// Code Editor Enhancement
function initializeCodeEditor() {
    // Syntax highlighting for code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        highlightSyntax(block);
    });
    
    // Auto-save functionality
    const textareas = document.querySelectorAll('textarea[data-autosave]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', debounce(autoSave, 1000));
    });
}

function highlightSyntax(element) {
    // Basic PHP syntax highlighting
    let content = element.innerHTML;
    
    // Keywords
    content = content.replace(/\b(class|function|public|private|protected|if|else|foreach|while|for|return|echo|print|var|const)\b/g, 
        '<span class="text-purple-400">$1</span>');
    
    // Strings
    content = content.replace(/(["'])((?:\\.|[^\\])*?)\1/g, 
        '<span class="text-green-400">$1$2$1</span>');
    
    // Comments
    content = content.replace(/(\/\/.*$|\/\*[\s\S]*?\*\/)/gm, 
        '<span class="text-gray-500">$1</span>');
    
    // Variables
    content = content.replace(/(\$\w+)/g, 
        '<span class="text-blue-400">$1</span>');
    
    element.innerHTML = content;
}

function autoSave(element) {
    const content = element.value;
    const key = element.getAttribute('data-autosave');
    localStorage.setItem(`autosave_${key}`, content);
    
    // Show save indicator
    const indicator = document.createElement('span');
    indicator.className = 'text-green-500 text-sm';
    indicator.textContent = ' ✓ Saved';
    element.parentNode.appendChild(indicator);
    
    setTimeout(() => indicator.remove(), 2000);
}

// File Manager (Simulated functions removed, now handled by appData.fileManager)
// initializeFileManager removed

// Terminal Emulator (Simulated functions removed, now handled by appData)
// initializeTerminal removed

// Chart Initialization
function initializeCharts() {
    // Set global chart defaults
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.plugins.legend.display = false;
    
    // Activity Chart
    const activityCtx = document.getElementById('activityChart');
    if (activityCtx) {
        new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Lines of Code',
                    data: [120, 190, 300, 500, 200, 300, 450],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true },
                    x: { grid: { display: false } }
                },
                elements: {
                    point: { radius: 4, hoverRadius: 8 }
                }
            }
        });
    }

    // Performance Chart
    const performanceCtx = document.getElementById('performanceChart');
    if (performanceCtx) {
        new Chart(performanceCtx, {
            type: 'doughnut',
            data: {
                labels: ['Loading Time', 'Database Queries', 'Memory Usage', 'Optimization'],
                datasets: [{
                    data: [30, 25, 20, 25],
                    backgroundColor: ['#ef4444', '#f59e0b', '#22c55e', '#3b82f6'],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { usePointStyle: true, padding: 20 }
                    }
                }
            }
        });
    }
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Project Management Functions (Simulated functions removed, now handled by appData)
// window.WordPressEngineer.createProject removed
// window.WordPressEngineer.generateCode removed

// Error Handling
window.addEventListener('error', function(e) {
    console.error('WordPress Engineer Error:', e.error);
    window.WordPressEngineer.showNotification('An error occurred. Check console for details.', 'error');
});

// Performance Monitoring
window.addEventListener('load', function() {
    const loadTime = performance.now();
    console.log(`WordPress Engineer loaded in ${loadTime.toFixed(2)}ms`);
    
    if (loadTime > 3000) {
        window.WordPressEngineer.showNotification('Slow loading detected. Consider optimizing.', 'warning');
    }
});

// Service Worker Registration (for offline support)
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/sw.js')
        .then(registration => {
            console.log('Service Worker registered:', registration);
        })
        .catch(error => {
            console.log('Service Worker registration failed:', error);
        });
}

console.log("WordPress Engineer Enhanced GUI loaded with full features.");
