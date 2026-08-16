/* UTH CloudBot — FE-02: tích hợp frontend với API BE-01. */

// Đổi USE_MOCK thành true khi cần demo frontend mà không chạy backend.
const USE_MOCK = false;
const API_BASE = "https://uth-cloudbot.onrender.com";
const CHAT_URL = `${API_BASE}/api/chat`;
const FEEDBACK_URL = `${API_BASE}/api/feedback`;
const HEALTH_URL = `${API_BASE}/api/health`;
const LOGIN_URL = `${API_BASE}/api/auth/login`;
const TIMEOUT_MS = 30000;

const mockKnowledgeBase = [
  {
    keywords: ["học phí", "hoc phi"],
    paragraphs: ["Học phí được tính theo số tín chỉ đã đăng ký."],
    list: ["Kiểm tra số tiền trên cổng sinh viên.", "Hoàn tất trước hạn ghi trên thông báo."],
    sources: [{ label: "Dữ liệu minh họa FE-02", url: null }]
  },
  {
    keywords: ["lịch thi", "lich thi"],
    paragraphs: ["Lịch thi được công bố trên cổng đào tạo."],
    list: [],
    sources: [{ label: "Dữ liệu minh họa FE-02", url: null }]
  }
];

const emptyState = document.getElementById("emptyState");
const thread = document.getElementById("thread");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const inputError = document.getElementById("inputError");
const sendBtn = document.getElementById("sendBtn");
const errorBanner = document.getElementById("errorBanner");
const errorBannerText = errorBanner.querySelector("span");
const retryBtn = document.getElementById("retryBtn");
const newChatBtn = document.getElementById("newChatBtn");
const themeToggle = document.getElementById("themeToggle");
const apiBadge = document.getElementById("apiBadge");
const sourcesEmpty = document.getElementById("sourcesEmpty");
const sourcesContent = document.getElementById("sourcesContent");
const sourceList = document.getElementById("sourceList");
const historyItems = document.querySelectorAll(".history-item");
const suggestionCards = document.querySelectorAll(".suggest-card");
const healthStatus = document.getElementById("healthStatus");
const authButton = document.getElementById("authButton");
const authDialog = document.getElementById("authDialog");
const authForm = document.getElementById("authForm");
const authCancel = document.getElementById("authCancel");
const authError = document.getElementById("authError");
const usernameInput = document.getElementById("usernameInput");
const passwordInput = document.getElementById("passwordInput");

let isSending = false;
let lastFailedQuestion = null;
let activeController = null;
let requestSequence = 0;
let authToken = sessionStorage.getItem("uthCloudBotToken") || "";
let currentStudent = JSON.parse(sessionStorage.getItem("uthCloudBotStudent") || "null");

apiBadge.textContent = USE_MOCK ? "MOCK" : "LIVE";
apiBadge.classList.toggle("is-live", !USE_MOCK);
updateAuthUi();

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function requestJson(url, options, timeoutMs = TIMEOUT_MS, controller = new AbortController()) {
  const timer = setTimeout(() => controller.abort("timeout"), timeoutMs);
  let response;
  try {
    response = await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    const requestError = new Error(controller.signal.reason === "timeout" ? "Yêu cầu quá thời gian chờ." : "Không thể kết nối tới backend.");
    requestError.kind = controller.signal.reason === "timeout" ? "timeout" : "network";
    throw requestError;
  } finally {
    clearTimeout(timer);
  }

  const raw = await response.text();
  let data = null;
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch (_error) {
      const invalidJson = new Error("Máy chủ trả về dữ liệu không phải JSON hợp lệ.");
      invalidJson.kind = "invalid_json";
      invalidJson.status = response.status;
      throw invalidJson;
    }
  }

  if (!response.ok) {
    const serverMessage = data && data.error && typeof data.error.message === "string"
      ? data.error.message.trim()
      : "";
    const httpError = new Error(serverMessage || httpMessage(response.status));
    httpError.kind = "http";
    httpError.status = response.status;
    throw httpError;
  }

  if (!data || typeof data !== "object" || Array.isArray(data)) {
    const invalidResponse = new Error("Phản hồi JSON từ máy chủ không hợp lệ.");
    invalidResponse.kind = "invalid_json";
    throw invalidResponse;
  }
  return data;
}

function httpMessage(status) {
  const messages = {
    400: "Câu hỏi không hợp lệ. Vui lòng kiểm tra và thử lại.",
    404: "Không tìm thấy API trên máy chủ.",
    405: "API không hỗ trợ phương thức gửi này.",
    413: "Câu hỏi quá dài để máy chủ xử lý.",
    500: "Máy chủ gặp lỗi. Vui lòng thử lại sau."
  };
  return messages[status] || `Máy chủ trả về lỗi HTTP ${status}.`;
}

async function mockAsk(question) {
  await wait(700);
  const normalizedQuestion = question.toLowerCase();
  const hit = mockKnowledgeBase.find(item => item.keywords.some(keyword => normalizedQuestion.includes(keyword)));
  return hit ? { answer: hit.paragraphs.join(" "), invalid: false, ...hit } : {
    answer: "Mình chưa có dữ liệu minh họa phù hợp cho câu hỏi này.",
    invalid: true,
    paragraphs: ["Mình chưa có dữ liệu minh họa phù hợp cho câu hỏi này."],
    list: [],
    sources: []
  };
}

const apiClient = {
  async ask(question, controller) {
    if (USE_MOCK) return mockAsk(question);
    return requestJson(CHAT_URL, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ message: question })
    }, TIMEOUT_MS, controller);
  },

  health() {
    return requestJson(HEALTH_URL, { method: "GET" }, TIMEOUT_MS);
  },

  login(username, password) {
    return requestJson(LOGIN_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }) }, 8000);
  },

  personal(path, options = {}) {
    return requestJson(`${API_BASE}${path}`, { ...options, headers: authHeaders(options.headers) }, 8000);
  },

  async sendFeedback(payload) {
    if (USE_MOCK) {
      await wait(300);
      return { status: "received" };
    }
    return requestJson(FEEDBACK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }, 8000);
  }
};

function authHeaders(extra = {}) {
  return { "Content-Type": "application/json", ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}), ...extra };
}

function stringArray(value) {
  return Array.isArray(value) ? value.filter(item => typeof item === "string") : [];
}

function normalizeResponse(data) {
  let paragraphs = stringArray(data.paragraphs);
  const answer = typeof data.answer === "string" ? data.answer : "";
  if (!paragraphs.length && answer) {
    paragraphs = answer.split(/\n+/).map(paragraph => paragraph.trim()).filter(Boolean);
  }
  if (!paragraphs.length) paragraphs = ["Máy chủ chưa cung cấp nội dung trả lời."];

  const sources = Array.isArray(data.sources)
    ? data.sources.filter(source => source && typeof source === "object").map(source => ({
      label: typeof source.label === "string" && source.label.trim() ? source.label : "Nguồn tham khảo",
      url: typeof source.url === "string" ? source.url : null
    }))
    : [];

  return {
    invalid: data.invalid === true,
    answer: answer || [...paragraphs, ...stringArray(data.list)].join(" "),
    paragraphs,
    list: stringArray(data.list),
    sources,
    messageId: typeof data.message_id === "string" && data.message_id.trim() ? data.message_id.trim() : null,
    intent: typeof data.intent === "string" ? data.intent : "unknown",
    source: data.source && typeof data.source === "object" ? data.source : null,
    updatedAt: typeof data.updated_at === "string" ? data.updated_at : null,
    latencyMs: Number.isFinite(data.latency_ms) ? data.latency_ms : null,
    items: data.data && Array.isArray(data.data.items) ? data.data.items.filter(item => item && typeof item === "object") : [],
    requiresAuthentication: data.requires_authentication === true,
    requiresConfirmation: data.requires_confirmation === true,
    confirmation: data.confirmation && typeof data.confirmation === "object" ? data.confirmation : null
  };
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function iconButton(vote, label) {
  const button = element("button", "fb-btn", vote === "up" ? "👍" : "👎");
  button.type = "button";
  button.dataset.fb = vote;
  button.setAttribute("aria-label", label);
  return button;
}

function setBusy(busy) {
  isSending = busy;
  sendBtn.disabled = busy;
  suggestionCards.forEach(button => { button.disabled = busy; });
  historyItems.forEach(button => { button.disabled = busy; });
  thread.querySelectorAll(".followup-btn").forEach(button => { button.disabled = busy; });
  chatInput.setAttribute("aria-busy", String(busy));
}

function scrollToBottom() {
  thread.scrollTop = thread.scrollHeight;
}

function renderSources(sources) {
  sourceList.replaceChildren();
  if (!sources.length) {
    sourcesEmpty.hidden = false;
    sourcesContent.hidden = true;
    return;
  }
  sources.forEach(source => {
    const item = element("div", "source-item");
    const safeUrl = safeHttpUrl(source.url);
    if (safeUrl) {
      const link = element("a", "source-link", source.label);
      link.href = safeUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      item.append(link);
    } else {
      item.append(element("span", "", source.label));
    }
    sourceList.append(item);
  });
  sourcesEmpty.hidden = true;
  sourcesContent.hidden = false;
}

function safeHttpUrl(value) {
  if (!value) return null;
  try {
    const url = new URL(value, window.location.href);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch (_error) {
    return null;
  }
}

function buildTurn(question) {
  emptyState.hidden = true;
  thread.hidden = false;
  const turn = element("div", "turn");
  turn.dataset.question = question;

  const questionRow = element("div", "q-row");
  const pill = element("div", "q-pill");
  pill.append(element("span", "", question));
  pill.append(element("span", "edit-ico", "✎"));
  questionRow.append(pill, element("div", "avatar avatar--user", "SV"));

  const answerRow = element("div", "a-row");
  const card = element("div", "a-card is-loading");
  const dots = element("div", "typing-dots");
  dots.append(element("span"), element("span"), element("span"));
  card.append(dots);
  answerRow.append(element("div", "avatar avatar--bot", "A"), card);
  turn.append(questionRow, answerRow);
  thread.append(turn);
  scrollToBottom();
  return turn;
}

function addFollowups(turn, invalid) {
  const followups = element("div", "followups");
  const choices = invalid
    ? [["Hỏi về học phí", "Học phí kỳ này là bao nhiêu?"], ["Hỏi về lịch thi", "Lịch thi cuối kỳ ở đâu?"]]
    : [["Trả lời ngắn gọn hơn", "shorter"], ["Cho ví dụ cụ thể", "example"], ["Nói thêm chi tiết", "more"]];
  choices.forEach(([label, value]) => {
    const button = element("button", "followup-btn", label);
    button.type = "button";
    if (invalid) button.dataset.q = value;
    else button.dataset.followup = value;
    followups.append(button);
  });
  turn.append(followups);
}

function resolveTurn(turn, rawResult) {
  const result = normalizeResponse(rawResult);
  const card = turn.querySelector(".a-card");
  card.classList.remove("is-loading");
  if (result.invalid) card.classList.add("is-invalid");
  card.replaceChildren();

  result.paragraphs.forEach(paragraph => card.append(element("p", "", paragraph)));
  if (result.list.length) {
    const list = element("ol");
    result.list.forEach(item => list.append(element("li", "", item)));
    card.append(list);
  }
  if (result.items.length) {
    const items = element("div", "data-items");
    result.items.forEach(item => {
      const title = item.title || item.course_name || item.content || item.id || "Mục dữ liệu";
      const detail = item.due_at || item.start_at || item.date || item.published_at || item.status || "";
      const row = element("div", "data-item");
      row.append(element("strong", "", String(title)), element("span", "", String(detail)));
      items.append(row);
    });
    card.append(items);
  }
  const details = [
    `Chủ đề: ${result.intent}`,
    result.source?.title ? `Nguồn: ${result.source.title}` : null,
    result.updatedAt ? `Cập nhật: ${result.updatedAt}` : null,
    result.latencyMs !== null ? `Phản hồi: ${result.latencyMs} ms` : null
  ].filter(Boolean);
  card.append(element("p", "response-meta", details.join(" · ")));
  if (result.requiresAuthentication) {
    const loginPrompt = element("button", "inline-action", "Đăng nhập để tiếp tục");
    loginPrompt.type = "button"; loginPrompt.dataset.openLogin = "true"; card.append(loginPrompt);
  }
  if (result.requiresConfirmation && result.confirmation) addConfirmation(card, result.confirmation);
  const meta = element("div", "a-meta");
  meta.append(iconButton("up", "Hữu ích"), iconButton("down", "Không hữu ích"));
  card.append(meta);

  turn.dataset.answer = result.answer;
  if (result.messageId) turn.dataset.messageId = result.messageId;
  addFollowups(turn, result.invalid);
  renderSources(result.sources);
  scrollToBottom();
}

function addConfirmation(card, confirmation) {
  const box = element("div", "confirmation-box");
  box.append(element("strong", "", "Xác nhận thao tác"), element("p", "", confirmation.raw_message || "Bạn có muốn tiếp tục?"));
  if (confirmation.action === "create_reminder") {
    const label = element("label", "reminder-time-label", "Thời gian nhắc");
    const input = element("input", "reminder-time-input");
    input.type = "datetime-local";
    input.dataset.reminderTime = "true";
    const defaultTime = new Date(Date.now() + 60 * 60 * 1000);
    defaultTime.setMinutes(defaultTime.getMinutes() - defaultTime.getTimezoneOffset());
    input.value = defaultTime.toISOString().slice(0, 16);
    const minimum = new Date();
    minimum.setMinutes(minimum.getMinutes() - minimum.getTimezoneOffset());
    input.min = minimum.toISOString().slice(0, 16);
    input.required = true;
    label.append(input); box.append(label);
  }
  const confirm = element("button", "inline-action", "Xác nhận");
  const cancel = element("button", "inline-action secondary", "Hủy");
  confirm.type = cancel.type = "button";
  confirm.dataset.confirmAction = confirmation.action || "";
  confirm.dataset.rawMessage = confirmation.raw_message || "";
  cancel.dataset.cancelConfirmation = "true";
  box.append(confirm, cancel); card.append(box);
}

async function handleConfirmation(button) {
  const box = button.closest(".confirmation-box");
  const action = button.dataset.confirmAction;
  const raw = button.dataset.rawMessage;
  button.disabled = true;
  try {
    const isReminder = action === "create_reminder";
    const timeInput = box.querySelector("[data-reminder-time]");
    if (isReminder && (!timeInput.value || new Date(timeInput.value).getTime() <= Date.now())) {
      throw new Error("Vui lòng chọn thời gian nhắc trong tương lai.");
    }
    const payload = isReminder ? { content: raw, remind_at: new Date(timeInput.value).toISOString() } : { content: raw };
    const base = isReminder ? "/api/me/reminders" : "/api/me/notes";
    const created = await apiClient.personal(base, { method: "POST", body: JSON.stringify(payload) });
    await apiClient.personal(`${base}/${encodeURIComponent(created.id)}/confirm`, { method: "POST" });
    box.replaceChildren(element("p", "confirmation-success", "Đã xác nhận và lưu dữ liệu demo."));
  } catch (error) {
    box.append(element("p", "feedback-status is-error", error.message)); button.disabled = false;
  }
}

function updateAuthUi() {
  authButton.textContent = currentStudent ? `Đăng xuất · ${currentStudent.id}` : "Đăng nhập";
  authButton.setAttribute("aria-label", currentStudent ? `Đăng xuất tài khoản ${currentStudent.id}` : "Đăng nhập tài khoản demo");
}

async function checkHealth() {
  if (USE_MOCK) { healthStatus.textContent = "Mock sẵn sàng"; return; }
  try {
    await apiClient.health();
    healthStatus.textContent = "API sẵn sàng";
    healthStatus.classList.add("is-ok");
    errorBanner.hidden = true;
  }
  catch (_error) { healthStatus.textContent = "API ngoại tuyến"; healthStatus.classList.remove("is-ok"); }
}

function showError(error) {
  const prefix = error.kind === "timeout" ? "⏱ " : "⚠ ";
  errorBannerText.textContent = prefix + (error.message || "Đã xảy ra lỗi. Vui lòng thử lại.");
  errorBanner.hidden = false;
}

function restoreEmptyStateIfNeeded() {
  if (!thread.children.length) {
    thread.hidden = true;
    emptyState.hidden = false;
  }
}

async function sendQuestion(rawText) {
  if (isSending) return;
  const text = typeof rawText === "string" ? rawText.trim() : "";
  const maxLength = Number(chatInput.maxLength) || 300;
  if (!text || text.length > maxLength) {
    inputError.textContent = !text
      ? "Vui lòng nhập câu hỏi trước khi gửi."
      : `Câu hỏi không được vượt quá ${maxLength} ký tự.`;
    inputError.hidden = false;
    chatInput.classList.add("is-invalid");
    chatInput.focus();
    return;
  }

  inputError.hidden = true;
  chatInput.classList.remove("is-invalid");
  errorBanner.hidden = true;
  chatInput.value = "";
  setBusy(true);
  const turn = buildTurn(text);
  activeController = new AbortController();
  const sequence = ++requestSequence;

  try {
    const result = await apiClient.ask(text, activeController);
    if (sequence === requestSequence) {
      resolveTurn(turn, result);
      lastFailedQuestion = null;
    }
  } catch (error) {
    turn.remove();
    restoreEmptyStateIfNeeded();
    if (sequence === requestSequence && activeController?.signal.reason !== "reset") {
      lastFailedQuestion = text;
      showError(error);
    }
  } finally {
    if (sequence === requestSequence) {
      activeController = null;
      setBusy(false);
      chatInput.focus();
    }
  }
}

function resetThread() {
  requestSequence += 1;
  if (activeController) activeController.abort("reset");
  activeController = null;
  thread.replaceChildren();
  thread.hidden = true;
  emptyState.hidden = false;
  errorBanner.hidden = true;
  inputError.hidden = true;
  chatInput.classList.remove("is-invalid");
  chatInput.value = "";
  lastFailedQuestion = null;
  renderSources([]);
  historyItems.forEach(item => item.classList.remove("is-active"));
  setBusy(false);
  chatInput.focus();
}

function showFeedbackStatus(turn, message, isError = false) {
  let status = turn.querySelector(".feedback-status");
  if (!status) {
    status = element("p", "feedback-status");
    turn.querySelector(".a-card").append(status);
  }
  status.textContent = message;
  status.classList.toggle("is-error", isError);
}

async function handleFeedback(button) {
  const turn = button.closest(".turn");
  const buttons = [...turn.querySelectorAll(".fb-btn")];
  if (buttons.some(item => item.disabled)) return;
  buttons.forEach(item => { item.disabled = true; });
  const vote = button.dataset.fb;
  const payload = turn.dataset.messageId
    ? { message_id: turn.dataset.messageId, helpful: vote === "up" }
    : { question: turn.dataset.question || "", answer: turn.dataset.answer || "", vote };

  try {
    await apiClient.sendFeedback(payload);
    buttons.forEach(item => item.classList.toggle("is-selected", item === button));
    showFeedbackStatus(turn, "Cảm ơn bạn đã phản hồi.");
  } catch (error) {
    showFeedbackStatus(turn, error.message || "Chưa gửi được phản hồi. Vui lòng thử lại.", true);
  } finally {
    buttons.forEach(item => { item.disabled = false; });
  }
}

themeToggle.addEventListener("click", () => {
  const dark = document.documentElement.getAttribute("data-theme") === "dark";
  document.documentElement.setAttribute("data-theme", dark ? "light" : "dark");
});

authButton.addEventListener("click", () => {
  if (currentStudent) {
    authToken = ""; currentStudent = null;
    sessionStorage.removeItem("uthCloudBotToken"); sessionStorage.removeItem("uthCloudBotStudent");
    updateAuthUi(); return;
  }
  authError.hidden = true; authDialog.showModal(); usernameInput.focus();
});
authCancel.addEventListener("click", () => authDialog.close());
authForm.addEventListener("submit", async event => {
  event.preventDefault(); authError.hidden = true;
  const submit = authForm.querySelector('button[type="submit"]'); submit.disabled = true;
  try {
    const result = await apiClient.login(usernameInput.value.trim(), passwordInput.value);
    authToken = result.access_token; currentStudent = result.student;
    sessionStorage.setItem("uthCloudBotToken", authToken); sessionStorage.setItem("uthCloudBotStudent", JSON.stringify(currentStudent));
    errorBanner.hidden = true;
    lastFailedQuestion = null;
    updateAuthUi(); authDialog.close(); chatInput.focus();
  } catch (error) { authError.textContent = error.message; authError.hidden = false; }
  finally { submit.disabled = false; }
});

newChatBtn.addEventListener("click", resetThread);

historyItems.forEach(item => item.addEventListener("click", () => {
  if (isSending) return;
  historyItems.forEach(history => history.classList.remove("is-active"));
  item.classList.add("is-active");
  sendQuestion(item.dataset.title || "");
}));

suggestionCards.forEach(card => card.addEventListener("click", () => {
  if (!isSending) sendQuestion(card.dataset.q || "");
}));

chatForm.addEventListener("submit", event => {
  event.preventDefault();
  sendQuestion(chatInput.value);
});

chatInput.addEventListener("input", () => {
  if (chatInput.value.trim()) {
    inputError.hidden = true;
    chatInput.classList.remove("is-invalid");
  }
});

retryBtn.addEventListener("click", () => {
  if (!isSending && lastFailedQuestion) sendQuestion(lastFailedQuestion);
});

thread.addEventListener("click", event => {
  const login = event.target.closest("[data-open-login]");
  if (login) { authDialog.showModal(); usernameInput.focus(); return; }
  const confirm = event.target.closest("[data-confirm-action]");
  if (confirm) { handleConfirmation(confirm); return; }
  const cancel = event.target.closest("[data-cancel-confirmation]");
  if (cancel) { cancel.closest(".confirmation-box").replaceChildren(element("p", "", "Đã hủy thao tác.")); return; }
  const feedback = event.target.closest(".fb-btn");
  if (feedback) {
    handleFeedback(feedback);
    return;
  }
  const followup = event.target.closest(".followup-btn");
  if (!followup || isSending) return;
  if (followup.dataset.q) {
    sendQuestion(followup.dataset.q);
    return;
  }
  const prefixes = {
    shorter: "(trả lời ngắn gọn hơn) ",
    example: "(cho ví dụ cụ thể) ",
    more: "(nói thêm chi tiết) "
  };
  const question = followup.closest(".turn").dataset.question || "";
  sendQuestion((prefixes[followup.dataset.followup] || "") + question);
});

checkHealth();
