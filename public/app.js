/* ── Gaadi SPA — vanilla JS, zero build step ───────────────────── */
"use strict";

const API = "/api";
let TOKEN = localStorage.getItem("gaadi_token") || "";
let CURRENT_USER = null;

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
};

function toast(msg) {
  let t = $("#toast");
  if (!t) { t = el("div"); t.id = "toast"; document.body.appendChild(t); }
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 2600);
}

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (TOKEN) headers["Authorization"] = `Bearer ${TOKEN}`;
  const res = await fetch(API + path, { ...opts, headers });
  if (res.status === 401 && TOKEN) { TOKEN = ""; localStorage.removeItem("gaadi_token"); render(); }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new Error((data && data.detail) || "Something went wrong");
  return data;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function fmtMoney(n) { return "Rs " + Number(n || 0).toLocaleString("en-PK", { maximumFractionDigits: 0 }); }
function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}
function fmtOdo(n) { return Number(n || 0).toLocaleString("en-PK") + " km"; }

/* ── view router ───────────────────────────────────────────────── */
const routes = {};

function render() {
  const app = $("#app");
  const hash = location.hash.replace(/^#\/?/, "") || "dashboard";
  const [name, param] = hash.split("/");

  if (!TOKEN && name !== "share") { app.innerHTML = ""; app.appendChild(authView()); return; }
  if (name === "share") { app.innerHTML = ""; app.appendChild(shareView(decodeURIComponent(param || ""))); return; }

  app.innerHTML = "";
  app.appendChild(layout(name));
  const content = $("#view");
  if (routes[name]) routes[name](content, param);
  else routes.dashboard(content);
}

/* ── auth ──────────────────────────────────────────────────────── */
function authView() {
  const wrap = el("div", "auth-wrap");
  const card = el("div", "card auth-card");
  card.innerHTML = `
    <div class="brand">Gaadi<span class="dot">.</span></div>
    <div class="auth-sub">Maintenance schedules & fuel mileage for your ride</div>
    <div class="tabs">
      <button class="tab active" data-tab="login">Login</button>
      <button class="tab" data-tab="register">Register</button>
    </div>
    <form id="auth-form">
      <div id="name-field" style="display:none">
        <label>Your name</label>
        <input name="name" type="text" placeholder="e.g. Ali" minlength="2">
      </div>
      <label>Email</label>
      <input name="email" type="email" placeholder="you@example.com" required>
      <label>Password</label>
      <input name="password" type="password" placeholder="min 8 characters" minlength="8" required>
      <div class="spacer"></div>
      <button class="btn block" type="submit">Continue</button>
    </form>`;
  wrap.appendChild(card);

  card.querySelectorAll(".tab").forEach((tab) =>
    tab.addEventListener("click", () => {
      card.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      $("#name-field").style.display = tab.dataset.tab === "register" ? "block" : "none";
      $("#name-field input[name=name]").required = tab.dataset.tab === "register";
    })
  );

  card.querySelector("#auth-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const isLogin = card.querySelector(".tab.active").dataset.tab === "login";
    const body = isLogin
      ? { email: fd.get("email"), password: fd.get("password") }
      : { name: fd.get("name"), email: fd.get("email"), password: fd.get("password") };
    try {
      const data = await api("/auth/" + (isLogin ? "login" : "register"), { method: "POST", body: JSON.stringify(body) });
      TOKEN = data.access_token;
      CURRENT_USER = data.user;
      localStorage.setItem("gaadi_token", TOKEN);
      location.hash = "#/dashboard";
      render();
      toast("Welcome back! 👋");
    } catch (err) { toast(err.message); }
  });
  return wrap;
}

/* ── layout ────────────────────────────────────────────────────── */
function layout(active) {
  const wrap = el("div");
  const nav = el("div", "topbar");
  nav.innerHTML = `
    <div class="brand"><a href="#/dashboard" style="color:var(--text)">Gaadi<span class="dot">.</span></a></div>
    <div class="top-actions">
      <a class="btn ghost small" href="#/vehicles">Vehicles</a>
      <a class="btn ghost small" href="#/share">My report</a>
      <button class="btn ghost small" id="logout">Logout</button>
    </div>`;
  wrap.appendChild(nav);
  const view = el("div", "container");
  view.id = "view";
  wrap.appendChild(view);
  nav.querySelector("#logout").addEventListener("click", () => {
    TOKEN = ""; localStorage.removeItem("gaadi_token"); render();
  });
  return wrap;
}

/* ── dashboard ─────────────────────────────────────────────────── */
routes.dashboard = async function (content) {
  content.innerHTML = `<div class="empty">Loading…</div>`;
  try {
    const [vehicles, me] = await Promise.all([api("/vehicles"), api("/auth/me")]);
    CURRENT_USER = me;
    let totalDue = 0, totalCost = 0;
    const schedules = {};
    for (const v of vehicles) {
      const [sched, stats] = await Promise.all([api(`/vehicles/${v.id}/schedule`), api(`/vehicles/${v.id}/fuel/stats`)]);
      schedules[v.id] = sched;
      totalDue += sched.filter((s) => s.overdue).length;
      totalCost += stats.total_cost || 0;
    }
    content.innerHTML = `
      <div class="section-title">Salam, ${esc(me.name.split(" ")[0])} 👋 <span class="sub">${new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })}</span></div>
      <div class="grid cols-3">
        <div class="card stat ${totalDue > 0 ? "red" : "green"}"><div class="num">${totalDue}</div><div class="lbl">Overdue services</div></div>
        <div class="card stat blue"><div class="num">${vehicles.length}</div><div class="lbl">Vehicles</div></div>
        <div class="card stat amber"><div class="num">${fmtMoney(totalCost)}</div><div class="lbl">Fuel spent all-time</div></div>
      </div>
      <div class="section-title">Your vehicles</div>
      ${vehicles.length === 0
        ? `<div class="card empty">No vehicles yet — add your first one.<div class="spacer"></div><a class="btn small" href="#/vehicles">Add a vehicle</a></div>`
        : vehicles.map((v) => `
          <div class="card vcard" data-id="${v.id}">
            <div>
              <div class="vname">${esc(v.name)}</div>
              <div class="vplate">${esc(v.plate)} · ${v.year} · ${esc(v.fuel_type)}</div>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              ${(schedules[v.id] || []).filter((s) => s.overdue).length > 0
                ? `<span class="chip bad">${(schedules[v.id] || []).filter((s) => s.overdue).length} overdue</span>`
                : `<span class="chip ok">all good</span>`}
              <span class="arrow">›</span>
            </div>
          </div>`).join("")}
    `;
    content.querySelectorAll(".vcard").forEach((c) =>
      c.addEventListener("click", () => (location.hash = `#/vehicle/${c.dataset.id}`))
    );
  } catch (err) { content.innerHTML = `<div class="empty">${esc(err.message)}</div>`; }
};

/* ── vehicles list + create ────────────────────────────────────── */
routes.vehicles = async function (content) {
  content.innerHTML = `<div class="empty">Loading…</div>`;
  try {
    const vehicles = await api("/vehicles");
    content.innerHTML = `
      <div class="section-title">Vehicles <button class="btn small" id="add-vehicle">+ Add vehicle</button></div>
      ${vehicles.length === 0
        ? `<div class="card empty">Nothing here yet. Add your first vehicle to start tracking.</div>`
        : vehicles.map((v) => `
          <div class="card vcard" data-id="${v.id}">
            <div>
              <div class="vname">${esc(v.name)}</div>
              <div class="vplate">${esc(v.plate)} · ${v.year} · ${esc(v.make)} ${esc(v.model)}</div>
            </div>
            <span class="arrow">›</span>
          </div>`).join("")}
      <div class="card">
        <h2>New vehicle</h2>
        <form id="vehicle-form">
          <label>Name</label><input name="name" placeholder="e.g. City 2019" required>
          <div class="grid cols-2">
            <div><label>Make</label><input name="make" placeholder="Honda" required></div>
            <div><label>Model</label><input name="model" placeholder="City" required></div>
          </div>
          <div class="grid cols-2">
            <div><label>Year</label><input name="year" type="number" min="1950" max="2100" value="2019" required></div>
            <div><label>Plate</label><input name="plate" placeholder="ABC-123" required></div>
          </div>
          <div class="grid cols-2">
            <div><label>Fuel type</label>
              <select name="fuel_type"><option value="petrol">Petrol</option><option value="diesel">Diesel</option><option value="CNG">CNG</option><option value="electric">Electric</option></select>
            </div>
            <div><label>Current odometer (km)</label><input name="odometer_km" type="number" min="0" value="0" step="any" required></div>
          </div>
          <div class="spacer"></div>
          <button class="btn block" type="submit">Save vehicle</button>
        </form>
      </div>`;
    content.querySelectorAll(".vcard").forEach((c) =>
      c.addEventListener("click", () => (location.hash = `#/vehicle/${c.dataset.id}`))
    );
    content.querySelector("#vehicle-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = {
        name: fd.get("name"), make: fd.get("make"), model: fd.get("model"),
        year: Number(fd.get("year")), plate: fd.get("plate"),
        fuel_type: fd.get("fuel_type"), odometer_km: Number(fd.get("odometer_km")),
      };
      try { await api("/vehicles", { method: "POST", body: JSON.stringify(body) }); toast("Vehicle added 🚗"); render(); }
      catch (err) { toast(err.message); }
    });
  } catch (err) { content.innerHTML = `<div class="empty">${esc(err.message)}</div>`; }
};

/* ── vehicle detail ────────────────────────────────────────────── */
routes.vehicle = async function (content, id) {
  content.innerHTML = `<div class="empty">Loading…</div>`;
  try {
    const [v, sched, services, fillups, stats] = await Promise.all([
      api(`/vehicles/${id}`), api(`/vehicles/${id}/schedule`),
      api(`/vehicles/${id}/services`), api(`/vehicles/${id}/fuel`),
      api(`/vehicles/${id}/fuel/stats`),
    ]);
    const overdue = sched.filter((s) => s.overdue);
    const upcoming = sched.filter((s) => !s.overdue);
    content.innerHTML = `
      <a href="#/vehicles" class="muted">← All vehicles</a>
      <div class="section-title">${esc(v.name)} <span class="sub">${esc(v.plate)} · ${v.year}</span></div>
      <div class="grid cols-3">
        <div class="card stat blue"><div class="num">${fmtOdo(v.odometer_km)}</div><div class="lbl">Odometer</div></div>
        <div class="card stat amber"><div class="num">${stats.avg_mileage_kmpl ?? "—"}</div><div class="lbl">Avg km/L</div></div>
        <div class="card stat ${overdue.length ? "red" : "green"}"><div class="num">${overdue.length}</div><div class="lbl">Overdue</div></div>
      </div>

      <div class="section-title">Maintenance schedule <button class="btn small" data-open="service-modal">+ Log service</button></div>
      ${sched.length === 0 ? `<div class="card empty">No schedule configured.</div>` : ""}
      ${[...overdue, ...upcoming].map((s) => `
        <div class="due-item ${s.overdue ? "overdue" : ""}">
          <div>
            <div class="due-name">${esc(s.name)} ${s.overdue ? '<span class="chip bad">overdue</span>' : s.reason === "Coming up soon — plan this service" ? '<span class="chip warn">soon</span>' : ""}</div>
            <div class="due-meta">due ${s.due_km ? fmtOdo(s.due_km) : "—"} · ${s.due_date ? fmtDate(s.due_date) : "—"}</div>
          </div>
          <div class="muted">${s.overdue ? "" : s.days_remaining > 0 ? `${s.days_remaining}d left` : ""}</div>
        </div>`).join("")}

      <div class="section-title">Fuel & mileage <button class="btn small" data-open="fuel-modal">+ Log fill-up</button></div>
      <div class="grid cols-3">
        <div class="card stat"><div class="num">${stats.avg_price_per_liter ?? "—"}</div><div class="lbl">Avg Rs/L</div></div>
        <div class="card stat"><div class="num">${stats.last_mileage_kmpl ?? "—"}</div><div class="lbl">Last km/L</div></div>
        <div class="card stat"><div class="num">${fmtMoney(stats.cost_per_km ?? 0)}</div><div class="lbl">Cost / km</div></div>
      </div>
      ${fillups.length === 0 ? `<div class="card empty">Log your first fill-up to see mileage.</div>` : fillups.slice(0, 8).map((f) => `
        <div class="list-row">
          <div class="row-main">
            <div class="row-title">${fmtDate(f.date)} · ${f.liters} L</div>
            <div class="row-sub">${fmtOdo(f.odometer_km)} · ${fmtMoney(f.cost)}${f.full_tank ? " · full tank" : ""}</div>
          </div>
          ${f.mileage_kmpl ? `<span class="chip ok">${f.mileage_kmpl} km/L</span>` : ""}
        </div>`).join("")}

      <div class="section-title">Service history</div>
      ${services.length === 0 ? `<div class="card empty">No services logged yet.</div>` : services.slice(0, 8).map((s) => `
        <div class="list-row">
          <div class="row-main">
            <div class="row-title">${esc(s.custom_name || s.service_type)}</div>
            <div class="row-sub">${fmtDate(s.date)} · ${fmtOdo(s.odometer_km)}${s.notes ? " · " + esc(s.notes) : ""}</div>
          </div>
          <div class="muted">${fmtMoney(s.cost)}</div>
        </div>`).join("")}

      <div class="spacer"></div>
      <div class="card">
        <h2>Share maintenance report</h2>
        <p class="muted">When enabled, anyone with the link can see this vehicle's service history — great for resale.</p>
        <div class="spacer"></div>
        <button class="btn small" id="toggle-share">${v.share_enabled ? "Disable sharing" : "Enable sharing"}</button>
        ${v.share_enabled ? `<div class="spacer"></div><div class="muted" style="word-break:break-all">${location.origin}/#/share/${v.share_token}</div>` : ""}
      </div>
    `;

    content.querySelector("[data-open='service-modal']").addEventListener("click", () => openModal(serviceForm(v.id)));
    content.querySelector("[data-open='fuel-modal']").addEventListener("click", () => openModal(fuelForm(v.id)));
    content.querySelector("#toggle-share").addEventListener("click", async () => {
      try {
        const updated = await api(`/vehicles/${id}/share`, { method: "PUT", body: JSON.stringify({ enabled: !v.share_enabled }) });
        toast(updated.share_enabled ? "Report is now public 🔗" : "Sharing disabled");
        render();
      } catch (err) { toast(err.message); }
    });
  } catch (err) { content.innerHTML = `<div class="empty">${esc(err.message)}</div>`; }
};

/* ── modals ────────────────────────────────────────────────────── */
function openModal(inner) {
  const bg = el("div", "modal-bg open");
  bg.innerHTML = `<div class="modal">${inner}</div>`;
  bg.addEventListener("click", (e) => { if (e.target === bg) bg.remove(); });
  document.body.appendChild(bg);
  bg.querySelector(".modal-close").addEventListener("click", () => bg.remove());
  return bg;
}

function serviceForm(vehicleId) {
  return `
    <button class="modal-close">×</button>
    <h3>Log a service</h3>
    <p class="muted">Record what was done and what it cost.</p>
    <form id="modal-form">
      <label>Service type</label>
      <select name="service_type">
        <option value="oil">Oil Change</option>
        <option value="tires">Tire Rotation</option>
        <option value="brakes">Brake Inspection</option>
        <option value="general">General Service</option>
        <option value="custom">Custom</option>
      </select>
      <div id="custom-wrap" style="display:none"><label>Custom name</label><input name="custom_name" placeholder="e.g. AC repair"></div>
      <label>Odometer at service (km)</label><input name="odometer_km" type="number" min="0" step="any" required>
      <label>Cost (Rs)</label><input name="cost" type="number" min="0" step="any" value="0">
      <label>Notes</label><textarea name="notes" rows="2" placeholder="Optional details"></textarea>
      <div class="spacer"></div>
      <button class="btn block" type="submit">Save service</button>
    </form>`;
}

function fuelForm(vehicleId) {
  return `
    <button class="modal-close">×</button>
    <h3>Log a fill-up</h3>
    <p class="muted">Mark "full tank" to calculate mileage vs the previous full fill.</p>
    <form id="modal-form">
      <label>Odometer (km)</label><input name="odometer_km" type="number" min="0" step="any" required>
      <label>Liters</label><input name="liters" type="number" min="0.1" step="any" required>
      <label>Cost (Rs)</label><input name="cost" type="number" min="0" step="any" required>
      <label style="display:flex;align-items:center;gap:8px;margin-top:14px">
        <input name="full_tank" type="checkbox" checked style="width:auto"> Full tank
      </label>
      <div class="spacer"></div>
      <button class="btn block" type="submit">Save fill-up</button>
    </form>`;
}

document.addEventListener("submit", async (e) => {
  const form = e.target;
  if (form.id !== "modal-form") return;
  e.preventDefault();
  const bg = form.closest(".modal-bg");
  const vehicleId = location.hash.split("/")[1];
  const fd = new FormData(form);
  const isService = form.closest(".modal").querySelector("h3").textContent.includes("service");
  const body = isService
    ? { service_type: fd.get("service_type"), custom_name: fd.get("custom_name") || null, odometer_km: Number(fd.get("odometer_km")), cost: Number(fd.get("cost") || 0), notes: fd.get("notes") || null }
    : { odometer_km: Number(fd.get("odometer_km")), liters: Number(fd.get("liters")), cost: Number(fd.get("cost")), full_tank: fd.get("full_tank") === "on" };
  try {
    await api(`/vehicles/${vehicleId}/${isService ? "services" : "fuel"}`, { method: "POST", body: JSON.stringify(body) });
    bg.remove(); toast(isService ? "Service logged ✅" : "Fill-up logged ⛽"); render();
  } catch (err) { toast(err.message); }
});

/* ── share page ────────────────────────────────────────────────── */
function shareView(token) {
  const wrap = el("div", "container");
  wrap.innerHTML = `<div class="empty">Loading report…</div>`;
  api(`/public/vehicles/${token}`).then((r) => {
    wrap.innerHTML = `
      <div class="share-hero">
        <h1>${esc(r.vehicle.name)}</h1>
        <p class="muted">${esc(r.vehicle.plate)} · ${r.vehicle.year} · ${esc(r.vehicle.fuel_type)}</p>
        <span class="share-badge">${fmtOdo(r.vehicle.odometer_km)}</span>
        <span class="share-badge">${r.service_count} services</span>
        <span class="share-badge">${fmtMoney(r.total_service_cost)} total</span>
      </div>
      <div class="card">
        <h2>Maintenance history</h2>
        ${r.services.length === 0 ? `<div class="empty">No services recorded yet.</div>` : r.services.map((s) => `
          <div class="list-row">
            <div class="row-main">
              <div class="row-title">${esc(s.custom_name || s.service_type)}</div>
              <div class="row-sub">${fmtDate(s.date)} · ${fmtOdo(s.odometer_km)}${s.notes ? " · " + esc(s.notes) : ""}</div>
            </div>
            <div class="muted">${fmtMoney(s.cost)}</div>
          </div>`).join("")}
      </div>
      <p class="muted" style="text-align:center">Powered by Gaadi — vehicle maintenance tracker</p>`;
  }).catch((err) => {
    wrap.innerHTML = `<div class="empty">${esc(err.message)}</div>`;
  });
  return wrap;
}

/* ── boot ──────────────────────────────────────────────────────── */
window.addEventListener("hashchange", render);
render();
