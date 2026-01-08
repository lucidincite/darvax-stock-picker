const API_URL = 'http://localhost:8000';

const tickersInput = document.getElementById('tickers');
const scanBtn = document.getElementById('scan-btn');
const resultsSection = document.getElementById('results-section');
const resultsBody = document.getElementById('results-body');
const loadingEl = document.getElementById('loading');
const noResultsEl = document.getElementById('no-results');
const resultsTable = document.getElementById('results-table');

// Chart Analysis Modal Elements
const modal = document.getElementById('analysis-modal');
const modalClose = document.getElementById('modal-close');
const modalTicker = document.getElementById('modal-ticker');
const chartUpload = document.getElementById('chart-upload');
const analyzeBtn = document.getElementById('analyze-btn');
const analysisLoading = document.getElementById('analysis-loading');
const analysisResult = document.getElementById('analysis-result');
const uploadSection = document.getElementById('upload-section');

let currentTicker = '';

scanBtn.addEventListener('click', async () => {
    const tickersText = tickersInput.value.trim();
    if (!tickersText) {
        alert('Please enter at least one ticker');
        return;
    }

    // Parse tickers (one per line, filter empty)
    const tickers = tickersText
        .split('\n')
        .map(t => t.trim())
        .filter(t => t.length > 0);

    if (tickers.length === 0) {
        alert('Please enter valid tickers');
        return;
    }

    // Show loading
    resultsSection.style.display = 'block';
    loadingEl.style.display = 'block';
    resultsTable.style.display = 'none';
    noResultsEl.style.display = 'none';
    scanBtn.disabled = true;
    scanBtn.textContent = 'Scanning...';

    try {
        const response = await fetch(`${API_URL}/api/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tickers }),
        });

        if (!response.ok) {
            throw new Error('Scan failed');
        }

        const results = await response.json();
        displayResults(results);
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to scan. Make sure the backend is running on localhost:8000');
    } finally {
        loadingEl.style.display = 'none';
        scanBtn.disabled = false;
        scanBtn.textContent = '🎯 Scan for Signals';
    }
});

function displayResults(results) {
    resultsBody.innerHTML = '';

    if (results.length === 0) {
        resultsTable.style.display = 'none';
        noResultsEl.style.display = 'block';
        return;
    }

    resultsTable.style.display = 'table';
    noResultsEl.style.display = 'none';

    // Sort by distance (tightest first)
    results.sort((a, b) => a.distance_pct - b.distance_pct);

    results.forEach(signal => {
        const row = document.createElement('tr');

        // TradingView link
        const tvSymbol = signal.ticker.replace('.NS', '').replace('.BO', '');
        const tvLink = `https://www.tradingview.com/chart/?symbol=NSE:${tvSymbol}`;

        // Priority styling
        let priorityClass = '';
        let priorityEmoji = '';
        switch (signal.priority) {
            case 'SNIPER':
                priorityClass = 'priority-sniper';
                priorityEmoji = '🎯';
                break;
            case 'TIGHT':
                priorityClass = 'priority-tight';
                priorityEmoji = '⚡';
                break;
            case 'STANDARD':
                priorityClass = 'priority-standard';
                priorityEmoji = '✓';
                break;
            case 'WIDE':
                priorityClass = 'priority-wide';
                priorityEmoji = '⚠️';
                break;
        }

        // ATH / Blue Sky styling
        let athClass = '';
        let athLabel = '';
        switch (signal.blue_sky) {
            case 'BLUE_SKY':
                athClass = 'ath-bluesky';
                athLabel = '🚀 BLUE SKY';
                break;
            case 'NEAR_ATH':
                athClass = 'ath-near';
                athLabel = '↗️ NEAR';
                break;
            case 'RESIST':
                athClass = 'ath-resist';
                athLabel = '⚠️ RESIST';
                break;
        }

        // Volume class
        const volClass = `volume-${signal.volume_status.toLowerCase()}`;

        row.innerHTML = `
            <td class="${priorityClass}">${priorityEmoji} ${signal.priority}</td>
            <td class="${athClass}">${athLabel}</td>
            <td><a href="${tvLink}" target="_blank" class="ticker-link">${signal.ticker}</a></td>
            <td>₹${signal.close.toFixed(2)}</td>
            <td class="trigger">₹${signal.trigger.toFixed(2)}</td>
            <td class="distance">${signal.distance_pct}%</td>
            <td class="stop">₹${signal.stop_loss.toFixed(2)}</td>
            <td class="${volClass}">${signal.volume_status}</td>
            <td><button class="analyze-chart-btn" data-ticker="${signal.ticker}">📊</button></td>
        `;

        resultsBody.appendChild(row);
    });

    // Add click listeners to analyze buttons
    document.querySelectorAll('.analyze-chart-btn').forEach(btn => {
        btn.addEventListener('click', () => openAnalysisModal(btn.dataset.ticker));
    });
}

// Modal Functions
function openAnalysisModal(ticker) {
    currentTicker = ticker;
    modalTicker.textContent = ticker;
    modal.style.display = 'flex';

    // Reset modal state
    chartUpload.value = '';
    analyzeBtn.disabled = true;
    analysisLoading.style.display = 'none';
    analysisResult.style.display = 'none';
    uploadSection.style.display = 'block';
}

modalClose.addEventListener('click', () => {
    modal.style.display = 'none';
});

modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

chartUpload.addEventListener('change', () => {
    analyzeBtn.disabled = !chartUpload.files.length;
});

analyzeBtn.addEventListener('click', async () => {
    if (!chartUpload.files.length) return;

    const file = chartUpload.files[0];
    const base64 = await fileToBase64(file);

    // Show loading
    uploadSection.style.display = 'none';
    analysisLoading.style.display = 'block';
    analysisResult.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/api/analyze-chart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ticker: currentTicker,
                image_base64: base64.split(',')[1] // Remove data URL prefix
            })
        });

        const result = await response.json();

        if (result.success) {
            analysisResult.innerHTML = markdownToHtml(result.analysis);
        } else {
            analysisResult.innerHTML = `<p class="error">Error: ${result.error}</p>`;
        }

        analysisLoading.style.display = 'none';
        analysisResult.style.display = 'block';
    } catch (error) {
        console.error('Error:', error);
        analysisLoading.style.display = 'none';
        analysisResult.innerHTML = `<p class="error">Failed to analyze chart. Check backend.</p>`;
        analysisResult.style.display = 'block';
    }
});

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

function markdownToHtml(md) {
    // Simple markdown conversion
    return md
        .replace(/## (.*)/g, '<h2>$1</h2>')
        .replace(/### (.*)/g, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/---/g, '<hr>')
        .replace(/\n/g, '<br>');
}

