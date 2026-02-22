const LB   = 'http://localhost:8000';
const MGMT = 'http://localhost:8004';

let processStatus = [];  // array from management API
let healthStatus  = {};  // dict from load balancer /status

// ── Polling ───────────────────────────────────────────────────────────────

async function pollStatus() {
  try {
    const [mgmtRes, lbRes] = await Promise.all([
      fetch(`${MGMT}/status`),
      fetch(`${LB}/status`),
    ]);
    processStatus = await mgmtRes.json();
    healthStatus  = await lbRes.json();
  } catch (_) {
    // silently retry next cycle
  }
  renderCards();
}

setInterval(pollStatus, 2000);
pollStatus();

// ── Render cards ──────────────────────────────────────────────────────────

function renderCards() {
  const container = document.getElementById('servers');
  const backends  = processStatus.slice(0, 3);  // ignore the load balancer entry

  container.innerHTML = backends.map((s, i) => {
    const url     = `http://localhost:${s.port}`;
    const running = s.running;
    const healthy = healthStatus[url] === true;

    const cardClass = !running ? 'stopped' : healthy ? 'healthy' : 'unhealthy';

    const procBadge = running
      ? '<span class="badge green">Process running</span>'
      : '<span class="badge gray">Process stopped</span>';

    const healthBadge = running
      ? (healthy
          ? '<span class="badge green">Health check OK</span>'
          : '<span class="badge red">Health check fail</span>')
      : '<span class="badge gray">Health check N/A</span>';

    return `
      <div class="card ${cardClass}">
        <div class="card-title">${s.label}</div>
        <div class="card-port">port ${s.port}</div>
        <div class="card-badges">${procBadge}${healthBadge}</div>
        <button class="btn btn-kill"  onclick="mgmtAction('kill', ${i + 1})">Kill</button>
        <button class="btn btn-start" onclick="mgmtAction('start', ${i + 1})">Start</button>
      </div>`;
  }).join('');
}

// ── Kill / Start via management API ───────────────────────────────────────

async function mgmtAction(action, n) {
  await fetch(`${MGMT}/${action}/${n}`, { method: 'POST' });
  await pollStatus();
}

// ── Send test request ─────────────────────────────────────────────────────

async function sendRequest() {
  const btn     = document.getElementById('sendBtn');
  const lastEl  = document.getElementById('lastResponse');
  btn.disabled  = true;

  const time = new Date().toLocaleTimeString();
  let serverName = null;
  let statusCode = null;

  try {
    const res = await fetch(LB);
    statusCode = res.status;
    if (res.ok) {
      const data = await res.json();
      serverName = data.server || 'Unknown';
    } else {
      serverName = `Error ${res.status}`;
    }
  } catch (_) {
    serverName = 'Unreachable';
  }

  const isError = serverName.startsWith('Error') || serverName === 'Unreachable';
  lastEl.innerHTML = isError
    ? `<span class="error">${serverName}</span>`
    : `Last handled by <span class="highlight">${serverName}</span>`;

  addLogEntry(time, serverName, statusCode);
  btn.disabled = false;
}

function addLogEntry(time, serverName, statusCode) {
  const log = document.getElementById('log');
  const div = document.createElement('div');
  div.className = 'log-entry';

  const colorClass =
    serverName === 'Backend Server 1' ? 's1' :
    serverName === 'Backend Server 2' ? 's2' :
    serverName === 'Backend Server 3' ? 's3' : 'err';

  div.innerHTML = `
    <span class="log-time">${time}</span>
    <span class="log-server ${colorClass}">${serverName}</span>
    <span class="log-status">${statusCode ? `HTTP ${statusCode}` : ''}</span>
  `;
  log.prepend(div);
}
