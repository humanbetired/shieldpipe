let scanData      = [];
let findingData   = [];
let findingFilter = 'ALL';
let chartGate, chartTrend, chartDist;

// ── Sections ─────────────────────────────────────────────────────────────────

function showSection(name, el) {
  ['overview','scans','detail','findings','run'].forEach(s => {
    document.getElementById('section-' + s).style.display = s === name ? '' : 'none';
  });
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');

  if (name === 'overview')  loadOverview();
  if (name === 'scans')     loadScans();
  if (name === 'findings')  loadTopFindings();
}

// ── Overview ──────────────────────────────────────────────────────────────────

async function loadOverview() {
  const stats = await fetch('/api/stats').then(r => r.json());
  document.getElementById('m-scans').textContent    = stats.total_scans;
  document.getElementById('m-blocked').textContent  = stats.blocked;
  document.getElementById('m-warned').textContent   = stats.warned;
  document.getElementById('m-passed').textContent   = stats.passed;
  document.getElementById('m-critical').textContent = stats.critical;
  document.getElementById('m-high').textContent     = stats.high;

  const clr = {
    critical: '#e8453c', high: '#f59e0b', medium: '#3b82f6',
    low: '#10b981', accent: '#6366f1', muted: '#6b7280', text: '#e2e6ef'
  };
  const chartBase = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } };

  if (chartGate)  { chartGate.destroy();  chartGate  = null; }
  if (chartTrend) { chartTrend.destroy(); chartTrend = null; }
  if (chartDist)  { chartDist.destroy();  chartDist  = null; }

  // Gate donut
  chartGate = new Chart(document.getElementById('chart-gate'), {
    type: 'doughnut',
    data: {
      labels: ['Blocked', 'Warned', 'Passed'],
      datasets: [{ data: [stats.blocked, stats.warned, stats.passed],
        backgroundColor: [clr.critical, clr.high, clr.low],
        borderWidth: 0, hoverOffset: 6 }]
    },
    options: { ...chartBase, cutout: '68%',
      plugins: { legend: { display: true, position: 'right',
        labels: { color: clr.muted, font: { size: 12 }, boxWidth: 12, padding: 12 } } } }
  });

  // Trend line
  const trend = await fetch('/api/findings/trend').then(r => r.json());
  trend.reverse();
  chartTrend = new Chart(document.getElementById('chart-trend'), {
    type: 'line',
    data: {
      labels: trend.map(d => d.date),
      datasets: [
        { label: 'Critical', data: trend.map(d => d.critical),
          borderColor: clr.critical, backgroundColor: 'rgba(232,69,60,0.08)',
          pointRadius: 3, tension: 0.4, fill: true, borderWidth: 2 },
        { label: 'High', data: trend.map(d => d.high),
          borderColor: clr.high, backgroundColor: 'rgba(245,158,11,0.08)',
          pointRadius: 3, tension: 0.4, fill: true, borderWidth: 2 },
      ]
    },
    options: { ...chartBase,
      plugins: { legend: { display: true, position: 'top',
        labels: { color: clr.muted, font: { size: 11 }, boxWidth: 12 } } },
      scales: {
        x: { ticks: { color: clr.muted, font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: clr.muted, font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } }
      }
    }
  });

  // Distribution bar
  const dist = await fetch('/api/findings/distribution').then(r => r.json());
  const scanners  = [...new Set(dist.map(d => d.scanner))];
  const severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const sevColors  = { CRITICAL: clr.critical, HIGH: clr.high, MEDIUM: clr.medium, LOW: clr.low };

  const datasets = severities.map(sev => ({
    label: sev,
    data: scanners.map(sc => {
      const row = dist.find(d => d.scanner === sc && d.severity === sev);
      return row ? row.count : 0;
    }),
    backgroundColor: sevColors[sev],
    borderRadius: 3,
  }));

  chartDist = new Chart(document.getElementById('chart-dist'), {
    type: 'bar',
    data: { labels: scanners, datasets },
    options: { ...chartBase,
      plugins: { legend: { display: true, position: 'top',
        labels: { color: clr.muted, font: { size: 11 }, boxWidth: 12 } } },
      scales: {
        x: { stacked: true, ticks: { color: clr.muted }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { stacked: true, ticks: { color: clr.muted }, grid: { color: 'rgba(255,255,255,0.04)' } }
      }
    }
  });
}

// ── Scan History ──────────────────────────────────────────────────────────────

async function loadScans() {
  const res = await fetch('/api/scans');
  scanData  = await res.json();
  renderScans();
}

function renderScans() {
  const q        = document.getElementById('scan-search').value.toLowerCase();
  const filtered = scanData.filter(s => !q || s.project_name.toLowerCase().includes(q));

  document.getElementById('scan-footer').textContent =
    `Showing ${filtered.length} of ${scanData.length} scans`;

  const tbody = document.getElementById('scan-tbody');
  if (!filtered.length) {
    tbody.innerHTML = '<tr><td colspan="9" class="loading-row">No scans found</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(s => `
    <tr>
      <td class="mono" style="font-size:11px">${s.scan_id.slice(0,8)}</td>
      <td style="font-weight:500">${s.project_name}</td>
      <td><span class="gate-${s.gate_result}">${s.gate_result}</span></td>
      <td style="color:var(--critical);font-weight:600">${s.total_critical}</td>
      <td style="color:var(--high);font-weight:600">${s.total_high}</td>
      <td style="color:var(--medium)">${s.total_medium}</td>
      <td style="color:var(--low)">${s.total_low}</td>
      <td class="mono" style="font-size:11px">${s.scanned_at}</td>
      <td><button class="btn btn-sm" onclick="loadDetail('${s.scan_id}')">View</button></td>
    </tr>
  `).join('');
}

// ── Scan Detail ───────────────────────────────────────────────────────────────

async function loadDetail(scan_id) {
  const res  = await fetch(`/api/scan/${scan_id}`);
  const data = await res.json();

  const scan = data.scan;
  findingData = data.findings;

  document.getElementById('detail-title').textContent =
    `${scan.project_name} — ${scan.gate_result}`;
  document.getElementById('detail-subtitle').textContent =
    `Scan ID: ${scan.scan_id.slice(0,8)} | Scanned: ${scan.scanned_at}`;
  document.getElementById('detail-ai').innerHTML =
    scan.ai_summary ? marked.parse(scan.ai_summary) : 'No AI summary available.';

  findingFilter = 'ALL';
  document.querySelectorAll('#section-detail .filter-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('#section-detail .f-all').classList.add('active');

  renderFindings();
  showSection('detail', null);
}

function setFindingFilter(filter, btn) {
  findingFilter = filter;
  document.querySelectorAll('#section-detail .filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderFindings();
}

function renderFindings() {
  const q = document.getElementById('finding-search').value.toLowerCase();
  const filtered = findingData.filter(f => {
    const matchFilter = findingFilter === 'ALL' || f.severity === findingFilter;
    const matchSearch = !q || [f.title, f.file_path, f.scanner, f.evidence]
      .some(v => v && v.toLowerCase().includes(q));
    return matchFilter && matchSearch;
  });

  document.getElementById('finding-footer').textContent =
    `Showing ${filtered.length} of ${findingData.length} findings`;

  const tbody = document.getElementById('finding-tbody');
  if (!filtered.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="loading-row">No findings</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(f => `
    <tr>
      <td style="font-size:12px;color:var(--muted)">${f.scanner}</td>
      <td><span class="severity-badge sev-${f.severity}">${f.severity}</span></td>
      <td class="truncate" title="${f.title}">${f.title}</td>
      <td class="mono truncate" style="color:var(--muted)">${f.file_path || '--'}</td>
      <td class="mono">${f.line_number || '--'}</td>
      <td class="mono truncate" style="color:var(--muted)" title="${f.evidence || ''}">${f.evidence || '--'}</td>
    </tr>
  `).join('');
}

// ── Top Findings ──────────────────────────────────────────────────────────────

async function loadTopFindings() {
  const data  = await fetch('/api/findings/top').then(r => r.json());
  const tbody = document.getElementById('top-tbody');

  if (!data.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="loading-row">No findings yet</td></tr>';
    return;
  }

  tbody.innerHTML = data.map(f => `
    <tr>
      <td>${f.title}</td>
      <td><span class="severity-badge sev-${f.severity}">${f.severity}</span></td>
      <td style="font-size:12px;color:var(--muted)">${f.scanner}</td>
      <td class="mono" style="color:var(--critical);font-weight:600">${f.count}</td>
    </tr>
  `).join('');
}

// ── Run Scan ──────────────────────────────────────────────────────────────────

let scanPolling = null;

async function runScan() {
  const name   = document.getElementById('input-name').value.trim();
  const target = document.getElementById('input-target').value.trim();
  const image  = document.getElementById('input-image').value.trim();
  const status = document.getElementById('run-status');
  const btn    = document.querySelector('#section-run .btn-primary');

  if (!target) {
    status.textContent = 'Target path is required.';
    status.className   = 'status-msg status-err';
    return;
  }

  try {
    const res  = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, name, image: image || null })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    // Disable button
    btn.disabled     = true;
    btn.textContent  = 'Scanning...';

    // Start polling
    startScanPolling();

  } catch(e) {
    status.textContent = 'Error: ' + e.message;
    status.className   = 'status-msg status-err';
  }
}

function startScanPolling() {
  const status = document.getElementById('run-status');
  const btn    = document.querySelector('#section-run .btn-primary');
  const steps  = [
    'Running Secret Scanner...',
    'Running SAST Scanner...',
    'Checking Dependencies...',
    'Scanning Container Image...',
    'Generating AI Summary...',
    'Saving results...',
  ];
  let stepIndex = 0;

  // Show animated step text
  status.className = 'status-msg';
  status.innerHTML = `<span class="scan-pulse"></span> ${steps[stepIndex]}`;

  const stepInterval = setInterval(() => {
    stepIndex = (stepIndex + 1) % steps.length;
    status.innerHTML = `<span class="scan-pulse"></span> ${steps[stepIndex]}`;
  }, 8000);

  // Poll actual status
  scanPolling = setInterval(async () => {
    try {
      const res  = await fetch('/api/scan-status');
      const data = await res.json();

      if (!data.status) {
        // Scan finished
        clearInterval(scanPolling);
        clearInterval(stepInterval);
        scanPolling = null;

        btn.disabled    = false;
        btn.textContent = 'Run Scan';
        status.innerHTML = '';
        status.textContent = 'Scan complete! Check Scan History for results.';
        status.className   = 'status-msg status-ok';
      }
    } catch(e) {
      clearInterval(scanPolling);
      clearInterval(stepInterval);
    }
  }, 3000);
}

// Check on page load if scan is already running
async function checkScanOnLoad() {
  const res  = await fetch('/api/scan-status');
  const data = await res.json();
  if (data.status) {
    const btn = document.querySelector('#section-run .btn-primary');
    if (btn) {
      btn.disabled    = true;
      btn.textContent = 'Scanning...';
      startScanPolling();
    }
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

window.onload = () => {
  document.getElementById('footer-date').textContent = new Date().toISOString().slice(0,10);
  loadOverview();
  checkScanOnLoad();
};