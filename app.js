/**
 * Vireo Audio Support Intelligence & AI Triage Platform
 * Frontend Controller & Interactive Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initThemeToggle();
  initOverviewTab();
  initTriageTab();
  initSimulatorTab();
  initExplorerTab();
});

// 1. Tab Navigation
function initNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
        if (targetId === 'tab-overview') renderOverviewChart();
      }
    });
  });
}

// 2. Theme Toggle
function initThemeToggle() {
  const themeBtn = document.getElementById('theme-btn');
  themeBtn.addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
    document.body.classList.toggle('dark-theme');
    renderOverviewChart(); // re-render chart grid lines with appropriate contrast
  });
}

// Global cached data
let overviewData = null;
let staffingData = [];
let explorerState = {
  q: '',
  team: '',
  category: '',
  channel: '',
  sla: '',
  page: 1,
  limit: 20
};

// 3. Overview Tab & SVG Line Chart
async function initOverviewTab() {
  try {
    const res = await fetch('/api/overview');
    overviewData = await res.json();
    renderOverviewChart();
  } catch (err) {
    console.error('Failed to load overview data:', err);
  }
}

function renderOverviewChart() {
  if (!overviewData || !overviewData.chart) return;
  const svg = document.getElementById('overview-svg');
  if (!svg) return;

  const data = overviewData.chart;
  const months = data.months;
  const bIn = data.billing_intake;
  const bRes = data.billing_resolving;
  const lIn = data.logistics_intake;
  const lRes = data.logistics_resolving;

  const width = 900;
  const height = 300;
  const padLeft = 45;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 40;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const allVals = [...bIn, ...bRes, ...lIn, ...lRes];
  const maxVal = Math.max(...allVals, 220);
  const minVal = 0;

  const getX = (idx) => padLeft + (idx / (months.length - 1)) * chartW;
  const getY = (val) => padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;

  const isLight = document.body.classList.contains('light-theme');
  const gridColor = isLight ? '#e2e8f0' : '#2a3449';
  const textColor = isLight ? '#64748b' : '#94a3b8';

  let svgContent = '';

  // Background Grid & Y-Axis Labels
  const yTicks = [0, 50, 100, 150, 200];
  yTicks.forEach(tick => {
    const y = getY(tick);
    svgContent += `<line x1="${padLeft}" y1="${y}" x2="${width - padRight}" y2="${y}" stroke="${gridColor}" stroke-dasharray="4,4" stroke-width="1"/>`;
    svgContent += `<text x="${padLeft - 10}" y="${y + 4}" fill="${textColor}" font-size="11" text-anchor="end">${tick}</text>`;
  });

  // X-Axis Labels (Every 2nd month)
  months.forEach((m, idx) => {
    if (idx % 2 === 0 || idx === months.length - 1) {
      const x = getX(idx);
      const label = m.substring(2); // YY-MM
      svgContent += `<text x="${x}" y="${height - 12}" fill="${textColor}" font-size="11" text-anchor="middle">${label}</text>`;
    }
  });

  // Helper to build line path
  function buildPath(arr) {
    return arr.map((v, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(v)}`).join(' ');
  }

  // Paths
  const pBIn = buildPath(bIn);
  const pBRes = buildPath(bRes);
  const pLIn = buildPath(lIn);
  const pLRes = buildPath(lRes);

  // Render Paths
  svgContent += `<path d="${pBIn}" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`;
  svgContent += `<path d="${pBRes}" fill="none" stroke="#3b82f6" stroke-width="2" stroke-dasharray="4,4" stroke-linecap="round" stroke-linejoin="round"/>`;
  svgContent += `<path d="${pLIn}" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="4,4" stroke-linecap="round" stroke-linejoin="round"/>`;
  svgContent += `<path d="${pLRes}" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;

  // Draw points on Logistics Resolving
  lRes.forEach((v, i) => {
    const cx = getX(i);
    const cy = getY(v);
    svgContent += `<circle cx="${cx}" cy="${cy}" r="3.5" fill="#10b981" stroke="#ffffff" stroke-width="1.5"/>`;
  });

  svg.innerHTML = svgContent;
}

// 4. AI Ticket Triage Tab
function initTriageTab() {
  const custInput = document.getElementById('input-cust-msg');
  const agentInput = document.getElementById('input-agent-notes');
  const btnClassify = document.getElementById('btn-classify');
  const btnClear = document.getElementById('btn-clear');

  const presetDelivery = document.getElementById('preset-delivery');
  const presetBattery = document.getElementById('preset-battery');
  const presetBluetooth = document.getElementById('preset-bluetooth');

  // Presets
  presetDelivery.addEventListener('click', () => {
    custInput.value = "Money was deducted from my bank account 5 days ago, but my headphones still haven't arrived. Tracking number VR889211 is not updating.";
    agentInput.value = "re: delivery delay | confirmed address with cx -> checked AWB with courier partner -> delivery expedited for tomorrow";
  });

  presetBattery.addEventListener('click', () => {
    custInput.value = "The left earbud of my Strata 3 is completely dead. Kept in charging case all night, green light is off, no power at all.";
    agentInput.value = "left bud not charging | walked cx through case pin cleaning -> pin dead -> replacement unit raised under DOA";
  });

  presetBluetooth.addEventListener('click', () => {
    custInput.value = "Bluetooth pairing fails every time I try on my iPhone 16. The device does not show up in the Bluetooth search list.";
    agentInput.value = "cx unable to pair | walked through 15-second hard reset protocol -> paired successfully on iOS";
  });

  btnClear.addEventListener('click', () => {
    custInput.value = '';
    agentInput.value = '';
    document.getElementById('result-empty').classList.remove('hidden');
    document.getElementById('result-filled').classList.add('hidden');
    document.getElementById('result-status-badge').textContent = 'Ready for Input';
  });

  btnClassify.addEventListener('click', async () => {
    const custMsg = custInput.value.trim();
    const agentNotes = agentInput.value.trim();

    if (!custMsg) {
      alert('Please enter a customer opening message to classify.');
      return;
    }

    btnClassify.disabled = true;
    btnClassify.textContent = 'Analyzing...';

    try {
      const res = await fetch('/api/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_message: custMsg, agent_notes: agentNotes })
      });
      const data = await res.json();
      renderClassificationResult(data);
    } catch (err) {
      alert('Classification failed: ' + err.message);
    } finally {
      btnClassify.disabled = false;
      btnClassify.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> Classify Ticket`;
    }
  });
}

function renderClassificationResult(data) {
  document.getElementById('result-empty').classList.add('hidden');
  document.getElementById('result-filled').classList.remove('hidden');
  document.getElementById('result-status-badge').textContent = 'Classified';

  document.getElementById('result-category').textContent = data.category;
  document.getElementById('result-team').textContent = data.owning_team;
  document.getElementById('result-confidence').textContent = (data.confidence * 100).toFixed(1) + '%';
  document.getElementById('result-conf-bar').style.width = (data.confidence * 100) + '%';
  document.getElementById('result-evidence').textContent = `"${data.primary_evidence}"`;
  document.getElementById('result-routing').textContent = data.routing_recommendation;

  const warningBox = document.getElementById('result-warning-box');
  const warningText = document.getElementById('result-warning-text');
  if (data.misrouting_warning) {
    warningBox.classList.remove('hidden');
    warningText.textContent = data.misrouting_warning;
  } else {
    warningBox.classList.add('hidden');
  }
}

// 5. Staffing Simulator Tab
async function initSimulatorTab() {
  try {
    const res = await fetch('/api/staffing');
    staffingData = await res.json();
    renderScenarioDetail(0);
  } catch (err) {
    console.error('Failed to load staffing scenarios:', err);
  }

  const scenarioCards = document.querySelectorAll('.scenario-card');
  scenarioCards.forEach(card => {
    card.addEventListener('click', () => {
      scenarioCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const idx = parseInt(card.getAttribute('data-scenario'));
      renderScenarioDetail(idx);
    });
  });
}

function renderScenarioDetail(idx) {
  if (!staffingData || !staffingData[idx]) return;
  const s = staffingData[idx];

  document.getElementById('sim-scenario-title').textContent = s.Scenario;
  document.getElementById('sim-log-headcount').textContent = `${s.Logistics_Headcount} Agents`;
  document.getElementById('sim-log-load').textContent = `${s.Logistics_Monthly_Workload_Per_Agent} tickets / agent / mo`;

  document.getElementById('sim-bill-headcount').textContent = `${s.Billing_Headcount} Agents`;
  document.getElementById('sim-bill-load').textContent = `${s.Billing_Monthly_Workload_Per_Agent} tickets / agent / mo`;

  document.getElementById('sim-cost').textContent = s.Annual_Cost_INR > 0 ? `₹${(s.Annual_Cost_INR/100000).toFixed(1)} Lakh / year` : '₹0 / year';
  document.getElementById('sim-tradeoff-text').textContent = s.Operational_Impact;

  const latBox = document.getElementById('sim-latency');
  if (idx === 2 || idx === 4) {
    latBox.textContent = '~18.4h Projected';
    latBox.className = 'sim-val text-success';
  } else if (idx === 3) {
    latBox.textContent = '~22.1h Projected';
    latBox.className = 'sim-val warning-text';
  } else {
    latBox.textContent = '26.16h Median';
    latBox.className = 'sim-val warning-text';
  }
}

// 6. Ticket Explorer Tab
function initExplorerTab() {
  const searchInput = document.getElementById('search-input');
  const filterTeam = document.getElementById('filter-team');
  const filterCategory = document.getElementById('filter-category');
  const filterChannel = document.getElementById('filter-channel');
  const filterSla = document.getElementById('filter-sla');
  const btnReset = document.getElementById('btn-reset-filters');

  const btnPrev = document.getElementById('btn-prev-page');
  const btnNext = document.getElementById('btn-next-page');

  // Debounced search
  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      explorerState.q = searchInput.value;
      explorerState.page = 1;
      fetchTickets();
    }, 250);
  });

  filterTeam.addEventListener('change', () => {
    explorerState.team = filterTeam.value;
    explorerState.page = 1;
    fetchTickets();
  });

  filterCategory.addEventListener('change', () => {
    explorerState.category = filterCategory.value;
    explorerState.page = 1;
    fetchTickets();
  });

  filterChannel.addEventListener('change', () => {
    explorerState.channel = filterChannel.value;
    explorerState.page = 1;
    fetchTickets();
  });

  filterSla.addEventListener('change', () => {
    explorerState.sla = filterSla.value;
    explorerState.page = 1;
    fetchTickets();
  });

  btnReset.addEventListener('click', () => {
    searchInput.value = '';
    filterTeam.value = '';
    filterCategory.value = '';
    filterChannel.value = '';
    filterSla.value = '';
    explorerState = { q: '', team: '', category: '', channel: '', sla: '', page: 1, limit: 20 };
    fetchTickets();
  });

  btnPrev.addEventListener('click', () => {
    if (explorerState.page > 1) {
      explorerState.page--;
      fetchTickets();
    }
  });

  btnNext.addEventListener('click', () => {
    explorerState.page++;
    fetchTickets();
  });

  // Modal close handlers
  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('ticket-modal').addEventListener('click', (e) => {
    if (e.target.id === 'ticket-modal') closeModal();
  });

  fetchTickets();
}

async function fetchTickets() {
  const params = new URLSearchParams({
    q: explorerState.q,
    team: explorerState.team,
    category: explorerState.category,
    channel: explorerState.channel,
    sla: explorerState.sla,
    page: explorerState.page,
    limit: explorerState.limit
  });

  try {
    const res = await fetch(`/api/tickets?${params.toString()}`);
    const data = await res.json();
    renderTicketsTable(data);
  } catch (err) {
    console.error('Failed to fetch tickets:', err);
  }
}

function renderTicketsTable(data) {
  const tbody = document.getElementById('tickets-tbody');
  tbody.innerHTML = '';

  document.getElementById('filtered-count').textContent = data.total.toLocaleString();
  document.getElementById('current-page-num').textContent = data.page;
  document.getElementById('total-page-num').textContent = data.total_pages;

  document.getElementById('btn-prev-page').disabled = data.page <= 1;
  document.getElementById('btn-next-page').disabled = data.page >= data.total_pages;

  if (!data.tickets || data.tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding: 24px; color: var(--text-dim);">No tickets match the selected filter criteria.</td></tr>`;
    return;
  }

  data.tickets.forEach(t => {
    const tr = document.createElement('tr');
    const slaClass = t.sla_status === 'Met' ? 'sla-met' : 'sla-breached';

    tr.innerHTML = `
      <td><strong>${t.id}</strong></td>
      <td>${t.date}</td>
      <td>${t.channel}</td>
      <td>${t.category}</td>
      <td>${t.initial_team}</td>
      <td>${t.resolving_team}</td>
      <td><span class="sla-badge ${slaClass}">${t.sla_status}</span></td>
      <td>${t.resolution_time}</td>
      <td>${t.csat}</td>
      <td><button class="btn-inspect" data-ticket='${JSON.stringify(t).replace(/'/g, "&apos;")}'>Inspect</button></td>
    `;
    tbody.appendChild(tr);
  });

  // Attach inspect handlers
  document.querySelectorAll('.btn-inspect').forEach(btn => {
    btn.addEventListener('click', () => {
      const ticket = JSON.parse(btn.getAttribute('data-ticket'));
      openModal(ticket);
    });
  });
}

function openModal(t) {
  document.getElementById('modal-ticket-id').textContent = `Ticket Details: ${t.id}`;
  document.getElementById('modal-date').textContent = t.date;
  document.getElementById('modal-channel').textContent = t.channel;
  document.getElementById('modal-category').textContent = t.category;
  document.getElementById('modal-initial-team').textContent = t.initial_team;
  document.getElementById('modal-resolving-team').textContent = t.resolving_team;
  document.getElementById('modal-sla').textContent = t.sla_status;
  document.getElementById('modal-res-time').textContent = t.resolution_time;
  document.getElementById('modal-csat').textContent = t.csat;
  document.getElementById('modal-cust-msg').textContent = t.customer_message || '(No customer message text)';
  document.getElementById('modal-agent-notes').textContent = t.agent_notes || '(No closing notes recorded)';

  document.getElementById('ticket-modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('ticket-modal').classList.add('hidden');
}
