/**
 * HygGeo Task Management - Enhanced UI JavaScript
 * Provides reusable utilities, animations, and interactions
 */

// ==================== Toast Notification System ====================
class ToastManager {
    constructor() {
        this.container = this.createContainer();
        this.queue = [];
        this.maxToasts = 3;
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                bottom: 30px;
                right: 30px;
                z-index: 9999;
                display: flex;
                flex-direction: column-reverse;
                gap: 15px;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'success', duration = 3000) {
        // Remove oldest toast if at max capacity
        if (this.container.children.length >= this.maxToasts) {
            this.container.firstChild?.remove();
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const colors = {
            success: 'var(--hygge-green)',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };

        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 15px;">
                <i class="fas ${icons[type]}" style="font-size: 1.5rem;"></i>
                <span style="flex: 1;">${message}</span>
                <button class="toast-close" style="background: none; border: none; color: white; cursor: pointer; font-size: 1.2rem; padding: 0; margin-left: 10px;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="toast-progress"></div>
        `;

        toast.style.cssText = `
            background: ${colors[type]};
            color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
            font-weight: 600;
            font-size: 1rem;
            min-width: 300px;
            position: relative;
            overflow: hidden;
            animation: slideInRight 0.3s ease;
            backdrop-filter: blur(10px);
        `;

        // Add progress bar
        const progressBar = toast.querySelector('.toast-progress');
        progressBar.style.cssText = `
            position: absolute;
            bottom: 0;
            left: 0;
            height: 4px;
            background: rgba(255,255,255,0.5);
            width: 100%;
            animation: toastProgress ${duration}ms linear;
        `;

        // Close button functionality
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.remove(toast));

        this.container.appendChild(toast);

        // Auto remove after duration
        setTimeout(() => this.remove(toast), duration);
    }

    remove(toast) {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }

    success(message, duration) {
        this.show(message, 'success', duration);
    }

    error(message, duration) {
        this.show(message, 'error', duration);
    }

    warning(message, duration) {
        this.show(message, 'warning', duration);
    }

    info(message, duration) {
        this.show(message, 'info', duration);
    }
}

// Global toast instance
window.toast = new ToastManager();

// ==================== Loading State System ====================
class LoadingManager {
    constructor() {
        this.overlay = null;
    }

    createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-circle"></div>
                <div class="loading-text">Loading...</div>
            </div>
        `;
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(248, 250, 252, 0.95);
            backdrop-filter: blur(8px);
            z-index: 9998;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.2s ease;
        `;
        return overlay;
    }

    show(text = 'Loading...') {
        if (this.overlay) return;

        this.overlay = this.createOverlay();
        if (text) {
            this.overlay.querySelector('.loading-text').textContent = text;
        }
        document.body.appendChild(this.overlay);
        document.body.style.overflow = 'hidden';
    }

    hide() {
        if (!this.overlay) return;

        this.overlay.style.animation = 'fadeOut 0.2s ease';
        setTimeout(() => {
            this.overlay?.remove();
            this.overlay = null;
            document.body.style.overflow = '';
        }, 200);
    }

    // Show loading on specific element
    showOnElement(element, size = 'medium') {
        const existingLoader = element.querySelector('.element-loader');
        if (existingLoader) return;

        const loader = document.createElement('div');
        loader.className = 'element-loader';

        const sizes = {
            small: '30px',
            medium: '50px',
            large: '70px'
        };

        loader.innerHTML = `
            <div class="spinner-circle" style="width: ${sizes[size]}; height: ${sizes[size]};"></div>
        `;

        loader.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: inherit;
            z-index: 10;
        `;

        element.style.position = 'relative';
        element.appendChild(loader);
    }

    hideOnElement(element) {
        const loader = element.querySelector('.element-loader');
        if (loader) {
            loader.style.animation = 'fadeOut 0.2s ease';
            setTimeout(() => loader.remove(), 200);
        }
    }
}

// Global loading manager instance
window.loading = new LoadingManager();

// ==================== Skeleton Screen System ====================
function showSkeleton(container, type = 'list', count = 3) {
    const skeletonHTML = {
        list: `
            <div class="skeleton-item" style="background: white; border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <div class="skeleton-line" style="width: 60%; height: 24px; margin-bottom: 15px;"></div>
                <div class="skeleton-line" style="width: 100%; height: 16px; margin-bottom: 10px;"></div>
                <div class="skeleton-line" style="width: 80%; height: 16px;"></div>
            </div>
        `,
        card: `
            <div class="skeleton-item" style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <div class="skeleton-circle" style="width: 60px; height: 60px; margin: 0 auto 20px;"></div>
                <div class="skeleton-line" style="width: 80%; height: 20px; margin: 0 auto 15px;"></div>
                <div class="skeleton-line" style="width: 60%; height: 16px; margin: 0 auto;"></div>
            </div>
        `,
        table: `
            <div class="skeleton-item" style="background: white; border-radius: 15px; padding: 20px; margin-bottom: 15px;">
                <div style="display: grid; grid-template-columns: 1fr 2fr 1fr 1fr; gap: 20px;">
                    <div class="skeleton-line" style="height: 16px;"></div>
                    <div class="skeleton-line" style="height: 16px;"></div>
                    <div class="skeleton-line" style="height: 16px;"></div>
                    <div class="skeleton-line" style="height: 16px;"></div>
                </div>
            </div>
        `
    };

    let html = '';
    for (let i = 0; i < count; i++) {
        html += skeletonHTML[type] || skeletonHTML.list;
    }

    container.innerHTML = `<div class="skeleton-container">${html}</div>`;
}

// ==================== Keyboard Shortcuts ====================
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in inputs
            if (e.target.matches('input, textarea, select')) return;

            const key = this.getKeyCombo(e);
            const handler = this.shortcuts.get(key);

            if (handler) {
                e.preventDefault();
                handler(e);
            }
        });

        // Register default shortcuts
        this.registerDefaults();
    }

    getKeyCombo(e) {
        const parts = [];
        if (e.ctrlKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        parts.push(e.key.toLowerCase());
        return parts.join('+');
    }

    register(keyCombo, handler, description) {
        this.shortcuts.set(keyCombo.toLowerCase(), handler);
    }

    registerDefaults() {
        // Ctrl+K: Focus search
        this.register('ctrl+k', () => {
            const searchInput = document.querySelector('input[type="text"][name="search"], input[type="search"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
                toast.info('Search focused - Start typing');
            }
        });

        // N: New task (when not in input)
        this.register('n', () => {
            const createBtn = document.querySelector('a[href*="task_create"]');
            if (createBtn) {
                window.location.href = createBtn.href;
            }
        });

        // D: Go to dashboard
        this.register('d', () => {
            const dashboardLink = document.querySelector('a[href*="dashboard"]');
            if (dashboardLink) {
                window.location.href = dashboardLink.href;
            }
        });

        // K: Go to kanban
        this.register('k', () => {
            const kanbanLink = document.querySelector('a[href*="kanban"]');
            if (kanbanLink) {
                window.location.href = kanbanLink.href;
            }
        });

        // Escape: Close modals/overlays
        this.register('escape', () => {
            loading.hide();
        });

        // ?: Show shortcuts help
        this.register('shift+/', () => {
            this.showHelp();
        });
    }

    showHelp() {
        const shortcuts = [
            { key: 'Ctrl+K', description: 'Focus search' },
            { key: 'N', description: 'Create new task' },
            { key: 'D', description: 'Go to dashboard' },
            { key: 'K', description: 'Go to kanban board' },
            { key: 'Esc', description: 'Close overlays' },
            { key: '?', description: 'Show this help' }
        ];

        const helpHTML = `
            <div class="shortcuts-help-overlay" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 10000; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.2s ease;">
                <div class="shortcuts-help-content" style="background: white; border-radius: 20px; padding: 40px; max-width: 500px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                    <h2 style="color: var(--hygge-green); margin-bottom: 30px; display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-keyboard"></i>
                        Keyboard Shortcuts
                    </h2>
                    <div class="shortcuts-list" style="display: grid; gap: 15px;">
                        ${shortcuts.map(s => `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #f8fafc; border-radius: 10px;">
                                <span style="font-weight: 600; color: #64748b;">${s.description}</span>
                                <kbd style="background: white; padding: 6px 12px; border-radius: 6px; border: 2px solid #e2e8f0; font-weight: 700; color: var(--hygge-green);">${s.key}</kbd>
                            </div>
                        `).join('')}
                    </div>
                    <button class="btn btn-hygge w-100 mt-4" onclick="this.closest('.shortcuts-help-overlay').remove()">
                        <i class="fas fa-times me-2"></i>Close
                    </button>
                </div>
            </div>
        `;

        const existing = document.querySelector('.shortcuts-help-overlay');
        if (existing) {
            existing.remove();
        } else {
            document.body.insertAdjacentHTML('beforeend', helpHTML);
        }
    }
}

// Initialize keyboard shortcuts
const keyboard = new KeyboardShortcuts();

// ==================== Smooth Scroll ====================
function smoothScrollTo(element, offset = 100) {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;

    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

// ==================== Form Validation Enhancement ====================
function enhanceFormValidation(form) {
    const inputs = form.querySelectorAll('input, textarea, select');

    inputs.forEach(input => {
        // Add visual feedback on validation
        input.addEventListener('invalid', (e) => {
            e.preventDefault();
            input.classList.add('is-invalid');

            // Create error message if doesn't exist
            let errorMsg = input.nextElementSibling;
            if (!errorMsg || !errorMsg.classList.contains('invalid-feedback')) {
                errorMsg = document.createElement('div');
                errorMsg.className = 'invalid-feedback';
                input.after(errorMsg);
            }

            errorMsg.textContent = input.validationMessage;
            errorMsg.style.display = 'block';

            // Shake animation
            input.style.animation = 'shake 0.4s ease';
            setTimeout(() => {
                input.style.animation = '';
            }, 400);
        });

        input.addEventListener('input', () => {
            if (input.classList.contains('is-invalid') && input.checkValidity()) {
                input.classList.remove('is-invalid');
                const errorMsg = input.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('invalid-feedback')) {
                    errorMsg.style.display = 'none';
                }
            }
        });
    });
}

// ==================== CSRF Token Helper ====================
function getCsrfToken() {
    // Try cookie first
    let csrfToken = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith('csrftoken=')) {
                csrfToken = decodeURIComponent(cookie.substring('csrftoken='.length));
                break;
            }
        }
    }

    // Fallback to form input
    if (!csrfToken) {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            csrfToken = csrfInput.value;
        }
    }

    // Fallback to meta tag
    if (!csrfToken) {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            csrfToken = csrfMeta.getAttribute('content');
        }
    }

    return csrfToken;
}

// ==================== Debounce Utility ====================
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

// ==================== Initialize on DOM Ready ====================
document.addEventListener('DOMContentLoaded', function() {
    // Add global styles
    const style = document.createElement('style');
    style.textContent = `
        /* Animations */
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }

        @keyframes toastProgress {
            from { width: 100%; }
            to { width: 0%; }
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
            20%, 40%, 60%, 80% { transform: translateX(10px); }
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Spinner */
        .spinner-circle {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(45, 90, 61, 0.2);
            border-top-color: var(--hygge-green);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        .loading-spinner {
            text-align: center;
        }

        .loading-text {
            margin-top: 20px;
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--hygge-green);
        }

        /* Skeleton Screens */
        .skeleton-line {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: pulse 1.5s ease-in-out infinite;
            border-radius: 8px;
        }

        .skeleton-circle {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: pulse 1.5s ease-in-out infinite;
            border-radius: 50%;
        }

        /* Focus States for Accessibility */
        *:focus-visible {
            outline: 3px solid var(--hygge-green);
            outline-offset: 2px;
            border-radius: 4px;
        }

        /* Smooth transitions for all interactive elements */
        button, a, input, select, textarea, .card, .task-item, .project-card {
            transition: all 0.3s ease;
        }

        /* Mobile responsive toast */
        @media (max-width: 768px) {
            #toast-container {
                bottom: 20px;
                right: 20px;
                left: 20px;
                max-width: 100%;
            }

            .toast {
                min-width: 100% !important;
            }
        }
    `;
    document.head.appendChild(style);

    // Enhance all forms
    document.querySelectorAll('form').forEach(form => {
        enhanceFormValidation(form);
    });

    // Add smooth scroll to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    smoothScrollTo(target);
                }
            }
        });
    });

    // Show page load complete
    console.log('%c✓ Task Management UI Enhanced', 'color: #2d5a3d; font-weight: bold; font-size: 14px;');
    console.log('%cKeyboard shortcuts available! Press ? to see them.', 'color: #64748b; font-style: italic;');
});

// Export for use in other scripts
window.TaskManagement = {
    toast,
    loading,
    showSkeleton,
    smoothScrollTo,
    getCsrfToken,
    debounce
};
