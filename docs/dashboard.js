// Dashboard Tab Switching
function switchDashboardTab(tabName) {
    document.querySelectorAll('.dashboard-tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.dashboard-tab-button').forEach(b => b.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');

    // Find and activate the corresponding button
    document.querySelectorAll('.dashboard-tab-button').forEach(b => {
        if (b.textContent.includes('Setup') && tabName === 'setup') b.classList.add('active');
        if (b.textContent.includes('Connection') && tabName === 'connection') b.classList.add('active');
        if (b.textContent.includes('Query') && tabName === 'query') b.classList.add('active');
    });

    // Update URL hash
    window.location.hash = tabName;

    if (tabName === 'query') {
        const connected = document.getElementById('statusDot').classList.contains('connected');
        const baseUrl = Storage.getBaseUrl();

        document.getElementById('queryCard').style.display = connected ? 'block' : 'none';
        document.getElementById('notConnectedMsg').style.display = connected ? 'none' : 'block';

        // Show connected info if connected
        const connectedInfo = document.getElementById('connectedInfo');
        if (connected) {
            document.getElementById('connectedUrl').textContent = baseUrl;
            connectedInfo.style.display = 'block';
        } else {
            connectedInfo.style.display = 'none';
        }
    }
}

// Handle hash changes and page load
function loadTabFromHash() {
    const hash = window.location.hash.substring(1) || 'setup';
    if (['setup', 'connection', 'query'].includes(hash)) {
        switchDashboardTab(hash);
    }
}

// Listen for hash changes
window.addEventListener('hashchange', loadTabFromHash);

// OS Switcher
function switchOS(os) {
    document.querySelectorAll('.os-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.os-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(os + '-venv').classList.add('active');
    event.target.classList.add('active');
}

// Copy Command to Clipboard
function copyCommand(text) {
    navigator.clipboard.writeText(text).then(() => {
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = originalText;
            btn.classList.remove('copied');
        }, 2000);
    });
}

// API Client Class
class AgentCorexClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.timeout = 60000; // 60 second timeout for model downloads
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                headers: { 'Content-Type': 'application/json', ...options.headers },
                signal: controller.signal,
                ...options
            });
            clearTimeout(timeoutId);

            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - backend may be downloading models');
            }
            throw error;
        }
    }

    async health() { return this.request('/health'); }
    async getTools() { return this.request('/tools'); }
    async getEndpoints() { return this.request('/endpoints'); }

    async retrieveTools(query, topK = 5, method = 'hybrid') {
        const params = new URLSearchParams({ query, top_k: topK, method });
        return this.request(`/retrieve_tools?${params}`);
    }
}

// Storage Manager
const Storage = {
    setBaseUrl(url) { localStorage.setItem('agent_corex_url', url); },
    getBaseUrl() { return localStorage.getItem('agent_corex_url') || 'http://localhost:8000'; },
    clear() { localStorage.removeItem('agent_corex_url'); }
};

// Test Connection
async function testConnection() {
    const baseUrl = document.getElementById('baseUrl').value.trim();
    if (!baseUrl) return alert('Enter valid URL');

    document.getElementById('statusDot').className = 'status-dot testing';
    const client = new AgentCorexClient(baseUrl);

    try {
        const health = await client.health();
        Storage.setBaseUrl(baseUrl);
        document.getElementById('statusDot').className = 'status-dot connected';
        document.getElementById('statusLabel').textContent = 'Connected';
        document.getElementById('statusMessage').textContent = 'Connected to backend';
        document.getElementById('connectionInfo').innerHTML = `<pre>${JSON.stringify(health, null, 2)}</pre>`;
        document.getElementById('statusDetails').style.display = 'block';
        document.getElementById('queryCard').style.display = 'block';
        document.getElementById('notConnectedMsg').style.display = 'none';
    } catch (error) {
        document.getElementById('statusDot').className = 'status-dot disconnected';
        document.getElementById('statusLabel').textContent = 'Failed';
        document.getElementById('statusMessage').textContent = 'Connection failed: ' + error.message;
        document.getElementById('statusDetails').style.display = 'none';
    }
}

// Search Tools
async function searchTools() {
    // Validate elements exist
    const queryElem = document.getElementById('query');
    const topKElem = document.getElementById('topK');
    const methodElem = document.getElementById('method');

    if (!queryElem) {
        alert('Error: Query input not found. Please refresh the page.');
        console.error('Element with id="query" not found');
        return;
    }

    const baseUrl = Storage.getBaseUrl();
    const query = (queryElem.value || '').trim();
    const topK = parseInt(topKElem?.value || 5) || 5;
    const method = methodElem?.value || 'hybrid';

    if (!query) return alert('Enter search query');

    console.log(`🔍 Searching with baseUrl: ${baseUrl}, query: ${query}, method: ${method}`);

    const client = new AgentCorexClient(baseUrl);
    document.getElementById('errorContainer').innerHTML = '';
    document.getElementById('resultsContainer').style.display = 'none';

    // Show loading state
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div style="text-align: center; padding: 20px;"><p style="color: #666;">🔄 Searching tools...</p><p style="font-size: 12px; color: #999;">First search may take longer while models load</p></div>';
    document.getElementById('resultsContainer').style.display = 'block';

    try {
        console.log(`📡 Making API call to: ${baseUrl}/retrieve_tools?query=${query}&top_k=${topK}&method=${method}`);
        const results = await client.retrieveTools(query, topK, method);
        console.log('✅ Got results:', results);
        const resultsHtml = (results || []).map(tool => `
            <div class="result-item">
                <div class="result-name">${tool.name}</div>
                <div class="result-description">${tool.description}</div>
                <div class="result-score">Score: ${(tool.score || 0).toFixed(4)}</div>
            </div>
        `).join('');
        resultsDiv.innerHTML = resultsHtml || '<p style="color:#999;">No results found</p>';
    } catch (error) {
        document.getElementById('resultsContainer').style.display = 'none';
        let errorMsg = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMsg = `Cannot reach backend at ${baseUrl}. Make sure your backend is running and the URL is correct.`;
        } else if (error.message.includes('timeout')) {
            errorMsg = `Request timeout (${error.message}). Try again - first query downloads AI models which can take 30-60 seconds.`;
        }
        document.getElementById('errorContainer').innerHTML = `<div class="error-message">❌ ${errorMsg}</div>`;
    }
}

// Clear Settings
function clearSettings() {
    Storage.clear();
    document.getElementById('baseUrl').value = 'http://localhost:8000';
    document.getElementById('statusDot').className = 'status-dot disconnected';
    document.getElementById('statusLabel').textContent = 'Disconnected';
    document.getElementById('statusMessage').textContent = 'Settings cleared';
}

// Initialize on page load
document.getElementById('baseUrl').value = Storage.getBaseUrl();

window.addEventListener('load', () => {
    const storedUrl = Storage.getBaseUrl();
    document.getElementById('baseUrl').value = storedUrl;

    console.log('Dashboard initialized. Stored URL:', storedUrl);
    console.log('Connection status dot:', document.getElementById('statusDot').className);

    // Load tab from URL hash
    loadTabFromHash();
});
