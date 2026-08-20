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

  // ---------- MOCK DATA (chỉ dùng khi CONFIG.USE_MOCK = true) ----------
  const MOCK_ANSWERS = [
    {
      match: /học phí|hoc phi|tuition/i,
      answer: "Học phí học kỳ này được tính theo tín chỉ đã đăng ký, xem chi tiết tại cổng sinh viên mục 'Tài chính'.",
      source: "Phòng Tài chính — Sổ tay sinh viên 2026",
    },
    {
      match: /lịch thi|lich thi|exam/i,
      answer: "Lịch thi học kỳ này dự kiến công bố trước 2 tuần thi, bạn kiểm tra ở mục 'Lịch thi' trên cổng đào tạo.",
      source: "Phòng Đào tạo — Lịch thi HK1",
    },
    {
      match: /lịch học|lich hoc|thời khóa biểu|tkb/i,
      answer: "Thời khóa biểu được cập nhật theo lớp đăng ký, bạn xem trong mục 'Thời khóa biểu' của cổng sinh viên.",
      source: "Phòng Đào tạo — TKB HK1",
    },
  ];
  const MOCK_DEFAULT = {
    answer: "Mình chưa có dữ liệu chính xác cho câu hỏi này. Bạn thử hỏi về học phí, lịch học hoặc lịch thi nhé.",
    source: "CloudBot — phản hồi mặc định",
  };

  function mockReply(question) {
    const hit = MOCK_ANSWERS.find((m) => m.match.test(question));
    const picked = hit || MOCK_DEFAULT;
    return new Promise((resolve, reject) => {
      const delay = 600 + Math.random() * 900;
      setTimeout(() => {
        // Giả lập trường hợp câu hỏi không hợp lệ (quá ngắn)
        if (question.trim().length < 3) {
          resolve({
            answer: "Câu hỏi hơi ngắn, bạn mô tả rõ hơn giúp mình nhé (ví dụ: 'lịch thi học kỳ 1 ở đâu?').",
            source: "CloudBot — kiểm tra đầu vào",
            updated_at: new Date().toISOString(),
          });
          return;
        }
        resolve({
          answer: picked.answer,
          source: picked.source,
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
      if (res.ok) {
        setStatus("ok", "Đã kết nối máy chủ");
      } else {
        setStatus("error", "Máy chủ phản hồi lỗi");
      }
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
      const d = new Date(iso);
      return d.toLocaleString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
      });
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
    const el = node.querySelector(".msg--loading");
    chatScroll.appendChild(node);
    scrollToBottom();
    return chatScroll.lastElementChild;
  }

  function addBotMessage({ answer, source, updated_at }) {
    const node = botTpl.content.cloneNode(true);
    node.querySelector(".msg__answer").textContent = answer;
    node.querySelector(".msg__source").textContent = "Nguồn: " + source;
    node.querySelector(".msg__time").textContent = fmtTime(updated_at);

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
  }

  function addErrorMessage(retryFn) {
    const node = errorTpl.content.cloneNode(true);
    node.querySelector(".retry-btn").addEventListener("click", retryFn, { once: true });
    chatScroll.appendChild(node);
    scrollToBottom();
    return chatScroll.lastElementChild;
  }

  // ---------- MAIN FLOW ----------
  let lastQuestion = "";
  let isSending = false;

  async function handleSend(question) {
    if (!question.trim() || isSending) return;
    isSending = true;
    sendBtn.disabled = true;
    lastQuestion = question;

    addUserMessage(question);
    input.value = "";

    const loadingEl = addLoadingMessage();

    try {
      const result = await callChatApi(question);
      loadingEl.remove();
      addBotMessage(result);
    } catch (err) {
      loadingEl.remove();
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

  // ---------- INIT ----------
  checkHealth();
})();
