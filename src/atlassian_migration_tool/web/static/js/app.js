/**
 * Jira Migration Tool - Web GUI Application JavaScript
 *
 * This file contains shared utilities and Alpine.js stores.
 */

// Global app store for Alpine.js
document.addEventListener('alpine:init', () => {
    Alpine.store('app', {
        toasts: [],
        toastCounter: 0,

        addToast(message, type = 'info', duration = 5000) {
            const id = ++this.toastCounter;
            this.toasts.push({ id, message, type, visible: true });

            if (duration > 0) {
                setTimeout(() => this.removeToast(id), duration);
            }

            return id;
        },

        removeToast(id) {
            const toast = this.toasts.find(t => t.id === id);
            if (toast) {
                toast.visible = false;
                setTimeout(() => {
                    this.toasts = this.toasts.filter(t => t.id !== id);
                }, 300);
            }
        }
    });
});

// Utility functions
const Utils = {
    /**
     * Format a date string for display
     */
    formatDate(dateStr) {
        if (!dateStr) return '-';
        try {
            return new Date(dateStr).toLocaleString();
        } catch {
            return dateStr;
        }
    },

    /**
     * Format bytes to human readable string
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Debounce function calls
     */
    debounce(func, wait) {
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

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            Alpine.store('app')?.addToast('Copied to clipboard', 'success', 2000);
            return true;
        } catch (err) {
            console.error('Failed to copy:', err);
            return false;
        }
    }
};

// Make utilities available globally
window.Utils = Utils;

// HTMX event handlers
document.body.addEventListener('htmx:responseError', function(event) {
    const xhr = event.detail.xhr;
    let message = 'Request failed';

    try {
        const response = JSON.parse(xhr.responseText);
        message = response.error || response.detail || message;
    } catch {
        message = xhr.statusText || message;
    }

    Alpine.store('app')?.addToast(message, 'error');
});

document.body.addEventListener('htmx:sendError', function(event) {
    Alpine.store('app')?.addToast('Network error. Please check your connection.', 'error');
});

// Console welcome message
console.log('%cJira Migration Tool', 'font-size: 20px; font-weight: bold; color: #3b82f6;');
console.log('Web GUI v0.1.0');
console.log('API docs available at /docs');
