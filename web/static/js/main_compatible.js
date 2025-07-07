// main.js - Compatible JavaScript for WordPress Engineer GUI (Alpine.js compatible)

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

// Global app state (non-conflicting)
window.WordPressEngineer = {
    currentProject: null,
    stats: {
        linesOfCode: 24500,
        projects: 12,
        plugins: 8,
        themes: 5
    },
    
    // Utility functions
    utils: {
        // Debounce function for performance
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Format file size
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        // Format date/time
        formatDateTime: function(date) {
            return new Date(date).toLocaleString();
        },
        
        // Copy to clipboard
        copyToClipboard: function(text) {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(text);
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                return new Promise((resolve, reject) => {
                    document.execCommand('copy') ? resolve() : reject();
                    textArea.remove();
                });
            }
        }
    },
    
    // API helpers
    api: {
        // Generic API call with error handling
        call: async function(url, options = {}) {
            try {
                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API call failed:', error);
                throw error;
            }
        },
        
        // Specific API methods
        generatePlugin: function(data) {
            return this.call('/api/generate/plugin', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        
        generateTheme: function(data) {
            return this.call('/api/generate/theme', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        
        validateCode: function(data) {
            return this.call('/api/code/validate', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        
        securityScan: function(data) {
            return this.call('/api/security/scan', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }
    }
};

// Keyboard shortcuts (global, non-interfering)
document.addEventListener('keydown', function(e) {
    // Only add shortcuts that don't interfere with Alpine.js
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 'k':
                // Quick search (if implemented)
                e.preventDefault();
                console.log('Quick search shortcut triggered');
                break;
            case '/':
                // Help shortcut
                e.preventDefault();
                console.log('Help shortcut triggered');
                break;
        }
    }
});

// Initialize non-conflicting features
document.addEventListener('DOMContentLoaded', function() {
    console.log('WordPress Engineer utilities loaded (Alpine.js compatible)');
    
    // Initialize any global features that don't manipulate DOM directly
    initializeCharts();
});

// Chart initialization (only if elements exist)
function initializeCharts() {
    // Only initialize charts if Chart.js is available and elements exist
    if (typeof Chart !== 'undefined') {
        // Activity Chart
        const activityCtx = document.getElementById('activityChart');
        if (activityCtx) {
            new Chart(activityCtx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Activity',
                        data: [12, 19, 3, 5, 2, 3, 20],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
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
                    labels: ['PHP', 'JavaScript', 'CSS', 'HTML'],
                    datasets: [{
                        data: [45, 25, 15, 15],
                        backgroundColor: [
                            'rgb(59, 130, 246)',
                            'rgb(16, 185, 129)',
                            'rgb(245, 158, 11)',
                            'rgb(239, 68, 68)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }
}

// Export utilities for use in Alpine.js components
window.WPUtils = window.WordPressEngineer.utils;
window.WPApi = window.WordPressEngineer.api;
