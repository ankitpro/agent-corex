// Dashboard Tab Switching
function switchDashboardTab(tabName) {
    console.log(`switchDashboardTab called with: ${tabName}`);

    document.querySelectorAll('.dashboard-tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.dashboard-tab-button').forEach(b => b.classList.remove('active'));

    const tabElement = document.getElementById(tabName);
    if (!tabElement) {
        console.error(`Tab element not found for: ${tabName}`);
        return;
    }

    tabElement.classList.add('active');
    console.log(`Tab ${tabName} activated`);

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
    const validTabs = ['setup', 'connection', 'query'];
    if (validTabs.includes(hash)) {
        switchDashboardTab(hash);
    } else if (hash) {
        console.warn(`Unknown tab hash: ${hash}, loading setup`);
        switchDashboardTab('setup');
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
        const t0 = Date.now();

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
            this.lastExecuteTime = Date.now() - t0;

            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            this.lastExecuteTime = Date.now() - t0;
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

// History Manager
const History = {
    MAX_ENTRIES: 20,
    KEY: 'agent_corex_history',

    getAll() {
        try {
            return JSON.parse(localStorage.getItem(this.KEY) || '[]');
        } catch {
            return [];
        }
    },

    add(query, topToolName, status) {
        const history = this.getAll();
        const entry = {
            query,
            topToolName,
            status,
            timestamp: new Date().toISOString()
        };
        history.unshift(entry);
        if (history.length > this.MAX_ENTRIES) {
            history.pop();
        }
        localStorage.setItem(this.KEY, JSON.stringify(history));
        renderHistory();
    },

    clear() {
        localStorage.removeItem(this.KEY);
        renderHistory();
    }
};

// Render History List
function renderHistory() {
    const historyList = document.getElementById('historyList');
    const historyEmpty = document.getElementById('historyEmpty');
    const history = History.getAll();

    if (history.length === 0) {
        historyList.innerHTML = '';
        historyEmpty.style.display = 'block';
        return;
    }

    historyEmpty.style.display = 'none';
    historyList.innerHTML = history.map((entry, index) => {
        const time = new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        return `
            <div class="history-entry" onclick="rerunHistoryEntry(${index})">
                <div class="history-entry-query">${entry.query}</div>
                <div class="history-entry-meta">
                    <span class="history-entry-status ${entry.status}">${entry.status === 'success' ? '✓' : '✗'} ${entry.status}</span>
                    ${time}
                </div>
            </div>
        `;
    }).join('');
}

// Rerun History Entry
function rerunHistoryEntry(index) {
    const history = History.getAll();
    if (index >= 0 && index < history.length) {
        const entry = history[index];
        document.getElementById('queryInput').value = entry.query;
        searchTools();
    }
}

// Clear History
function clearHistory() {
    if (confirm('Clear search history?')) {
        History.clear();
    }
}

// Update Connection Banner
function updateConnectionBanner(connected, url) {
    const banner = document.getElementById('connectionBanner');
    const icon = document.getElementById('bannerIcon');
    const text = document.getElementById('bannerText');

    if (connected) {
        banner.classList.remove('banner-disconnected');
        banner.classList.add('banner-connected');
        icon.textContent = '✅';
        text.textContent = `Connected to ${url}`;
    } else {
        banner.classList.remove('banner-connected');
        banner.classList.add('banner-disconnected');
        icon.textContent = '❌';
        text.textContent = 'Not Connected';
    }
}

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
        updateConnectionBanner(true, baseUrl);
    } catch (error) {
        document.getElementById('statusDot').className = 'status-dot disconnected';
        document.getElementById('statusLabel').textContent = 'Failed';
        document.getElementById('statusMessage').textContent = 'Connection failed: ' + error.message;
        document.getElementById('statusDetails').style.display = 'none';
        updateConnectionBanner(false);
    }
}

// Friendly Error Handler
function friendlyError(error, baseUrl) {
    const message = error.message || '';

    if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
        return {
            text: `Cannot reach backend at ${baseUrl}. Make sure your backend is running and the URL is correct.`,
            fix: 'Start your backend with: uvicorn agent_core.api.main:app --reload'
        };
    } else if (message.includes('timeout')) {
        return {
            text: `Request timeout (${message}). Try again - first query downloads AI models which can take 30-60 seconds.`,
            fix: 'The first search takes longer while downloading models. Subsequent searches are fast.'
        };
    } else if (message.includes('HTTP 400') || message.includes('Invalid')) {
        return {
            text: `Invalid request: ${message}`,
            fix: 'Check your query and try again.'
        };
    } else if (message.includes('HTTP 500')) {
        return {
            text: `Server error: ${message}. Backend may have encountered an issue.`,
            fix: 'Check backend logs and try again.'
        };
    } else {
        return {
            text: `Error: ${message}`,
            fix: 'Please try again or check the connection settings.'
        };
    }
}

// Update Agent Thinking Panel
function updateThinkingPanel(tools) {
    const thinkingPanel = document.getElementById('thinkingPanel');
    const toolCountEl = document.getElementById('thinkingToolCount');
    const selectedToolEl = document.getElementById('thinkingSelectedTool');
    const confidenceEl = document.getElementById('thinkingConfidence');
    const reasoningEl = document.getElementById('thinkingReasoning');

    if (!tools || tools.length === 0) {
        thinkingPanel.style.display = 'none';
        return;
    }

    // Get tool count and selected tool
    const toolCount = tools.length;
    const selectedTool = tools[0]; // Top result is selected
    const selectedToolName = selectedTool.name;

    // Calculate confidence level with detailed reasoning
    let confidence, confidenceClass, reasoning;
    if (toolCount === 1) {
        confidence = 'High';
        confidenceClass = 'high-confidence';
        reasoning = 'Only one tool matches your query. High confidence in this selection.';
    } else if (toolCount <= 3) {
        confidence = 'Medium';
        confidenceClass = 'medium-confidence';
        reasoning = `Found ${toolCount} potential matches. Selected the most relevant based on similarity score.`;
    } else {
        confidence = 'Low';
        confidenceClass = 'low-confidence';
        reasoning = `Found ${toolCount} possible matches. Try refining your query with more specific terms for better results.`;
    }

    // Update panel elements
    const toolLabel = toolCount === 1 ? 'tool' : 'tools';
    toolCountEl.textContent = `${toolCount} ${toolLabel}`;
    selectedToolEl.textContent = selectedToolName;
    confidenceEl.textContent = confidence;
    confidenceEl.className = `thinking-value ${confidenceClass}`;
    reasoningEl.textContent = reasoning;

    // Show the panel
    thinkingPanel.style.display = 'block';
}

// Render Tool Card
function renderToolCard(tool, index) {
    return `
        <div class="tool-card" id="tool-card-${index}">
            <div class="tool-card-header">
                <div class="tool-card-name">${tool.name}</div>
                <div class="tool-card-score">${(tool.score || 0).toFixed(2)}</div>
            </div>
            <div class="tool-card-desc">${tool.description || 'No description'}</div>
            <div class="tool-card-params">
                <span class="param-tag">Query Match</span>
                <span class="tool-tag">Available</span>
            </div>
        </div>
    `;
}

// Highlight Tool Card
function highlightTool(index) {
    const card = document.getElementById(`tool-card-${index}`);
    if (card) {
        card.classList.add('tool-card-highlight');
        setTimeout(() => {
            card.classList.remove('tool-card-highlight');
        }, 1000);
    }
}

// Run Example Query
function runExample(query) {
    const queryInput = document.getElementById('queryInput');
    queryInput.value = query;
    searchTools();
}

// Search Tools
async function searchTools() {
    // Validate elements exist
    const queryElem = document.getElementById('queryInput');  // Changed from 'query' to 'queryInput'
    const topKElem = document.getElementById('topK');
    const methodElem = document.getElementById('method');

    console.log('searchTools() called');
    console.log('queryElem found:', !!queryElem);
    console.log('queryElem.value:', queryElem?.value);
    console.log('queryCard visible:', document.getElementById('queryCard')?.style.display);

    if (!queryElem) {
        alert('Error: Query input not found. Please refresh the page.');
        console.error('Element with id="queryInput" not found');
        return;
    }

    const baseUrl = Storage.getBaseUrl();
    const rawQuery = queryElem.value || '';
    const query = rawQuery.trim();

    console.log('rawQuery:', `"${rawQuery}"`);
    console.log('trimmed query:', `"${query}"`);

    const topK = parseInt(topKElem?.value || 5) || 5;
    const method = methodElem?.value || 'hybrid';

    if (!query) {
        console.warn('Query is empty!');
        return alert('Please enter a search query');
    }

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
        const resultsHtml = (results || []).map((tool, index) => renderToolCard(tool, index)).join('');
        resultsDiv.innerHTML = resultsHtml || '<p style="color:#999;">No results found</p>';

        // Display latency badge
        const latencyBadge = document.getElementById('latencyBadge');
        latencyBadge.textContent = `${client.lastExecuteTime}ms`;
        latencyBadge.style.display = 'inline-block';

        // Update Agent Thinking panel
        updateThinkingPanel(results);

        // Record in history
        const topToolName = (results && results.length > 0) ? results[0].name : 'No results';
        History.add(query, topToolName, 'success');
    } catch (error) {
        document.getElementById('resultsContainer').style.display = 'none';
        document.getElementById('thinkingPanel').style.display = 'none';
        const errorInfo = friendlyError(error, baseUrl);
        document.getElementById('errorContainer').innerHTML = `
            <div class="error-message">❌ ${errorInfo.text}</div>
            <div class="error-fix">💡 ${errorInfo.fix}</div>
        `;

        // Record in history
        History.add(query, '', 'error');
    }
}

// Clear Settings
function clearSettings() {
    Storage.clear();
    document.getElementById('baseUrl').value = 'http://localhost:8000';
    document.getElementById('statusDot').className = 'status-dot disconnected';
    document.getElementById('statusLabel').textContent = 'Disconnected';
    document.getElementById('statusMessage').textContent = 'Settings cleared';
    updateConnectionBanner(false);
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

    // Initialize history panel
    renderHistory();
});
