const $ = (selector) => document.querySelector(selector);
let currentDesk = null;

function employee() {
  return $("#employee").value.trim();
}

function showMessage(text, kind = "ok") {
  const el = $("#message");
  el.textContent = text;
  el.className = kind;
}

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = res.status === 204 ? null : await res.json();
  if (!res.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : "Dados inválidos. Confira os campos.";
    throw new Error(detail);
  }
  return data;
}

function el(tag, text, attrs = {}) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}

// ---------- abas ----------
function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  for (const panel of ["desks", "rooms", "mine"]) $(`#panel-${panel}`).hidden = panel !== name;
}
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => switchTab(t.dataset.tab)));

// ---------- mesas ----------
async function loadDesks() {
  const desks = await api(`/api/desks?floor=${$("#desk-floor").value}`);
  const grid = $("#desk-grid");
  grid.replaceChildren();
  for (const desk of desks) {
    const button = el("button", `Mesa ${desk.number}`, { "data-testid": `desk-${desk.id}`, class: "desk" });
    button.addEventListener("click", () => selectDesk(desk));
    grid.append(button);
  }
  $("#desk-detail").hidden = true;
}

async function selectDesk(desk) {
  currentDesk = desk;
  document.querySelectorAll(".desk").forEach((b) =>
    b.classList.toggle("selected", b.dataset.testid === `desk-${desk.id}`));
  const days = await api(`/api/desks/${desk.id}/availability`);
  $("#desk-title").textContent = `Mesa ${desk.number} · ${desk.floor}º andar (${desk.id})`;
  const box = $("#desk-days");
  box.replaceChildren();
  if (days.length === 0) box.append(el("p", "Esta mesa não tem dias livres no período permitido."));
  for (const day of days) {
    const row = el("div", undefined, { class: "day-row" });
    const select = el("select", undefined, { "data-day": day.day, "data-testid": `period-${day.day}` });
    select.append(el("option", "Não reservar", { value: "" }));
    for (const p of day.free) select.append(el("option", p.label, { value: p.value }));
    row.append(el("span", day.label), select);
    box.append(row);
  }
  $("#desk-detail").hidden = false;
}

$("#desk-book").addEventListener("click", async () => {
  const selections = [...document.querySelectorAll("#desk-days select")]
    .filter((s) => s.value)
    .map((s) => ({ day: s.dataset.day, period: s.value }));
  try {
    const created = await api(`/api/desks/${currentDesk.id}/bookings`, {
      method: "POST",
      body: JSON.stringify({ employee: employee(), selections }),
    });
    showMessage(`Mesa ${currentDesk.id} reservada para ${created.length} dia(s).`);
    await selectDesk(currentDesk);
  } catch (err) {
    showMessage(err.message, "error");
  }
});

$("#desk-floor").addEventListener("change", loadDesks);

// ---------- início ----------
try { $("#employee").value = localStorage.getItem("employee") || ""; } catch { /* sem storage */ }
$("#employee").addEventListener("change", () => {
  try { localStorage.setItem("employee", employee()); } catch { /* sem storage */ }
});
loadDesks();