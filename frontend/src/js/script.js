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

  // ---------- Đăng nhập demo (giả lập, không xác thực thật) ----------
  // Dữ liệu cá nhân chỉ lưu trong bộ nhớ trình duyệt (không gửi lên server nào).
  const loginOverlay = document.getElementById("loginOverlay");
  const loginForm = document.getElementById("loginForm");
  const mainShell = document.getElementById("mainShell");
  const sidebarStudent = document.getElementById("sidebarStudent");
  const studentNameLabel = document.getElementById("studentNameLabel");
  const studentIdLabel = document.getElementById("studentIdLabel");

  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = document.getElementById("loginName").value.trim();
      const id = document.getElementById("loginId").value.trim();
      if (!name || !id) return;

      if (sidebarStudent) {
        studentNameLabel.textContent = name;
        studentIdLabel.textContent = "MSSV: " + id;
        sidebarStudent.hidden = false;
      }
      loginOverlay.hidden = true;
      mainShell.hidden = false;
      input && input.focus();
    });
  } else {
    // Không có màn đăng nhập trên trang này -> hiện luôn giao diện chat.
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

  function updateInfoPanel({ source, source_type, updated_at }, question) {
    if (!infoPanelBody) return;
    const resolvedType = inferSourceType(source_type, source);
    const meta = CONFIG.SOURCE_LABELS[resolvedType];
    infoPanelBody.innerHTML = `
      <div class="infopanel__row"><strong>Câu hỏi</strong>${question}</div>
      <div class="infopanel__row"><strong>Loại nguồn</strong>${meta.label}</div>
      <div class="infopanel__row"><strong>Nguồn</strong>${source}</div>
      <div class="infopanel__row"><strong>Cập nhật</strong>${fmtTime(updated_at)}</div>
      ${meta.note ? `<div class="infopanel__row" style="color:var(--plum); font-style:italic;">${meta.note}</div>` : ""}
    `;
  }

  // ---------- MOCK DATA (chỉ dùng khi CONFIG.USE_MOCK = true) ----------
  const MOCK_ANSWERS = [
    { match: /học phí|hoc phi|tuition/i, answer: "Học phí học kỳ này được tính theo tín chỉ đã đăng ký, xem chi tiết tại cổng sinh viên mục 'Tài chính'.", source: "Phòng Tài chính — Sổ tay sinh viên 2026", source_type: "faq" },
    { match: /lịch thi|lich thi|exam/i, answer: "Lịch thi học kỳ này dự kiến công bố trước 2 tuần thi, bạn kiểm tra ở mục 'Lịch thi' trên cổng đào tạo.", source: "Phòng Đào tạo — Lịch thi HK1", source_type: "faq" },
    { match: /lịch học|lich hoc|thời khóa biểu|tkb/i, answer: "Thời khóa biểu được cập nhật theo lớp đăng ký, bạn xem trong mục 'Thời khóa biểu' của cổng sinh viên.", source: "Phòng Đào tạo — TKB HK1", source_type: "demo" },
  ];
  const MOCK_DEFAULT = {
    answer: "Mình chưa có dữ liệu chính xác cho câu hỏi này. Bạn thử hỏi về học phí, lịch học hoặc lịch thi nhé.",
    source: "CloudBot — phản hồi mặc định",
    source_type: "fallback",
  };

  function mockReply(question) {
    const hit = MOCK_ANSWERS.find((m) => m.match.test(question));
    const picked = hit || MOCK_DEFAULT;
    return new Promise((resolve) => {
      const delay = 600 + Math.random() * 900;
      setTimeout(() => {
        if (question.trim().length < 3) {
          resolve({
            answer: "Câu hỏi hơi ngắn, bạn mô tả rõ hơn giúp mình nhé.",
            source: "CloudBot — kiểm tra đầu vào",
            source_type: "fallback",
            updated_at: new Date().toISOString(),
          });
          return;
        }
        resolve({
          answer: picked.answer,
          source: picked.source,
          source_type: picked.source_type,
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

    const res = await withTimeout(
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
      CONFIG.REQUEST_TIMEOUT_MS
    );

    if (!res.ok) {
      throw new Error("HTTP " + res.status);
    }

    const data = await res.json();
    return {
      answer: data[CONFIG.RESPONSE_FIELDS.answer] || "(Không có nội dung trả lời)",
      source: data[CONFIG.RESPONSE_FIELDS.source] || "Không rõ nguồn",
      source_type: data[CONFIG.RESPONSE_FIELDS.sourceType] || null,
      updated_at: data[CONFIG.RESPONSE_FIELDS.updatedAt] || new Date().toISOString(),
    };
  }

  async function sendFeedback(question, answer, rating) {
    if (CONFIG.USE_MOCK) return true;
    try {
      const url = CONFIG.API_BASE_URL.replace(/\/$/, "") + CONFIG.ENDPOINTS.feedback;
      const body = {};
      body[CONFIG.FEEDBACK_FIELDS.question] = question;
      body[CONFIG.FEEDBACK_FIELDS.answer] = answer;
      body[CONFIG.FEEDBACK_FIELDS.rating] = rating;
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

  function addBotMessage({ answer, source, source_type, updated_at }, lastQuestion) {
    const node = botTpl.content.cloneNode(true);
    const resolvedType = inferSourceType(source_type, source);
    const meta = CONFIG.SOURCE_LABELS[resolvedType];

    node.querySelector(".msg__answer").textContent = answer;
    node.querySelector(".msg__source-badge").textContent = meta.label;
    node.querySelector(".msg__source-badge").classList.add("badge--" + resolvedType);
    node.querySelector(".msg__source").textContent = "Nguồn: " + source;
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
    updateInfoPanel({ source, source_type, updated_at }, lastQuestion);
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
