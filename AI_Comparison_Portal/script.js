/**
 * AI Coding Assistants Comparison Portal
 * Simplified version with embedded data
 */

// Tool Data (embedded for file:// compatibility)
const TOOLS_DATA = [
    {
        id: "tool-copilot",
        name: "GitHub Copilot",
        subtitle: "(Microsoft)",
        category: "IDE Extension",
        iconHtml: '<i class="fa-brands fa-github"></i>',
        tagline: "The industry standard for AI pair programming",
        description: "Pioneer in AI pair programming with deep IDE integration, enterprise-grade security, and Agent Mode for autonomous coding.",
        pricing: "$10/mo Pro | $39/mo Pro+",
        highlights: ["Agent Mode", "192k context", "Enterprise SSO"],
        advantages: ["Seamless VS Code & JetBrains integration", "Enterprise security with IP indemnification", "Agent Mode with multi-model support"],
        disadvantages: ["Pro+ required for full agentic capabilities", "Cloud-only, no offline mode"],
        customers: ["Shopify", "Stripe", "Mercedes-Benz"],
        company: "GitHub (Microsoft)",
        primaryInterface: "IDE Extension",
        autonomousExecution: "Yes (Agent Mode)",
        multiFileRefactoring: "Excellent",
        modelAccess: "GPT-4o, O3, Claude 4",
        contextWindow: "192k tokens",
        ideSupport: "VS Code, JetBrains, Visual Studio",
        freeTier: "Yes (2000/mo)",
        localModels: "No",
        securityFeatures: "SSO, Audit Logs, IP Indemnification"
    },
    {
        id: "tool-cursor",
        name: "Cursor",
        subtitle: "(Anysphere)",
        category: "AI-First IDE",
        iconHtml: '<i class="fa-solid fa-terminal"></i>',
        tagline: "The AI-native code editor developers love",
        description: "VS Code fork built around AI with Composer for multi-file edits and background agents for autonomous tasks.",
        pricing: "$20/mo Pro | $40/mo Business",
        highlights: ["Composer", "Background Agents", "Instant Apply"],
        advantages: ["Composer for massive codebase refactors", "Ultra-fast iterations with instant apply", "Full VS Code extension compatibility"],
        disadvantages: ["Requires switching from your IDE", "Premium credits deplete quickly"],
        customers: ["Midjourney", "Vercel", "Notion"],
        company: "Anysphere",
        primaryInterface: "Custom IDE",
        autonomousExecution: "Yes (Composer + Agents)",
        multiFileRefactoring: "Exceptional",
        modelAccess: "Claude 4, GPT-4o, O3, Gemini",
        contextWindow: "Unlimited",
        ideSupport: "Cursor (VS Code Fork)",
        freeTier: "Yes (Limited)",
        localModels: "Yes",
        securityFeatures: "Privacy Mode, SOC2"
    },
    {
        id: "tool-claude",
        name: "Claude Code",
        subtitle: "(Anthropic)",
        category: "CLI Agent",
        iconHtml: '<i class="fa-solid fa-cube"></i>',
        tagline: "Terminal-native AI agent with superior reasoning",
        description: "Agentic CLI tool built on Claude 4 with extended thinking. Manipulates repos directly from terminal.",
        pricing: "$20/mo Pro | $100/mo Max",
        highlights: ["CLI Native", "200k+ context", "Extended Thinking"],
        advantages: ["No editor lock-in, works anywhere", "Runs commands and self-corrects", "Superior reasoning capabilities"],
        disadvantages: ["Terminal UX can be intimidating", "Costs scale on large repos"],
        customers: ["YC Startups", "Figma", "Notion"],
        company: "Anthropic",
        primaryInterface: "CLI Tool",
        autonomousExecution: "Yes (Full Agent)",
        multiFileRefactoring: "Excellent",
        modelAccess: "Claude 4 (Opus, Sonnet)",
        contextWindow: "200k+ tokens",
        ideSupport: "Any (CLI)",
        freeTier: "No",
        localModels: "No",
        securityFeatures: "Permission System, Read-Only Mode"
    },
    {
        id: "tool-gemini",
        name: "Gemini Code Assist",
        subtitle: "(Google)",
        category: "IDE Extension",
        iconHtml: '<i class="fa-solid fa-gem" style="color: #4285f4;"></i>',
        tagline: "Google's AI with industry-leading 1M token context",
        description: "Enterprise-grade AI assistant powered by Gemini 2.0 with the largest context window and native Google Cloud integration.",
        pricing: "Free | $19/mo Standard",
        highlights: ["1M Context", "Free Tier", "Google Cloud"],
        advantages: ["Massive 1M token context window", "Generous free tier available", "Native Google Cloud integration"],
        disadvantages: ["Agentic features still maturing", "Best within Google ecosystem"],
        customers: ["Google", "Wayfair", "Woolworths"],
        company: "Google",
        primaryInterface: "IDE Extension",
        autonomousExecution: "Yes (Gemini Agent)",
        multiFileRefactoring: "Strong",
        modelAccess: "Gemini 2.0 (Flash, Pro)",
        contextWindow: "1M tokens",
        ideSupport: "VS Code, JetBrains",
        freeTier: "Yes (Generous)",
        localModels: "No",
        securityFeatures: "Google Cloud Security"
    },
    {
        id: "tool-windsurf",
        name: "Windsurf",
        subtitle: "(Codeium)",
        category: "AI-First IDE",
        iconHtml: '<i class="fa-solid fa-water" style="color: #0ea5e9;"></i>',
        tagline: "Agentic IDE with ultra-low latency",
        description: "AI-powered IDE featuring the 'Cascade' flow that blends agentic automation with the fastest autocomplete.",
        pricing: "Free | $15/mo Pro",
        highlights: ["Cascade Flow", "Free Tier", "Ultra-fast"],
        advantages: ["Cascade for agentic automation", "Industry-leading low latency", "Generous free tier"],
        disadvantages: ["New IDE to learn", "Extension ecosystem growing"],
        customers: ["Startups", "Scale AI", "Indie Devs"],
        company: "Codeium",
        primaryInterface: "Custom IDE",
        autonomousExecution: "Yes (Cascade Mode)",
        multiFileRefactoring: "Excellent",
        modelAccess: "Claude, GPT-4o, Codeium",
        contextWindow: "Unlimited",
        ideSupport: "Windsurf Editor",
        freeTier: "Yes (Generous)",
        localModels: "No",
        securityFeatures: "Zero Data Retention, SOC2"
    },
    {
        id: "tool-codeium",
        name: "Codeium",
        subtitle: "(Exafunction)",
        category: "IDE Extension",
        iconHtml: '<i class="fa-solid fa-bolt" style="color: #10b981;"></i>',
        tagline: "Best free AI autocomplete for any editor",
        description: "Industry-leading free AI code completion supporting 70+ editors with ultra-low latency.",
        pricing: "Free (Unlimited) | $15/mo Pro",
        highlights: ["70+ Editors", "Free Unlimited", "<100ms Latency"],
        advantages: ["Truly unlimited free autocomplete", "Supports 70+ different editors", "Fastest response times"],
        disadvantages: ["Agentic features need Windsurf", "Chat less sophisticated"],
        customers: ["Dell", "Anduril", "Zillow"],
        company: "Exafunction",
        primaryInterface: "IDE Extension",
        autonomousExecution: "No",
        multiFileRefactoring: "Basic",
        modelAccess: "Codeium Models",
        contextWindow: "Full Repo",
        ideSupport: "70+ Editors",
        freeTier: "Yes (Unlimited)",
        localModels: "Enterprise",
        securityFeatures: "Zero Retention, SOC2"
    }
];

// State
let aiToolsData = [...TOOLS_DATA];
let filteredTools = [...TOOLS_DATA];
let lastUpdateTimestamp = new Date();
let currentFilter = 'all';
let searchQuery = '';
let allExpanded = false;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    renderAll();
    setupEventListeners();
});

function renderAll() {
    renderToolsGrid();
    renderComparisonTable();
    updateTimestamps();
    updateStats();
    updateVisibleToolsCount();
    
    const indicator = document.getElementById('data-source-indicator');
    if (indicator) {
        indicator.textContent = 'Embedded';
        indicator.className = 'data-source-badge local-source';
    }
}

function renderToolsGrid() {
    const grid = document.getElementById('dynamic-tools-grid');
    const noResults = document.getElementById('no-results');
    if (!grid) return;

    if (filteredTools.length === 0) {
        grid.innerHTML = '';
        if (noResults) noResults.style.display = 'flex';
        return;
    }
    if (noResults) noResults.style.display = 'none';

    grid.innerHTML = filteredTools.map((tool, i) => `
        <article class="tool-card slide-up visible" id="${tool.id}" style="transition-delay: ${i * 0.05}s">
            <div class="card-header" onclick="toggleCard('${tool.id}')">
                <div class="tool-icon">${tool.iconHtml || '<i class="fa-solid fa-code"></i>'}</div>
                <div class="tool-title-group">
                    <h3>${tool.name} <span class="powered-by">${tool.subtitle || ''}</span></h3>
                    <span class="tool-tagline">${tool.tagline || ''}</span>
                </div>
                <div class="card-toggle"><i class="fa-solid fa-chevron-down"></i></div>
            </div>
            <div class="card-summary">
                <div class="summary-row">
                    <span class="tool-category">${tool.category}</span>
                    <span class="tool-pricing">${tool.pricing}</span>
                </div>
                <div class="highlight-tags">${(tool.highlights || []).map(h => `<span class="highlight-tag">${h}</span>`).join('')}</div>
            </div>
            <div class="card-body collapsed">
                <p class="tool-desc">${tool.description || ''}</p>
                <div class="pros-cons">
                    <div class="pros">
                        <h4><i class="fa-solid fa-check-circle text-success"></i> Pros</h4>
                        <ul>${(tool.advantages || []).map(p => `<li>${p}</li>`).join('')}</ul>
                    </div>
                    <div class="cons">
                        <h4><i class="fa-solid fa-times-circle text-danger"></i> Cons</h4>
                        <ul>${(tool.disadvantages || []).map(c => `<li>${c}</li>`).join('')}</ul>
                    </div>
                </div>
                ${tool.customers?.length ? `
                <div class="customers">
                    <h4><i class="fa-solid fa-building"></i> Used by</h4>
                    <div class="customer-tags">${tool.customers.map(c => `<span>${c}</span>`).join('')}</div>
                </div>` : ''}
            </div>
        </article>
    `).join('');
}

function renderComparisonTable() {
    const container = document.getElementById('dynamic-table-container');
    if (!container) return;

    const rows = [
        { label: "Company", key: "company" },
        { label: "Interface", key: "primaryInterface" },
        { label: "Context Window", key: "contextWindow" },
        { label: "Pricing", key: "pricing" },
        { label: "Autonomous", key: "autonomousExecution" },
        { label: "Multi-file Edit", key: "multiFileRefactoring" },
        { label: "Models", key: "modelAccess" },
        { label: "IDE Support", key: "ideSupport" },
        { label: "Free Tier", key: "freeTier" },
        { label: "Local Models", key: "localModels" },
        { label: "Security", key: "securityFeatures" }
    ];

    container.innerHTML = `
        <table class="comparison-table">
            <thead>
                <tr>
                    <th class="sticky-col">Feature</th>
                    ${filteredTools.map(t => `<th>${t.name}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${rows.map(row => `
                    <tr>
                        <td class="sticky-col"><strong>${row.label}</strong></td>
                        ${filteredTools.map(t => {
                            let val = t[row.key] || '-';
                            if (row.key === 'autonomousExecution') {
                                val = val.toLowerCase().startsWith('yes') 
                                    ? `<i class="fa-solid fa-check text-success"></i> ${val.replace(/^yes\s*/i, '')}`
                                    : `<i class="fa-solid fa-xmark text-danger"></i> ${val.replace(/^no\s*/i, '')}`;
                            }
                            return `<td>${val}</td>`;
                        }).join('')}
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function updateTimestamps() {
    const formatted = lastUpdateTimestamp.toLocaleString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', timeZoneName: 'short'
    });
    document.querySelectorAll('#last-updated-timestamp, #hero-timestamp').forEach(el => {
        if (el) el.textContent = formatted;
    });
}

function updateStats() {
    const total = aiToolsData.length;
    const agentic = aiToolsData.filter(t => t.autonomousExecution?.toLowerCase().startsWith('yes')).length;
    const free = aiToolsData.filter(t => t.freeTier?.toLowerCase().startsWith('yes')).length;
    const categories = [...new Set(aiToolsData.map(t => t.category))].length;

    animateNumber('stat-tools-count', total);
    animateNumber('stat-agentic-count', agentic);
    animateNumber('stat-free-count', free);
    animateNumber('stat-categories-count', categories);
    
    const footerCount = document.getElementById('footer-tools-count');
    if (footerCount) footerCount.textContent = total;
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    let current = 0;
    const step = target / 50;
    const animate = () => {
        current += step;
        if (current >= target) { el.textContent = target; }
        else { el.textContent = Math.floor(current); requestAnimationFrame(animate); }
    };
    animate();
}

function updateVisibleToolsCount() {
    const el = document.getElementById('visible-tools-count');
    if (el) el.textContent = filteredTools.length;
}

function filterTools() {
    filteredTools = aiToolsData.filter(tool => {
        const matchCat = currentFilter === 'all' || tool.category === currentFilter;
        const matchSearch = !searchQuery || 
            tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            tool.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            tool.category?.toLowerCase().includes(searchQuery.toLowerCase());
        return matchCat && matchSearch;
    });
    renderToolsGrid();
    renderComparisonTable();
    updateVisibleToolsCount();
}

function toggleCard(cardId) {
    const card = document.getElementById(cardId);
    if (!card) return;
    const body = card.querySelector('.card-body');
    const icon = card.querySelector('.card-toggle i');
    body.classList.toggle('collapsed');
    icon?.classList.toggle('fa-chevron-down');
    icon?.classList.toggle('fa-chevron-up');
    card.classList.toggle('expanded');
}

function toggleAllCards() {
    allExpanded = !allExpanded;
    const btn = document.getElementById('expand-all-btn');
    document.querySelectorAll('.tool-card').forEach(card => {
        const body = card.querySelector('.card-body');
        const icon = card.querySelector('.card-toggle i');
        if (allExpanded) {
            body?.classList.remove('collapsed');
            icon?.classList.remove('fa-chevron-down');
            icon?.classList.add('fa-chevron-up');
            card.classList.add('expanded');
        } else {
            body?.classList.add('collapsed');
            icon?.classList.add('fa-chevron-down');
            icon?.classList.remove('fa-chevron-up');
            card.classList.remove('expanded');
        }
    });
    if (btn) {
        btn.classList.toggle('active', allExpanded);
        btn.innerHTML = allExpanded 
            ? '<i class="fa-solid fa-compress"></i> Collapse' 
            : '<i class="fa-solid fa-expand"></i> Expand';
    }
}

function refreshData() {
    showToast('Data refreshed!');
    lastUpdateTimestamp = new Date();
    renderAll();
}

function exportComparison() {
    const headers = ['Feature', ...filteredTools.map(t => t.name)];
    const rows = [
        ['Company', ...filteredTools.map(t => t.company || '-')],
        ['Interface', ...filteredTools.map(t => t.primaryInterface || '-')],
        ['Context', ...filteredTools.map(t => t.contextWindow || '-')],
        ['Pricing', ...filteredTools.map(t => t.pricing || '-')],
        ['Free Tier', ...filteredTools.map(t => t.freeTier || '-')],
        ['IDE Support', ...filteredTools.map(t => t.ideSupport || '-')]
    ];
    let csv = headers.join(',') + '\n' + rows.map(r => r.map(c => `"${c}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `ai-tools-comparison-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    showToast('Comparison exported!');
}

function showToast(msg, isError = false) {
    const toast = document.getElementById('toast');
    const text = document.getElementById('toast-message');
    const icon = toast?.querySelector('i');
    if (!toast || !text) return;
    text.textContent = msg;
    toast.classList.toggle('error', isError);
    if (icon) icon.className = isError ? 'fa-solid fa-circle-xmark' : 'fa-solid fa-check-circle';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function setupEventListeners() {
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            filterTools();
        });
    });

    // Search
    const search = document.getElementById('tool-search');
    if (search) search.addEventListener('input', e => { searchQuery = e.target.value; filterTools(); });

    // Buttons
    document.getElementById('refresh-btn')?.addEventListener('click', refreshData);
    document.getElementById('refresh-footer-btn')?.addEventListener('click', e => { e.preventDefault(); refreshData(); });
    document.getElementById('export-btn')?.addEventListener('click', exportComparison);
    document.getElementById('expand-all-btn')?.addEventListener('click', toggleAllCards);

    // Mobile menu
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileNav = document.getElementById('mobile-nav');
    if (menuBtn && mobileNav) {
        menuBtn.addEventListener('click', () => {
            mobileNav.classList.toggle('show');
            const icon = menuBtn.querySelector('i');
            icon?.classList.toggle('fa-bars');
            icon?.classList.toggle('fa-xmark');
        });
        mobileNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileNav.classList.remove('show');
                const icon = menuBtn.querySelector('i');
                icon?.classList.add('fa-bars');
                icon?.classList.remove('fa-xmark');
            });
        });
    }

    // Navbar scroll
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => navbar?.classList.toggle('scrolled', window.scrollY > 50));

    // Smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const pos = target.getBoundingClientRect().top + window.pageYOffset - 80;
                window.scrollTo({ top: pos, behavior: 'smooth' });
            }
        });
    });

    // Animations
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('visible'); });
    }, { threshold: 0.15 });
    setTimeout(() => document.querySelectorAll('.fade-in, .slide-up').forEach(el => observer.observe(el)), 100);
}
