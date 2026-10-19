"use strict";

const ICONS = {
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  week: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18M7 15h10"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>',
  bulb: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>',
  done: '<circle cx="12" cy="12" r="9"/><path d="M9 12l2 2 4-4"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  x: '<path d="M18 6L6 18M6 6l12 12"/>',
  check: '<path d="M5 12l5 5L20 7"/>',
  repeat: '<path d="M4 12V9a3 3 0 0 1 3-3h13m-3-3 3 3-3 3M20 12v3a3 3 0 0 1-3 3H4m3 3-3-3 3-3"/>',
  note: '<path d="M5 6h14M5 12h14M5 18h8"/>',
  restore: '<path d="M9 14l-4-4 4-4"/><path d="M5 10h11a4 4 0 1 1 0 8h-1"/>',
};

function icon(name) {
  return `<span class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg></span>`;
}

const VIEWS = [
  { id: "today", label: "오늘", icon: "sun" },
  { id: "week", label: "이번 주", icon: "week" },
  { id: "later", label: "나중에", icon: "clock" },
  { id: "someday", label: "아이디어", icon: "bulb" },
  null,
  { id: "done", label: "완료", icon: "done" },
  { id: "trash", label: "휴지통", icon: "trash" },
];
const BUCKETS = ["today", "week", "later", "someday"];
const LABEL = Object.fromEntries(VIEWS.filter(Boolean).map(v => [v.id, v.label]));
const RECURRENCE = { daily: "매일", weekly: "매주", monthly: "매월" };
const WEEKDAYS = "일월화수목금토";

// The tray popup (popup.html) reuses this file: Today only, no sidebar or detail panel.
const POPUP = document.body.classList.contains("popup");
const S = { view: "today", project: "", selected: null, data: null };
const $ = id => document.getElementById(id);
const api = () => window.pywebview.api;

// --- helpers ---------------------------------------------------------------

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function parseDate(s) {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function localToday() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function daysUntil(due) {
  return Math.round((parseDate(due) - parseDate(S.data.today)) / 86400000);
}

function hue(name) {
  // Golden-angle spread so names differing by one character ("논문A"/"논문B") get distinct colors.
  let h = 0;
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  h = Math.round((h * 137.508) % 360);
  return h >= 10 && h <= 50 ? h + 140 : h;  // skip the orange/clay band
}

// --- rendering -------------------------------------------------------------

async function load() {
  S.data = await api().state(S.view, S.project);
  if (S.selected && !S.data.tasks.some(t => t.id === S.selected)) closeDetail();
  render();
}

function applyTheme(theme) {
  if (theme === "system") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.dataset.theme = theme;
  document.querySelectorAll("[data-theme-set]").forEach(b => b.setAttribute("aria-checked", b.dataset.themeSet === theme));
}

function render() {
  applyTheme(S.data.theme);
  if (!POPUP) renderNav();
  renderHeader();
  renderList();
}

function renderNav() {
  const { counts, projects } = S.data;
  $("nav").innerHTML = VIEWS.map(v => v === null ? '<li class="sep"></li>' : `
    <li data-view="${v.id}" class="${v.id === S.view ? "on" : ""}">
      ${icon(v.icon)}${v.label}
      ${counts[v.id] && v.id !== "trash" ? `<span class="count">${counts[v.id]}</span>` : ""}
    </li>`).join("");
  $("projects").innerHTML = projects.length
    ? projects.map(p => `
      <li data-project="${esc(p)}" class="${p === S.project ? "on" : ""}">
        <span class="dot" style="--h:${hue(p)}"></span>${esc(p)}
      </li>`).join("")
    : '<li class="empty-projects">할 일 편집에서 프로젝트를 지정하면 여기에 모여요</li>';
}

function fmtDay(d, withMonth = true) {
  return `${withMonth ? `${d.getMonth() + 1}월 ` : ""}${d.getDate()}일 (${WEEKDAYS[d.getDay()]})`;
}

function stat(n, label, cls = "") {
  return `<div class="stat ${cls}"><b>${n}</b><span>${label}</span></div>`;
}

function renderHeader() {
  const { today, tasks } = S.data;
  const t = parseDate(today);
  $("title").textContent = LABEL[S.view] + (S.project ? ` · ${S.project}` : "");

  let date = "";
  if (S.view === "today") {
    date = fmtDay(t);
  } else if (S.view === "week") {
    // Monday-to-Sunday week containing today.
    const mon = new Date(t);
    mon.setDate(t.getDate() - ((t.getDay() + 6) % 7));
    const sun = new Date(mon);
    sun.setDate(mon.getDate() + 6);
    date = `${fmtDay(mon)} – ${fmtDay(sun, sun.getMonth() !== mon.getMonth())}`;
  }
  $("subtitle").textContent = date;

  const open = tasks.filter(x => !x.done).length;
  if (POPUP) {
    $("stats").innerHTML = stat(open, "남은 할 일");
  } else if (S.view === "today") {
    const overdue = tasks.filter(x => !x.done && x.due_date && daysUntil(x.due_date) < 0).length;
    $("stats").innerHTML = stat(open, "남은 할 일")
      + (overdue ? stat(overdue, "지난 마감", "danger") : "")
      + stat(tasks.length - open, "완료", "muted");
  } else if (S.view === "trash") {
    $("stats").innerHTML = stat(tasks.length, "항목", "muted");
  } else {
    $("stats").innerHTML = stat(tasks.length, { done: "완료", someday: "아이디어" }[S.view] || "할 일");
  }
  if (POPUP) return;
  const canAdd = BUCKETS.includes(S.view);
  $("quick-add").hidden = !canAdd;
  if (canAdd) $("quick-input").placeholder = S.view === "someday" ? "떠오른 아이디어 적기" : `'${LABEL[S.view]}'에 할 일 추가`;
  $("hint").textContent = S.view === "trash"
    ? "30일이 지나면 자동으로 영구 삭제됩니다."
    : "클릭: 상세 편집 · Delete: 휴지통으로 · Esc: 닫기";
}

function renderList() {
  const tasks = S.data.tasks;
  let html = "";
  if (S.view === "today") {
    const overdue = tasks.filter(t => !t.done && t.due_date && daysUntil(t.due_date) < 0);
    const open = tasks.filter(t => !t.done && !overdue.includes(t));
    const done = tasks.filter(t => t.done);
    html += section("지난 마감", overdue, "overdue");
    html += overdue.length || done.length ? section("오늘", open) : open.map(taskRow).join("");
    html += section("오늘 완료", done);
    if (!open.length && !overdue.length) {
      html = empty(done.length ? "오늘 할 일을 모두 끝냈어요" : "오늘 할 일을 추가해 보세요",
                   done.length ? "수고했어요." : "위 입력칸에 쓰고 Enter를 누르면 됩니다.") + html;
    }
  } else {
    html = tasks.map(taskRow).join("") || empty(
      S.view === "trash" ? "휴지통이 비어 있어요" : S.view === "done" ? "완료한 할 일이 여기에 모여요"
        : S.view === "someday" ? "떠오른 아이디어를 적어 두세요" : `'${LABEL[S.view]}'에 둘 할 일을 추가해 보세요`, "");
  }
  $("list").innerHTML = html;
}

function section(title, tasks, cls = "") {
  if (!tasks.length) return "";
  return `<div class="section ${cls}">${title}<span class="n">${tasks.length}</span></div>` + tasks.map(taskRow).join("");
}

function empty(big, small) {
  return `<div class="empty"><div class="big">${big}</div>${small}</div>`;
}

function taskRow(t) {
  const meta = [];
  if (t.due_date && !t.done) {
    const n = daysUntil(t.due_date);
    const d = parseDate(t.due_date);
    const date = `${d.getMonth() + 1}/${d.getDate()}(${WEEKDAYS[d.getDay()]})`;
    if (n < 0) meta.push(`<span class="chip danger">D+${-n} · ${date}</span>`);
    else if (n === 0) meta.push(`<span class="chip today">D-day</span>`);
    else meta.push(`<span class="chip">D-${n} · ${date}</span>`);
  }
  if (t.due_time) meta.push(`<span class="info time">${icon("clock")}${t.due_time}</span>`);
  if (t.project) meta.push(`<span class="chip project" style="--h:${hue(t.project)}">${esc(t.project)}</span>`);
  if (t.recurrence) meta.push(`<span class="info">${icon("repeat")}${RECURRENCE[t.recurrence]}</span>`);
  if (t.notes) meta.push(`<span class="info" title="메모">${icon("note")}</span>`);
  if (S.view === "today" && t.bucket !== "today" && !t.done) meta.push(`<span class="info">${LABEL[t.bucket]}</span>`);

  const trash = S.view === "trash";
  const lead = trash ? "" : `<div class="check" data-check role="checkbox" aria-checked="${t.done}" aria-label="완료">${icon("check")}</div>`;
  const tail = trash
    ? `<div class="row-actions">
         <button class="ghost icon-btn" data-restore title="복원" aria-label="복원">${icon("restore")}</button>
         <button class="ghost icon-btn danger" data-purge title="영구 삭제" aria-label="영구 삭제">${icon("trash")}</button>
       </div>`
    : "";
  return `
    <div class="task ${t.done ? "done" : ""} ${t.id === S.selected ? "selected" : ""}" data-id="${t.id}">
      ${lead}
      <div class="body"><span class="t">${esc(t.title)}</span>${meta.join("")}</div>
      ${tail}
    </div>`;
}

// --- detail panel ----------------------------------------------------------

function openDetail(id) {
  const t = S.data.tasks.find(x => x.id === id);
  if (!t || S.view === "trash") return;
  S.selected = id;
  $("f-title").value = t.title;
  $("f-bucket").value = t.bucket;
  $("f-project").value = t.project;
  $("f-date").value = t.due_date || "";
  $("f-time").value = t.due_time || "";
  $("f-time").disabled = !t.due_date;
  $("f-recurrence").value = t.recurrence || "";
  $("f-notes").value = t.notes;
  $("project-options").innerHTML = S.data.projects.map(p => `<option value="${esc(p)}">`).join("");
  $("detail").hidden = false;
  renderList();
}

function closeDetail() {
  S.selected = null;
  $("detail").hidden = true;
}

async function save(fields) {
  if (!S.selected) return;
  await api().update(S.selected, fields);
  await load();
}

function bindDetail() {
  $("detail-close").onclick = () => { closeDetail(); renderList(); };
  $("f-title").addEventListener("change", e => {
    const v = e.target.value.trim();
    if (v) save({ title: v });
    else e.target.value = S.data.tasks.find(t => t.id === S.selected).title;
  });
  $("f-title").addEventListener("keydown", e => { if (e.key === "Enter") e.target.blur(); });
  $("f-bucket").addEventListener("change", e => {
    const t = S.data.tasks.find(x => x.id === S.selected);
    const fields = { bucket: e.target.value };
    // A due date of today or earlier keeps the task in Today regardless of bucket.
    if (e.target.value !== "today" && t.due_date && daysUntil(t.due_date) <= 0 &&
        confirm("마감일이 오늘이거나 지나서 '오늘'에 계속 표시됩니다.\n마감일을 지우고 이동할까요?")) {
      fields.due_date = "";
    }
    save(fields);
  });
  $("f-project").addEventListener("change", e => save({ project: e.target.value.trim() }));
  $("f-date").addEventListener("change", e => {
    $("f-time").disabled = !e.target.value;
    if (!e.target.value) $("f-time").value = "";
    save({ due_date: e.target.value });
  });
  $("f-time").addEventListener("change", e => save({ due_time: e.target.value }));
  $("f-recurrence").addEventListener("change", e => save({ recurrence: e.target.value }));
  $("f-notes").addEventListener("change", e => save({ notes: e.target.value }));
  $("detail-delete").onclick = async () => {
    const id = S.selected;
    closeDetail();
    await api().delete(id);
    await load();
  };
}

// --- events ----------------------------------------------------------------

function bindPopup() {
  $("open-main").onclick = () => api().show_main(null);
  // Behave like a flyout: hide when focus leaves, refresh when shown.
  window.addEventListener("blur", () => api().hide_popup());
  document.addEventListener("keydown", e => { if (e.key === "Escape") api().hide_popup(); });
}

// Called from Python when a popup row is clicked.
window.focusTask = async id => {
  S.view = "today";
  S.project = "";
  await load();
  openDetail(id);
};

function bindShared() {
  $("quick-add").addEventListener("submit", async e => {
    e.preventDefault();
    const title = $("quick-input").value.trim();
    if (!title) return;
    $("quick-input").value = "";
    await api().add(title, S.view, S.project);
    await load();
  });
  $("list").addEventListener("click", async e => {
    const row = e.target.closest(".task");
    if (!row) return;
    const id = Number(row.dataset.id);
    if (e.target.closest("[data-check]")) {
      const done = !row.classList.contains("done");
      row.classList.toggle("done", done);
      row.classList.add("leaving");
      await new Promise(r => setTimeout(r, 180));
      await api().set_done(id, done);
      return load();
    }
    if (e.target.closest("[data-restore]")) { await api().restore(id); return load(); }
    if (e.target.closest("[data-purge]")) {
      if (confirm("이 항목을 영구 삭제할까요? 되돌릴 수 없습니다.")) { await api().purge(id); await load(); }
      return;
    }
    if (POPUP) return api().show_main(id);
    openDetail(id);
  });
  // Other windows may have changed data; refresh whenever this one gets focus.
  window.addEventListener("focus", () => { if (S.data) load(); });
  // Re-evaluate Today/D-day when the date rolls over while the app is open.
  setInterval(() => { if (S.data && localToday() !== S.data.today) load(); }, 60000);
}

function bind() {
  bindShared();
  if (POPUP) return bindPopup();
  $("nav").addEventListener("click", e => {
    const li = e.target.closest("[data-view]");
    if (!li) return;
    S.view = li.dataset.view;
    closeDetail();
    load();
  });
  $("theme").addEventListener("click", async e => {
    const b = e.target.closest("[data-theme-set]");
    if (!b) return;
    S.data.theme = b.dataset.themeSet;
    applyTheme(S.data.theme);
    await api().set_theme(S.data.theme);
  });
  $("projects").addEventListener("click", e => {
    const li = e.target.closest("[data-project]");
    if (!li) return;
    S.project = S.project === li.dataset.project ? "" : li.dataset.project;
    load();
  });
  document.addEventListener("keydown", async e => {
    const typing = e.target.matches("input, textarea, select");
    if (e.key === "Escape" && !$("detail").hidden) { closeDetail(); renderList(); }
    if (e.key === "Delete" && !typing && S.selected) {
      const id = S.selected;
      closeDetail();
      await api().delete(id);
      await load();
    }
  });
  bindDetail();
}

document.querySelectorAll("[data-icon]").forEach(el => { el.outerHTML = icon(el.dataset.icon); });
bind();
if (window.pywebview?.api?.state) load();
else window.addEventListener("pywebviewready", load);
