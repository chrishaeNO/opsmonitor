"""OPS Monitor admin portal – OWASP-hardened single-page app."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-portal"])

_HTML = """<!doctype html>
<html lang="no">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
  <title>OPS Monitor – Admin</title>
  <script src="https://cdn.tailwindcss.com?plugins=forms"></script>
  <style>
    :root { color-scheme: dark; }
    body  { background:#020617; font-family:system-ui,-apple-system,sans-serif; }
    .glass{backdrop-filter:blur(18px);background:rgba(15,23,42,.95);
           border:1px solid rgba(148,163,184,.12);}
    .key-mono{font-family:'Courier New',monospace;letter-spacing:.04em;word-break:break-all;}
    input,select{color-scheme:dark;}
    .tab-btn{transition:color .15s,border-color .15s;}
    .tab-btn.active{color:#60a5fa;border-bottom-color:#60a5fa;}
    .tab-btn:not(.active){color:#64748b;border-bottom-color:transparent;}
    .badge-admin{background:#451a03;color:#fbbf24;border:1px solid #92400e;}
    .badge-user {background:#0c1a2e;color:#60a5fa;border:1px solid #1e3a5f;}
    .row-hover:hover{background:rgba(30,41,59,.6);}
    #toast{transition:opacity .3s;pointer-events:none;}
  </style>
</head>
<body class="min-h-screen text-slate-100 p-4 md:p-8">

<!-- ── Toast notification ─────────────────────────────────────────────── -->
<div id="toast" class="fixed top-4 right-4 z-50 opacity-0 px-5 py-3 rounded-xl text-sm font-semibold shadow-2xl"></div>

<div class="max-w-5xl mx-auto space-y-6">

  <!-- ── Header ───────────────────────────────────────────────────────── -->
  <header class="flex items-center justify-between gap-4">
    <div class="flex items-center gap-3">
      <div class="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-600/30 text-sm font-bold">OPS</div>
      <div>
        <h1 class="text-lg font-semibold tracking-tight">OPS Monitor</h1>
        <p id="headerOrg" class="text-xs text-slate-400">Administrasjon</p>
      </div>
    </div>
    <div class="flex items-center gap-3" id="sessionBar" style="display:none!important">
      <span id="sessionTimer" class="text-xs text-slate-500 tabular-nums"></span>
      <div id="avatar" class="h-8 w-8 rounded-full bg-blue-700 flex items-center justify-center text-sm font-bold cursor-pointer" title="Innlogget"></div>
      <button id="logoutBtn" class="text-xs text-slate-400 hover:text-red-400 transition-colors">Logg ut</button>
    </div>
  </header>

  <!-- ── Login card ────────────────────────────────────────────────────── -->
  <section id="loginSection" class="flex justify-center pt-8">
    <div class="glass rounded-2xl p-8 w-full max-w-sm shadow-2xl space-y-5">
      <div>
        <h2 class="text-xl font-semibold">Logg inn som admin</h2>
        <p class="text-sm text-slate-400 mt-1">Kun brukere med admin-rolle har tilgang.</p>
      </div>
      <div class="space-y-3">
        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">E-post</label>
          <input id="loginEmail" type="email" autocomplete="username"
            class="w-full rounded-lg bg-slate-900 border border-slate-700 text-sm px-3 py-2.5
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="admin@bedrift.no"/>
        </div>
        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Passord</label>
          <input id="loginPw" type="password" autocomplete="current-password"
            class="w-full rounded-lg bg-slate-900 border border-slate-700 text-sm px-3 py-2.5
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="••••••••" minlength="8"/>
        </div>
      </div>
      <p id="loginErr" class="text-xs text-red-400 min-h-[1rem]"></p>
      <button id="loginBtn"
        class="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600
               hover:bg-blue-500 text-sm font-semibold py-2.5 transition-colors
               disabled:opacity-50 disabled:cursor-not-allowed">
        Logg inn
      </button>
      <p class="text-xs text-slate-500 text-center">
        Opprett bedriftskonto via <a href="/auth/register" class="text-blue-400 hover:underline">API</a> eller desktop-appen.
      </p>
    </div>
  </section>

  <!-- ── Dashboard ─────────────────────────────────────────────────────── -->
  <div id="dashboard" style="display:none" class="space-y-6">

    <!-- tabs -->
    <div class="border-b border-slate-800 flex gap-6">
      <button class="tab-btn active pb-2 border-b-2 text-sm font-medium" data-tab="users">Brukere</button>
      <button class="tab-btn pb-2 border-b-2 text-sm font-medium" data-tab="apikeys">API-nøkler</button>
      <button class="tab-btn pb-2 border-b-2 text-sm font-medium" data-tab="org">Organisasjon</button>
    </div>

    <!-- ── Users tab ───────────────────────────────────────────────────── -->
    <div id="tab-users" class="tab-panel space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="font-semibold">Brukere</h2>
          <p class="text-xs text-slate-400">Legg til og fjern brukere i organisasjonen.</p>
        </div>
        <button id="showAddUser"
          class="text-sm bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2
                 rounded-lg transition-colors">+ Legg til bruker</button>
      </div>

      <!-- Add user form (hidden by default) -->
      <div id="addUserForm" class="glass rounded-xl p-5 space-y-3 hidden">
        <h3 class="text-sm font-semibold">Ny bruker</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div class="md:col-span-1">
            <label class="block text-xs font-medium text-slate-300 mb-1">E-post</label>
            <input id="newEmail" type="email"
              class="w-full rounded-lg bg-slate-900 border border-slate-700 text-xs px-3 py-2
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="bruker@bedrift.no"/>
          </div>
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Passord</label>
            <input id="newPw" type="password"
              class="w-full rounded-lg bg-slate-900 border border-slate-700 text-xs px-3 py-2
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Minst 8 tegn"/>
          </div>
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Rolle</label>
            <select id="newRole"
              class="w-full rounded-lg bg-slate-900 border border-slate-700 text-xs px-3 py-2
                     focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="user">Bruker</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>
        <p id="addUserErr" class="text-xs text-red-400 min-h-[1rem]"></p>
        <div class="flex gap-2">
          <button id="createUserBtn"
            class="text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2
                   rounded-lg transition-colors disabled:opacity-50">Opprett</button>
          <button id="cancelAddUser"
            class="text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded-lg transition-colors">Avbryt</button>
        </div>
      </div>

      <div class="glass rounded-xl overflow-hidden">
        <table class="min-w-full text-xs">
          <thead class="bg-slate-900/80 text-slate-400">
            <tr>
              <th class="px-4 py-3 text-left font-medium">E-post</th>
              <th class="px-4 py-3 text-left font-medium">Rolle</th>
              <th class="px-4 py-3 text-left font-medium">Opprettet</th>
              <th class="px-4 py-3 text-right font-medium">Handling</th>
            </tr>
          </thead>
          <tbody id="usersBody" class="divide-y divide-slate-800"></tbody>
        </table>
        <p id="usersEmpty" class="text-center text-slate-500 py-8 text-xs hidden">Ingen brukere funnet.</p>
      </div>
    </div>

    <!-- ── API keys tab ───────────────────────────────────────────────── -->
    <div id="tab-apikeys" class="tab-panel space-y-4 hidden">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="font-semibold">API-nøkler</h2>
          <p class="text-xs text-slate-400">
            Generer nøkler som brukes i desktop-appen under <strong class="text-slate-300">Innstillinger → Konto / API</strong>.
          </p>
        </div>
        <button id="createKeyBtn"
          class="text-sm bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2
                 rounded-lg transition-colors">+ Ny nøkkel</button>
      </div>

      <!-- Create key form -->
      <div id="createKeyForm" class="glass rounded-xl p-5 space-y-3 hidden">
        <h3 class="text-sm font-semibold">Ny API-nøkkel</h3>
        <div class="flex gap-3">
          <input id="keyName" type="text"
            class="flex-1 rounded-lg bg-slate-900 border border-slate-700 text-xs px-3 py-2
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder='f.eks. "Desktop – kontor 1"'/>
          <button id="doCreateKey"
            class="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2
                   rounded-lg transition-colors">Generer</button>
          <button id="cancelCreateKey"
            class="text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-3 py-2 rounded-lg">Avbryt</button>
        </div>
      </div>

      <!-- Newly created key display -->
      <div id="newKeyReveal" class="hidden glass rounded-xl p-5 border border-emerald-700/50 space-y-3">
        <div class="flex items-center gap-2">
          <span class="text-emerald-400 font-semibold text-sm">✓ Nøkkel opprettet</span>
          <span class="text-xs text-slate-400">– kopier og lagre den nå, den vises bare én gang.</span>
        </div>
        <div class="flex items-center gap-2">
          <code id="newKeyText"
            class="key-mono flex-1 text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-emerald-300 select-all"></code>
          <button id="copyKeyBtn"
            class="text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-3 py-2 rounded-lg whitespace-nowrap transition-colors">
            Kopier
          </button>
        </div>
        <p class="text-xs text-slate-400">
          Lim inn denne nøkkelen i desktop-appen under <strong class="text-slate-300">Innstillinger → Konto / API → API-nøkkel</strong>.
        </p>
      </div>

      <div class="glass rounded-xl overflow-hidden">
        <table class="min-w-full text-xs">
          <thead class="bg-slate-900/80 text-slate-400">
            <tr>
              <th class="px-4 py-3 text-left font-medium">Navn</th>
              <th class="px-4 py-3 text-left font-medium">Prefiks</th>
              <th class="px-4 py-3 text-left font-medium">Opprettet</th>
              <th class="px-4 py-3 text-left font-medium">Sist brukt</th>
              <th class="px-4 py-3 text-right font-medium">Handling</th>
            </tr>
          </thead>
          <tbody id="keysBody" class="divide-y divide-slate-800"></tbody>
        </table>
        <p id="keysEmpty" class="text-center text-slate-500 py-8 text-xs hidden">Ingen API-nøkler opprettet ennå.</p>
      </div>
    </div>

    <!-- ── Organisation tab ───────────────────────────────────────────── -->
    <div id="tab-org" class="tab-panel space-y-4 hidden">
      <h2 class="font-semibold">Organisasjon</h2>
      <div class="glass rounded-xl p-5 text-sm space-y-3">
        <div class="flex justify-between border-b border-slate-800 pb-3">
          <span class="text-slate-400">Navn</span>
          <span id="orgName" class="font-medium"></span>
        </div>
        <div class="flex justify-between border-b border-slate-800 pb-3">
          <span class="text-slate-400">Innlogget som</span>
          <span id="orgAdmin" class="font-mono text-xs"></span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-400">Org-ID</span>
          <span id="orgId" class="font-mono text-xs text-slate-300"></span>
        </div>
      </div>
      <div class="glass rounded-xl p-5 space-y-2">
        <h3 class="text-sm font-semibold text-amber-400">Sikkerhetsinfo (OWASP)</h3>
        <ul class="text-xs text-slate-400 space-y-1 list-disc list-inside">
          <li>Token lagres kun i minnet – aldri i localStorage eller cookies.</li>
          <li>Konto låses etter 5 feil påloggingsforsøk i 15 minutter.</li>
          <li>Passord må være minst 8 og maks 72 tegn.</li>
          <li>API-nøkler hashes med SHA-256 og vises kun én gang ved opprettelse.</li>
          <li>Alle API-svar inkluderer HSTS, CSP og X-Frame-Options header.</li>
          <li>Autologout etter 30 minutters inaktivitet.</li>
        </ul>
      </div>
    </div>

  </div><!-- /dashboard -->
</div><!-- /container -->

<script>
"use strict";
// ── State ──────────────────────────────────────────────────────────────────
let _token = null;
let _me    = null;
let _sessionExpiry = null;
let _sessionInterval = null;

const SESSION_MS = 30 * 60 * 1000; // 30 minutes – OWASP A07

// ── Helpers ────────────────────────────────────────────────────────────────
function toast(msg, ok = true) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `fixed top-4 right-4 z-50 px-5 py-3 rounded-xl text-sm font-semibold shadow-2xl
    ${ok ? "bg-emerald-700 text-white" : "bg-red-700 text-white"}`;
  el.style.opacity = "1";
  clearTimeout(el._t);
  el._t = setTimeout(() => el.style.opacity = "0", 3500);
}

function fmt(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("nb-NO", { dateStyle:"short", timeStyle:"short" });
}

async function api(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  if (_token) headers["Authorization"] = "Bearer " + _token;
  const res = await fetch(path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

// ── Session timer (OWASP A07 – auto-logout) ────────────────────────────────
function resetSession() { _sessionExpiry = Date.now() + SESSION_MS; }

function startSessionTimer() {
  resetSession();
  document.addEventListener("mousemove", resetSession, { passive: true });
  document.addEventListener("keydown",   resetSession, { passive: true });
  _sessionInterval = setInterval(() => {
    if (!_token) return;
    const rem = Math.max(0, _sessionExpiry - Date.now());
    const m = String(Math.floor(rem / 60000)).padStart(2, "0");
    const s = String(Math.floor((rem % 60000) / 1000)).padStart(2, "0");
    const el = document.getElementById("sessionTimer");
    if (el) el.textContent = `Utløper: ${m}:${s}`;
    if (rem === 0) doLogout();
  }, 1000);
}

function stopSessionTimer() {
  clearInterval(_sessionInterval);
  document.removeEventListener("mousemove", resetSession);
  document.removeEventListener("keydown",   resetSession);
}

// ── Auth ───────────────────────────────────────────────────────────────────
async function doLogin() {
  const btn = document.getElementById("loginBtn");
  const errEl = document.getElementById("loginErr");
  errEl.textContent = "";
  const email = document.getElementById("loginEmail").value.trim();
  const pw    = document.getElementById("loginPw").value;
  if (!email || !pw) { errEl.textContent = "Fyll inn e-post og passord."; return; }

  btn.disabled = true; btn.textContent = "Logger inn…";
  try {
    const tok = await api("POST", "/auth/login", { email, password: pw });
    _token = tok.access_token;
    _me    = await api("GET", "/me");
    if (_me.role !== "admin") {
      _token = null; _me = null;
      errEl.textContent = "Kun admin-brukere har tilgang.";
      return;
    }
    showDashboard();
    startSessionTimer();
  } catch (e) {
    errEl.textContent = (e.message || "Innlogging feilet").slice(0, 120);
  } finally {
    btn.disabled = false; btn.textContent = "Logg inn";
  }
}

function doLogout() {
  _token = null; _me = null;
  stopSessionTimer();
  document.getElementById("dashboard").style.display = "none";
  document.getElementById("loginSection").style.removeProperty("display");
  document.getElementById("sessionBar").style.setProperty("display", "none", "important");
  document.getElementById("loginEmail").value = "";
  document.getElementById("loginPw").value = "";
  document.getElementById("loginErr").textContent = "";
  document.getElementById("headerOrg").textContent = "Administrasjon";
}

function showDashboard() {
  document.getElementById("loginSection").style.display = "none";
  document.getElementById("dashboard").style.removeProperty("display");
  const sb = document.getElementById("sessionBar");
  sb.style.removeProperty("display");
  document.getElementById("avatar").textContent = (_me.email || "?")[0].toUpperCase();
  document.getElementById("headerOrg").textContent = _me.organization_name || "Organisasjon";
  document.getElementById("orgName").textContent  = _me.organization_name || "—";
  document.getElementById("orgAdmin").textContent = _me.email || "—";
  document.getElementById("orgId").textContent    = _me.organization_id ?? "—";
  loadUsers();
  loadKeys();
}

// ── Tabs ───────────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.remove("hidden");
  });
});

// ── Users ──────────────────────────────────────────────────────────────────
async function loadUsers() {
  const tbody  = document.getElementById("usersBody");
  const empty  = document.getElementById("usersEmpty");
  tbody.innerHTML = "";
  try {
    const users = await api("GET", "/users");
    if (!users.length) { empty.classList.remove("hidden"); return; }
    empty.classList.add("hidden");
    users.forEach(u => {
      const tr = document.createElement("tr");
      tr.className = "row-hover";
      const isSelf = u.id === _me?.id;
      tr.innerHTML = `
        <td class="px-4 py-3">
          <div class="font-medium text-slate-100">${esc(u.email)}</div>
          ${isSelf ? '<div class="text-[10px] text-blue-400">deg</div>' : ""}
        </td>
        <td class="px-4 py-3">
          <span class="badge-${u.role} text-[10px] font-semibold px-2 py-0.5 rounded-full">
            ${u.role === "admin" ? "Admin" : "Bruker"}
          </span>
        </td>
        <td class="px-4 py-3 text-slate-400">${fmt(u.created_at)}</td>
        <td class="px-4 py-3 text-right">
          ${isSelf ? "" : `<button class="text-red-400 hover:text-red-300 text-xs transition-colors"
             onclick="removeUser(${u.id},'${esc(u.email)}')">Fjern</button>`}
        </td>`;
      tbody.appendChild(tr);
    });
  } catch(e) { toast("Feil: " + e.message, false); }
}

async function removeUser(id, email) {
  if (!confirm(`Fjern brukeren ${email}?`)) return;
  try {
    await api("DELETE", `/users/${id}`);
    toast("Bruker fjernet.");
    loadUsers();
  } catch(e) { toast("Feil: " + e.message, false); }
}

document.getElementById("showAddUser").addEventListener("click", () => {
  document.getElementById("addUserForm").classList.toggle("hidden");
});
document.getElementById("cancelAddUser").addEventListener("click", () => {
  document.getElementById("addUserForm").classList.add("hidden");
});
document.getElementById("createUserBtn").addEventListener("click", async () => {
  const email = document.getElementById("newEmail").value.trim();
  const pw    = document.getElementById("newPw").value;
  const role  = document.getElementById("newRole").value;
  const errEl = document.getElementById("addUserErr");
  errEl.textContent = "";
  if (!email || !pw) { errEl.textContent = "E-post og passord er påkrevd."; return; }
  if (pw.length < 8)  { errEl.textContent = "Passord må ha minst 8 tegn."; return; }
  try {
    await api("POST", "/users", { email, password: pw, role });
    toast("Bruker opprettet.");
    document.getElementById("newEmail").value = "";
    document.getElementById("newPw").value    = "";
    document.getElementById("addUserForm").classList.add("hidden");
    loadUsers();
  } catch(e) { errEl.textContent = (e.message || "Feil").slice(0, 160); }
});

// ── API Keys ───────────────────────────────────────────────────────────────
async function loadKeys() {
  const tbody = document.getElementById("keysBody");
  const empty = document.getElementById("keysEmpty");
  tbody.innerHTML = "";
  try {
    const keys = await api("GET", "/apikeys");
    const active = keys.filter(k => !k.revoked);
    if (!active.length) { empty.classList.remove("hidden"); return; }
    empty.classList.add("hidden");
    active.forEach(k => {
      const tr = document.createElement("tr");
      tr.className = "row-hover";
      tr.innerHTML = `
        <td class="px-4 py-3 font-medium text-slate-100">${esc(k.name)}</td>
        <td class="px-4 py-3"><code class="key-mono text-slate-300 text-[11px] bg-slate-900 px-2 py-0.5 rounded">${esc(k.key_prefix)}…</code></td>
        <td class="px-4 py-3 text-slate-400">${fmt(k.created_at)}</td>
        <td class="px-4 py-3 text-slate-400">${fmt(k.last_used_at)}</td>
        <td class="px-4 py-3 text-right">
          <button class="text-red-400 hover:text-red-300 text-xs transition-colors"
            onclick="revokeKey(${k.id},'${esc(k.name)}')">Trekk tilbake</button>
        </td>`;
      tbody.appendChild(tr);
    });
  } catch(e) { toast("Feil: " + e.message, false); }
}

async function revokeKey(id, name) {
  if (!confirm(`Trekk tilbake nøkkelen "${name}"?\nDette kan ikke angres.`)) return;
  try {
    await api("DELETE", `/apikeys/${id}`);
    toast("Nøkkel tilbakekalt.");
    document.getElementById("newKeyReveal").classList.add("hidden");
    loadKeys();
  } catch(e) { toast("Feil: " + e.message, false); }
}

document.getElementById("createKeyBtn").addEventListener("click", () => {
  document.getElementById("createKeyForm").classList.toggle("hidden");
  document.getElementById("newKeyReveal").classList.add("hidden");
});
document.getElementById("cancelCreateKey").addEventListener("click", () => {
  document.getElementById("createKeyForm").classList.add("hidden");
});
document.getElementById("doCreateKey").addEventListener("click", async () => {
  const name = document.getElementById("keyName").value.trim();
  if (!name) { toast("Skriv inn et navn for nøkkelen.", false); return; }
  try {
    const k = await api("POST", "/apikeys", { name });
    document.getElementById("createKeyForm").classList.add("hidden");
    document.getElementById("keyName").value = "";
    const reveal = document.getElementById("newKeyReveal");
    document.getElementById("newKeyText").textContent = k.key;
    reveal.classList.remove("hidden");
    reveal.scrollIntoView({ behavior: "smooth", block: "nearest" });
    toast("Nøkkel generert – kopier den nå!");
    loadKeys();
  } catch(e) { toast("Feil: " + e.message, false); }
});

document.getElementById("copyKeyBtn").addEventListener("click", () => {
  const txt = document.getElementById("newKeyText").textContent;
  navigator.clipboard.writeText(txt).then(() => toast("Nøkkel kopiert!"))
    .catch(() => { document.getElementById("newKeyText").select?.(); toast("Marker og kopier manuelt.", false); });
});

// ── Escape HTML ────────────────────────────────────────────────────────────
function esc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
         .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}

// ── Wire up ────────────────────────────────────────────────────────────────
document.getElementById("loginBtn").addEventListener("click", doLogin);
document.getElementById("logoutBtn").addEventListener("click", doLogout);
document.getElementById("loginPw").addEventListener("keydown", e => { if (e.key === "Enter") doLogin(); });
document.getElementById("loginEmail").addEventListener("keydown", e => { if (e.key === "Enter") document.getElementById("loginPw").focus(); });
</script>
</body>
</html>"""


@router.get("/admin", response_class=HTMLResponse)
def admin_portal() -> str:
    return _HTML
