"""Enkel web-basert admin-portal for OPS Monitor.

Moderne, responsivt UI levert som ren HTML/JS (Tailwind fra CDN),
og bruker eksisterende API-endepunkter for innlogging og brukeradmin.

Merk: Denne portalen er ment for administratorer. Auth skjer via
JWT i minnet i nettleseren (ikke lagret i localStorage/cookies) for
å redusere angrepsflate ved XSS.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-portal"])


@router.get("/admin", response_class=HTMLResponse)
def admin_portal() -> str:
    # Minimal single-page admin-app. Tailwind via CDN for moderne uttrykk.
    return """
<!doctype html>
<html lang="no">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OPS Monitor – Admin</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,typography"></script>
    <style>
      body { background: radial-gradient(circle at top, #020617 0, #020617 40%, #000 100%); }
      .glass {
        backdrop-filter: blur(18px);
        background: rgba(15,23,42,0.92);
        border: 1px solid rgba(148,163,184,0.2);
      }
    </style>
  </head>
  <body class="min-h-screen text-slate-100">
    <div class="max-w-6xl mx-auto px-4 py-8 space-y-8">
      <!-- Header -->
      <header class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-blue-500/90 flex items-center justify-center shadow-lg shadow-blue-500/40">
            <span class="font-semibold text-white">OPS</span>
          </div>
          <div>
            <h1 class="text-xl font-semibold tracking-tight">OPS Monitor – Admin</h1>
            <p class="text-sm text-slate-400">Administrer organisasjoner og brukere for operasjonssentralen.</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <div id="adminAvatar" class="h-8 w-8 rounded-full bg-slate-700 flex items-center justify-center text-sm font-semibold"></div>
          <button id="logoutBtn" class="text-sm text-slate-300 hover:text-red-400 hidden">Logg ut</button>
        </div>
      </header>

      <!-- Layout -->
      <main class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <!-- Login / Org-info -->
        <section class="glass rounded-2xl p-6 shadow-xl lg:col-span-1">
          <h2 class="text-sm font-semibold text-slate-300 tracking-wide mb-4">Innlogging</h2>
          <form id="loginForm" class="space-y-4">
            <div>
              <label class="block text-sm mb-1" for="email">E-post</label>
              <input id="email" type="email" required class="w-full rounded-lg bg-slate-900/60 border border-slate-700 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="admin@bedrift.no" />
            </div>
            <div>
              <label class="block text-sm mb-1" for="password">Passord</label>
              <input id="password" type="password" required minlength="8" class="w-full rounded-lg bg-slate-900/60 border border-slate-700 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="••••••••" />
            </div>
            <p id="loginError" class="text-xs text-red-400 min-h-[1.25rem]"></p>
            <button type="submit" class="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-blue-500 hover:bg-blue-400 text-sm font-semibold py-2.5 shadow-lg shadow-blue-500/30 transition-colors">
              Logg inn som admin
            </button>
          </form>

          <div id="orgInfo" class="mt-6 hidden border-t border-slate-700/70 pt-4 text-sm space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Organisasjon</span>
              <span id="orgName" class="font-medium text-slate-100"></span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">E-post (innlogget)</span>
              <span id="adminEmail" class="font-mono text-xs text-slate-200"></span>
            </div>
          </div>
        </section>

        <!-- Users panel -->
        <section class="glass rounded-2xl p-6 shadow-xl lg:col-span-2">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 class="text-sm font-semibold text-slate-300 tracking-wide">Brukere</h2>
              <p class="text-xs text-slate-400">Legg til og fjern brukere for organisasjonen.</p>
            </div>
            <button id="refreshUsers" class="inline-flex items-center gap-1 text-xs text-slate-300 hover:text-white disabled:opacity-40" disabled>
              ↻ Oppdater
            </button>
          </div>
          <div id="usersEmpty" class="text-xs text-slate-500 border border-dashed border-slate-700 rounded-lg px-4 py-6 text-center">
            Logg inn som admin for å se brukere.
          </div>
          <div id="usersPanel" class="hidden space-y-4">
            <div class="flex flex-wrap items-end gap-3">
              <div class="flex-1 min-w-[180px]">
                <label class="block text-xs mb-1" for="newUserEmail">E-post</label>
                <input id="newUserEmail" type="email" class="w-full rounded-lg bg-slate-900/60 border border-slate-700 text-xs px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="bruker@bedrift.no" />
              </div>
              <div class="flex-1 min-w-[140px]">
                <label class="block text-xs mb-1" for="newUserPassword">Passord</label>
                <input id="newUserPassword" type="password" class="w-full rounded-lg bg-slate-900/60 border border-slate-700 text-xs px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Minst 8 tegn" />
              </div>
              <div>
                <label class="block text-xs mb-1" for="newUserRole">Rolle</label>
                <select id="newUserRole" class="rounded-lg bg-slate-900/60 border border-slate-700 text-xs px-2.5 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option value="user">Bruker</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <button id="createUser" class="inline-flex items-center justify-center rounded-lg bg-emerald-500 hover:bg-emerald-400 text-xs font-semibold px-4 py-2 shadow-md shadow-emerald-500/30 disabled:opacity-40" disabled>
                + Legg til bruker
              </button>
            </div>
            <p id="usersError" class="text-xs text-red-400 min-h-[1.25rem]"></p>
            <div class="border border-slate-800 rounded-xl overflow-hidden">
              <table class="min-w-full text-xs">
                <thead class="bg-slate-900/80 text-slate-300">
                  <tr>
                    <th class="px-3 py-2 text-left font-medium">E-post</th>
                    <th class="px-3 py-2 text-left font-medium">Rolle</th>
                    <th class="px-3 py-2 text-left font-medium">Opprettet</th>
                    <th class="px-3 py-2 text-right font-medium">Handling</th>
                  </tr>
                </thead>
                <tbody id="usersTable" class="divide-y divide-slate-800 bg-slate-950/40"></tbody>
              </table>
            </div>
          </div>
        </section>
      </main>
    </div>

    <script>
      const apiBase = "";
      let accessToken = null;

      function setLoggedIn(user) {
        accessToken = user ? user.access_token || accessToken : null;
        const avatar = document.getElementById("adminAvatar");
        const logoutBtn = document.getElementById("logoutBtn");
        const orgInfo = document.getElementById("orgInfo");
        const orgName = document.getElementById("orgName");
        const adminEmail = document.getElementById("adminEmail");
        const usersPanel = document.getElementById("usersPanel");
        const usersEmpty = document.getElementById("usersEmpty");
        const refreshUsers = document.getElementById("refreshUsers");
        const createUser = document.getElementById("createUser");

        if (!accessToken) {
          avatar.textContent = "";
          avatar.className = "h-8 w-8 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center text-sm font-semibold text-slate-500";
          logoutBtn.classList.add("hidden");
          orgInfo.classList.add("hidden");
          usersPanel.classList.add("hidden");
          usersEmpty.classList.remove("hidden");
          refreshUsers.disabled = true;
          createUser.disabled = true;
          return;
        }

        const email = user && user.email ? user.email : "";
        const org = user && user.organization_name ? user.organization_name : "";
        avatar.textContent = email ? email[0].toUpperCase() : "?";
        avatar.className = "h-8 w-8 rounded-full bg-blue-600 shadow-md shadow-blue-500/50 flex items-center justify-center text-sm font-semibold";
        logoutBtn.classList.remove("hidden");
        orgInfo.classList.remove("hidden");
        usersPanel.classList.remove("hidden");
        usersEmpty.classList.add("hidden");
        refreshUsers.disabled = false;
        createUser.disabled = false;
        orgName.textContent = org || "Ukjent organisasjon";
        adminEmail.textContent = email || "";
        loadUsers();
      }

      async function api(path, options = {}) {
        const headers = options.headers || {};
        headers["Content-Type"] = "application/json";
        if (accessToken) {
          headers["Authorization"] = "Bearer " + accessToken;
        }
        const res = await fetch(apiBase + path, { ...options, headers });
        if (!res.ok) {
          const text = await res.text();
          let detail = text;
          try {
            const data = JSON.parse(text);
            detail = data.detail || text;
          } catch (_) {}
          throw new Error(detail);
        }
        if (res.status === 204) return null;
        return await res.json();
      }

      document.getElementById("loginForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const errorEl = document.getElementById("loginError");
        errorEl.textContent = "";
        try {
          const token = await api("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
          });
          accessToken = token.access_token;
          const me = await api("/me");
          if (me.role !== "admin") {
            accessToken = null;
            errorEl.textContent = "Kun admin-brukere har tilgang til admin-portalen.";
            setLoggedIn(null);
            return;
          }
          setLoggedIn({ ...me, access_token: token.access_token });
        } catch (err) {
          errorEl.textContent = (err && err.message) ? err.message.slice(0, 120) : "Kunne ikke logge inn.";
          setLoggedIn(null);
        }
      });

      document.getElementById("logoutBtn").addEventListener("click", () => {
        accessToken = null;
        setLoggedIn(null);
      });

      async function loadUsers() {
        const tbody = document.getElementById("usersTable");
        const errorEl = document.getElementById("usersError");
        errorEl.textContent = "";
        tbody.innerHTML = "";
        try {
          const users = await api("/users");
          if (!Array.isArray(users)) return;
          for (const u of users) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
              <td class="px-3 py-2 align-middle">
                <div class="flex flex-col">
                  <span class="font-medium text-slate-100">${u.email}</span>
                  <span class="text-[10px] text-slate-500">ID ${u.id}</span>
                </div>
              </td>
              <td class="px-3 py-2 align-middle">
                <span class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                  u.role === "admin" ? "bg-amber-500/10 text-amber-300 border border-amber-500/40" : "bg-slate-700/40 text-slate-200 border border-slate-600/60"
                }">
                  ${u.role}
                </span>
              </td>
              <td class="px-3 py-2 align-middle text-slate-400">
                <span class="text-[11px]">${new Date(u.created_at).toLocaleString("nb-NO")}</span>
              </td>
              <td class="px-3 py-2 align-middle text-right">
                <button class="text-[11px] text-red-400 hover:text-red-300" data-id="${u.id}">Fjern</button>
              </td>
            `;
            tbody.appendChild(tr);
          }
          tbody.querySelectorAll("button[data-id]").forEach((btn) => {
            btn.addEventListener("click", async () => {
              const id = btn.getAttribute("data-id");
              if (!confirm("Vil du fjerne denne brukeren?")) return;
              try {
                await api("/users/" + id, { method: "DELETE" });
                loadUsers();
              } catch (err) {
                errorEl.textContent = (err && err.message) ? err.message.slice(0, 120) : "Kunne ikke fjerne bruker.";
              }
            });
          });
        } catch (err) {
          errorEl.textContent = (err && err.message) ? err.message.slice(0, 120) : "Kunne ikke hente brukere.";
        }
      }

      document.getElementById("refreshUsers").addEventListener("click", (e) => {
        if (!accessToken) return;
        loadUsers();
      });

      document.getElementById("createUser").addEventListener("click", async () => {
        const email = document.getElementById("newUserEmail").value.trim();
        const password = document.getElementById("newUserPassword").value;
        const role = document.getElementById("newUserRole").value;
        const errorEl = document.getElementById("usersError");
        errorEl.textContent = "";
        if (!email || !password) {
          errorEl.textContent = "Fyll inn e-post og passord for ny bruker.";
          return;
        }
        if (password.length < 8) {
          errorEl.textContent = "Passord må ha minst 8 tegn.";
          return;
        }
        try {
          await api("/users", {
            method: "POST",
            body: JSON.stringify({ email, password, role })
          });
          document.getElementById("newUserEmail").value = "";
          document.getElementById("newUserPassword").value = "";
          loadUsers();
        } catch (err) {
          errorEl.textContent = (err && err.message) ? err.message.slice(0, 160) : "Kunne ikke opprette bruker.";
        }
      });
    </script>
  </body>
</html>
    """

