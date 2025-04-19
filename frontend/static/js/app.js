// ========== Utility Functions ==========
/**
 * Formats time to HH:MM format
 * @param {Date} date - Date object to format (defaults to current time)
 * @returns {string} Formatted time string
 */
function formatTime(date = new Date()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Updates the document count in the UI
 * @param {number} count - Number of documents
 */
function updateDocumentCount(count) {
    document.getElementById('docCount').textContent = count || 0;
}

// ========== Initialization Functions ==========
/**
 * Loads initial document and chunk counts from the server
 */
async function loadInitialCounts() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        document.getElementById('docCount').textContent = 
            (await countDocuments()) || 0;
        document.getElementById('chunkCount').textContent = 
            data.documents || 0;
    } catch (error) {
        console.error("Error loading initial counts:", error);
    }
}

/**
 * Counts documents by fetching from the server
 * @returns {Promise<number>} Number of documents
 */
async function countDocuments() {
    try {
        const response = await fetch('/list-documents');
        const data = await response.json();
        return data.files ? data.files.length : 0;
    } catch (error) {
        console.error("Error counting documents:", error);
        return 0;
    }
}

// ========== Event Listeners ==========
// File upload handling
document.getElementById('files').addEventListener('change', function(e) {
    const fileList = document.getElementById('fileList');
    const filePreview = document.getElementById('filePreview');
    const files = e.target.files;
    
    fileList.innerHTML = '';
    
    if (files.length > 0) {
        filePreview.style.display = 'block';
        
        for (let i = 0; i < files.length; i++) {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <span><i class="bi bi-file-earmark me-2"></i>${files[i].name}</span>
                <small class="text-muted">${(files[i].size / 1024).toFixed(1)} KB</small>
            `;
            fileList.appendChild(fileItem);
        }
    } else {
        filePreview.style.display = 'none';
    }
});

// Clear files button
document.getElementById('clearFiles').addEventListener('click', function() {
    document.getElementById('files').value = '';
    document.getElementById('filePreview').style.display = 'none';
});

// Upload form submission
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const statusElement = document.getElementById('uploadStatus');
    const submitButton = this.querySelector('button[type="submit"]');
    
    // Save original button content
    const originalButtonContent = submitButton.innerHTML;
    
    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Uploading...
    `;
    
    statusElement.innerHTML = '';
    
    const formData = new FormData();
    const files = document.getElementById('files').files;
    
    if (files.length === 0) {
        statusElement.innerHTML = `
            <div class="alert alert-warning alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Please select at least one file to upload
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonContent;
        return;
    }
    
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusElement.innerHTML = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="bi bi-check-circle me-2"></i>
                    ${result.message} - ${result.files.length} file(s) uploaded
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            
            // Update document count
            updateDocumentCount(result.files.length);
            
            // Clear file selection
            document.getElementById('files').value = '';
            document.getElementById('filePreview').style.display = 'none';
        } else {
            statusElement.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="bi bi-x-circle me-2"></i>
                    ${result.error || 'Failed to upload files'}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        }
    } catch (error) {
        statusElement.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-x-circle me-2"></i>
                Error: ${error.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonContent;
    }
});

// Database population button
document.getElementById('populateBtn').addEventListener('click', async function() {
    const statusElement = document.getElementById('dbStatus');
    const populateButton = this;
    const reset = document.getElementById('resetCheck').checked;
    
    populateButton.disabled = true;
    statusElement.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Processing...';
    
    try {
        const response = await fetch('/populate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reset })
        });

        const result = await response.json();
        
        if (response.ok) {
            // Update counts in the UI
            document.getElementById('docCount').textContent = result.document_count || 0;
            document.getElementById('chunkCount').textContent = result.chunk_count || 0;
            
            statusElement.innerHTML = `
                <div class="alert alert-success">
                    ${result.message}
                    <div class="mt-2">
                        <small>Documents: ${result.document_count}</small><br>
                        <small>Chunks: ${result.chunk_count}</small>
                    </div>
                </div>
            `;
        } else {
            throw new Error(result.message || 'Failed to populate database');
        }
    } catch (error) {
        statusElement.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    } finally {
        populateButton.disabled = false;
    }
});

// Query form submission
document.getElementById('queryForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const question = document.getElementById('questionInput').value.trim();
    if (!question) return;
    
    const chatContainer = document.getElementById('chatContainer');
    const sourcesContainer = document.getElementById('sourcesContainer');
    const askButton = document.getElementById('askButton');
    
    // Remove empty state if present
    const emptyState = chatContainer.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
    
    // Add user question to chat
    chatContainer.innerHTML += `
        <div class="user-message">
            <strong>You:</strong> ${question}
            <small class="message-time">${formatTime()}</small>
        </div>
    `;
    
    // Show typing indicator
    chatContainer.innerHTML += `
        <div class="bot-message typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    // Disable input and button while processing
    document.getElementById('questionInput').disabled = true;
    askButton.disabled = true;
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const result = await response.json();
        
        // Remove typing indicator
        const typingIndicators = chatContainer.querySelectorAll('.typing-indicator');
        typingIndicators[typingIndicators.length - 1].remove();
        
        if (response.ok) {
            // Add bot response
            chatContainer.innerHTML += `
                <div class="bot-message">
                    <strong>Assistant:</strong> ${result.response}
                    <small class="message-time">${formatTime()}</small>
                </div>
            `;
            
            // Add sources if available
            sourcesContainer.innerHTML = '';
            if (result.sources && result.sources.length > 0) {
                sourcesContainer.innerHTML = `
                    <h6>Sources:</h6>
                    <ul class="list-group">
                        ${result.sources.map(source => `
                            <li class="list-group-item source-item">
                                <i class="bi bi-file-earmark-text me-2"></i>
                                ${source}
                            </li>
                        `).join('')}
                    </ul>
                `;
                document.getElementById('sourcesCount').textContent = `${result.sources.length} documents referenced`;
            } else {
                document.getElementById('sourcesCount').textContent = 'No sources referenced';
            }
        } else {
            chatContainer.innerHTML += `
                <div class="bot-message alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${result.error || 'Unknown error occurred'}
                    <small class="message-time">${formatTime()}</small>
                </div>
            `;
            document.getElementById('sourcesCount').textContent = 'No sources referenced';
        }
    } catch (error) {
        // Remove typing indicator
        const typingIndicators = chatContainer.querySelectorAll('.typing-indicator');
        typingIndicators[typingIndicators.length - 1].remove();
        
        chatContainer.innerHTML += `
            <div class="bot-message alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Error: ${error.message}
                <small class="message-time">${formatTime()}</small>
            </div>
        `;
        document.getElementById('sourcesCount').textContent = 'No sources referenced';
    } finally {
        // Re-enable input and button
        document.getElementById('questionInput').disabled = false;
        askButton.disabled = false;
        
        // Clear input and focus
        document.getElementById('questionInput').value = '';
        document.getElementById('questionInput').focus();
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});

// Clear chat history
document.getElementById('clearChat').addEventListener('click', function() {
    const chatContainer = document.getElementById('chatContainer');
    const sourcesContainer = document.getElementById('sourcesContainer');
    
    chatContainer.innerHTML = `
        <div class="empty-state">
            <i class="bi bi-chat-square-text"></i>
            <h5>No messages yet</h5>
            <p>Ask a question about your documents to get started</p>
        </div>
    `;
    
    sourcesContainer.innerHTML = '';
    document.getElementById('sourcesCount').textContent = '0 documents referenced';
});

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadInitialCounts();
});