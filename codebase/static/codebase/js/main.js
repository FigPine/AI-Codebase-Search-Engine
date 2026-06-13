/* codebase/static/codebase/js/main.js */
document.addEventListener('DOMContentLoaded', () => {
    let currentRepo = null;
    
    // UI Elements
    const uploadForm = document.getElementById('uploadForm');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    const repoList = document.getElementById('repoList');
    const activeRepoTitle = document.getElementById('activeRepoTitle');
    const activeRepoSubtitle = document.getElementById('activeRepoSubtitle');
    const chatMessages = document.getElementById('chatMessages');
    const queryInput = document.getElementById('queryInput');
    const sendBtn = document.getElementById('sendBtn');
    
    // Select repo logic
    function selectRepo(repoName) {
        currentRepo = repoName;
        
        // Update UI
        document.querySelectorAll('.repo-item').forEach(el => el.classList.remove('active'));
        const selectedEl = document.querySelector(`.repo-item[data-repo="${repoName}"]`);
        if (selectedEl) selectedEl.classList.add('active');
        
        activeRepoTitle.textContent = repoName;
        activeRepoSubtitle.textContent = "Ask questions about " + repoName;
        queryInput.disabled = false;
        sendBtn.disabled = false;
        queryInput.focus();
        
        // Clear chat
        chatMessages.innerHTML = `<div class="message bot">You are now chatting with the <strong>${repoName}</strong> codebase. What would you like to know?</div>`;
    }
    
    // Initialize clicking on existing repos
    document.querySelectorAll('.repo-item').forEach(item => {
        item.addEventListener('click', () => selectRepo(item.dataset.repo));
    });
    
    // Handle Upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('repoZip');
            if (!fileInput.files.length) return;
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('repo_zip', file);
            
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="loader"></span> Indexing...';
            uploadStatus.style.display = 'block';
            uploadStatus.textContent = 'Uploading and extracting...';
            uploadStatus.style.color = 'black';
            
            try {
                const response = await fetch('/upload/', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (response.ok) {
                    uploadStatus.textContent = 'Success! Added to library.';
                    
                    // Add to UI if not exists
                    if (!document.querySelector(`.repo-item[data-repo="${data.repo_name}"]`)) {
                        const repoHtml = `
                            <div class="repo-item" data-repo="${data.repo_name}">
                                <strong>${data.repo_name}</strong>
                                <div style="font-size: 0.8rem; color: gray;">Just now</div>
                            </div>
                        `;
                        // Remove empty message if present
                        const emptyMsg = repoList.querySelector('p');
                        if(emptyMsg) emptyMsg.remove();
                        
                        repoList.insertAdjacentHTML('afterbegin', repoHtml);
                        
                        // Add listener to new item
                        const newItem = repoList.firstElementChild;
                        newItem.addEventListener('click', () => selectRepo(data.repo_name));
                    }
                    
                    // Auto select
                    selectRepo(data.repo_name);
                    fileInput.value = '';
                } else {
                    throw new Error(data.message || 'Upload failed');
                }
            } catch (error) {
                uploadStatus.textContent = 'Error: ' + error.message;
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Index Codebase';
            }
        });
    }
    
    // Handle Chat
    async function sendMessage() {
        const query = queryInput.value.trim();
        if (!query || !currentRepo) return;
        
        // Add user message
        chatMessages.insertAdjacentHTML('beforeend', `
            <div class="message user">${query}</div>
        `);
        queryInput.value = '';
        scrollToBottom();
        
        // Add loading bot message
        const loaderId = 'loader-' + Date.now();
        chatMessages.insertAdjacentHTML('beforeend', `
            <div class="message bot" id="${loaderId}">
                <span class="loader"></span> Analyzing codebase...
            </div>
        `);
        scrollToBottom();
        
        try {
            const formData = new FormData();
            formData.append('query', query);
            formData.append('repo_name', currentRepo);
            
            const response = await fetch('/ask/', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            const loaderEl = document.getElementById(loaderId);
            
            if (response.ok) {
                // Formatting basic markdown (very simple)
                let formattedAnswer = data.answer.replace(/\n/g, '<br>');
                formattedAnswer = formattedAnswer.replace(/\`\`\`([\s\S]*?)\`\`\`/g, '<pre><code>$1</code></pre>');
                formattedAnswer = formattedAnswer.replace(/\`([^\`]+)\`/g, '<code>$1</code>');
                
                let contextHtml = '';
                if (data.context_files && data.context_files.length > 0) {
                    contextHtml = `<div class="context-files"><strong>Sources:</strong> ${data.context_files.join(', ')}</div>`;
                }
                
                loaderEl.innerHTML = formattedAnswer + contextHtml;
            } else {
                throw new Error(data.message || 'Error getting answer');
            }
        } catch (error) {
            const loaderEl = document.getElementById(loaderId);
            loaderEl.innerHTML = `<span>Error: ${error.message}</span>`;
        }
        scrollToBottom();
    }
    
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    if (queryInput) {
        queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
