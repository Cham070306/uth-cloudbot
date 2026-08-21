(function () {
  "use strict";

  const chatScroll = document.getElementById("chatScroll");
  const form = document.getElementById("composerForm");
  const input = document.getElementById("questionInput");
  const sendBtn = document.getElementById("sendBtn");
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");

  const botTpl = document.getElementById("botMsgTemplate");
  const userTpl = document.getElementById("userMsgTemplate");
  const loadingTpl = document.getElementById("loadingMsgTemplate");
  const errorTpl = document.getElementById("errorMsgTemplate");

  // Các phần tử mới thêm cho giao diện sidebar (có thể không tồn tại ở bản cũ,
  // nên luôn kiểm tra tồn tại trước khi dùng để không lỗi ở index.html cũ).
  const envPill = document.getElementById("envPill");
  const infoPanelBody = document.getElementById("infoPanelBody");
  const newChatBtn = document.getElementById("newChatBtn");
  const suggestionBtns = document.querySelectorAll(".sidebar__suggestion");

  if (envPill) {
    envPill.textContent = CONFIG.ENV === "local" ? "Môi trường: Local" : "Môi trường: Render";
  }

  // ---------- Đăng nhập (gọi backend thật /api/auth/login) ----------
  const loginOverlay = document.getElementById("loginOverlay");
  const loginForm = document.getElementById("loginForm");
  const mainShell = document.getElementById("mainShell");
  const sidebarStudent = document.getElementById("sidebarStudent");
  const studentNameLabel = document.getElementById("studentNameLabel");
  const studentIdLabel = document.getElementById("studentIdLabel");

  // Lưu trong bộ nhớ phiên làm việc (không dùng localStorage).
  let authToken = null;

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("loginName").value.trim();
      const password = document.getElementById("loginId").value.trim();
      if (!username || !password) return;

      const submitBtn = loginForm.querySelector(".loginCard__submit");
      const errorEl = document.getElementById("loginError");
      submitBtn.disabled = true;
      submitBtn.textContent = "Đang đăng nhập…";
      if (errorEl) errorEl.hidden = true;

      try {
        if (CONFIG.USE_MOCK) {
          throw new Error("mock"); // mock mode -> bỏ qua gọi API, vào thẳng demo
        }
        const url = CONFIG.API_BASE_URL.replace(/\/$/, "") + CONFIG.ENDPOINTS.login;
        const res = await withTimeout(
          fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
          }),
          8000
        );
        if (!res.ok) {
          const errBody = await res.json().catch(() => null);
          const msg = errBody && errBody.error && errBody.error.message
            ? errBody.error.message
            : "Tài khoản hoặc mật khẩu không đúng.";
          throw new Error(msg);
        }
        const data = await res.json();
        authToken = data.access_token || null;
        const student = data.student || {};
        if (sidebarStudent) {
          studentNameLabel.textContent = student.name || username;
          studentIdLabel.textContent = "MSSV: " + (student.id || username);
          sidebarStudent.hidden = false;
        }
        loginOverlay.hidden = true;
        mainShell.hidden = false;
        input && input.focus();
      } catch (err) {
        if (err && err.message === "mock") {
          // Chế độ mock: cho vào thẳng, không có token thật.
          if (sidebarStudent) {
            studentNameLabel.textContent = username;
            studentIdLabel.textContent = "MSSV: " + password;
            sidebarStudent.hidden = false;
          }
          loginOverlay.hidden = true;
          mainShell.hidden = false;
          input && input.focus();
        } else if (errorEl) {
          errorEl.textContent = err.message || "Không đăng nhập được. Kiểm tra lại tài khoản demo.";
          errorEl.hidden = false;
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Vào trò chuyện";
      }
    });
  } else {
    if (mainShell) mainShell.hidden = false;
  }

  if (newChatBtn) {
    newChatBtn.addEventListener("click", () => {
      chatScroll.innerHTML = "";
      const node = document.createElement("div");
      node.className = "msg msg--bot";
      node.innerHTML = '<div class="msg__avatar">B</div><div class="msg__bubble"><p>Chào bạn! Bắt đầu cuộc trò chuyện mới nhé — hỏi mình về học phí, lịch học hoặc lịch thi.</p></div>';
      chatScroll.appendChild(node);
      if (infoPanelBody) infoPanelBody.innerHTML = '<p class="infopanel__empty">Chưa có câu hỏi nào được gửi.</p>';
    });
  }

  suggestionBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      input.value = btn.textContent.trim();
      handleSend(input.value);
    });
  });

  function updateInfoPanel({ sourceObj, sourceText, aiGenerated, fallbackUsed, updated_at }, question) {
    if (!infoPanelBody) return;
    const resolvedType = inferSourceType(sourceObj, aiGenerated, fallbackUsed);
    const meta = CONFIG.SOURCE_LABELS[resolvedType];
    infoPanelBody.innerHTML = `
      <div class="infopanel__row"><strong>Câu hỏi</strong>${question}</div>
      <div class="infopanel__row"><strong>Loại nguồn</strong>${meta.label}</div>
      <div class="infopanel__row"><strong>Nguồn</strong>${sourceText}</div>
      <div class="infopanel__row"><strong>Cập nhật</strong>${fmtTime(updated_at)}</div>
      ${meta.note ? `<div class="infopanel__row" style="color:var(--plum); font-style:italic;">${meta.note}</div>` : ""}
    `;
  }

  // ---------- MOCK DATA (chỉ dùng khi CONFIG.USE_MOCK = true) ----------
  const MOCK_ANSWERS = [
    { match: /học phí|hoc phi|tuition/i, answer: "Học phí học kỳ này được tính theo tín chỉ đã đăng ký, xem chi tiết tại cổng sinh viên mục 'Tài chính'.", sourceObj: { type: "sample", title: "Phòng Tài chính — Sổ tay sinh viên 2026" } },
    { match: /lịch thi|lich thi|exam/i, answer: "Lịch thi học kỳ này dự kiến công bố trước 2 tuần thi, bạn kiểm tra ở mục 'Lịch thi' trên cổng đào tạo.", sourceObj: { type: "sample", title: "Phòng Đào tạo — Lịch thi HK1" } },
    { match: /lịch học|lich hoc|thời khóa biểu|tkb/i, answer: "Thời khóa biểu được cập nhật theo lớp đăng ký, bạn xem trong mục 'Thời khóa biểu' của cổng sinh viên.", sourceObj: { type: "mock", title: "Dữ liệu demo — TKB HK1" } },
  ];
  const MOCK_DEFAULT = {
    answer: "Mình chưa có dữ liệu chính xác cho câu hỏi này. Bạn thử hỏi về học phí, lịch học hoặc lịch thi nhé.",
    sourceObj: { type: "fallback", title: "CloudBot — phản hồi mặc định" },
  };

  function mockReply(question) {
    const hit = MOCK_ANSWERS.find((m) => m.match.test(question));
    const picked = hit || MOCK_DEFAULT;
    return new Promise((resolve) => {
      const delay = 600 + Math.random() * 900;
      setTimeout(() => {
        if (question.trim().length < 3) {
          const s = { type: "fallback", title: "CloudBot — kiểm tra đầu vào" };
          resolve({
            answer: "Câu hỏi hơi ngắn, bạn mô tả rõ hơn giúp mình nhé.",
            sourceObj: s,
            sourceText: formatSourceText(s),
            aiGenerated: false,
            fallbackUsed: true,
            updated_at: new Date().toISOString(),
          });
          return;
        }
        resolve({
          answer: picked.answer,
          sourceObj: picked.sourceObj,
          sourceText: formatSourceText(picked.sourceObj),
          aiGenerated: picked.sourceObj.type === "gemini",
          fallbackUsed: picked.sourceObj.type === "fallback",
          updated_at: new Date().toISOString(),
        });
      }, delay);
    });
  }

  // ---------- API CALLS THẬT ----------
  function withTimeout(promise, ms) {
    return Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
    ]);
  }

  async function callChatApi(question) {
    if (CONFIG.USE_MOCK) {
      return mockReply(question);
    }

    const url = CONFIG.API_BASE_URL.replace(/\/$/, "") + CONFIG.ENDPOINTS.chat;
    const body = {};
    body[CONFIG.REQUEST_FIELDS.question] = question;

    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = "Bearer " + authToken;

    const res = await withTimeout(
      fetch(url, { method: "POST", headers, body: JSON.stringify(body) }),
      CONFIG.REQUEST_TIMEOUT_MS
    );

    if (!res.ok) {
      throw new Error("HTTP " + res.status);
    }

    const data = await res.json();
    const sourceObj = data[CONFIG.RESPONSE_FIELDS.source] || null;
    return {
      answer: data[CONFIG.RESPONSE_FIELDS.answer] || "(Không có nội dung trả lời)",
      intent: data.intent || "unknown",
      items: data.data && Array.isArray(data.data.items) ? data.data.items : [],
      sourceObj,
      sourceText: formatSourceText(sourceObj),
      aiGenerated: !!data[CONFIG.RESPONSE_FIELDS.aiGenerated],
      fallbackUsed: !!data[CONFIG.RESPONSE_FIELDS.fallbackUsed],
      updated_at: data[CONFIG.RESPONSE_FIELDS.updatedAt] || new Date().toISOString(),
    };
  }

  async function sendFeedback(question, answer, vote) {
    if (CONFIG.USE_MOCK) return true;
    try {
      const url = CONFIG.API_BASE_URL.replace(/\/$/, "") + CONFIG.ENDPOINTS.feedback;
      const body = {};
      body[CONFIG.FEEDBACK_FIELDS.question] = question;
      body[CONFIG.FEEDBACK_FIELDS.answer] = answer;
      body[CONFIG.FEEDBACK_FIELDS.vote] = vote; // "up" | "down"
      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  async function checkHealth() {
    if (CONFIG.USE_MOCK) {
      setStatus("ok", "Chế độ giả lập (mock data)");
      return;
    }
    try {
      const url = CONFIG.API_BASE_URL.replace(/\/$/, "") + CONFIG.ENDPOINTS.health;
      const res = await withTimeout(fetch(url), 5000);
      setStatus(res.ok ? "ok" : "error", res.ok ? "Đã kết nối máy chủ" : "Máy chủ phản hồi lỗi");
    } catch (e) {
      setStatus("error", "Không kết nối được máy chủ");
    }
  }

  function setStatus(kind, text) {
    statusDot.className = "dot dot--" + kind;
    statusText.textContent = text;
  }

  // ---------- RENDER HELPERS ----------
  function scrollToBottom() {
    chatScroll.scrollTop = chatScroll.scrollHeight;
  }

  function fmtTime(iso) {
    try {
      return new Date(iso).toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" });
    } catch (e) {
      return "";
    }
  }

  function addUserMessage(text) {
    const node = userTpl.content.cloneNode(true);
    node.querySelector(".msg__bubble").textContent = text;
    chatScroll.appendChild(node);
    scrollToBottom();
  }

  function addLoadingMessage() {
    const node = loadingTpl.content.cloneNode(true);
    chatScroll.appendChild(node);
    scrollToBottom();
    return chatScroll.lastElementChild;
  }

  function fmtDate(value, includeTime = false) {
    if (!value) return "Chưa cập nhật";
    try {
      const options = { day: "2-digit", month: "2-digit", year: "numeric" };
      if (includeTime) Object.assign(options, { hour: "2-digit", minute: "2-digit" });
      return new Date(value).toLocaleString("vi-VN", options);
    } catch (e) {
      return String(value);
    }
  }

  function detailRow(label, value) {
    const row = document.createElement("span");
    row.className = "msg__detail-meta";
    row.textContent = label + ": " + (value || "Chưa cập nhật");
    return row;
  }

  function renderDetails(container, intent, items) {
    if (!items.length) return;
    const visibleItems = items.slice(0, 8);

    visibleItems.forEach((item) => {
      const card = document.createElement("article");
      card.className = "msg__detail-card";
      const title = document.createElement("strong");
      title.className = "msg__detail-title";

      if (intent === "personal_schedule") {
        title.textContent = item.course_name || item.course_code || "Buổi học";
        card.append(title, detailRow("Ngày", fmtDate(item.date)), detailRow("Thời gian", [item.start_time, item.end_time].filter(Boolean).join("–")), detailRow("Phòng", item.room));
      } else if (intent === "personal_assignment" || intent === "personal_deadline") {
        title.textContent = item.title || item.course_name || "Bài tập";
        card.append(title, detailRow("Môn", item.course_name), detailRow("Hạn nộp", fmtDate(item.due_at, true)), detailRow("Trạng thái", item.status));
      } else if (intent === "personal_exam") {
        title.textContent = item.title || item.course_name || "Lịch kiểm tra";
        card.append(title, detailRow("Môn", item.course_name), detailRow("Thời gian", fmtDate(item.start_at, true)), detailRow("Phòng", item.room || item.platform));
      } else if (intent === "personal_announcement") {
        title.textContent = item.title || "Thông báo";
        const content = document.createElement("p");
        content.className = "msg__detail-content";
        content.textContent = item.content || "";
        card.append(title, content, detailRow("Đăng lúc", fmtDate(item.published_at, true)));
      } else {
        return;
      }
      container.appendChild(card);
    });

    if (container.children.length) {
      container.hidden = false;
      if (items.length > visibleItems.length) {
        const more = document.createElement("p");
        more.className = "msg__detail-more";
        more.textContent = `Còn ${items.length - visibleItems.length} mục khác.`;
        container.appendChild(more);
      }
    }
  }

  function markdownToPlainText(value) {
    return String(value || "")
      .replace(/```[a-zA-Z0-9_+-]*\s*/g, "")
      .replace(/```|`/g, "")
      .replace(/^\s{0,3}#{1,6}\s*/gm, "")
      .replace(/^\s*>\s?/gm, "")
      .replace(/\*\*(.+?)\*\*|__(.+?)__/g, (_match, boldA, boldB) => boldA || boldB)
      .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1$2")
      .replace(/(^|[^_])_([^_\n]+)_(?!_)/g, "$1$2")
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1 ($2)")
      .replace(/^\s*[-*+]\s+/gm, "• ")
      .replace(/^\s*([-*_])(?:\s*\1){2,}\s*$/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function renderStructuredAnswer(container, value) {
    const lines = markdownToPlainText(value).split("\n");
    let activeList = null;
    let activeType = "";

    lines.forEach((rawLine) => {
      const line = rawLine.trim();
      if (!line) {
        activeList = null;
        activeType = "";
        return;
      }

      const bullet = line.match(/^•\s+(.+)/);
      const numbered = line.match(/^\d{1,2}\.\s+(.+)/);
      const listType = bullet ? "ul" : numbered ? "ol" : "";
      if (listType) {
        if (!activeList || activeType !== listType) {
          activeList = document.createElement(listType);
          activeList.className = "msg__answer-list";
          container.appendChild(activeList);
          activeType = listType;
        }
        const item = document.createElement("li");
        item.textContent = (bullet || numbered)[1];
        activeList.appendChild(item);
        return;
      }

      activeList = null;
      activeType = "";
      const paragraph = document.createElement("p");
      if (line.endsWith(":") && line.length <= 80) {
        paragraph.className = "msg__answer-heading";
        const heading = document.createElement("strong");
        heading.textContent = line;
        paragraph.appendChild(heading);
      } else {
        paragraph.textContent = line;
      }
      container.appendChild(paragraph);
    });
  }

  function addBotMessage({ answer, intent, items = [], sourceObj, sourceText, aiGenerated, fallbackUsed, updated_at }, lastQuestion) {
    const node = botTpl.content.cloneNode(true);
    const resolvedType = inferSourceType(sourceObj, aiGenerated, fallbackUsed);
    const meta = CONFIG.SOURCE_LABELS[resolvedType];

    const answerEl = node.querySelector(".msg__answer");
    if (aiGenerated) renderStructuredAnswer(answerEl, answer);
    else answerEl.textContent = answer;
    renderDetails(node.querySelector(".msg__details"), intent, items);
    node.querySelector(".msg__source-badge").textContent = meta.label;
    node.querySelector(".msg__source-badge").classList.add("badge--" + resolvedType);
    node.querySelector(".msg__source").textContent = "Nguồn: " + sourceText;
    node.querySelector(".msg__time").textContent = fmtTime(updated_at);

    const disclaimerEl = node.querySelector(".msg__disclaimer");
    if (meta.note) {
      disclaimerEl.textContent = meta.note;
      disclaimerEl.hidden = false;
    } else {
      disclaimerEl.hidden = true;
    }

    const upBtn = node.querySelector(".fb-up");
    const downBtn = node.querySelector(".fb-down");
    const thanks = node.querySelector(".msg__fb-thanks");

    function lockFeedback(msg) {
      upBtn.disabled = true;
      downBtn.disabled = true;
      thanks.textContent = msg;
    }

    upBtn.addEventListener("click", async () => {
      lockFeedback("Đã ghi nhận, cảm ơn bạn!");
      await sendFeedback(lastQuestion, answer, "up");
    });
    downBtn.addEventListener("click", async () => {
      lockFeedback("Cảm ơn phản hồi, mình sẽ cải thiện.");
      await sendFeedback(lastQuestion, answer, "down");
    });

    chatScroll.appendChild(node);
    scrollToBottom();
    updateInfoPanel({ sourceObj, sourceText, aiGenerated, fallbackUsed, updated_at }, lastQuestion);
  }

  function addErrorMessage(retryFn) {
    const node = errorTpl.content.cloneNode(true);
    node.querySelector(".retry-btn").addEventListener("click", retryFn, { once: true });
    chatScroll.appendChild(node);
    scrollToBottom();
    return chatScroll.lastElementChild;
  }

  // ---------- MAIN FLOW ----------
  let isSending = false;

  async function handleSend(question) {
    if (!question.trim() || isSending) return;
    isSending = true;
    sendBtn.disabled = true;

    addUserMessage(question);
    input.value = "";

    const loadingEl = addLoadingMessage();

    try {
      const result = await callChatApi(question);
      loadingEl.remove();
      addBotMessage(result, question);
    } catch (err) {
      loadingEl.remove();
      // Giữ nguyên câu hỏi gốc khi retry (kể cả khi lỗi do timeout gọi Gemini lâu)
      addErrorMessage(() => {
        chatScroll.lastElementChild.remove();
        handleSend(question);
      });
    } finally {
      isSending = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    handleSend(input.value);
  });

  checkHealth();
})();
