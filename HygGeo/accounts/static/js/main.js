/**
 * HygGeo - Main JavaScript Functions
 * Combining Danish Hygge with Sustainable Travel
 */

// Global namespace for HygGeo
const HygGeo = {
    init: function() {
        this.initAnimations();
        this.initInteractions();
        this.initAccessibility();
        this.initUtils();
    },

    // Initialize scroll-based animations
    initAnimations: function() {
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    
                    // Add staggered animation for child elements
                    const children = entry.target.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .scale-in');
                    children.forEach((child, index) => {
                        setTimeout(() => {
                            child.classList.add('visible');
                        }, index * 100);
                    });
                }
            });
        }, observerOptions);

        // Observe elements with animation classes
        document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .scale-in').forEach(el => {
            observer.observe(el);
        });

        // Observe all cards for entrance animations
        document.querySelectorAll('.card-hygge').forEach(card => {
            if (!card.classList.contains('fade-in')) {
                card.classList.add('fade-in');
            }
            observer.observe(card);
        });
    },

    // Initialize interactive elements
    initInteractions: function() {
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Enhanced form interactions
        this.initFormEnhancements();

        // Button loading states
        this.initButtonStates();

        // Card hover effects
        this.initCardEffects();

        // Navigation enhancements
        this.initNavigationEnhancements();
    },

    // Form enhancements
    initFormEnhancements: function() {
        // Auto-resize textareas
        document.querySelectorAll('textarea').forEach(textarea => {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
        });

        // Form validation feedback
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('loading');
                    submitBtn.disabled = true;
                    
                    // Add loading spinner
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>' + submitBtn.textContent;
                    
                    // Reset after 3 seconds if form doesn't redirect
                    setTimeout(() => {
                        if (submitBtn) {
                            submitBtn.classList.remove('loading');
                            submitBtn.disabled = false;
                            submitBtn.innerHTML = originalText;
                        }
                    }, 3000);
                }
            });
        });

        // Real-time form validation
        document.querySelectorAll('input[required], textarea[required]').forEach(input => {
            input.addEventListener('blur', function() {
                this.classList.toggle('is-valid', this.value.trim() !== '');
                this.classList.toggle('is-invalid', this.value.trim() === '');
            });

            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') && this.value.trim() !== '') {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });

        // Password strength indicator
        document.querySelectorAll('input[type="password"]').forEach(input => {
            if (input.name.includes('password1')) {
                input.addEventListener('input', this.showPasswordStrength);
            }
        });
    },

    // Password strength indicator
    showPasswordStrength: function(e) {
        const password = e.target.value;
        const strength = HygGeo.calculatePasswordStrength(password);
        
        let indicator = e.target.parentNode.querySelector('.password-strength');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'password-strength mt-2';
            e.target.parentNode.appendChild(indicator);
        }
        
        const colors = ['#dc3545', '#fd7e14', '#ffc107', '#28a745'];
        const labels = ['Weak', 'Fair', 'Good', 'Strong'];
        
        indicator.innerHTML = `
            <div class="progress" style="height: 4px;">
                <div class="progress-bar" style="width: ${strength * 25}%; background-color: ${colors[strength - 1] || colors[0]};"></div>
            </div>
            <small class="text-muted">${labels[strength - 1] || 'Too short'}</small>
        `;
    },

    // Calculate password strength
    calculatePasswordStrength: function(password) {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^a-zA-Z\d]/.test(password)) strength++;
        return strength;
    },

    // Button loading states
    initButtonStates: function() {
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                if (this.dataset.loading !== 'false') {
                    this.classList.add('loading');
                    
                    setTimeout(() => {
                        this.classList.remove('loading');
                    }, 2000);
                }
            });
        });
    },

    // Card hover effects
    initCardEffects: function() {
        document.querySelectorAll('.card-hygge').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-8px) scale(1.02)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    },

    // Navigation enhancements
    initNavigationEnhancements: function() {
        // Active page highlighting
        const currentPath = window.location.pathname;
        document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });

        // Mobile menu auto-close
        document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
            link.addEventListener('click', () => {
                const navbarCollapse = document.querySelector('.navbar-collapse');
                if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                    const toggleBtn = document.querySelector('.navbar-toggler');
                    if (toggleBtn) toggleBtn.click();
                }
            });
        });

        // Scroll-based navbar styling
        let lastScrollY = window.scrollY;
        window.addEventListener('scroll', () => {
            const navbar = document.querySelector('.navbar');
            if (navbar) {
                if (window.scrollY > 100) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }

                // Hide/show navbar on scroll
                if (window.scrollY > lastScrollY && window.scrollY > 200) {
                    navbar.style.transform = 'translateY(-100%)';
                } else {
                    navbar.style.transform = 'translateY(0)';
                }
                lastScrollY = window.scrollY;
            }
        });
    },

    // Accessibility improvements
    initAccessibility: function() {
        // Keyboard navigation for custom checkboxes
        document.querySelectorAll('.custom-checkbox input').forEach(input => {
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.checked = !this.checked;
                    this.dispatchEvent(new Event('change'));
                }
            });
        });

        // Focus management for modals and dropdowns
        document.querySelectorAll('[data-bs-toggle="modal"]').forEach(trigger => {
            trigger.addEventListener('click', function() {
                setTimeout(() => {
                    const modal = document.querySelector('.modal.show');
                    if (modal) {
                        const focusable = modal.querySelector('input, button, textarea, select');
                        if (focusable) focusable.focus();
                    }
                }, 150);
            });
        });

        // Announce dynamic content changes to screen readers
        this.createAriaLiveRegion();
    },

    // Create ARIA live region for announcements
    createAriaLiveRegion: function() {
        if (!document.getElementById('aria-live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'aria-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
    },

    // Announce message to screen readers
    announce: function(message) {
        const liveRegion = document.getElementById('aria-live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    },

    // Utility functions
    initUtils: function() {
        // Lazy loading for images
        this.initLazyLoading();

        // Local storage helpers
        this.initLocalStorage();

        // Performance monitoring
        this.initPerformanceMonitoring();
    },

    // Lazy loading for images
    initLazyLoading: function() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    },

    // Local storage helpers (with fallback)
    initLocalStorage: function() {
        this.storage = {
            set: function(key, value) {
                try {
                    localStorage.setItem(key, JSON.stringify(value));
                } catch (e) {
                    console.warn('Local storage not available:', e);
                }
            },
            get: function(key) {
                try {
                    const item = localStorage.getItem(key);
                    return item ? JSON.parse(item) : null;
                } catch (e) {
                    console.warn('Local storage not available:', e);
                    return null;
                }
            },
            remove: function(key) {
                try {
                    localStorage.removeItem(key);
                } catch (e) {
                    console.warn('Local storage not available:', e);
                }
            }
        };
    },

    // Performance monitoring
    initPerformanceMonitoring: function() {
        // Monitor Core Web Vitals
        if ('PerformanceObserver' in window) {
            // Largest Contentful Paint
            new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                console.log('LCP:', lastEntry.startTime);
            }).observe({ entryTypes: ['largest-contentful-paint'] });

            // First Input Delay
            new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    console.log('FID:', entry.processingStart - entry.startTime);
                });
            }).observe({ entryTypes: ['first-input'] });
        }
    },

    // Survey-specific functionality
    survey: {
        updateProgress: function() {
            const sections = document.querySelectorAll('[data-section]');
            const progressBar = document.getElementById('progressBar');
            if (!progressBar) return;

            let completedSections = 0;
            
            sections.forEach(section => {
                const checkboxes = section.querySelectorAll('input[type="checkbox"]:checked');
                const radios = section.querySelectorAll('input[type="radio"]:checked');
                const textInputs = section.querySelectorAll('input[type="text"], textarea');
                
                let hasValue = checkboxes.length > 0 || radios.length > 0;
                
                if (!hasValue) {
                    textInputs.forEach(input => {
                        if (input.value.trim() !== '') {
                            hasValue = true;
                        }
                    });
                }
                
                if (hasValue) completedSections++;
            });
            
            const progress = Math.round((completedSections / sections.length) * 100);
            progressBar.style.width = progress + '%';
            progressBar.setAttribute('aria-valuenow', progress);
            
            // Announce progress to screen readers
            if (progress === 100) {
                HygGeo.announce('Survey completed! Ready to submit.');
            }
        },

        validateSection: function(sectionElement) {
            const requiredGroups = sectionElement.querySelectorAll('[data-required]');
            let isValid = true;

            requiredGroups.forEach(group => {
                const checked = group.querySelectorAll('input:checked');
                if (checked.length === 0) {
                    isValid = false;
                    group.classList.add('has-error');
                } else {
                    group.classList.remove('has-error');
                }
            });

            return isValid;
        }
    },

    // Profile functionality
    profile: {
        initImageUpload: function() {
            const fileInput = document.querySelector('input[type="file"][accept*="image"]');
            if (fileInput) {
                fileInput.addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file && file.type.startsWith('image/')) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const preview = document.querySelector('.profile-image-preview');
                            if (preview) {
                                preview.src = e.target.result;
                            }
                        };
                        reader.readAsDataURL(file);
                    }
                });
            }
        }
    },

    // Utility methods
    utils: {
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

        throttle: function(func, limit) {
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
        },

        formatDate: function(date) {
            return new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            }).format(date);
        },

        showToast: function(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            toast.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, 5000);
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    HygGeo.init();
    
    // Page-specific initializations
    if (document.querySelector('.survey-form')) {
        // Survey page specific code
        const surveyInputs = document.querySelectorAll('#surveyForm input, #surveyForm textarea');
        surveyInputs.forEach(input => {
            input.addEventListener('change', HygGeo.survey.updateProgress);
            input.addEventListener('input', HygGeo.utils.debounce(HygGeo.survey.updateProgress, 300));
        });
        
        // Initial progress calculation
        HygGeo.survey.updateProgress();
    }
    
    if (document.querySelector('.profile-page')) {
        // Profile page specific code
        HygGeo.profile.initImageUpload();
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden - pause any animations or timers
        document.body.classList.add('page-hidden');
    } else {
        // Page is visible - resume activities
        document.body.classList.remove('page-hidden');
    }
});

// Export for global access
window.HygGeo = HygGeo;