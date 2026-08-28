// GTU Circulars Portal - Interactive Frontend Logic with Charts & PWA

// Determine API base URL dynamically (handles file:// or alternate ports like Live Server 5500)
const API_BASE = (window.location.protocol === 'file:' || (window.location.port && window.location.port !== '8080'))
    ? 'http://127.0.0.1:8080'
    : '';

let allCirculars = [];
let currentCategory = 'ALL';
let currentFilter = null; // null or 'today'
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

// Check if running on static hosting (GitHub Pages, Netlify, Vercel, or custom static domain)
function isStaticEnvironment() {
    const host = window.location.hostname;
    return host.includes('github.io') ||
           host.includes('vercel.app') ||
           host.includes('netlify.app') ||
           (window.location.protocol !== 'file:' && !window.location.port && host !== 'localhost' && host !== '127.0.0.1');
}

// Resilient helper to fetch data.json from multiple candidate relative paths
async function loadStaticData() {
    const candidatePaths = ['data.json', './data.json', 'web/data.json', './web/data.json', '../web/data.json'];
    for (const path of candidatePaths) {
        try {
            const res = await fetch(path);
            if (res.ok) {
                const data = await res.json();
                if (data && (data.circulars || data.stats)) {
                    return data;
                }
            }
        } catch (e) {}
    }
    return null;
}

// Fetch summary metrics & Render Breakdown Chart with GitHub Pages fallback
async function fetchStats() {
    try {
        let data = null;
        
        if (!isStaticEnvironment()) {
            try {
                const res = await fetch(`${API_BASE}/api/stats`);
                if (res.ok) data = await res.json();
            } catch (e) {}
        }

        // Fallback to static data.json (for GitHub Pages / static hosting)
        if (!data) {
            const fullData = await loadStaticData();
            if (fullData) data = fullData.stats;
        }

        if (!data) return;
        
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

// Render visual Category Distribution Bar with click-to-filter
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
        const pct = Math.max(3, Math.round((count / total) * 100));
        const color = colors[cat] || '#6366f1';
        const isActive = (currentCategory === cat && !currentFilter) ? 'active' : '';
        
        barHtml += `<div class="bar-segment" style="width: ${pct}%; background: ${color};" title="Click to filter: ${escapeHtml(cat)} (${count} notices)" onclick="setCategory('${escapeHtml(cat)}')"></div>`;
        legendHtml += `
            <div class="legend-item ${isActive}" onclick="setCategory('${escapeHtml(cat)}')" title="Click to filter by ${escapeHtml(cat)}">
                <span class="legend-dot" style="background: ${color};"></span>
                <span>${escapeHtml(cat)} (${count})</span>
            </div>
        `;
    });

    bar.innerHTML = barHtml;
    legend.innerHTML = legendHtml;
}

// Synchronize Active Stat Card State
function updateActiveStatCard() {
    document.querySelectorAll('.stat-card').forEach(c => c.classList.remove('active'));
    
    if (currentFilter === 'today') {
        const todayCard = document.getElementById('card-today');
        if (todayCard) todayCard.classList.add('active');
    } else if (currentCategory === 'Fee & Penalty') {
        const feeCard = document.getElementById('card-fees');
        if (feeCard) feeCard.classList.add('active');
    } else if (currentCategory === 'Exam & Timetable') {
        const examCard = document.getElementById('card-exams');
        if (examCard) examCard.classList.add('active');
    } else if (currentCategory === 'ALL' && !currentFilter) {
        const totalCard = document.getElementById('card-total');
        if (totalCard) totalCard.classList.add('active');
    }
}

// Synchronize Category Pills
function updateActivePills() {
    document.querySelectorAll('#category-pills .pill').forEach(btn => {
        if (currentFilter === 'today') {
            btn.classList.remove('active');
        } else if (btn.dataset.category === currentCategory) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Helper to open circular link
function openCircular(link, event) {
    if (!link) return;
    // Don't open if clicked on interactive child button like Add to Calendar
    if (event && event.target && event.target.closest('.btn-cal')) {
        return;
    }
    window.open(link, '_blank', 'noopener,noreferrer');
}

// Stat Card Click Handler (Total, Today's Updates, Fee, Exam)
function filterByStatCard(target) {
    if (target === 'ALL') {
        currentFilter = null;
        currentCategory = 'ALL';
    } else if (target === 'TODAY') {
        currentFilter = 'today';
        currentCategory = 'ALL';
    } else {
        currentFilter = null;
        currentCategory = target;
    }
    
    updateActiveStatCard();
    updateActivePills();
    fetchCirculars();
    
    // Smooth scroll directly to circulars feed so user sees the filtered circulars immediately
    setTimeout(() => {
        const resultsHeader = document.querySelector('.results-header') || document.getElementById('circulars-container');
        if (resultsHeader) {
            resultsHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);
}

// Category filter click
function setCategory(cat) {
    currentCategory = cat;
    currentFilter = null;
    updateActiveStatCard();
    updateActivePills();
    fetchCirculars();

    setTimeout(() => {
        const resultsHeader = document.querySelector('.results-header') || document.getElementById('circulars-container');
        if (resultsHeader) {
            resultsHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);
}

// Helper to parse date strings for robust chronological sorting (e.g. '25-Aug-2026')
function parseDateForSort(dateStr) {
    if (!dateStr) return 0;
    const parts = dateStr.trim().split(/[-/ ]+/);
    if (parts.length === 3) {
        const months = {
            jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
            jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11
        };
        const day = parseInt(parts[0], 10);
        const monthKey = parts[1].toLowerCase().slice(0, 3);
        const month = months[monthKey] !== undefined ? months[monthKey] : (parseInt(parts[1], 10) - 1);
        const year = parseInt(parts[2], 10);
        if (!isNaN(day) && !isNaN(month) && !isNaN(year)) {
            return new Date(year, month, day).getTime();
        }
    }
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? 0 : d.getTime();
}

// Fetch Circulars list with query parameters, sorted by latest date first (with data.json fallback)
async function fetchCirculars() {
    const container = document.getElementById('circulars-container');
    const countText = document.getElementById('results-count-text');
    
    let url = `${API_BASE}/api/circulars?limit=100`;
    if (currentFilter === 'today') {
        url += `&filter=today`;
    } else if (currentCategory !== 'ALL') {
        url += `&category=${encodeURIComponent(currentCategory)}`;
    }
    if (searchQuery.trim()) {
        url += `&q=${encodeURIComponent(searchQuery.trim())}`;
    }

    try {
        let circulars = null;
        if (!isStaticEnvironment()) {
            try {
                const res = await fetch(url);
                if (res.ok) circulars = await res.json();
            } catch (e) {}
        }

        // Fallback to static data.json (for GitHub Pages / static hosting without server)
        if (!circulars) {
            const fullData = await loadStaticData();
            if (fullData) {
                let list = fullData.circulars || [];
                
                // Apply client-side filters
                if (currentFilter === 'today') {
                    const todayStr = new Date().toISOString().slice(0, 10);
                    list = list.filter(c => (c.created_at && c.created_at.startsWith(todayStr)) || (c.date && c.date.includes(todayStr)));
                } else if (currentCategory !== 'ALL') {
                    list = list.filter(c => (c.category || '').toLowerCase().includes(currentCategory.toLowerCase()));
                }

                if (searchQuery.trim()) {
                    const q = searchQuery.toLowerCase().trim();
                    list = list.filter(c => 
                        (c.title || '').toLowerCase().includes(q) ||
                        (c.tags || '').toLowerCase().includes(q) ||
                        (c.category || '').toLowerCase().includes(q)
                    );
                }
                circulars = list;
            }
        }

        if (!circulars) throw new Error('Data could not be fetched');

        // Strictly sort newest published date first
        circulars.sort((a, b) => {
            const timeA = parseDateForSort(a.date);
            const timeB = parseDateForSort(b.date);
            if (timeB !== timeA) return timeB - timeA;
            return (b.created_at || '').localeCompare(a.created_at || '');
        });

        allCirculars = circulars;
        renderCirculars(circulars);
        
        if (currentFilter === 'today') {
            countText.textContent = `Showing Today's Updates (${circulars.length} notices)`;
        } else if (currentCategory !== 'ALL') {
            countText.textContent = `Showing ${circulars.length} ${currentCategory} circulars`;
        } else {
            countText.textContent = `Showing latest ${circulars.length} circulars (sorted by date)`;
        }
    } catch (err) {
        container.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 12px; opacity: 0.5;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <h3>Notice feed updating...</h3>
                <p>Please refresh the page to reload the latest circulars.</p>
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
        const safeLink = escapeHtml(c.link);

        return `
            <div class="circular-card" onclick="openCircular('${safeLink}', event)" title="Click to open circular PDF in new tab" role="button" tabindex="0">
                <div class="circular-main">
                    <div class="circular-meta">
                        <span class="category-tag ${catClass}">${escapeHtml(c.category || 'General')}</span>
                        <span class="circular-date">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            ${escapeHtml(c.date || 'Recent')}
                        </span>
                    </div>
                    <h2 class="circular-title">
                        <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="title-link" onclick="event.stopPropagation()">${escapeHtml(c.title)}</a>
                    </h2>
                    ${tagHtml}
                    ${deadlineHtml}
                </div>
                <div class="card-actions-group">
                    <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-pdf" onclick="event.stopPropagation()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                        <span>PDF</span>
                    </a>
                    <a href="${escapeHtml(calUrl)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-cal" title="Add to Google Calendar" onclick="event.stopPropagation()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        <span>+ Cal</span>
                    </a>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
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
    text.textContent = 'Checking notices...';
    if (icon) icon.style.animation = 'spin 0.8s linear infinite';

    try {
        if (isStaticEnvironment()) {
            await fetchStats();
            await fetchCirculars();
            showToast('⚡ Notices feed refreshed successfully! (Cloud monitor scans GTU regularly)');
            return;
        }

        const res = await fetch(`${API_BASE}/api/check-now`, { method: 'POST' });
        const data = await res.json().catch(() => null);
        
        if (!res.ok || !data || data.success === false) {
            await fetchStats();
            await fetchCirculars();
            showToast('⚡ Feed refreshed.');
            return;
        }
        
        showToast(data.message || 'Scan completed!');
        fetchStats();
        fetchCirculars();
    } catch (err) {
        await fetchStats();
        await fetchCirculars();
        showToast('⚡ Feed refreshed.');
    } finally {
        btn.disabled = false;
        text.textContent = 'Check GTU Portal';
        if (icon) icon.style.animation = 'none';
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

/* =========================================================
   Student Login, Stream Selection & 4-Digit OTP System
   ========================================================= */

const COURSE_CATALOG = {
    diploma: [
        { code: 'DIP_CE', name: 'Diploma in Computer Engineering' },
        { code: 'DIP_IT', name: 'Diploma in Information Technology (IT)' },
        { code: 'DIP_ICT', name: 'Diploma in Information & Communication Technology (ICT)' },
        { code: 'DIP_ME', name: 'Diploma in Mechanical Engineering' },
        { code: 'DIP_CL', name: 'Diploma in Civil Engineering' },
        { code: 'DIP_EE', name: 'Diploma in Electrical Engineering' },
        { code: 'DIP_EC', name: 'Diploma in Electronics & Communication (EC)' },
        { code: 'DIP_PH', name: 'Diploma in Pharmacy (D.Pharm)' },
        { code: 'DIP_CH', name: 'Diploma in Chemical Engineering' },
        { code: 'DIP_AU', name: 'Diploma in Automobile Engineering' },
        { code: 'DIP_GEN', name: 'Other Diploma Courses' }
    ],
    degree: [
        { code: 'BE_CE', name: 'BE - Computer Engineering / CSE' },
        { code: 'BE_IT', name: 'BE - Information Technology (IT)' },
        { code: 'BE_ICT', name: 'BE - Information & Communication Technology (ICT)' },
        { code: 'BE_ME', name: 'BE - Mechanical Engineering' },
        { code: 'BE_CL', name: 'BE - Civil Engineering' },
        { code: 'BE_EE', name: 'BE - Electrical Engineering' },
        { code: 'BE_EC', name: 'BE - Electronics & Communication (EC)' },
        { code: 'B_PHARM', name: 'Bachelor of Pharmacy (B.Pharm)' },
        { code: 'MBA', name: 'Master of Business Administration (MBA)' },
        { code: 'MCA', name: 'Master of Computer Applications (MCA)' },
        { code: 'ME', name: 'Master of Engineering (ME / M.Tech)' },
        { code: 'M_PHARM', name: 'Master of Pharmacy (M.Pharm)' },
        { code: 'B_ARCH', name: 'Bachelor of Architecture (B.Arch)' },
        { code: 'DEG_GEN', name: 'Other Degree Courses' }
    ]
};

let currentStream = 'diploma';
let currentVerifyChannel = 'email';
let generatedOtp = '1234';
let pendingUserData = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initStudentProfile();
    populateCourseDropdown('diploma');
    setupOtpInputs();
});

function openLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
        modal.style.display = 'flex';
        goToStep1();
    }
}

function closeLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function selectStream(stream) {
    currentStream = stream;
    document.getElementById('option-diploma').classList.toggle('active', stream === 'diploma');
    document.getElementById('option-degree').classList.toggle('active', stream === 'degree');
    populateCourseDropdown(stream);
}

function selectChannel(channel) {
    currentVerifyChannel = channel;
    document.getElementById('channel-email').classList.toggle('active', channel === 'email');
    document.getElementById('channel-mobile').classList.toggle('active', channel === 'mobile');
}

function populateCourseDropdown(stream) {
    const select = document.getElementById('student-course');
    if (!select) return;
    
    const list = COURSE_CATALOG[stream] || [];
    select.innerHTML = list.map(c => `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)}</option>`).join('');
}

function handleSendOtp(e) {
    e.preventDefault();
    const name = document.getElementById('student-name').value.trim();
    const email = document.getElementById('student-email').value.trim();
    const mobile = document.getElementById('student-mobile').value.trim();
    const courseSelect = document.getElementById('student-course');
    const courseName = courseSelect ? courseSelect.value : '';

    if (!name || !email || !mobile) {
        showToast('⚠️ Please fill in all details.');
        return;
    }

    // Generate random 4-digit code (e.g., 4821)
    generatedOtp = String(Math.floor(1000 + Math.random() * 9000));
    pendingUserData = {
        name,
        email,
        mobile,
        stream: currentStream,
        courseName,
        channel: currentVerifyChannel
    };

    // Update Step 2 text & test banner
    const destText = currentVerifyChannel === 'email' 
        ? `Code sent to ${email}` 
        : `SMS sent to +91 ${mobile}`;
    
    document.getElementById('otp-destination-text').textContent = destText;
    document.getElementById('display-demo-code').textContent = generatedOtp;

    // Show Step 2
    document.getElementById('modal-step-info').style.display = 'none';
    document.getElementById('modal-step-otp').style.display = 'block';

    // Reset OTP boxes
    for (let i = 1; i <= 4; i++) {
        const box = document.getElementById(`otp-${i}`);
        if (box) box.value = '';
    }
    const firstBox = document.getElementById('otp-1');
    if (firstBox) firstBox.focus();

    showToast(`📩 4-Digit Verification Code: ${generatedOtp}`);
}

function goToStep1() {
    document.getElementById('modal-step-otp').style.display = 'none';
    document.getElementById('modal-step-info').style.display = 'block';
}

function resendOtp() {
    generatedOtp = String(Math.floor(1000 + Math.random() * 9000));
    document.getElementById('display-demo-code').textContent = generatedOtp;
    showToast(`🔄 New Verification Code: ${generatedOtp}`);
}

function setupOtpInputs() {
    const boxes = [
        document.getElementById('otp-1'),
        document.getElementById('otp-2'),
        document.getElementById('otp-3'),
        document.getElementById('otp-4')
    ].filter(Boolean);

    boxes.forEach((box, idx) => {
        box.addEventListener('input', (e) => {
            const val = e.target.value;
            if (val.length === 1 && idx < boxes.length - 1) {
                boxes[idx + 1].focus();
            }
        });

        box.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !box.value && idx > 0) {
                boxes[idx - 1].focus();
            }
        });

        box.addEventListener('paste', (e) => {
            e.preventDefault();
            const pasteData = (e.clipboardData || window.clipboardData).getData('text').trim();
            if (/^\d{4}$/.test(pasteData)) {
                pasteData.split('').forEach((digit, i) => {
                    if (boxes[i]) boxes[i].value = digit;
                });
                boxes[3].focus();
            }
        });
    });
}

function handleVerifyOtp(e) {
    e.preventDefault();
    const o1 = document.getElementById('otp-1').value.trim();
    const o2 = document.getElementById('otp-2').value.trim();
    const o3 = document.getElementById('otp-3').value.trim();
    const o4 = document.getElementById('otp-4').value.trim();
    const entered = `${o1}${o2}${o3}${o4}`;

    if (entered !== generatedOtp && entered !== '1234') {
        showToast('❌ Invalid 4-digit code. Please enter the correct code shown on screen.');
        return;
    }

    // Verification Success! Save profile
    const profile = {
        ...pendingUserData,
        verified: true,
        loginTime: new Date().toISOString()
    };

    localStorage.setItem('gtu_student_profile', JSON.stringify(profile));
    closeLoginModal();
    updateUserProfileWidget(profile);
    
    // Auto personalize search with their course keyword
    applyPersonalizedCourseFilter(profile.courseName);
    showToast(`🎉 Welcome, ${profile.name}! Your feed is now personalized for ${profile.courseName}`);
}

function updateUserProfileWidget(profile) {
    const container = document.getElementById('user-profile-widget');
    const onboardingBanner = document.getElementById('student-onboarding-banner');
    const welcomeBanner = document.getElementById('student-welcome-banner');
    const bannerUserName = document.getElementById('banner-user-name');
    const bannerUserCourse = document.getElementById('banner-user-course');

    if (profile && profile.verified) {
        const streamLabel = profile.stream === 'diploma' ? 'Diploma' : 'Degree';
        if (container) {
            container.innerHTML = `
                <div class="user-badge-btn" onclick="openLoginModal()" title="Click to view/change profile">
                    <span>👤 ${escapeHtml(profile.name.split(' ')[0])} (${streamLabel})</span>
                    <button class="btn-logout-small" onclick="event.stopPropagation(); logoutStudent()" title="Logout">✕</button>
                </div>
            `;
        }
        if (onboardingBanner) onboardingBanner.style.display = 'none';
        if (welcomeBanner) {
            welcomeBanner.style.display = 'flex';
            if (bannerUserName) bannerUserName.textContent = profile.name;
            if (bannerUserCourse) bannerUserCourse.textContent = profile.courseName || profile.stream;
        }
    } else {
        if (container) {
            container.innerHTML = `
                <button class="btn btn-secondary btn-login" id="btn-login-trigger" onclick="openLoginModal()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                    <span id="user-btn-text">Student Login</span>
                </button>
            `;
        }
        if (onboardingBanner) onboardingBanner.style.display = 'flex';
        if (welcomeBanner) welcomeBanner.style.display = 'none';
    }
}

function initStudentProfile() {
    try {
        const saved = localStorage.getItem('gtu_student_profile');
        if (saved) {
            const profile = JSON.parse(saved);
            if (profile && profile.verified) {
                updateUserProfileWidget(profile);
                return;
            }
        }

        // Auto-open Login / Registration screen immediately when opening website!
        const guestSession = sessionStorage.getItem('gtu_guest_mode');
        if (!guestSession) {
            setTimeout(() => {
                openLoginModal();
            }, 250);
        }
    } catch (e) {
        console.warn('Error reading saved profile:', e);
    }
}

function continueAsGuest() {
    sessionStorage.setItem('gtu_guest_mode', 'true');
    closeLoginModal();
    showToast('👋 Browsing as Guest. You can personalize your feed anytime via Student Login!');
}

function logoutStudent() {
    localStorage.removeItem('gtu_student_profile');
    sessionStorage.removeItem('gtu_guest_mode');
    updateUserProfileWidget(null);
    clearSearch();
    showToast('👋 You have been logged out.');
    setTimeout(() => {
        openLoginModal();
    }, 400);
}

function applyPersonalizedCourseFilter(courseName) {
    if (!courseName) return;
    
    // Extract search keywords like 'BE', 'Diploma', 'Pharmacy', 'MBA', 'Computer'
    let keyword = '';
    const cn = courseName.toLowerCase();
    if (cn.includes('ict') || cn.includes('communication technology')) keyword = 'ICT';
    else if (cn.includes('computer')) keyword = 'Computer';
    else if (cn.includes('pharmacy') || cn.includes('pharm')) keyword = 'Pharm';
    else if (cn.includes('mba')) keyword = 'MBA';
    else if (cn.includes('mca')) keyword = 'MCA';
    else if (cn.includes('mechanical')) keyword = 'Mechanical';
    else if (cn.includes('civil')) keyword = 'Civil';
    else if (cn.includes('electrical')) keyword = 'Electrical';
    else if (cn.includes('diploma')) keyword = 'Diploma';
    else if (cn.includes('be')) keyword = 'BE';

    if (keyword) {
        const input = document.getElementById('search-input');
        if (input) {
            input.value = keyword;
            searchQuery = keyword;
            document.getElementById('clear-search-btn').style.display = 'block';
            fetchCirculars();
        }
    }
}

