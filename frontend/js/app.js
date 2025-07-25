/**
 * VisuaLens Frontend JavaScript
 * Handles UI interactions, API communication, and application state
 */

class VisuaLensApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.sessionId = this.generateSessionId();
        this.currentImage = null;
        this.isProcessing = false;
        this.questionHistory = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSession();
        this.checkAPIHealth();
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setupEventListeners() {
        // File upload listeners
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('imageFile');
        const removeImageBtn = document.getElementById('remove-image-btn');
        
        // Drag and drop
        uploadZone.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadZone.addEventListener('drop', this.handleDrop.bind(this));
        
        // File input
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Upload zone click to trigger file input
        uploadZone.addEventListener('click', (e) => {
            console.log('Upload zone clicked!', e.target);
            // Only trigger file input if clicking on the upload zone itself, not on existing image
            if (!this.currentImage && !e.target.closest('.image-preview')) {
                console.log('Triggering file input...');
                fileInput.click();
            }
        });
        
        // Remove image
        removeImageBtn.addEventListener('click', this.removeImage.bind(this));
        
        // Question input
        const questionInput = document.getElementById('question-input');
        questionInput.addEventListener('input', this.handleQuestionInput.bind(this));
        questionInput.addEventListener('keydown', this.handleQuestionKeydown.bind(this));
        
        // Quick questions
        const quickTags = document.querySelectorAll('.quick-tag');
        quickTags.forEach(tag => {
            tag.addEventListener('click', () => {
                questionInput.value = tag.textContent;
                this.updateCharCounter();
                questionInput.focus();
            });
        });
        
        // Form submission
        const questionForm = document.getElementById('question-form');
        if (questionForm) {
            questionForm.addEventListener('submit', this.handleSubmit.bind(this));
        }
        
        // Submit button
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', this.handleSubmit.bind(this));
        }
        
        // History controls
        const clearHistoryBtn = document.getElementById('clear-history-btn');
        const exportHistoryBtn = document.getElementById('export-history-btn');
        
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', this.clearHistory.bind(this));
        }
        
        if (exportHistoryBtn) {
            exportHistoryBtn.addEventListener('click', this.exportHistory.bind(this));
        }
        
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        }
        
        // Window events
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
        window.addEventListener('online', () => this.showNotification('Connection restored', 'success'));
        window.addEventListener('offline', () => this.showNotification('Connection lost', 'warning'));
    }
    
    // File handling methods
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const uploadZone = document.getElementById('upload-zone');
        uploadZone.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const uploadZone = document.getElementById('upload-zone');
        uploadZone.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const uploadZone = document.getElementById('upload-zone');
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleImageFile(files[0]);
        }
    }
    
    handleFileSelect(e) {
        console.log('File input changed!', e.target.files);
        const file = e.target.files[0];
        if (file) {
            console.log('File selected:', file.name, file.type, file.size);
            this.handleImageFile(file);
        }
    }
    
    handleImageFile(file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            this.showNotification('Please select a valid image file (JPEG, PNG, GIF, BMP, WebP)', 'error');
            return;
        }
        
        // Validate file size (10MB limit)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showNotification('Image file is too large. Please select an image under 10MB.', 'error');
            return;
        }
        
        this.currentImage = file;
        this.displayImagePreview(file);
        this.updateUIState();
    }
    
    displayImagePreview(file) {
        const uploadZone = document.getElementById('upload-zone');
        const placeholder = uploadZone.querySelector('.upload-placeholder');
        
        // Create image preview
        const preview = document.createElement('div');
        preview.className = 'image-preview';
        preview.innerHTML = `
            <img src="${URL.createObjectURL(file)}" alt="Image preview">
            <div class="image-info">
                <span class="image-name">${file.name}</span>
                <span class="image-size">${this.formatFileSize(file.size)}</span>
            </div>
            <button type="button" class="remove-image-btn" id="removeImage" title="Remove image">
                ×
            </button>
        `;
        
        placeholder.style.display = 'none';
        uploadZone.appendChild(preview);
        
        // Update remove button listener
        const removeBtn = preview.querySelector('.remove-image-btn');
        removeBtn.addEventListener('click', this.removeImage.bind(this));
    }
    
    removeImage() {
        const uploadZone = document.getElementById('upload-zone');
        const placeholder = uploadZone.querySelector('.upload-placeholder');
        const preview = uploadZone.querySelector('.image-preview');
        
        if (preview) {
            preview.remove();
        }
        
        placeholder.style.display = 'block';
        this.currentImage = null;
        
        // Clear file input
        const fileInput = document.getElementById('imageFile');
        fileInput.value = '';
        
        this.updateUIState();
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Question handling
    handleQuestionInput(e) {
        this.updateCharCounter();
        this.updateUIState();
    }
    
    handleQuestionKeydown(e) {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            this.handleSubmit();
        }
    }
    
    updateCharCounter() {
        const questionInput = document.getElementById('question-input');
        const charCounter = document.getElementById('char-count');
        const maxLength = 500;
        
        if (charCounter) {
            const currentLength = questionInput.value.length;
            charCounter.textContent = `${currentLength}/${maxLength}`;
            
            charCounter.className = 'char-counter';
            if (currentLength > maxLength * 0.9) {
                charCounter.classList.add('warning');
            }
            if (currentLength > maxLength) {
                charCounter.classList.add('error');
            }
        }
    }
    
    updateUIState() {
        const submitBtn = document.getElementById('submit-btn');
        const questionInput = document.getElementById('question-input');
        
        const hasImage = this.currentImage !== null;
        const hasQuestion = questionInput.value.trim().length > 0;
        const canSubmit = hasImage && hasQuestion && !this.isProcessing;
        
        submitBtn.disabled = !canSubmit;
        
        // Update submit button text
        if (this.isProcessing) {
            submitBtn.innerHTML = `
                <span class="btn-loading">
                    <span class="loading-spinner"></span>
                    Processing...
                </span>
            `;
        } else {
            submitBtn.innerHTML = 'Ask Question';
        }
    }
    
    // Form submission and API communication
    async handleSubmit(e) {
        if (e) e.preventDefault();
        
        if (this.isProcessing) return;
        
        const questionInput = document.getElementById('question-input');
        const question = questionInput.value.trim();
        
        if (!this.currentImage || !question) {
            this.showNotification('Please select an image and enter a question', 'warning');
            return;
        }
        
        this.isProcessing = true;
        this.updateUIState();
        
        try {
            const answer = await this.askQuestion(question);
            this.displayAnswer(answer);
            this.addToHistory(question, answer);
            questionInput.value = '';
            this.updateCharCounter();
            this.showNotification('Question answered successfully!', 'success');
        } catch (error) {
            console.error('Error asking question:', error);
            this.showNotification(`Failed to get answer: ${error.message}`, 'error');
            
            // Display error in answer area
            this.displayError(error.message);
        } finally {
            this.isProcessing = false;
            this.updateUIState();
        }
    }
    
    async askQuestion(question) {
        const formData = new FormData();
        formData.append('file', this.currentImage);  // Changed from 'image' to 'file'
        formData.append('question', question);
        formData.append('session_id', this.sessionId);
        
        // Get advanced options
        const detailedAnalysis = document.getElementById('alternative-model')?.checked || false;
        if (detailedAnalysis) {
            formData.append('use_alternative_model', 'true');
        }
        
        // Add system prompt if available
        const systemPrompt = document.getElementById('system-prompt')?.value;
        if (systemPrompt && systemPrompt.trim()) {
            formData.append('system_prompt', systemPrompt.trim());
        }
        
        const startTime = Date.now();
        
        const response = await fetch(`${this.apiBaseUrl}/ask`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
                console.error('API Error:', errorData);
            } catch (e) {
                console.error('Failed to parse error response:', e);
            }
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        const responseTime = Date.now() - startTime;
        
        return {
            ...data,
            response_time: responseTime
        };
    }
    
    displayAnswer(answerData) {
        const answerContainer = document.getElementById('answer-container');
        if (!answerContainer) {
            console.error('Answer container not found');
            this.showNotification('Error: Answer display area not found', 'error');
            return;
        }
        
        const placeholder = answerContainer.querySelector('.answer-placeholder');
        
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        const answerContent = document.createElement('div');
        answerContent.className = 'answer-content';
        answerContent.innerHTML = `
            <div class="answer-header">
                <div class="answer-meta">
                    <span class="model-badge">${answerData.model_used || 'LLaVA'}</span>
                    <span class="response-time">${(answerData.response_time / 1000).toFixed(2)}s</span>
                    <span class="session-info">${this.sessionId}</span>
                </div>
                <div class="answer-actions">
                    <button type="button" class="action-btn" onclick="app.copyAnswer(this)" title="Copy answer">
                        📋
                    </button>
                    <button type="button" class="action-btn" onclick="app.shareAnswer(this)" title="Share answer">
                        🔗
                    </button>
                    <button type="button" class="action-btn" onclick="app.exportAnswer(this)" title="Export answer">
                        💾
                    </button>
                </div>
            </div>
            <div class="answer-text">${answerData.answer}</div>
            <div class="answer-footer">
                <div class="token-info">
                    ${answerData.tokens ? `Tokens: ${answerData.tokens}` : ''}
                </div>
                <button type="button" class="follow-up-btn" onclick="app.askFollowUp()">
                    Ask Follow-up
                </button>
            </div>
        `;
        
        // Clear previous answers
        const existingAnswers = answerContainer.querySelectorAll('.answer-content');
        existingAnswers.forEach(answer => answer.remove());
        
        answerContainer.appendChild(answerContent);
        
        // Scroll to answer
        answerContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    displayError(errorMessage) {
        const answerContainer = document.getElementById('answer-container');
        const placeholder = answerContainer.querySelector('.answer-placeholder');
        
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        const errorContent = document.createElement('div');
        errorContent.className = 'answer-content error';
        errorContent.innerHTML = `
            <div class="answer-header">
                <div class="answer-meta">
                    <span class="model-badge error">Error</span>
                    <span class="response-time">${new Date().toLocaleTimeString()}</span>
                </div>
            </div>
            <div class="answer-text error-text">
                <strong>Error:</strong> ${errorMessage}
                <br><br>
                <em>Please check your image and question, then try again.</em>
            </div>
            <div class="answer-footer">
                <div class="token-info">
                    Request failed
                </div>
                <button type="button" class="follow-up-btn" onclick="app.askFollowUp()">
                    Try Again
                </button>
            </div>
        `;
        
        // Clear previous answers
        const existingAnswers = answerContainer.querySelectorAll('.answer-content');
        existingAnswers.forEach(answer => answer.remove());
        
        answerContainer.appendChild(errorContent);
        
        // Scroll to error
        errorContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // History management
    addToHistory(question, answerData) {
        const historyItem = {
            id: Date.now(),
            question,
            answer: answerData.answer,
            model: answerData.model_used || 'LLaVA',
            timestamp: new Date().toISOString(),
            response_time: answerData.response_time,
            image_name: this.currentImage ? this.currentImage.name : null
        };
        
        this.questionHistory.unshift(historyItem);
        this.updateHistoryDisplay();
        this.saveSession();
    }
    
    updateHistoryDisplay() {
        const historyContainer = document.getElementById('history-container');
        if (!historyContainer) {
            console.warn('History container not found');
            return;
        }
        
        const placeholder = historyContainer.querySelector('.history-placeholder');
        
        if (this.questionHistory.length === 0) {
            if (placeholder) placeholder.style.display = 'block';
            return;
        }
        
        if (placeholder) placeholder.style.display = 'none';
        
        // Clear existing items
        const existingItems = historyContainer.querySelectorAll('.history-item');
        existingItems.forEach(item => item.remove());
        
        // Add history items
        this.questionHistory.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="history-question">${this.truncateText(item.question, 100)}</div>
                <div class="history-answer">${this.truncateText(item.answer, 150)}</div>
                <div class="history-meta">
                    <span>${this.formatDate(item.timestamp)}</span>
                    <span>${item.model}</span>
                    <span>${(item.response_time / 1000).toFixed(1)}s</span>
                </div>
            `;
            
            historyItem.addEventListener('click', () => {
                this.showHistoryModal(item);
            });
            
            historyContainer.appendChild(historyItem);
        });
        
        // Update session info
        const sessionInfo = document.getElementById('session-info');
        if (sessionInfo) {
            sessionInfo.textContent = `${this.questionHistory.length} questions`;
        }
    }
    
    showHistoryModal(item) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>Question History</h3>
                    <button type="button" class="modal-close">×</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Question:</label>
                        <p>${item.question}</p>
                    </div>
                    <div class="form-group">
                        <label>Answer:</label>
                        <p>${item.answer}</p>
                    </div>
                    <div class="form-group">
                        <label>Details:</label>
                        <p>Model: ${item.model} | Response Time: ${(item.response_time / 1000).toFixed(2)}s</p>
                        <p>Date: ${this.formatDate(item.timestamp)}</p>
                        ${item.image_name ? `<p>Image: ${item.image_name}</p>` : ''}
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        Close
                    </button>
                    <button type="button" class="btn btn-primary" onclick="app.copyHistoryItem('${item.id}')">
                        Copy
                    </button>
                </div>
            </div>
        `;
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });
        
        document.body.appendChild(modal);
    }
    
    clearHistory() {
        if (confirm('Are you sure you want to clear the question history?')) {
            this.questionHistory = [];
            this.updateHistoryDisplay();
            this.saveSession();
            this.showNotification('History cleared', 'success');
        }
    }
    
    exportHistory() {
        if (this.questionHistory.length === 0) {
            this.showNotification('No history to export', 'warning');
            return;
        }
        
        const data = {
            session_id: this.sessionId,
            exported_at: new Date().toISOString(),
            questions: this.questionHistory
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `visualens_history_${this.sessionId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        this.showNotification('History exported', 'success');
    }
    
    // Session management
    loadSession() {
        try {
            const saved = localStorage.getItem('visualens_session');
            if (saved) {
                const data = JSON.parse(saved);
                this.questionHistory = data.history || [];
                this.updateHistoryDisplay();
            }
        } catch (error) {
            console.warn('Failed to load session:', error);
        }
    }
    
    saveSession() {
        try {
            const data = {
                session_id: this.sessionId,
                history: this.questionHistory,
                saved_at: new Date().toISOString()
            };
            localStorage.setItem('visualens_session', JSON.stringify(data));
        } catch (error) {
            console.warn('Failed to save session:', error);
        }
    }
    
    handleBeforeUnload() {
        this.saveSession();
    }
    
    // API health check
    async checkAPIHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            if (response.ok) {
                this.showNotification('Connected to VisuaLens API', 'success');
            } else {
                throw new Error('API health check failed');
            }
        } catch (error) {
            console.warn('API health check failed:', error);
            this.showNotification('Warning: Cannot connect to VisuaLens API', 'warning');
        }
    }
    
    // Utility methods
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }
    
    formatDate(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString();
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer') || this.createNotificationContainer();
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-message">${message}</div>
            </div>
            <button type="button" class="notification-close">×</button>
        `;
        
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'notification-container';
        document.body.appendChild(container);
        return container;
    }
    
    // Action methods
    copyAnswer(button) {
        const answerText = button.closest('.answer-content').querySelector('.answer-text').textContent;
        navigator.clipboard.writeText(answerText).then(() => {
            this.showNotification('Answer copied to clipboard', 'success');
        }).catch(() => {
            this.showNotification('Failed to copy answer', 'error');
        });
    }
    
    shareAnswer(button) {
        const answerText = button.closest('.answer-content').querySelector('.answer-text').textContent;
        if (navigator.share) {
            navigator.share({
                title: 'VisuaLens Answer',
                text: answerText
            });
        } else {
            this.copyAnswer(button);
        }
    }
    
    exportAnswer(button) {
        const answerContent = button.closest('.answer-content');
        const answerText = answerContent.querySelector('.answer-text').textContent;
        const model = answerContent.querySelector('.model-badge').textContent;
        const responseTime = answerContent.querySelector('.response-time').textContent;
        
        const data = {
            answer: answerText,
            model: model,
            response_time: responseTime,
            exported_at: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `visualens_answer_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        this.showNotification('Answer exported', 'success');
    }
    
    askFollowUp() {
        const questionInput = document.getElementById('question-input');
        questionInput.focus();
        questionInput.scrollIntoView({ behavior: 'smooth' });
    }
    
    copyHistoryItem(itemId) {
        const item = this.questionHistory.find(h => h.id == itemId);
        if (item) {
            const text = `Question: ${item.question}\n\nAnswer: ${item.answer}`;
            navigator.clipboard.writeText(text).then(() => {
                this.showNotification('History item copied', 'success');
            });
        }
    }
    
    toggleTheme() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('visualens_theme', isDark ? 'dark' : 'light');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VisuaLensApp();
    
    // Load theme preference
    const savedTheme = localStorage.getItem('visualens_theme');
    if (savedTheme === 'dark' || (savedTheme === null && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-theme');
    }
});

// Service Worker registration for PWA features (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
