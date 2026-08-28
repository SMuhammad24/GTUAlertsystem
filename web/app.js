// GTU Circulars Portal - Interactive Frontend Logic with Charts & PWA

let allCirculars = [];
let currentCategory = 'ALL';
let searchQuery = '';
let searchTimeout = null;

// Register Service Worker for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js').catch(() => {});
    });
}

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchCirculars();
});

// Fetch summary metrics & Render Breakdown Chart
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        if (!res.ok) return;
        const data = await res.json();
        
        document.getElementById('stat-total').textContent = data.total || 0;
        document.getElementById('stat-today').textContent = data.today || 0;
        
        const categories = data.categories || {};
        const feeCount = categories['Fee & Penalty'] || 0;
        const examCount = categories['Exam & Timetable'] || categories['Exam'] || 0;
        
        document.getElementById('stat-fees').textContent = feeCount;
        document.getElementById('stat-exams').textContent = examCount;

        renderCategoryChart(categories, data.total || 1);
    } catch (err) {
        console.error('Error fetching stats:', err);
    }
}

// Render visual Category Distribution Bar
function renderCategoryChart(categories, total) {
    const bar = document.getElementById('category-bar');
    const legend = document.getElementById('category-legend');
    if (!bar || !legend) return;

    const colors = {
        'Fee & Penalty': '#f43f5e',
        'Exam & Timetable': '#38bdf8',
        'Result': '#10b981',
        'Admission & Enrollment': '#f59e0b',
        'Academics & Syllabus': '#a855f7',
        'General Circular': '#6b7280'
    };

    let barHtml = '';
    let legendHtml = '';

    const entries = Object.entries(categories);
    if (entries.length === 0) {
        bar.innerHTML = '<div class="bar-segment" style="width: 100%; background: #6366f1;"></div>';
        return;
    }

    entries.forEach(([cat, count]) => {
        const pct = Math.max(2, Math.round((count / total) * 100));
        const color = colors[cat] || '#6366f1';
        
        barHtml += `<div class="bar-segment" style="width: ${pct}%; background: ${color};" title="${cat}: ${count} (${pct}%)"></div>`;
        legendHtml += `
            <div class="legend-item">
                <span class="legend-dot" style="background: ${color};"></span>
                <span>${escapeHtml(cat)} (${count})</span>
            </div>
        `;
    });

    bar.innerHTML = barHtml;
    legend.innerHTML = legendHtml;
}

// Fetch Circulars list with query parameters
async function fetchCirculars() {
    const container = document.getElementById('circulars-container');
    const countText = document.getElementById('results-count-text');
    
    let url = `/api/circulars?limit=50`;
    if (currentCategory !== 'ALL') {
        url += `&category=${encodeURIComponent(currentCategory)}`;
    }
    if (searchQuery.trim()) {
        url += `&q=${encodeURIComponent(searchQuery.trim())}`;
    }

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error('Network response not ok');
        const circulars = await res.json();
        allCirculars = circulars;

        renderCirculars(circulars);
        countText.textContent = `Showing ${circulars.length} ${currentCategory === 'ALL' ? '' : currentCategory} circulars`;
    } catch (err) {
        container.innerHTML = `
            <div class="empty-state">
                <p>⚠️ Unable to load circulars. Please ensure server is running via <code>python main.py --web</code></p>
            </div>
        `;
    }
}

function getCategoryClass(cat) {
    if (!cat) return 'general';
    const c = cat.toLowerCase();
    if (c.includes('fee') || c.includes('penalty')) return 'fee';
    if (c.includes('exam') || c.includes('timetable')) return 'exam';
    if (c.includes('result')) return 'result';
    if (c.includes('admission') || c.includes('enrollment')) return 'admission';
    if (c.includes('academic') || c.includes('syllabus')) return 'academics';
    return 'general';
}

function getCalendarUrl(title, dateStr, link) {
    const eventTitle = encodeURIComponent(`GTU Notice: ${title.slice(0, 60)}`);
    const details = encodeURIComponent(`${title}\n\nPDF Link: ${link}`);
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${eventTitle}&details=${details}&location=GTU`;
}

function renderCirculars(list) {
    const container = document.getElementById('circulars-container');
    if (!list || list.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 12px; opacity: 0.5;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <h3>No circulars found</h3>
                <p>Try searching for a different branch, semester or keyword.</p>
            </div>
        `;
        return;
    }

    const html = list.map(c => {
        const catClass = getCategoryClass(c.category);
        const tags = c.tags ? c.tags.split(',').filter(Boolean) : [];
        
        let tagHtml = '';
        if (tags.length > 0) {
            tagHtml = `<div class="circular-tags-list">` +
                tags.map(t => `<span class="sub-tag">${escapeHtml(t.trim())}</span>`).join('') +
                `</div>`;
        }

        let deadlineHtml = '';
        if (c.deadlines && c.deadlines.length > 0) {
            deadlineHtml = `<div class="deadline-highlight">⏰ Key Dates: ${escapeHtml(c.deadlines.join(', '))}</div>`;
        }

        const calUrl = getCalendarUrl(c.title, c.date, c.link);

        return `
            <div class="circular-card">
                <div class="circular-main">
                    <div class="circular-meta">
                        <span class="category-tag ${catClass}">${escapeHtml(c.category || 'General')}</span>
                        <span class="circular-date">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            ${escapeHtml(c.date || 'Recent')}
                        </span>
                    </div>
                    <h2 class="circular-title">${escapeHtml(c.title)}</h2>
                    ${tagHtml}
                    ${deadlineHtml}
                </div>
                <div class="card-actions-group">
                    <a href="${escapeHtml(c.link)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                        <span>PDF</span>
                    </a>
                    <a href="${escapeHtml(calUrl)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" title="Add to Google Calendar">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        <span>+ Cal</span>
                    </a>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

// Category filter click
function setCategory(cat) {
    currentCategory = cat;
    document.querySelectorAll('#category-pills .pill').forEach(btn => {
        if (btn.dataset.category === cat) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    fetchCirculars();
}

// Search Handler with 250ms debounce
function handleSearch() {
    const val = document.getElementById('search-input').value;
    const clearBtn = document.getElementById('clear-search-btn');
    clearBtn.style.display = val ? 'block' : 'none';

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        searchQuery = val;
        fetchCirculars();
    }, 250);
}

function clearSearch() {
    const input = document.getElementById('search-input');
    input.value = '';
    document.getElementById('clear-search-btn').style.display = 'none';
    searchQuery = '';
    fetchCirculars();
}

// Trigger Live Scan
async function triggerScan() {
    const btn = document.getElementById('btn-scan');
    const text = document.getElementById('scan-text');
    const icon = document.getElementById('scan-icon');

    btn.disabled = true;
    text.textContent = 'Scanning GTU...';
    icon.style.animation = 'spin 0.8s linear infinite';

    try {
        const res = await fetch('/api/check-now', { method: 'POST' });
        const data = await res.json();
        
        showToast(data.message || 'Scan completed!');
        fetchStats();
        fetchCirculars();
    } catch (err) {
        showToast('⚠️ Scan request failed.');
    } finally {
        btn.disabled = false;
        text.textContent = 'Check GTU Portal';
        icon.style.animation = 'none';
    }
}

// Export CSV
function exportData(type) {
    if (!allCirculars || allCirculars.length === 0) {
        showToast('No data available to export.');
        return;
    }

    if (type === 'csv') {
        const headers = ['ID', 'Title', 'Date', 'Category', 'Link', 'Tags'];
        const rows = allCirculars.map(c => [
            `"${(c.id || '').replace(/"/g, '""')}"`,
            `"${(c.title || '').replace(/"/g, '""')}"`,
            `"${c.date || ''}"`,
            `"${c.category || ''}"`,
            `"${c.link || ''}"`,
            `"${c.tags || ''}"`
        ]);

        const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `gtu_circulars_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('📥 CSV downloaded successfully!');
    }
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
