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
  panel: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
  wsun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  wmoon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  wpartly: '<path d="M8 2.5V4M3.4 4.4l1 1M2 9h1.5"/><path d="M5.2 11.6A4 4 0 1 1 12.4 6.8"/><path d="M9 21h8a3.5 3.5 0 0 0 .4-7A5 5 0 0 0 8 15a3 3 0 0 0 1 6z"/>',
  wcloud: '<path d="M7 19h10a4 4 0 0 0 .5-7.97A6 6 0 0 0 6.1 10.1 4.5 4.5 0 0 0 7 19z"/>',
  wrain: '<path d="M7 15h10a4 4 0 0 0 .5-7.97A6 6 0 0 0 6.1 6.1 4.5 4.5 0 0 0 7 15z"/><path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3"/>',
  wsnow: '<path d="M7 15h10a4 4 0 0 0 .5-7.97A6 6 0 0 0 6.1 6.1 4.5 4.5 0 0 0 7 15z"/><path d="M8 18.5h.01M12 18.5h.01M16 18.5h.01M10 21.5h.01M14 21.5h.01"/>',
  wsleet: '<path d="M7 15h10a4 4 0 0 0 .5-7.97A6 6 0 0 0 6.1 6.1 4.5 4.5 0 0 0 7 15z"/><path d="M8 18l-1 3M12 19h.01M16 18l-1 3"/>',
  paper: '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
  bookmark: '<path d="M7 4h10v16l-5-4-5 4z"/>',
  umbrella: '<path d="M3 12a9 9 0 0 1 18 0z"/><path d="M12 12v6a2 2 0 0 0 4 0"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
};

function icon(name) {
  return `<span class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg></span>`;
}

// --- strings ---------------------------------------------------------------

const STRINGS = {
  ko: {
    today: "오늘", week: "이번 주", later: "나중에", someday: "아이디어", done: "완료", trash: "휴지통", settings: "설정",
    projects: "프로젝트", noProjects: "프로젝트 없음", toggleSidebar: "사이드바 접기/펼치기",
    overdue: "지난 마감", weekTasks: "할 일", qaHint: "Enter로 추가", doneToday: "오늘 완료", open: "남은 할 일", items: "항목", tasks: "할 일", ideas: "아이디어",
    ph: { today: "오늘 할 일 추가", week: "이번 주 할 일 추가", later: "나중에 할 일 추가", someday: "아이디어 추가" },
    empty: {
      today: "오늘 할 일을 추가하세요", week: "이번 주에 할 일을 추가하세요", later: "나중에 할 일을 추가하세요",
      someday: "아이디어를 적어 두세요", done: "완료한 할 일이 없어요", trash: "휴지통이 비어 있어요",
      project: "이 프로젝트에 할 일이 없어요",
    },
    phProject: p => `${p}에 할 일 추가`,
    allDone: "오늘 할 일을 모두 끝냈어요",
    hint: "클릭: 편집 · Delete: 휴지통 · Esc: 닫기", hintTrash: "휴지통 항목은 30일 후 자동 삭제됩니다",
    addTask: "할 일 추가", close: "닫기", title: "제목", bucket: "분류", project: "프로젝트", none: "없음",
    due: "마감", dueDate: "마감일", time: "시간", repeat: "반복", notes: "메모", moveToTrash: "휴지통으로",
    daily: "매일", weekly: "매주", monthly: "매월", restore: "복원", purge: "영구 삭제", complete: "완료",
    confirmPurge: "이 항목을 영구 삭제할까요? 되돌릴 수 없습니다.", ok: "확인", cancel: "취소",
    confirmClearDue: b => `마감일에 맞춰 '${b}'에 표시되는 할 일이에요.\n마감일을 지우고 옮길까요?`,
    openMain: "전체 창 열기",
    general: "일반", theme: "테마", themeSystem: "시스템", themeLight: "라이트", themeDark: "다크",
    language: "언어", font: "글꼴", fontDefault: "기본 (Pretendard)",
    autostart: "Windows 시작 시 자동 실행", on: "켜기", off: "끄기",
    autostartDesc: "로그인하면 트레이에서 바로 시작", autostartDev: "설치한 앱에서만 쓸 수 있어요",
    events: "일정", allDay: "종일",
    weather: "날씨", kmaKey: "기상청 API 키", kmaKeyDesc: "기상청 API 허브에서 발급한 인증키",
    kmaKeySaved: "저장됨 · 바꾸려면 새 키 입력", location: "위치", save: "저장",
    weatherGrid: (nx, ny) => `기상청 격자 ${nx}, ${ny}`, weatherUpdated: t => `업데이트 ${t}`,
    weatherNone: "동네를 검색해서 고르세요", weatherBadKey: "키를 확인하세요",
    placeSearch: "동네 검색 (예: 대구 동구)", placeNone: "찾는 동네가 없어요", placeMore: n => `외 ${n}곳 · 더 자세히 입력하세요`,
    weatherError: "날씨 오류", hourly: "시간별 예보",
    papers: "논문", papersNew: "새 논문", papersFetch: "지금 가져오기", papersFetching: "가져오는 중…",
    papersUpdated: d => `최근 7일 논문 · 업데이트 ${d}`, papersNever: "아직 가져오지 않았어요",
    papersEmpty: "새 논문이 없어요", papersNoSource: "설정 → 논문 알림에서 기준 논문이나 키워드를 추가하세요",
    papersSave: "읽을 거리로 추가", papersSaved: "추가됨", papersHide: "숨기기", papersPreprint: "프리프린트",
    hintPapers: "제목 클릭: 논문 열기 · 읽을 거리로 추가하면 '나중에'에 할 일이 생겨요",
    reasonSeed: "기준 논문 추천", reasonKeyword: v => `키워드: ${v}`, reasonJournal: v => `저널: ${v}`,
    authors: (a, n) => (n > 1 ? `${a} 외 ${n - 1}명` : a),
    papersGroup: "논문 알림", papersEnabled: "논문 알림", papersPreprints: "프리프린트 포함",
    papersPreprintsDesc: "arXiv, Research Square 같은 심사 전 논문", include: "포함", exclude: "제외",
    notifyText: "알림 문구", notifyTextDesc: n => `새 논문이 오면 Windows 알림으로 표시 · 최대 ${n}자 · 비우면 기본 문구`,
    notifyDefault: "새 논문이 도착했어요.",
    seeds: "기준 논문", seedsDesc: "DOI로 추가하면 관련된 최근 논문을 추천해요",
    seedPh: "DOI 붙여 넣기 (예: 10.1175/JCLI-D-17-0034.1)",
    keywords: "키워드", keywordsDesc: "제목·초록에 이 구절이 들어간 최근 논문 · 넓은 단어보다 구체적인 구절이나 저널 지정이 정확해요",
    keywordPh: "예: atmospheric blocking",
    journals: "저널", journalsDesc: "고르면 키워드 검색을 이 저널로 좁혀요", journalPh: "저널 이름 검색",
    add: "추가", remove: "삭제",
    paperErr: {
      rate_limited: "추천 서비스가 요청을 잠시 거절했어요. 조금 뒤 다시 시도하세요.", network: "인터넷 연결을 확인하세요.",
      not_found: "그 DOI의 논문을 찾지 못했어요.", bad_doi: "DOI 형식이 아니에요.", too_long: "50자 이내로 써 주세요.",
      too_many: "최대 10개까지 추가할 수 있어요.", empty: "내용을 입력하세요.",
    },
    notifications: "알림", remind: "일정 시작 전 알림", remindOff: "끄기", minutes: n => `${n}분`,
    remindDesc: "시간이 정해진 오늘 할 일과 캘린더 일정",
    hotkey: "빠른 입력 단축키", hotkeyDesc: "어디서든 눌러 오늘 할 일을 바로 추가",
    hotkeyBusy: "다른 프로그램이 사용 중이라 쓸 수 없어요",
    gcal: "구글 캘린더", gcalAccount: "계정 연결",
    gcalNeedClient: "OAuth 클라이언트 파일(client_secret.json)을 먼저 가져오세요.",
    gcalImport: "파일 가져오기", gcalConnect: "연결", gcalConnecting: "브라우저에서 로그인하세요…",
    gcalDisconnect: "연결 해제", gcalSyncNow: "지금 동기화", gcalNotConnected: "연결되지 않음",
    gcalConnected: a => `${a ? a + " · " : ""}연결됨`, gcalLastSync: t => `마지막 동기화 ${t}`, gcalError: "동기화 오류",
    gcalFailed: "연결하지 못했어요. 다시 시도하세요.",
    gcalExpired: "구글 캘린더 로그인이 만료됐어요. 다시 연결하세요.", gcalReconnect: "다시 연결",
    confirmDisconnect: "구글 캘린더 연결을 해제할까요? 이미 올라간 일정은 캘린더에 그대로 남습니다.",
    gcalColors: "캘린더 색상", gcalColorsDesc: "이 앱에서 보이는 색만 바뀌고, 구글 캘린더에는 영향이 없어요. 구글에서 일정에 따로 정한 색이 있으면 그 색이 먼저 보여요.",
    colorDefault: "기본",
    updates: "업데이트", updateVersion: "버전", updateCurrent: v => `현재 ${v}`,
    updateAvailable: v => `새 버전(${v})이 나왔어요`, updateUpToDate: "최신 버전이에요", updateChecked: t => `${t} 확인`,
    updateCheck: "업데이트 확인", updateInstall: "업데이트", updateChecking: "확인하는 중…",
    updateInstalling: "내려받는 중이에요. 설치가 끝나면 앱이 다시 켜져요.",
    updateAuto: "자동으로 확인", updateAutoDesc: "하루 한 번 새 버전을 확인하고 알려 줘요.",
    updateErr: { network: "인터넷 연결을 확인해 주세요.", corrupt: "받은 파일이 손상됐어요. 다시 시도해 주세요.",
                 dev: "개발 모드로 실행 중이라 설치할 수 없어요.", no_update: "설치할 새 버전이 없어요." },
    day: (d, withMonth = true) => `${withMonth ? `${d.getMonth() + 1}월 ` : ""}${d.getDate()}일 (${"일월화수목금토"[d.getDay()]})`,
    chipDate: d => `${d.getMonth() + 1}/${d.getDate()}(${"일월화수목금토"[d.getDay()]})`,
  },
  en: {
    today: "Today", week: "This week", later: "Later", someday: "Ideas", done: "Done", trash: "Trash", settings: "Settings",
    projects: "Projects", noProjects: "No projects", toggleSidebar: "Collapse/expand sidebar",
    overdue: "Overdue", weekTasks: "Tasks", qaHint: "Enter to add", doneToday: "Done today", open: "to do", items: "items", tasks: "tasks", ideas: "ideas",
    ph: { today: "Add a task for today", week: "Add a task for this week", later: "Add a task for later", someday: "Add an idea" },
    empty: {
      today: "Add a task for today", week: "Add a task for this week", later: "Add a task for later",
      someday: "Write down an idea", done: "No completed tasks", trash: "Trash is empty",
      project: "No tasks in this project",
    },
    phProject: p => `Add a task to ${p}`,
    allDone: "All done for today",
    hint: "Click: edit · Delete: trash · Esc: close", hintTrash: "Items in trash are deleted after 30 days",
    addTask: "Add task", close: "Close", title: "Title", bucket: "List", project: "Project", none: "None",
    due: "Due", dueDate: "Due date", time: "Time", repeat: "Repeat", notes: "Notes", moveToTrash: "Move to trash",
    daily: "Daily", weekly: "Weekly", monthly: "Monthly", restore: "Restore", purge: "Delete forever", complete: "Complete",
    confirmPurge: "Delete this item forever? This can't be undone.", ok: "OK", cancel: "Cancel",
    confirmClearDue: b => `Its due date keeps this task in ${b}.\nClear the due date and move it?`,
    openMain: "Open full window",
    general: "General", theme: "Theme", themeSystem: "System", themeLight: "Light", themeDark: "Dark",
    language: "Language", font: "Font", fontDefault: "Default (Pretendard)",
    autostart: "Start with Windows", on: "On", off: "Off",
    autostartDesc: "Start in the tray when you sign in", autostartDev: "Available in the installed app",
    events: "Events", allDay: "All day",
    weather: "Weather", kmaKey: "KMA API key", kmaKeyDesc: "Auth key issued by the KMA API Hub",
    kmaKeySaved: "Saved · enter a new key to replace it", location: "Location", save: "Save",
    weatherGrid: (nx, ny) => `KMA grid ${nx}, ${ny}`, weatherUpdated: t => `Updated ${t}`,
    weatherNone: "Search for your neighbourhood", weatherBadKey: "Check the key",
    placeSearch: "Search places (e.g. 대구 동구)", placeNone: "No matching place", placeMore: n => `${n} more · type more to narrow`,
    weatherError: "Weather error", hourly: "Hourly forecast",
    papers: "Papers", papersNew: "new", papersFetch: "Fetch now", papersFetching: "Fetching…",
    papersUpdated: d => `Papers from the last 7 days · updated ${d}`, papersNever: "Not fetched yet",
    papersEmpty: "No new papers", papersNoSource: "Add seed papers or keywords in Settings → Paper alerts",
    papersSave: "Add to reading list", papersSaved: "Added", papersHide: "Hide", papersPreprint: "Preprint",
    hintPapers: "Click a title to open it · adding to the reading list creates a task in Later",
    reasonSeed: "From your seed papers", reasonKeyword: v => `Keyword: ${v}`, reasonJournal: v => `Journal: ${v}`,
    authors: (a, n) => (n > 1 ? `${a} et al.` : a),
    papersGroup: "Paper alerts", papersEnabled: "Paper alerts", papersPreprints: "Include preprints",
    papersPreprintsDesc: "Not yet peer reviewed, e.g. arXiv, Research Square", include: "Include", exclude: "Exclude",
    notifyText: "Notification text", notifyTextDesc: n => `Shown as a Windows notification · up to ${n} characters · empty for default`,
    notifyDefault: "New papers have arrived.",
    seeds: "Seed papers", seedsDesc: "Add by DOI to get related recent papers",
    seedPh: "Paste a DOI (e.g. 10.1175/JCLI-D-17-0034.1)",
    keywords: "Keywords", keywordsDesc: "Recent papers with this phrase in the title or abstract · specific phrases or chosen journals work best",
    keywordPh: "e.g. atmospheric blocking",
    journals: "Journals", journalsDesc: "Narrow keyword results to these journals", journalPh: "Search journals",
    add: "Add", remove: "Remove",
    paperErr: {
      rate_limited: "The recommendation service is busy. Try again shortly.", network: "Check your internet connection.",
      not_found: "No paper found for that DOI.", bad_doi: "That isn't a DOI.", too_long: "Keep it within 50 characters.",
      too_many: "You can add up to 10.", empty: "Type something first.",
    },
    notifications: "Notifications", remind: "Remind before start", remindOff: "Off", minutes: n => `${n} min`,
    remindDesc: "Timed tasks and calendar events today",
    hotkey: "Quick add shortcut", hotkeyDesc: "Press anywhere to add a task for today",
    hotkeyBusy: "Unavailable — another program is using it",
    gcal: "Google Calendar", gcalAccount: "Account",
    gcalNeedClient: "Import the OAuth client file (client_secret.json) first.",
    gcalImport: "Import file", gcalConnect: "Connect", gcalConnecting: "Sign in in your browser…",
    gcalDisconnect: "Disconnect", gcalSyncNow: "Sync now", gcalNotConnected: "Not connected",
    gcalConnected: a => `${a ? a + " · " : ""}Connected`, gcalLastSync: t => `Last synced ${t}`, gcalError: "Sync error",
    gcalFailed: "Couldn't connect. Try again.",
    gcalExpired: "Your Google Calendar sign-in expired. Reconnect to keep syncing.", gcalReconnect: "Reconnect",
    confirmDisconnect: "Disconnect Google Calendar? Events already created stay in your calendar.",
    gcalColors: "Calendar colors", gcalColorsDesc: "Changes colors in this app only; Google Calendar is untouched. A color set on an event in Google still takes priority.",
    colorDefault: "Default",
    updates: "Updates", updateVersion: "Version", updateCurrent: v => `Current ${v}`,
    updateAvailable: v => `Version ${v} is available`, updateUpToDate: "Up to date", updateChecked: t => `checked ${t}`,
    updateCheck: "Check for updates", updateInstall: "Update", updateChecking: "Checking…",
    updateInstalling: "Downloading. The app restarts when the update is installed.",
    updateAuto: "Check automatically", updateAutoDesc: "Looks for a new version once a day and lets you know.",
    updateErr: { network: "Check your internet connection.", corrupt: "The download was damaged. Please try again.",
                 dev: "Running from source; nothing to install.", no_update: "No new version to install." },
    day: (d, withMonth = true) => d.toLocaleDateString("en-US", withMonth
      ? { weekday: "short", month: "short", day: "numeric" } : { weekday: "short", day: "numeric" }),
    chipDate: d => d.toLocaleDateString("en-US", { weekday: "short", month: "numeric", day: "numeric" }),
  },
};
let T = STRINGS.ko;

const VIEWS = [
  { id: "today", icon: "sun" }, { id: "week", icon: "week" }, { id: "later", icon: "clock" },
  { id: "someday", icon: "bulb" }, { id: "papers", icon: "paper" }, null, { id: "done", icon: "done" }, { id: "trash", icon: "trash" },
];
const BUCKETS = ["today", "week", "later", "someday"];
// Pretendard ships with the app (web/fonts, SIL OFL); the rest are fallbacks.
const DEFAULT_FONT = '"Pretendard", "Segoe UI", "Malgun Gothic", -apple-system, "Apple SD Gothic Neo", sans-serif';

// The tray popup (popup.html) reuses this file: Today only, no sidebar or detail panel.
const POPUP = document.body.classList.contains("popup");
const S = { view: "today", project: "", selected: null, data: null, fonts: null };
const $ = id => document.getElementById(id);
const api = () => window.pywebview.api;

// --- helpers ---------------------------------------------------------------

// In-app confirm. The browser's own confirm() titles itself with the local server address.
function ask(text, okLabel = T.ok, danger = false) {
  return new Promise(resolve => {
    const done = ok => {
      $("modal").hidden = true;
      document.removeEventListener("keydown", onKey, true);
      resolve(ok);
    };
    const onKey = e => {
      if (e.key !== "Escape") return;
      e.stopImmediatePropagation();  // Esc here cancels the dialog, not the detail panel behind it
      done(false);
    };
    $("modal-text").textContent = text;
    $("modal-ok").textContent = okLabel;
    $("modal-ok").classList.toggle("danger", danger);
    $("modal-ok").onclick = () => done(true);
    $("modal-cancel").onclick = () => done(false);
    $("modal").onclick = e => { if (e.target === $("modal")) done(false); };
    document.addEventListener("keydown", onKey, true);
    $("modal").hidden = false;
    $("modal-ok").focus();
  });
}

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

// A project's colour: the one picked on its page, else one derived from its name.
function projectColor(name) {
  return (S.data.project_colors || {})[name] || "";
}

function hue(name) {
  // Golden-angle spread so names differing by one character ("논문A"/"논문B") get distinct colors.
  let h = 0;
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  h = Math.round((h * 137.508) % 360);
  return h >= 10 && h <= 50 ? h + 140 : h;  // skip the orange/clay band
}

// --- settings applied to the page ----------------------------------------

function applySettings() {
  const { theme, lang, font, sidebar } = S.data.settings;
  if (theme === "system") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.dataset.theme = theme;
  document.documentElement.style.setProperty("--font", font ? `"${font}", ${DEFAULT_FONT}` : DEFAULT_FONT);
  if (T !== STRINGS[lang]) {
    T = STRINGS[lang];
    document.documentElement.lang = lang;
    applyStaticStrings();
  }
  if (!POPUP) $("app").classList.toggle("collapsed", sidebar === "collapsed");
}

function applyStaticStrings() {
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = T[el.dataset.i18n]; });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = T[el.dataset.i18nPh]; });
  document.querySelectorAll("[data-i18n-aria]").forEach(el => el.setAttribute("aria-label", T[el.dataset.i18nAria]));
  document.querySelectorAll("[data-i18n-title]").forEach(el => { el.title = T[el.dataset.i18nTitle]; });
}

async function setSetting(key, value) {
  S.data.settings[key] = value;
  applySettings();
  await api().set_setting(key, value);
}

// --- rendering -------------------------------------------------------------

async function load() {
  // Settings and Papers still need counts for the sidebar; fetch Today behind them.
  const own = ["settings", "papers"].includes(S.view);
  S.data = await api().state(own ? "today" : S.view, S.project);
  if (S.view === "papers") S.papers = await api().papers_list();
  if (S.selected && !S.data.tasks.some(t => t.id === S.selected)) closeDetail();
  render();
}

function render() {
  applySettings();
  if (!POPUP) renderNav();
  const settings = S.view === "settings";
  if (!POPUP) {
    for (const id of ["quick-add", "list", "hint"]) $(id).hidden = settings;
    $("settings").hidden = !settings;
    $("project-options").innerHTML = S.data.projects.map(p => `<option value="${esc(p)}">`).join("");
  }
  renderHeader();
  if (settings) return renderSettings();
  if (S.view === "papers") return renderPapers();
  renderList();
}

function renderNav() {
  const { counts, projects } = S.data;
  $("nav").innerHTML = VIEWS.map(v => v === null ? '<li class="sep"></li>' : `
    <li data-view="${v.id}" class="${v.id === S.view ? "on" : ""}" title="${T[v.id]}">
      ${icon(v.icon)}<span class="label">${T[v.id]}</span>
      ${counts[v.id] && v.id !== "trash" ? `<span class="count">${counts[v.id]}</span>` : ""}
    </li>`).join("");
  $("projects").innerHTML = projects.length
    ? projects.map(p => `
      <li data-project="${esc(p)}" class="${S.view === "project" && p === S.project ? "on" : ""}" title="${esc(p)}">
        <span class="dot" style="${projectColor(p) ? `background:${projectColor(p)}` : `--h:${hue(p)}`}"></span><span class="label">${esc(p)}</span>
      </li>`).join("")
    : `<li class="empty-projects"><span class="label">${T.noProjects}</span></li>`;
  $("settings-btn").classList.toggle("on", S.view === "settings");
}

function weatherIcon(w) {
  const name = { rain: "wrain", shower: "wrain", sleet: "wsleet", snow: "wsnow" }[w.pty]
    || (w.sky === "cloudy" ? "wcloud" : w.sky === "partly" ? "wpartly" : w.night ? "wmoon" : "wsun");
  return icon(name);
}

function renderWeather() {
  const w = S.data.weather;
  const show = !!w && (POPUP || S.view === "today");
  $("weather").hidden = !show;
  if (!show) { $("weather-panel").hidden = true; return; }
  const range = w.tmin != null && w.tmax != null ? `<span>${w.tmin}° / ${w.tmax}°</span>` : "";
  const rain = w.pop_max >= 60 ? `<span class="rain">${icon("umbrella")}${w.pop_max}%</span>` : "";
  $("weather").innerHTML = `${weatherIcon(w)}<span class="now">${w.temp ?? "-"}°</span>${range}${rain}`;
  $("weather").title = T.hourly;
  $("weather-panel").innerHTML = w.hourly.map(h => `
    <div class="hour"><span>${h.time.slice(0, 2)}${T === STRINGS.ko ? "시" : ""}</span>${weatherIcon(h)}<b>${h.temp}°</b>
      <span class="pop ${h.pop < 30 ? "low" : ""}">${h.pop}%</span></div>`).join("");
}

function stat(n, label, cls = "") {
  return `<div class="stat ${cls}"><b>${n}</b><span>${label}</span></div>`;
}

function renderHeader() {
  const { today, tasks } = S.data;
  const t = parseDate(today);
  const settings = S.view === "settings";
  const papersView = S.view === "papers";
  const projectView = S.view === "project";
  $("title").textContent = projectView ? S.project : T[S.view];
  if (!POPUP) $("papers-fetch").hidden = !papersView;

  let date = "";
  if (S.view === "today") {
    date = T.day(t);
  } else if (S.view === "week") {
    // Monday-to-Sunday week containing today.
    const mon = new Date(t);
    mon.setDate(t.getDate() - ((t.getDay() + 6) % 7));
    const sun = new Date(mon);
    sun.setDate(mon.getDate() + 6);
    date = `${T.day(mon)} – ${T.day(sun, sun.getMonth() !== mon.getMonth())}`;
  }
  if (papersView) date = S.papers.last_fetch ? T.papersUpdated(S.papers.last_fetch) : T.papersNever;
  if (projectView) date = T.project;
  if (!POPUP) {
    $("proj-colors").hidden = !projectView;
    if (projectView) {
      const mine = projectColor(S.project);
      $("proj-colors").innerHTML = `<button class="swatch-default" data-color="" aria-pressed="${!mine}">${T.colorDefault}</button>`
        + S.data.palette.map(c => `<button class="swatch" data-color="${c}" style="background:${c}"
            aria-pressed="${mine === c}" aria-label="${c}"></button>`).join("");
    }
  }
  $("subtitle").textContent = date;
  renderWeather();

  const open = tasks.filter(x => !x.done).length;
  let stats = "";
  if (settings) {
    stats = "";
  } else if (papersView) {
    const fresh = S.papers.papers.filter(p => p.status === "new").length;
    stats = stat(fresh, T.papersNew) + stat(S.papers.papers.length, T.papers, "muted");
  } else if (S.view === "today") {
    const overdue = tasks.filter(x => !x.done && x.due_date && daysUntil(x.due_date) < 0).length;
    stats = stat(open, T.open) + (overdue ? stat(overdue, T.overdue, "danger") : "")
      + (POPUP ? "" : stat(tasks.length - open, T.done, "muted"));
  } else if (S.view === "trash") {
    stats = stat(tasks.length, T.items, "muted");
  } else if (projectView) {
    stats = stat(open, T.open) + stat(tasks.length - open, T.done, "muted");
  } else {
    stats = stat(tasks.length, { done: T.done, someday: T.ideas }[S.view] || T.tasks);
  }
  $("stats").innerHTML = stats;
  $("stats").hidden = !stats;

  const canAdd = BUCKETS.includes(S.view) || projectView;
  $("quick-add").hidden = !canAdd;
  if (canAdd) $("quick-input").placeholder = projectView ? T.phProject(S.project) : T.ph[S.view];
  if (!POPUP) $("hint").textContent = S.view === "trash" ? T.hintTrash : papersView ? T.hintPapers : T.hint;
}

function renderList() {
  const tasks = S.data.tasks;
  let html = "";
  if (S.view === "today") {
    const overdue = tasks.filter(t => !t.done && t.due_date && daysUntil(t.due_date) < 0);
    const open = tasks.filter(t => !t.done && !overdue.includes(t));
    const done = tasks.filter(t => t.done);
    const events = eventsSection();
    html += section(T.overdue, overdue, "overdue") + events;
    html += overdue.length || done.length || events ? section(T.today, open) : open.map(taskRow).join("");
    html += section(T.doneToday, done);
    if (!open.length && !overdue.length) html = empty(done.length ? T.allDone : T.empty.today) + html;
    if (S.data.gcal_reauth && !POPUP) {
      html = `<div class="banner">${T.gcalExpired}<button class="btn" data-goto-settings>${T.gcalReconnect}</button></div>` + html;
    }
  } else if (S.view === "project") {
    // The whole project on one page, grouped the way the sidebar views would show it.
    const open = tasks.filter(t => !t.done);
    html = BUCKETS.map(b => section(T[b], open.filter(t => t.bucket === b))).join("")
      + section(T.done, tasks.filter(t => t.done));
    html ||= empty(T.empty.project);
  } else if (S.view === "week" && (S.data.events || []).length) {
    html = eventsSection() + (section(T.weekTasks, tasks) || empty(T.empty.week));
  } else {
    html = tasks.map(taskRow).join("") || empty(T.empty[S.view]);
  }
  $("list").innerHTML = html;
}

function eventsSection() {
  const evs = S.data.events || [];
  if (!evs.length) return "";
  const week = S.view === "week";  // events span several days here, so each row names its day
  return `<div class="section">${T.events}<span class="n">${evs.length}</span></div>` + evs.map(e => `
    <div class="event">
      <span class="ev-bar" style="background:${esc(e.color || "var(--accent)")}"></span>
      ${week ? `<span class="ev-day">${T.chipDate(parseDate(e.date))}</span>` : ""}
      <span class="ev-time">${e.all_day ? T.allDay : `${e.start}–${e.end}`}</span>
      <span class="ev-title">${esc(e.title)}</span>
      <span class="ev-cal">${esc(e.calendar)}</span>
    </div>`).join("");
}

function renderPapers() {
  const { papers, has_sources, error } = S.papers;
  const reason = p => p.reason_kind === "seed" ? T.reasonSeed
    : p.reason_kind === "keyword" ? T.reasonKeyword(p.reason_value) : T.reasonJournal(p.reason_value);
  let html = error ? `<div class="banner">${T.paperErr[error] || error}</div>` : "";
  html += papers.map(p => `
    <div class="paper" data-paper="${esc(p.key)}">
      <span class="new-dot ${p.status === "new" ? "" : "off"}"></span>
      <div class="body">
        <div class="ptitle" data-paper-open>${esc(p.title)}</div>
        <div class="pmeta">
          ${p.first_author ? `<span>${esc(T.authors(p.first_author, p.author_count))}</span>` : ""}
          ${p.venue ? `<span>${esc(p.venue)}</span>` : ""}
          ${p.pub_date ? `<span>${p.pub_date}</span>` : ""}
          <span class="chip">${esc(reason(p))}</span>
          ${p.preprint ? `<span class="chip">${T.papersPreprint}</span>` : ""}
        </div>
      </div>
      <div class="pactions">
        ${p.status === "saved" ? `<span class="saved">${T.papersSaved}</span>`
          : `<button class="ghost icon-btn" data-paper-save title="${T.papersSave}" aria-label="${T.papersSave}">${icon("bookmark")}</button>`}
        <button class="ghost icon-btn" data-paper-hide title="${T.papersHide}" aria-label="${T.papersHide}">${icon("x")}</button>
      </div>
    </div>`).join("");
  if (!papers.length) html += empty(has_sources ? T.papersEmpty : T.papersNoSource);
  $("list").innerHTML = html;
}

async function onPaperClick(e, row) {
  const key = row.dataset.paper;
  if (e.target.closest("[data-paper-open]")) return api().open_paper(key);
  if (e.target.closest("[data-paper-save]")) { await api().save_paper(key); return load(); }
  if (e.target.closest("[data-paper-hide]")) { await api().hide_paper(key); return load(); }
}

function section(title, tasks, cls = "") {
  if (!tasks.length) return "";
  return `<div class="section ${cls}">${title}<span class="n">${tasks.length}</span></div>` + tasks.map(taskRow).join("");
}

function empty(text) {
  return `<div class="empty">${text}</div>`;
}

function taskRow(t) {
  const meta = [];
  if (t.due_date && !t.done) {
    const n = daysUntil(t.due_date);
    const date = T.chipDate(parseDate(t.due_date));
    if (n < 0) meta.push(`<span class="chip danger">D+${-n} · ${date}</span>`);
    else if (n === 0) meta.push(`<span class="chip today">D-day</span>`);
    else meta.push(`<span class="chip">D-${n} · ${date}</span>`);
  }
  if (t.due_time) meta.push(`<span class="info time">${icon("clock")}${t.due_time}</span>`);
  if (t.project && S.view !== "project") {
    const c = projectColor(t.project);
    meta.push(c ? `<span class="chip project custom" style="--pc:${c}">${esc(t.project)}</span>`
                : `<span class="chip project" style="--h:${hue(t.project)}">${esc(t.project)}</span>`);
  }
  if (t.recurrence) meta.push(`<span class="info">${icon("repeat")}${T[t.recurrence]}</span>`);
  if (t.notes) meta.push(`<span class="info" title="${T.notes}">${icon("note")}</span>`);
  if (S.view === "today" && t.bucket !== "today" && !t.done) meta.push(`<span class="info">${T[t.bucket]}</span>`);

  const trash = S.view === "trash";
  const lead = trash ? "" : `<div class="check" data-check role="checkbox" aria-checked="${t.done}" aria-label="${T.complete}">${icon("check")}</div>`;
  const tail = trash
    ? `<div class="row-actions">
         <button class="ghost icon-btn" data-restore title="${T.restore}" aria-label="${T.restore}">${icon("restore")}</button>
         <button class="ghost icon-btn danger" data-purge title="${T.purge}" aria-label="${T.purge}">${icon("trash")}</button>
       </div>`
    : "";
  return `
    <div class="task ${t.done ? "done" : ""} ${t.id === S.selected ? "selected" : ""}" data-id="${t.id}">
      ${lead}
      <div class="body"><span class="t">${esc(t.title)}</span>${meta.join("")}</div>
      ${tail}
    </div>`;
}

// --- settings page ---------------------------------------------------------

async function renderSettings() {
  const { theme, lang, font } = S.data.settings;
  $("set-theme").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.value === theme));
  $("set-lang").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.value === lang));
  if (!S.fonts) S.fonts = await api().fonts();
  $("set-font").innerHTML = `<option value="">${T.fontDefault}</option>`
    + S.fonts.map(f => `<option value="${esc(f)}">${esc(f)}</option>`).join("");
  $("set-font").value = font;
  $("set-remind").innerHTML = ["off", "5", "10", "15", "30"].map(v =>
    `<button data-value="${v}" aria-pressed="${v === S.data.settings.remind}">${v === "off" ? T.remindOff : T.minutes(v)}</button>`).join("");
  renderWeatherSettings(await api().weather_settings());
  renderPapersSettings(await api().papers_settings());
  const info = await api().app_info();
  renderAutostart(info);
  $("hotkey-desc").textContent = info.hotkey_ok ? T.hotkeyDesc : T.hotkeyBusy;
  $("hotkey-desc").classList.toggle("setting-error", !info.hotkey_ok);
  $("hotkey-key").textContent = info.hotkey;
  renderGcal(await api().gcal_status());
  renderUpdate(await api().update_status());
}

function renderUpdate(st, note = "") {
  let desc = T.updateCurrent(st.current);
  if (st.latest) desc += ` · ${T.updateAvailable(st.latest)}`;
  else if (st.checked && !st.error) desc += ` · ${T.updateUpToDate}`;
  if (st.checked) desc += ` (${T.updateChecked(st.checked)})`;
  const err = note in T.updateErr ? T.updateErr[note] : st.error && T.updateErr[st.error];
  $("update-desc").innerHTML = esc(desc) + (err ? `<div class="setting-error">${esc(err)}</div>`
    : note ? `<div>${esc(note)}</div>` : "");
  const busy = note === T.updateChecking || note === T.updateInstalling;
  $("update-actions").innerHTML = `<button class="btn" data-act="check" ${busy ? "disabled" : ""}>${T.updateCheck}</button>`
    + (st.latest && st.can_install ? `<button class="btn primary" data-act="install" ${busy ? "disabled" : ""}>${T.updateInstall}</button>` : "");
  $("set-update-auto").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.value === st.auto));
}

function renderAutostart(info) {
  $("autostart-desc").textContent = info.autostart_supported ? T.autostartDesc : T.autostartDev;
  $("set-autostart").querySelectorAll("button").forEach(b => {
    b.disabled = !info.autostart_supported;
    b.setAttribute("aria-pressed", (b.dataset.value === "on") === info.autostart);
  });
}

function renderPapersSettings(st, errorCode = "") {
  $("set-papers-enabled").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.value === st.enabled));
  $("set-papers-preprints").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.value === st.preprints));
  $("set-notify-text").placeholder = T.notifyDefault;
  $("set-notify-text").value = st.notify_text;
  $("notify-text-desc").textContent = T.notifyTextDesc(st.notify_max);
  const chip = (label, attr, value) =>
    `<span class="chip-item" title="${esc(label)}"><span>${esc(label)}</span><button ${attr}="${esc(value)}" aria-label="${T.remove}">${icon("x")}</button></span>`;
  $("seed-list").innerHTML = st.seeds.map(s => chip(s.title ? `${s.title} (${s.doi})` : s.doi, "data-seed", s.doi)).join("");
  $("keyword-list").innerHTML = st.keywords.map(k => chip(k, "data-keyword", k)).join("");
  $("journal-list").innerHTML = st.journals.map(j => chip(j.name, "data-journal", j.id)).join("");
  $("papers-settings-error").hidden = !errorCode;
  $("papers-settings-error").textContent = T.paperErr[errorCode] || "";
}

async function papersAction(call) {
  try {
    renderPapersSettings(await call());
    return true;
  } catch (err) {
    const code = String(err && (err.message || err)).match(/[a-z_]+$/);
    renderPapersSettings(await api().papers_settings(), code ? code[0] : "network");
    return false;
  }
}

let journalTimer = null;

function renderWeatherSettings(st, failed = false) {
  $("set-kma-key").placeholder = st.has_key ? T.kmaKeySaved : "";
  $("set-kma-key").value = "";
  let desc = st.grid ? [st.place, T.weatherGrid(...st.grid)].filter(Boolean).map(esc).join(" · ") : T.weatherNone;
  if (st.updated && !st.error) desc += ` · ${T.weatherUpdated(st.updated)}`;
  if (failed) desc += `<div class="setting-error">${T.weatherBadKey}</div>`;
  else if (st.error) desc += `<div class="setting-error">${T.weatherError}: ${esc(st.error)}</div>`;
  $("weather-desc").innerHTML = desc;
}

let placeTimer = null;
async function searchPlaces() {
  const q = $("place-input").value.trim();
  const box = $("place-results");
  if (!q) { box.hidden = true; return; }
  const { results, total } = await api().search_places(q);
  if (q !== $("place-input").value.trim()) return;  // a newer keystroke already ran
  box.innerHTML = results.length
    ? results.map(r => `<button data-place="${r.id}">${esc(r.name)}</button>`).join("")
      + (total > results.length ? `<div class="more">${T.placeMore(total - results.length)}</div>` : "")
    : `<div class="more">${T.placeNone}</div>`;
  box.hidden = false;
}

async function choosePlace(id) {
  $("place-results").hidden = true;
  $("place-input").value = "";
  renderWeatherSettings(await api().set_weather_place(id));
}

function renderGcal(st, busy = false) {
  let desc, actions;
  if (!st.has_client) {
    desc = T.gcalNeedClient;
    actions = `<button class="btn" data-act="import">${T.gcalImport}</button>`;
  } else if (!st.connected) {
    desc = busy ? T.gcalConnecting : T.gcalNotConnected;
    actions = `<button class="btn primary" data-act="connect" ${busy ? "disabled" : ""}>${T.gcalConnect}</button>`;
  } else if (st.needs_reauth) {
    desc = busy ? T.gcalConnecting : T.gcalExpired;
    actions = `<button class="btn primary" data-act="connect" ${busy ? "disabled" : ""}>${T.gcalReconnect}</button>
               <button class="btn" data-act="disconnect">${T.gcalDisconnect}</button>`;
  } else {
    desc = T.gcalConnected(st.account) + (st.last_sync ? ` · ${T.gcalLastSync(st.last_sync)}` : "");
    actions = `<button class="btn" data-act="sync" ${busy ? "disabled" : ""}>${T.gcalSyncNow}</button>
               <button class="btn" data-act="disconnect">${T.gcalDisconnect}</button>`;
  }
  if (st.error) desc += `<div class="setting-error">${T.gcalError}: ${esc(st.error)}</div>`;
  $("gcal-desc").innerHTML = desc;
  $("gcal-actions").innerHTML = actions;
  const cals = st.connected && !st.needs_reauth ? st.calendars || [] : [];
  $("gcal-colors-row").hidden = !cals.length;
  $("gcal-colors").innerHTML = cals.map(c => `
    <div class="cal-row">
      <span class="cal-name"><span class="cal-dot" style="background:${esc(c.custom || c.color)}"></span>${esc(c.name)}</span>
      <span class="swatches">
        <button class="swatch-default" data-cal="${esc(c.id)}" data-color="" aria-pressed="${!c.custom}">${T.colorDefault}</button>
        ${st.palette.map(p => `<button class="swatch" data-cal="${esc(c.id)}" data-color="${p}" style="background:${p}"
          aria-pressed="${c.custom === p}" aria-label="${p}"></button>`).join("")}
      </span>
    </div>`).join("");
}

function bindSettings() {
  $("set-theme").addEventListener("click", e => {
    const b = e.target.closest("[data-value]");
    if (b) setSetting("theme", b.dataset.value).then(renderSettings);
  });
  $("set-lang").addEventListener("click", e => {
    const b = e.target.closest("[data-value]");
    if (b) setSetting("lang", b.dataset.value).then(render);
  });
  $("set-font").addEventListener("change", e => setSetting("font", e.target.value));
  $("set-autostart").addEventListener("click", async e => {
    const b = e.target.closest("[data-value]");
    if (b && !b.disabled) renderAutostart(await api().set_autostart(b.dataset.value === "on"));
  });
  for (const [id, key] of [["set-papers-enabled", "papers_enabled"], ["set-papers-preprints", "papers_preprints"]]) {
    $(id).addEventListener("click", e => {
      const b = e.target.closest("[data-value]");
      if (b) setSetting(key, b.dataset.value).then(async () => renderPapersSettings(await api().papers_settings()));
    });
  }
  $("notify-text-save").addEventListener("click", () => papersAction(() => api().set_papers_notify_text($("set-notify-text").value)));
  const addOnEnter = (input, button) => $(input).addEventListener("keydown", e => { if (e.key === "Enter") $(button).click(); });
  $("seed-add").addEventListener("click", async () => {
    if (await papersAction(() => api().add_paper_seed($("seed-input").value))) $("seed-input").value = "";
  });
  $("keyword-add").addEventListener("click", async () => {
    if (await papersAction(() => api().add_paper_keyword($("keyword-input").value))) $("keyword-input").value = "";
  });
  addOnEnter("seed-input", "seed-add");
  addOnEnter("keyword-input", "keyword-add");
  $("settings").addEventListener("click", e => {
    const b = e.target.closest("[data-seed], [data-keyword], [data-journal]");
    if (!b) return;
    if (b.dataset.seed) papersAction(() => api().remove_paper_seed(b.dataset.seed));
    else if (b.dataset.keyword) papersAction(() => api().remove_paper_keyword(b.dataset.keyword));
    else papersAction(() => api().remove_paper_journal(b.dataset.journal));
  });
  $("journal-input").addEventListener("input", () => {
    clearTimeout(journalTimer);
    journalTimer = setTimeout(async () => {
      const q = $("journal-input").value.trim();
      const box = $("journal-results");
      if (!q) { box.hidden = true; return; }
      const found = await api().search_journals(q);
      if (q !== $("journal-input").value.trim()) return;
      box.innerHTML = found.length
        ? found.map(j => `<button data-journal-id="${esc(j.id)}" data-journal-name="${esc(j.name)}">${esc(j.name)}</button>`).join("")
        : `<div class="more">${T.placeNone}</div>`;
      box.hidden = false;
    }, 250);
  });
  $("journal-results").addEventListener("click", async e => {
    const b = e.target.closest("[data-journal-id]");
    if (!b) return;
    $("journal-results").hidden = true;
    $("journal-input").value = "";
    await papersAction(() => api().add_paper_journal(b.dataset.journalId, b.dataset.journalName));
  });
  document.addEventListener("click", e => {
    if (!e.target.closest("#journal-input, #journal-results")) $("journal-results").hidden = true;
  });
  $("papers-fetch").addEventListener("click", async () => {
    $("papers-fetch").disabled = true;
    $("papers-fetch").textContent = T.papersFetching;
    S.papers = await api().fetch_papers_now();
    $("papers-fetch").disabled = false;
    $("papers-fetch").textContent = T.papersFetch;
    await load();
  });
  $("kma-key-save").addEventListener("click", async () => {
    try {
      renderWeatherSettings(await api().set_weather_key($("set-kma-key").value));
    } catch {
      renderWeatherSettings(await api().weather_settings(), true);
    }
  });
  $("place-input").addEventListener("input", () => {
    clearTimeout(placeTimer);
    placeTimer = setTimeout(searchPlaces, 120);
  });
  $("place-input").addEventListener("keydown", e => {
    const items = [...$("place-results").querySelectorAll("[data-place]")];
    if (!items.length) return;
    const i = items.findIndex(b => b.classList.contains("active"));
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const next = items[(i + (e.key === "ArrowDown" ? 1 : items.length - 1) + (i < 0 && e.key === "ArrowUp" ? 1 : 0)) % items.length];
      items.forEach(b => b.classList.toggle("active", b === next));
      next.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
      choosePlace((items[i] || items[0]).dataset.place);
    } else if (e.key === "Escape") {
      $("place-results").hidden = true;
    }
  });
  $("place-results").addEventListener("click", e => {
    const b = e.target.closest("[data-place]");
    if (b) choosePlace(b.dataset.place);
  });
  document.addEventListener("click", e => {
    if (!e.target.closest(".place-search")) $("place-results").hidden = true;
  });
  $("set-remind").addEventListener("click", e => {
    const b = e.target.closest("[data-value]");
    if (b) setSetting("remind", b.dataset.value).then(renderSettings);
  });
  $("gcal-colors").addEventListener("click", async e => {
    const b = e.target.closest("[data-cal]");
    if (b) renderGcal(await api().set_calendar_color(b.dataset.cal, b.dataset.color));
  });
  $("set-update-auto").addEventListener("click", e => {
    const b = e.target.closest("[data-value]");
    if (b) setSetting("update_auto", b.dataset.value).then(async () => renderUpdate(await api().update_status()));
  });
  $("update-actions").addEventListener("click", async e => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (!act) return;
    renderUpdate(await api().update_status(), act === "check" ? T.updateChecking : T.updateInstalling);
    try {
      renderUpdate(await (act === "check" ? api().check_update_now() : api().install_update()),
                   act === "install" ? T.updateInstalling : "");
    } catch (err) {
      const code = String(err && (err.message || err)).match(/[a-z_]+$/);
      renderUpdate(await api().update_status(), code ? code[0] : "network");
    }
  });
  $("gcal-actions").addEventListener("click", async e => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (!act) return;
    const st = await api().gcal_status();
    if (act === "import") return renderGcal(await api().gcal_import_client());
    if (act === "disconnect") {
      if (await ask(T.confirmDisconnect, T.gcalDisconnect)) renderGcal(await api().gcal_disconnect());
      return;
    }
    renderGcal(st, true);
    try {
      renderGcal(await (act === "connect" ? api().gcal_connect() : api().gcal_sync_now()));
    } catch {
      renderGcal({ ...(await api().gcal_status()), error: T.gcalFailed });
    }
  });
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
  if (!POPUP) $("detail").hidden = true;
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
  $("f-bucket").addEventListener("change", async e => {
    const t = S.data.tasks.find(x => x.id === S.selected);
    // A dated task shows where its date puts it (t.bucket); another bucket only makes sense without the date.
    if (t.due_date && e.target.value !== t.bucket) {
      if (!await ask(T.confirmClearDue(T[t.bucket]))) { e.target.value = t.bucket; return; }
      return save({ bucket: e.target.value, due_date: "" });
    }
    save({ bucket: e.target.value });
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
  // Behave like a flyout: hide when focus leaves.
  window.addEventListener("blur", () => api().popup_blurred());
  document.addEventListener("keydown", e => { if (e.key === "Escape") api().hide_popup(); });
}

// Called from Python after a calendar sync changed tasks or today's events.
window.reloadData = async () => {
  if (!S.data) return;
  if (S.view !== "settings") return load();
  S.data = await api().state("today");  // keep the sidebar counts current without redrawing the form
  if (!POPUP) renderNav();
};

// Called from Python for the global quick-add hotkey.
window.focusQuickAdd = () => { $("quick-input").focus(); $("quick-input").select(); };

// Called from Python when a popup row is clicked.
window.focusTask = async id => {
  S.view = "today";
  S.project = "";
  await load();
  openDetail(id);
};

function bindShared() {
  $("weather").addEventListener("click", () => { $("weather-panel").hidden = !$("weather-panel").hidden; });
  $("quick-add").addEventListener("submit", async e => {
    e.preventDefault();
    const title = $("quick-input").value.trim();
    if (!title) return;
    $("quick-input").value = "";
    if (POPUP) {
      await api().add(title, S.view, S.project);
      return load();
    }
    // Options under the main window's input: fill any of them before pressing Enter.
    const opt = id => $(id).value;
    let date = opt("qa-date");
    const time = opt("qa-time"), recurrence = opt("qa-recurrence");
    if (!date && (time || recurrence)) date = S.data.today;  // a time or repeat needs a day to hang on
    const id = await api().add(title, S.view, opt("qa-project").trim() || S.project);
    if (date) await api().update(id, { due_date: date, due_time: time, recurrence });
    for (const f of ["qa-date", "qa-time", "qa-recurrence", "qa-project"]) $(f).value = "";
    await load();
    $("quick-input").focus();
  });
  if (!POPUP) {
    // Date/time fields switch off the browser's own Enter-to-submit, so submit from any field here.
    $("quick-add").addEventListener("keydown", e => {
      if (e.key === "Enter" && e.target.tagName !== "SELECT") { e.preventDefault(); $("quick-add").requestSubmit(); }
    });
  }
  $("list").addEventListener("click", async e => {
    if (e.target.closest("[data-goto-settings]")) { S.view = "settings"; return load(); }
    const paperRow = e.target.closest(".paper");
    if (paperRow) return onPaperClick(e, paperRow);
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
      if (await ask(T.confirmPurge, T.purge, true)) { await api().purge(id); await load(); }
      return;
    }
    if (POPUP) return api().show_main(id);
    openDetail(id);
  });
  // Other windows may have changed data or settings; refresh whenever this one gets focus.
  window.addEventListener("focus", () => { if (S.data) load(); });
  // Re-evaluate Today/D-day when the date rolls over while the app is open.
  setInterval(() => { if (S.data && localToday() !== S.data.today) load(); }, 60000);
}

function bind() {
  bindShared();
  if (POPUP) return bindPopup();
  document.querySelector(".sidebar").addEventListener("click", e => {
    const li = e.target.closest("[data-view]");
    if (!li) return;
    S.view = li.dataset.view;
    S.project = "";  // a sidebar view always shows everything, not one project
    closeDetail();
    load();
  });
  $("side-toggle").onclick = () =>
    setSetting("sidebar", S.data.settings.sidebar === "collapsed" ? "expanded" : "collapsed");
  $("projects").addEventListener("click", e => {
    const li = e.target.closest("[data-project]");
    if (!li) return;
    // Clicking the open project again goes back to Today.
    const same = S.view === "project" && S.project === li.dataset.project;
    S.view = same ? "today" : "project";
    S.project = same ? "" : li.dataset.project;
    closeDetail();
    load();
  });
  $("proj-colors").addEventListener("click", async e => {
    const b = e.target.closest("[data-color]");
    if (!b) return;
    await api().set_project_color(S.project, b.dataset.color);
    await load();
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
  bindSettings();
}

document.querySelectorAll("[data-icon]").forEach(el => { el.outerHTML = icon(el.dataset.icon); });
// Hidden windows (the tray popup) don't fetch fonts until shown; load it now to avoid a flash.
document.fonts.load('16px "Pretendard"');
applyStaticStrings();
bind();
if (window.pywebview?.api?.state) load();
else window.addEventListener("pywebviewready", load);
