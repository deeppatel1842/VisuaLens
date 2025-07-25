/**
 * VisuaLens Utility Functions
 * Helper functions for common tasks and UI enhancements
 */

// Loading spinner utility
class LoadingSpinner {
    static create(size = 'medium') {
        const spinner = document.createElement('div');
        spinner.className = `loading-spinner ${size}`;
        spinner.innerHTML = `
            <div class="spinner-ring"></div>
        `;
        return spinner;
    }
    
    static show(element, text = 'Loading...') {
        const spinner = this.create();
        const container = document.createElement('div');
        container.className = 'loading-container';
        container.innerHTML = `
            ${spinner.outerHTML}
            <span class="loading-text">${text}</span>
        `;
        
        element.appendChild(container);
        return container;
    }
    
    static hide(element) {
        const loader = element.querySelector('.loading-container');
        if (loader) {
            loader.remove();
        }
    }
}

// Image processing utilities
class ImageUtils {
    static async resizeImage(file, maxWidth = 1024, maxHeight = 1024, quality = 0.8) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            img.onload = () => {
                let { width, height } = img;
                
                // Calculate new dimensions
                if (width > height) {
                    if (width > maxWidth) {
                        height = (height * maxWidth) / width;
                        width = maxWidth;
                    }
                } else {
                    if (height > maxHeight) {
                        width = (width * maxHeight) / height;
                        height = maxHeight;
                    }
                }
                
                canvas.width = width;
                canvas.height = height;
                
                // Draw and compress
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob(resolve, file.type, quality);
            };
            
            img.src = URL.createObjectURL(file);
        });
    }
    
    static getImageDimensions(file) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                resolve({
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    aspectRatio: img.naturalWidth / img.naturalHeight
                });
            };
            img.src = URL.createObjectURL(file);
        });
    }
    
    static async extractImageMetadata(file) {
        const dimensions = await this.getImageDimensions(file);
        
        return {
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: new Date(file.lastModified),
            dimensions,
            isLandscape: dimensions.aspectRatio > 1,
            isPortrait: dimensions.aspectRatio < 1,
            isSquare: Math.abs(dimensions.aspectRatio - 1) < 0.1
        };
    }
}

// API error handling
class APIError extends Error {
    constructor(message, status, code) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.code = code;
    }
}

class APIClient {
    constructor(baseUrl, options = {}) {
        this.baseUrl = baseUrl;
        this.timeout = options.timeout || 30000;
        this.retries = options.retries || 2;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            timeout: this.timeout,
            ...options
        };
        
        for (let attempt = 0; attempt <= this.retries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);
                
                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new APIError(
                        errorData.detail || `HTTP ${response.status}`,
                        response.status,
                        errorData.code
                    );
                }
                
                return response;
            } catch (error) {
                if (attempt === this.retries) {
                    throw error;
                }
                
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
            }
        }
    }
    
    async get(endpoint, params = {}) {
        const url = new URL(endpoint, this.baseUrl);
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return this.request(url.pathname + url.search);
    }
    
    async post(endpoint, data, options = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: data,
            ...options
        });
    }
}

// Form validation utilities
class FormValidator {
    constructor(form) {
        this.form = form;
        this.errors = {};
        this.rules = {};
    }
    
    addRule(fieldName, validator, message) {
        if (!this.rules[fieldName]) {
            this.rules[fieldName] = [];
        }
        this.rules[fieldName].push({ validator, message });
        return this;
    }
    
    required(fieldName, message = 'This field is required') {
        return this.addRule(fieldName, (value) => value && value.trim() !== '', message);
    }
    
    minLength(fieldName, length, message) {
        return this.addRule(
            fieldName,
            (value) => !value || value.length >= length,
            message || `Minimum ${length} characters required`
        );
    }
    
    maxLength(fieldName, length, message) {
        return this.addRule(
            fieldName,
            (value) => !value || value.length <= length,
            message || `Maximum ${length} characters allowed`
        );
    }
    
    fileType(fieldName, types, message) {
        return this.addRule(
            fieldName,
            (file) => !file || types.includes(file.type),
            message || `Invalid file type. Allowed: ${types.join(', ')}`
        );
    }
    
    fileSize(fieldName, maxSize, message) {
        return this.addRule(
            fieldName,
            (file) => !file || file.size <= maxSize,
            message || `File size too large. Maximum: ${this.formatFileSize(maxSize)}`
        );
    }
    
    validate() {
        this.errors = {};
        const formData = new FormData(this.form);
        
        Object.keys(this.rules).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            let value = formData.get(fieldName);
            
            // Handle file inputs
            if (field && field.type === 'file') {
                value = field.files[0];
            }
            
            this.rules[fieldName].forEach(({ validator, message }) => {
                if (!validator(value)) {
                    if (!this.errors[fieldName]) {
                        this.errors[fieldName] = [];
                    }
                    this.errors[fieldName].push(message);
                }
            });
        });
        
        this.displayErrors();
        return Object.keys(this.errors).length === 0;
    }
    
    displayErrors() {
        // Clear previous errors
        this.form.querySelectorAll('.field-error').forEach(error => error.remove());
        this.form.querySelectorAll('.field-invalid').forEach(field => {
            field.classList.remove('field-invalid');
        });
        
        Object.keys(this.errors).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('field-invalid');
                
                const errorContainer = document.createElement('div');
                errorContainer.className = 'field-error';
                errorContainer.innerHTML = this.errors[fieldName]
                    .map(error => `<span class="error-message">${error}</span>`)
                    .join('');
                
                field.parentNode.appendChild(errorContainer);
            }
        });
    }
    
    formatFileSize(bytes) {
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }
}

// Performance monitoring
class PerformanceMonitor {
    constructor() {
        this.marks = {};
        this.measures = {};
    }
    
    start(name) {
        this.marks[name] = performance.now();
    }
    
    end(name) {
        if (this.marks[name]) {
            const duration = performance.now() - this.marks[name];
            this.measures[name] = duration;
            delete this.marks[name];
            return duration;
        }
        return null;
    }
    
    measure(name, fn) {
        this.start(name);
        const result = fn();
        this.end(name);
        return result;
    }
    
    async measureAsync(name, fn) {
        this.start(name);
        const result = await fn();
        this.end(name);
        return result;
    }
    
    getReport() {
        return {
            measures: { ...this.measures },
            activeMarks: Object.keys(this.marks)
        };
    }
    
    clear() {
        this.marks = {};
        this.measures = {};
    }
}

// Local storage utilities
class StorageManager {
    constructor(prefix = 'visualens_') {
        this.prefix = prefix;
    }
    
    set(key, value, expiry = null) {
        const data = {
            value,
            timestamp: Date.now(),
            expiry
        };
        
        try {
            localStorage.setItem(this.prefix + key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.warn('Storage failed:', error);
            return false;
        }
    }
    
    get(key) {
        try {
            const item = localStorage.getItem(this.prefix + key);
            if (!item) return null;
            
            const data = JSON.parse(item);
            
            // Check expiry
            if (data.expiry && Date.now() > data.expiry) {
                this.remove(key);
                return null;
            }
            
            return data.value;
        } catch (error) {
            console.warn('Storage retrieval failed:', error);
            return null;
        }
    }
    
    remove(key) {
        try {
            localStorage.removeItem(this.prefix + key);
            return true;
        } catch (error) {
            console.warn('Storage removal failed:', error);
            return false;
        }
    }
    
    clear() {
        try {
            Object.keys(localStorage)
                .filter(key => key.startsWith(this.prefix))
                .forEach(key => localStorage.removeItem(key));
            return true;
        } catch (error) {
            console.warn('Storage clear failed:', error);
            return false;
        }
    }
    
    size() {
        return Object.keys(localStorage)
            .filter(key => key.startsWith(this.prefix))
            .length;
    }
}

// Event emitter for component communication
class EventEmitter {
    constructor() {
        this.events = {};
    }
    
    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
        
        // Return unsubscribe function
        return () => {
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        };
    }
    
    emit(event, ...args) {
        if (this.events[event]) {
            this.events[event].forEach(callback => {
                try {
                    callback(...args);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }
    
    once(event, callback) {
        const unsubscribe = this.on(event, (...args) => {
            unsubscribe();
            callback(...args);
        });
        return unsubscribe;
    }
    
    off(event, callback) {
        if (this.events[event]) {
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        }
    }
    
    clear(event) {
        if (event) {
            delete this.events[event];
        } else {
            this.events = {};
        }
    }
}

// Debounce and throttle utilities
function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// DOM utilities
const DOM = {
    ready(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    },
    
    create(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        Object.keys(attributes).forEach(key => {
            if (key === 'className') {
                element.className = attributes[key];
            } else if (key === 'innerHTML') {
                element.innerHTML = attributes[key];
            } else {
                element.setAttribute(key, attributes[key]);
            }
        });
        
        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });
        
        return element;
    },
    
    find(selector, parent = document) {
        return parent.querySelector(selector);
    },
    
    findAll(selector, parent = document) {
        return Array.from(parent.querySelectorAll(selector));
    },
    
    remove(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    },
    
    empty(element) {
        while (element.firstChild) {
            element.removeChild(element.firstChild);
        }
    },
    
    addClass(element, className) {
        element.classList.add(className);
    },
    
    removeClass(element, className) {
        element.classList.remove(className);
    },
    
    toggleClass(element, className) {
        element.classList.toggle(className);
    },
    
    hasClass(element, className) {
        return element.classList.contains(className);
    }
};

// Export utilities for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LoadingSpinner,
        ImageUtils,
        APIError,
        APIClient,
        FormValidator,
        PerformanceMonitor,
        StorageManager,
        EventEmitter,
        debounce,
        throttle,
        DOM
    };
}
