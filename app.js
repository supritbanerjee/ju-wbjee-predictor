// Application Logic for JU FET Branch Predictor 2026

// Global State
let dataset = null;
let currentChannel = 'wbjee';

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    try {
        // Load dataset directly from global variable defined in data.js to bypass file:// protocol CORS block
        dataset = CUTOFF_DATA;
        
        // Setup initial dropdowns
        switchChannel('wbjee');
        
        // Setup navigation active state based on scroll
        setupScrollSpy();
        
        // Initial run for Cutoff Explorer filters
        updateExplorerFilters();
    } catch (error) {
        console.error("Error initializing cutoff data:", error);
        alert("Failed to initialize cutoff data. Please check that data.js is loaded correctly.");
    }
});

// Setup ScrollSpy for Nav Links
function setupScrollSpy() {
    const sections = document.querySelectorAll('.scroll-offset');
    const navLinks = document.querySelectorAll('.nav-link');
    
    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= (sectionTop - 120)) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').slice(1) === current) {
                link.classList.add('active');
            }
        });
    });
}

// Helper to normalize branch names cleanly and eliminate duplicates
function normalizeBranchName(branchName) {
    if (!branchName) return '';
    if (branchName.includes("Construction Engineering")) {
        return "Construction Engineering";
    }
    return branchName;
}

// Switch Admission Channels (tabs)
function switchChannel(channel) {
    currentChannel = channel;
    
    // Toggle active tab button
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeTab = document.getElementById(`tab-${channel}`);
    if (activeTab) activeTab.classList.add('active');
    
    // Update Quota display (Always hide for WBJEE / B.Pharm)
    const quotaGroup = document.getElementById('quota-group');
    if (quotaGroup) {
        quotaGroup.classList.add('hidden-quota');
        document.getElementById('user-quota').value = 'HS';
    }
    
    // Update Rank input hint
    const rankHint = document.getElementById('rank-hint');
    if (rankHint) {
        if (channel === 'wbjee') {
            rankHint.textContent = "Enter your WBJEE General Merit Rank (GMR).";
        } else if (channel === 'bpharm') {
            rankHint.textContent = "Enter your WBJEE Pharmacy Merit Rank (PMR).";
        }
    }
    
    // Reset Form and Results
    document.getElementById('user-rank').value = '';
    document.getElementById('results-container').classList.add('hidden');
    document.getElementById('welcome-dashboard').classList.remove('hidden');
    
    // Populate Categories
    populateCategories(channel);
}

// Populate Categories dropdown dynamically based on selected channel
function populateCategories(channel) {
    const categorySelect = document.getElementById('user-category');
    categorySelect.innerHTML = '<option value="" disabled selected>Select category...</option>';
    
    if (!dataset || !dataset[channel]) return;
    
    // Get unique categories for this channel
    const categories = new Set();
    dataset[channel].forEach(item => {
        if (item.category) categories.add(item.category);
    });
    
    // Sort categories, placing General first
    const sortedCategories = Array.from(categories).sort((a, b) => {
        if (a === 'General') return -1;
        if (b === 'General') return 1;
        return a.localeCompare(b);
    });
    
    sortedCategories.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat;
        categorySelect.appendChild(opt);
    });
}

// Category fallback helper for robust predictions (handles OBC-A/B matching 2022 generic OBC)
function getMatchingCategories(selectedCat) {
    const matches = [selectedCat];
    if (selectedCat === 'OBC-A' || selectedCat === 'OBC-B') {
        matches.push('OBC');
    }
    if (selectedCat === 'General-PwD' || selectedCat === 'SC-PwD' || selectedCat === 'ST-PwD') {
        matches.push('PwD');
    }
    return matches;
}

// Predict Branches
function handlePrediction(event) {
    event.preventDefault();
    
    const rankInput = document.getElementById('user-rank');
    const categorySelect = document.getElementById('user-category');
    
    const userRank = parseInt(rankInput.value, 10);
    const selectedCategory = categorySelect.value;
    
    if (isNaN(userRank) || userRank <= 0) {
        alert("Please enter a valid positive rank.");
        return;
    }
    
    if (!selectedCategory) {
        alert("Please select your category.");
        return;
    }
    
    // Hide welcome dashboard and show results container
    document.getElementById('welcome-dashboard').classList.add('hidden');
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.classList.remove('hidden');
    
    // Update Results Headers
    document.getElementById('res-rank').textContent = userRank;
    document.getElementById('res-cat').textContent = selectedCategory;
    
    // Process matching data
    const records = dataset[currentChannel] || [];
    const matchingCats = getMatchingCategories(selectedCategory);
    
    // Group records by sanitized branch names
    const branchDataMap = {};
    records.forEach(rec => {
        if (matchingCats.includes(rec.category)) {
            const branch = normalizeBranchName(rec.branch);
            if (!branchDataMap[branch]) {
                branchDataMap[branch] = [];
            }
            branchDataMap[branch].push(rec);
        }
    });
    
    const results = [];
    let countSafe = 0;
    let countModerate = 0;
    let countLow = 0;
    
    // Run prediction scoring for each branch
    for (const [branch, branchRecords] of Object.entries(branchDataMap)) {
        
        // Group all rounds by year to ensure comprehensive calculations
        const yearRoundData = {};
        branchRecords.forEach(rec => {
            const yr = rec.year;
            if (!yearRoundData[yr]) {
                yearRoundData[yr] = [];
            }
            yearRoundData[yr].push(rec);
        });
        
        const years = Object.keys(yearRoundData).map(Number).sort((a, b) => b - a);
        if (years.length === 0) continue;
        
        // Predict probability based on checking across ALL structural entries
        let score = 0;
        let validEntryCount = 0;
        
        branchRecords.forEach(rec => {
            const cr = rec.cr;
            validEntryCount++;
            if (userRank <= cr) {
                score += 1.0; // fully safe entry point
            } else if (userRank <= cr * 1.15) {
                score += 0.4; // borderline chance entry point
            }
        });
        
        const probability = validEntryCount > 0 ? (score / validEntryCount) : 0;
        let safetyLabel = '';
        let safetyClass = '';
        
        if (probability >= 0.7) {
            safetyLabel = 'Highly Likely';
            safetyClass = 'safe';
            countSafe++;
        } else if (probability >= 0.25) {
            safetyLabel = 'Borderline Chance';
            safetyClass = 'moderate';
            countModerate++;
        } else {
            safetyLabel = 'Low Chance';
            safetyClass = 'low';
            countLow++;
        }
        
        // Determine latest entries for display tags
        const latestYear = Math.max(...years);
        const latestRecords = yearRoundData[latestYear] || [];
        // Sort descending to make sure the final cutoff round is picked as reference indicator
        latestRecords.sort((a, b) => (b.cr - a.cr));
        const referenceLatestRecord = latestRecords[0] || { cr: 0, or: 0 };
        
        results.push({
            branch: branch,
            probability: probability,
            safetyLabel: safetyLabel,
            safetyClass: safetyClass,
            branchRecords: branchRecords.sort((a, b) => {
                if (a.year !== b.year) return a.year - b.year; // ascending years
                return (a.round || '').localeCompare(b.round || ''); // sequential rounds
            }),
            latestYear: latestYear,
            latestCR: referenceLatestRecord.cr,
            years: Array.from(new Set(years)).sort((a, b) => a - b) // ascending unique years for trend mapping
        });
    }
    
    // Sort results: Safe -> Moderate -> Low, then by closing rank in latest year
    results.sort((a, b) => {
        const safetyOrder = { 'safe': 1, 'moderate': 2, 'low': 3 };
        if (safetyOrder[a.safetyClass] !== safetyOrder[b.safetyClass]) {
            return safetyOrder[a.safetyClass] - safetyOrder[b.safetyClass];
        }
        return a.latestCR - b.latestCR;
    });
    
    // Update summary counts
    document.getElementById('count-safe').textContent = countSafe;
    document.getElementById('count-moderate').textContent = countModerate;
    document.getElementById('count-low').textContent = countLow;
    
    // Store results globally to prevent quote conflicts in inline HTML attributes
    window.currentResults = results;
    
    // Render list
    renderResultsList(results, userRank);
}

// Render Results List
function renderResultsList(results, userRank) {
    const listContainer = document.getElementById('results-list-target');
    listContainer.innerHTML = '';
    
    if (results.length === 0) {
        listContainer.innerHTML = `
            <div class="glass-card text-center" style="padding: 40px;">
                <i class="fa-solid fa-folder-open" style="font-size: 3rem; color: var(--color-text-muted); margin-bottom: 16px;"></i>
                <h4>No Matching Data Found</h4>
                <p style="color: var(--color-text-muted); margin-top: 8px;">We do not have historical cutoff records for this category in the selected entry channel.</p>
            </div>
        `;
        return;
    }
    
    results.forEach((res, index) => {
        const cardId = `branch-card-${index}`;
        const card = document.createElement('div');
        card.className = 'branch-card';
        card.id = cardId;
        
        // Render all counseling entries (Round 1, Round 2, etc.) in details table
        let tableRowsHTML = '';
        res.branchRecords.forEach(rec => {
            tableRowsHTML += `
                <tr>
                    <td><strong>${rec.year}</strong></td>
                    <td>${rec.round || 'Final'}</td>
                    <td class="text-center">${rec.or || '—'}</td>
                    <td class="text-center font-weight-bold" style="color: var(--color-gold);">${rec.cr}</td>
                </tr>
            `;
        });
        
        card.innerHTML = `
            <div class="branch-card-header" onclick="toggleCard('${cardId}', ${index}, ${userRank})">
                <div class="branch-title-area">
                    <span class="branch-title">${res.branch}</span>
                    <div class="branch-meta">
                        <span><i class="fa-solid fa-calendar-days"></i> Data available: ${res.years.join(', ')}</span>
                        <span><i class="fa-solid fa-graduation-cap"></i> Latest Max CR (${res.latestYear}): <strong>${res.latestCR}</strong></span>
                    </div>
                </div>
                <div style="display: flex; align-items: center;">
                    <span class="prob-badge prob-badge-${res.safetyClass}">
                        <i class="fa-solid ${res.safetyClass === 'safe' ? 'fa-circle-check' : res.safetyClass === 'moderate' ? 'fa-circle-info' : 'fa-circle-xmark'}"></i>
                        ${res.safetyLabel}
                    </span>
                    <i class="fa-solid fa-chevron-down expand-icon"></i>
                </div>
            </div>
            <div class="branch-card-details">
                <div class="details-inner">
                    <div class="chart-container">
                        <span class="chart-title">Cutoff Trend vs Your Rank (${userRank})</span>
                        <div id="chart-svg-container-${cardId}">
                            </div>
                    </div>
                    <div class="details-table-container">
                        <span class="details-table-title">Historical Counselling Rounds Summary</span>
                        <table class="details-table">
                            <thead>
                                <tr>
                                    <th>Year</th>
                                    <th>Round</th>
                                    <th class="text-center">Opening Rank</th>
                                    <th class="text-center">Closing Rank</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tableRowsHTML}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        listContainer.appendChild(card);
    });
}

// Toggle expansion of branch detail cards
function toggleCard(cardId, resIndex, userRank) {
    const card = document.getElementById(cardId);
    const isExpanded = card.classList.contains('expanded');
    
    // Close other expanded cards
    document.querySelectorAll('.branch-card').forEach(c => {
        if (c.id !== cardId) c.classList.remove('expanded');
    });
    
    if (!isExpanded) {
        card.classList.add('expanded');
        const res = window.currentResults[resIndex];
        // Render chart SVG
        renderCutoffChart(cardId, res, userRank);
    } else {
        card.classList.remove('expanded');
    }
}

// Render dynamic SVG Line Chart
function renderCutoffChart(cardId, res, userRank) {
    const container = document.getElementById(`chart-svg-container-${cardId}`);
    if (!container) return;
    
    const width = 320;
    const height = 140;
    const paddingLeft = 40;
    const paddingRight = 20;
    const paddingTop = 20;
    const paddingBottom = 20;
    
    // Compile peak structural points per year for dynamic vector pathing
    const dataPoints = [];
    res.years.forEach(yr => {
        const yearRecords = res.branchRecords.filter(r => r.year === yr);
        if (yearRecords.length > 0) {
            // Pick max entry rank of that season for trending line points
            const maxCr = Math.max(...yearRecords.map(r => r.cr));
            dataPoints.push({ year: yr, cr: maxCr });
        }
    });
    
    const ranks = dataPoints.map(d => d.cr).concat([userRank]);
    const maxRank = Math.max(...ranks);
    const minRank = Math.min(...ranks);
    
    const rankRange = maxRank - minRank;
    const yMax = maxRank + (rankRange > 0 ? rankRange * 0.15 : 50);
    const yMin = Math.max(1, minRank - (rankRange > 0 ? rankRange * 0.15 : 50));
    
    const getX = (year) => {
        const yearIndex = year - 2022; // index positions mapping 2022-2025
        const chartWidth = width - paddingLeft - paddingRight;
        return paddingLeft + (yearIndex / 3) * chartWidth;
    };
    
    const getY = (rank) => {
        const chartHeight = height - paddingTop - paddingBottom;
        const ratio = (rank - yMin) / (yMax - yMin);
        return height - paddingBottom - ratio * chartHeight;
    };
    
    const coords = dataPoints.map(d => `${getX(d.year)},${getY(d.cr)}`);
    const linePath = coords.join(' ');
    const userRankY = getY(userRank);
    
    let svgContent = `
        <svg class="chart-svg" viewBox="0 0 ${width} ${height}">
            <line x1="${paddingLeft}" y1="${paddingTop}" x2="${width - paddingRight}" y2="${paddingTop}" stroke="rgba(255,255,255,0.05)" />
            <line x1="${paddingLeft}" y1="${height - paddingBottom}" x2="${width - paddingRight}" y2="${height - paddingBottom}" stroke="rgba(255,255,255,0.15)" />
            
            <text x="${paddingLeft - 8}" y="${paddingTop + 4}" font-family="var(--font-body)" font-size="8" fill="var(--color-text-muted)" text-anchor="end">${Math.round(yMin)}</text>
            <text x="${paddingLeft - 8}" y="${height - paddingBottom + 3}" font-family="var(--font-body)" font-size="8" fill="var(--color-text-muted)" text-anchor="end">${Math.round(yMax)}</text>
            
            ${[2022, 2023, 2024, 2025].map(yr => `
                <text x="${getX(yr)}" y="${height - 4}" font-family="var(--font-body)" font-size="8" fill="var(--color-text-muted)" text-anchor="middle">${yr}</text>
                <line x1="${getX(yr)}" y1="${height - paddingBottom}" x2="${getX(yr)}" y2="${height - paddingBottom + 3}" stroke="rgba(255,255,255,0.2)" />
            `).join('')}
            
            <line x1="${paddingLeft}" y1="${userRankY}" x2="${width - paddingRight}" y2="${userRankY}" stroke="var(--color-gold)" stroke-width="1.5" stroke-dasharray="3,3" />
            <text x="${width - paddingRight}" y="${userRankY - 4}" font-family="var(--font-heading)" font-size="8" font-weight="700" fill="var(--color-gold)" text-anchor="end">Your Rank: ${userRank}</text>
            
            ${coords.length > 1 ? `<polyline points="${linePath}" fill="none" stroke="var(--color-red-glow)" stroke-width="2.5" class="chart-line" />` : ''}
            
            ${dataPoints.map(d => `
                <circle cx="${getX(d.year)}" cy="${getY(d.cr)}" r="4.5" fill="var(--color-bg-dark)" stroke="var(--color-red-deep)" stroke-width="2" class="chart-dot" />
                <text x="${getX(d.year)}" y="${getY(d.cr) - 8}" font-family="var(--font-body)" font-size="8.5" font-weight="600" fill="var(--color-text-white)" text-anchor="middle">${d.cr}</text>
            `).join('')}
        </svg>
    `;
    
    container.innerHTML = svgContent;
}


// --- HISTORICAL CUTOFF EXPLORER FUNCTIONS ---

// Update filters dynamically when channel changes in Cutoff Explorer
function updateExplorerFilters() {
    if (!dataset) return;
    
    const channel = document.getElementById('exp-channel').value;
    const records = dataset[channel] || [];
    
    // Unique Categories
    const categories = new Set();
    const branches = new Set();
    
    records.forEach(rec => {
        if (rec.category) categories.add(rec.category);
        if (rec.branch) branches.add(normalizeBranchName(rec.branch));
    });
    
    // Populate Categories Filter
    const catSelect = document.getElementById('exp-category');
    catSelect.innerHTML = '<option value="all">All Categories</option>';
    Array.from(categories).sort().forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat;
        catSelect.appendChild(opt);
    });
    
    // Populate Branches Filter
    const branchSelect = document.getElementById('exp-branch');
    branchSelect.innerHTML = '<option value="all">All Branches</option>';
    Array.from(branches).sort().forEach(br => {
        const opt = document.createElement('option');
        opt.value = br;
        opt.textContent = br;
        branchSelect.appendChild(opt);
    });
    
    // Run search to show initial table rows
    runExplorerSearch();
}

// Filter and render Cutoff Explorer Table
function runExplorerSearch() {
    const tableBody = document.getElementById('explorer-table-body');
    if (!dataset || !tableBody) return;
    
    const channel = document.getElementById('exp-channel').value;
    const yearFilter = document.getElementById('exp-year').value;
    const catFilter = document.getElementById('exp-category').value;
    const branchFilter = document.getElementById('exp-branch').value;
    
    const records = dataset[channel] || [];
    
    // Filter records
    const filteredRecords = records.filter(rec => {
        const normalizedBranchName = normalizeBranchName(rec.branch);
        const matchYear = (yearFilter === 'all' || String(rec.year) === yearFilter);
        const matchCat = (catFilter === 'all' || rec.category === catFilter);
        const matchBranch = (branchFilter === 'all' || normalizedBranchName === branchFilter);
        return matchYear && matchCat && matchBranch;
    });
    
    // Sort records: Year desc, Branch asc, Category asc, Round asc
    filteredRecords.sort((a, b) => {
        const branchA = normalizeBranchName(a.branch);
        const branchB = normalizeBranchName(b.branch);
        if (a.year !== b.year) return b.year - a.year;
        if (branchA !== branchB) return branchA.localeCompare(branchB);
        if (a.category !== b.category) return a.category.localeCompare(b.category);
        const aRound = a.round || '';
        const bRound = b.round || '';
        return aRound.localeCompare(bRound);
    });
    
    // Render table rows
    tableBody.innerHTML = '';
    
    if (filteredRecords.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center" style="padding: 30px; color: var(--color-text-muted);">
                    <i class="fa-solid fa-circle-exclamation" style="font-size: 1.5rem; margin-bottom: 8px; display: block;"></i>
                    No cutoff records found matching the active filters.
                </td>
            </tr>
        `;
        return;
    }
    
    filteredRecords.forEach(rec => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${rec.year}</strong></td>
            <td>${normalizeBranchName(rec.branch)}</td>
            <td><span class="badge-cat">${rec.category}</span></td>
            <td>${rec.quota || '—'}</td>
            <td>${rec.round || 'Final'}</td>
            <td class="text-center">${rec.or || '—'}</td>
            <td class="text-center" style="font-weight: 600; color: var(--color-gold);">${rec.cr}</td>
        `;
        tableBody.appendChild(row);
    });
}