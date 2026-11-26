const $ = (selector) => document.querySelector(selector);
let currentDesk = null;

function employee() {
  return $("#employee").value.trim();
}

function localToday() {
  return new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD no fuso local
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
  if (name === "rooms") loadRoomSchedule();
  if (name === "mine") loadMine();
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

// ---------- salas ----------
async function loadRooms() {
  const rooms = await api(`/api/rooms?floor=${$("#room-floor").value}`);
  const select = $("#room-select");
  select.replaceChildren(...rooms.map((r) => el("option", `Sala ${r.number} (${r.id})`, { value: r.id })));
  await loadRoomSchedule();
}

async function loadRoomSchedule() {
  const list = $("#room-schedule");
  const roomId = $("#room-select").value;
  const day = $("#room-day").value;
  list.replaceChildren();
  if (!roomId || !day) return;
  const bookings = await api(`/api/rooms/${roomId}/bookings?day=${day}`);
  if (bookings.length === 0) list.append(el("li", "Nenhuma reserva neste dia."));
  for (const b of bookings) {
    list.append(el("li", `${b.start}–${b.end} · ${b.employee}${b.title ? " · " + b.title : ""}`));
  }
}

$("#room-book").addEventListener("click", async () => {
  const roomId = $("#room-select").value;
  try {
    await api(`/api/rooms/${roomId}/bookings`, {
      method: "POST",
      body: JSON.stringify({
        employee: employee(),
        day: $("#room-day").value,
        start: $("#room-start").value,
        end: $("#room-end").value,
        title: $("#room-title").value,
      }),
    });
    showMessage(`Sala ${roomId} reservada.`);
    await loadRoomSchedule();
  } catch (err) {
    showMessage(err.message, "error");
  }
});

$("#room-floor").addEventListener("change", loadRooms);
$("#room-select").addEventListener("change", loadRoomSchedule);
$("#room-day").addEventListener("change", loadRoomSchedule);

// ---------- minhas reservas ----------
async function loadMine() {
  const list = $("#my-bookings");
  list.replaceChildren();
  if (!employee()) {
    list.append(el("li", "Informe seu nome no topo da página para ver suas reservas."));
    return;
  }
  const data = await api(`/api/bookings?employee=${encodeURIComponent(employee())}`);
  if (data.desks.length + data.rooms.length === 0) list.append(el("li", "Você não tem reservas futuras."));
  for (const b of data.desks) {
    addMineRow(list, `Mesa ${b.desk_id} · ${b.day_label} · ${b.period_label}`,
      `/api/desk-bookings/${b.id}`, `cancel-desk-${b.id}`);
  }
  for (const b of data.rooms) {
    addMineRow(list, `Sala ${b.room_id} · ${b.day_label} · ${b.start}–${b.end}`,
      `/api/room-bookings/${b.id}`, `cancel-room-${b.id}`);
  }
}

function addMineRow(list, text, url, testId) {
  const item = el("li", undefined);
  const button = el("button", "Cancelar", { "data-testid": testId });
  button.addEventListener("click", async () => {
    try {
      await api(`${url}?employee=${encodeURIComponent(employee())}`, { method: "DELETE" });
      showMessage("Reserva cancelada.");
      await loadMine();
    } catch (err) {
      showMessage(err.message, "error");
    }
  });
  item.append(el("span", text), button);
  list.append(item);
}

// ---------- início ----------
try { $("#employee").value = localStorage.getItem("employee") || ""; } catch { /* sem storage */ }
$("#employee").addEventListener("change", () => {
  try { localStorage.setItem("employee", employee()); } catch { /* sem storage */ }
});
$("#room-day").value = localToday();
$("#room-day").min = localToday();
loadDesks();
loadRooms();