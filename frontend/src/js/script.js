/* ==========================================================
   UTH Chatbot — FE-02: Tích hợp API
   Kết nối giao diện với:
     POST /api/chat      { question }              -> câu trả lời
     POST /api/feedback  { question, answer, vote } -> ghi nhận đánh giá
   Xử lý: loading, lỗi mạng, timeout, câu hỏi rỗng.

   Đang chạy ở chế độ MOCK (USE_MOCK = true) vì backend team 2
   (backend/app.py) chưa có endpoint thật. Khi backend deploy xong,
   đổi USE_MOCK = false và chỉnh API_BASE bên dưới là chạy được ngay
   — không cần sửa gì thêm trong phần render/UI.
   ========================================================== */

// ---------- Cấu hình API ----------
const USE_MOCK   = true;              // false khi backend đã sẵn sàng
const API_BASE    = "";                // vd: "https://uth-cloudbot-api.example.com"
const CHAT_URL     = `${API_BASE}/api/chat`;
const FEEDBACK_URL = `${API_BASE}/api/feedback`;
const TIMEOUT_MS   = 12000;            // 12s — quá thời gian này coi là timeout

// ---------- fetch có timeout ----------
function fetchWithTimeout(url, options = {}, timeoutMs = TIMEOUT_MS){
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  return fetch(url, { ...options, signal: controller.signal })
    .then(res => { clearTimeout(timer); return res; })
    .catch(err => {
      clearTimeout(timer);
      if (err.name === "AbortError"){
        const e = new Error("timeout");
        e.kind = "timeout";
        throw e;
      }
      const e = new Error("network");
      e.kind = "network";
      throw e;
    });
}

// ---------- Mock knowledge base (chỉ dùng khi USE_MOCK = true) ----------
const mockKnowledgeBase = [
  {
    keywords: ["học phí", "hoc phi", "tiền học", "đóng tiền"],
    paragraphs: ["Học phí học kỳ này được tính theo số tín chỉ đăng ký, cụ thể như sau:"],
    list: [
      "<strong>Mức phí:</strong> 850.000đ / tín chỉ đối với chương trình đại trà.",
      "<strong>Hạn đóng:</strong> chậm nhất ngày 20 hằng tháng kể từ khi mở học kỳ.",
      "<strong>Hình thức:</strong> đóng online qua cổng sinh viên, mục \"Tài chính\".",
      "<strong>Trễ hạn:</strong> hệ thống sẽ khóa đăng ký môn học kỳ sau nếu chưa hoàn tất."
    ],
    sources: [
      { label: "Thông báo học phí HK1 2026", url: "#" },
      { label: "Cổng thanh toán sinh viên", url: "#" }
    ]
  },
  {
    keywords: ["lịch thi", "thi cuối kỳ", "lich thi"],
    paragraphs: ["Lịch thi cuối kỳ được công bố và cập nhật trên cổng đào tạo:"],
    list: [
      "Vào mục <strong>\"Lịch thi\"</strong> trên cổng đào tạo để tra theo mã lớp.",
      "Phòng thi cụ thể hiển thị trước ngày thi <strong>3 ngày</strong>.",
      "Nếu trùng lịch thi, làm đơn xin đổi ca tại phòng Đào tạo trước 1 tuần."
    ],
    sources: [
      { label: "Lịch thi học kỳ 1", url: "#" },
      { label: "Hướng dẫn tra cứu phòng thi", url: "#" }
    ]
  },
  {
    keywords: ["đăng ký môn", "dang ky mon", "đăng ký học phần"],
    paragraphs: ["Quy trình đăng ký học phần gồm các bước sau:"],
    list: [
      "Đăng nhập cổng đào tạo trong <strong>thời gian mở đăng ký</strong>.",
      "Chọn học phần theo chương trình đào tạo của ngành.",
      "Tối đa <strong>24 tín chỉ</strong> mỗi học kỳ, tối thiểu 12 tín chỉ.",
      "Xác nhận và không chỉnh sửa được sau khi hết thời gian mở cổng."
    ],
    sources: [{ label: "Sổ tay sinh viên 2025 — Chương 3", url: "#" }]
  }
];

function wait(ms){ return new Promise(r => setTimeout(r, ms)); }

async function mockAsk(question){
  await wait(900 + Math.random() * 700);
  const q = question.toLowerCase();

  // gõ câu có chữ "timeout" hoặc "lỗi mạng" để demo 2 trạng thái lỗi khác nhau
  if (q.includes("timeout")){
    await wait(TIMEOUT_MS + 500); // sẽ tự bị AbortController huỷ trước khi tới đây
  }
  if (q.includes("lỗi mạng")){
    const e = new Error("network");
    e.kind = "network";
    throw e;
  }

  const hit = mockKnowledgeBase.find(item => item.keywords.some(k => q.includes(k)));
  if (hit) return { invalid: false, ...hit };
  return { invalid: true };
}

// ---------- API client thật ----------
const apiClient = {
  async ask(question){
    if (USE_MOCK) return mockAsk(question);

    let res;
    try{
      res = await fetchWithTimeout(CHAT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });
    } catch(err){
      throw err; // giữ nguyên err.kind = 'timeout' | 'network'
    }

    if (!res.ok){
      const e = new Error("server_error");
      e.kind = "network";
      e.status = res.status;
      throw e;
    }

    const data = await res.json();
    // Hợp đồng API kỳ vọng từ backend:
    // { invalid: false, paragraphs: string[], list?: string[], sources: [{label,url}] }
    // hoặc { invalid: true }
    return data;
  },

  async sendFeedback(payload){
    if (USE_MOCK){
      await wait(300);
      console.info("[mock feedback]", payload);
      return { ok: true };
    }
    const res = await fetchWithTimeout(FEEDBACK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }, 8000);
    if (!res.ok) throw new Error("feedback_failed");
    return res.json();
  }
};

// ---------- DOM refs ----------
const emptyState    = document.getElementById('emptyState');
const thread         = document.getElementById('thread');
const chatForm        = document.getElementById('chatForm');
const chatInput       = document.getElementById('chatInput');
const inputError      = document.getElementById('inputError');
const sendBtn         = document.getElementById('sendBtn');
const errorBanner     = document.getElementById('errorBanner');
const errorBannerText = errorBanner.querySelector('span');
const retryBtn        = document.getElementById('retryBtn');
const newChatBtn      = document.getElementById('newChatBtn');
const themeToggle     = document.getElementById('themeToggle');
const apiBadge        = document.getElementById('apiBadge');
const sourcesEmpty    = document.getElementById('sourcesEmpty');
const sourcesContent  = document.getElementById('sourcesContent');
const sourceList      = document.getElementById('sourceList');
const historyItems    = document.querySelectorAll('.history-item');

let lastFailedQuestion = null;

apiBadge.textContent = USE_MOCK ? 'MOCK' : 'LIVE';
apiBadge.classList.toggle('is-live', !USE_MOCK);

// ---------- Theme toggle ----------
themeToggle.addEventListener('click', () => {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
});

// ---------- New chat ----------
newChatBtn.addEventListener('click', () => resetThread());

function resetThread(){
  thread.innerHTML = '';
  thread.hidden = true;
  emptyState.hidden = false;
  errorBanner.hidden = true;
  sourcesEmpty.hidden = false;
  sourcesContent.hidden = true;
  historyItems.forEach(h => h.classList.remove('is-active'));
  chatInput.focus();
}

// ---------- History items (demo: load lại câu hỏi đó) ----------
historyItems.forEach(item => {
  item.addEventListener('click', () => {
    historyItems.forEach(h => h.classList.remove('is-active'));
    item.classList.add('is-active');
    sendQuestion(item.dataset.title);
  });
});

// ---------- Suggestion cards (empty state) ----------
document.querySelectorAll('.suggest-card').forEach(card => {
  card.addEventListener('click', () => sendQuestion(card.dataset.q));
});

// ---------- Helpers ----------
function escapeHtml(str){
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
function scrollToBottom(){ thread.scrollTop = thread.scrollHeight; }

function renderSources(sources){
  if (!sources || !sources.length){
    sourcesEmpty.hidden = false;
    sourcesContent.hidden = true;
    return;
  }
  sourceList.innerHTML = sources.map(s => `
    <div class="source-item">
      <span>${escapeHtml(s.label)}</span>
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M5.5 8.5L8.5 5.5M6 4.5L6.7 3.8C7.7 2.8 9.3 2.8 10.2 3.8C11.2 4.7 11.2 6.3 10.2 7.2L9.5 8M8 9.5L7.3 10.2C6.3 11.2 4.7 11.2 3.8 10.2C2.8 9.3 2.8 7.7 3.8 6.7L4.5 6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
      </svg>
    </div>`).join('');
  sourcesEmpty.hidden = true;
  sourcesContent.hidden = false;
}

// ---------- Build a turn (question pill + answer card) ----------
function buildTurn(questionText){
  emptyState.hidden = true;
  thread.hidden = false;

  const turn = document.createElement('div');
  turn.className = 'turn';
  turn.dataset.question = questionText;
  turn.innerHTML = `
    <div class="q-row">
      <div class="q-pill">
        <span>${escapeHtml(questionText)}</span>
        <svg class="edit-ico" width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10.5 2.5L12.5 4.5L5 12H3V10L10.5 2.5Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="avatar avatar--user">SV</div>
    </div>
    <div class="a-row">
      <div class="avatar avatar--bot">A</div>
      <div class="a-card is-loading">
        <div class="typing-dots"><span></span><span></span><span></span></div>
        <p></p>
      </div>
    </div>
  `;
  thread.appendChild(turn);
  scrollToBottom();
  return turn;
}

function resolveTurn(turn, result){
  const card = turn.querySelector('.a-card');
  card.classList.remove('is-loading');

  if (result.invalid){
    card.classList.add('is-invalid');
    card.innerHTML = `
      <p>Mình chưa hiểu rõ câu hỏi này. Bạn có thể hỏi cụ thể hơn, ví dụ về học phí, lịch thi hoặc đăng ký môn học không?</p>
      <div class="a-meta">
        <button class="fb-btn" data-fb="up" aria-label="Hữu ích">👍</button>
        <button class="fb-btn" data-fb="down" aria-label="Không hữu ích">👎</button>
      </div>`;
    turn.insertAdjacentHTML('beforeend', `
      <div class="followups">
        <button class="followup-btn" data-q="Học phí kỳ này là bao nhiêu?">Hỏi về học phí</button>
        <button class="followup-btn" data-q="Lịch thi cuối kỳ ở đâu?">Hỏi về lịch thi</button>
        <button class="followup-btn" data-q="Làm sao để đăng ký môn học?">Hỏi về đăng ký môn</button>
      </div>`);
    renderSources([]);
    scrollToBottom();
    return;
  }

  const paraHtml = (result.paragraphs || []).map(p => `<p>${p}</p>`).join('');
  const listHtml = result.list && result.list.length
    ? `<ol>${result.list.map(li => `<li>${li}</li>`).join('')}</ol>`
    : '';
  const answerText = (result.paragraphs || []).join(' ') +
    (result.list ? ' ' + result.list.join(' ') : '');
  turn.dataset.answer = answerText;

  card.innerHTML = `
    ${paraHtml}
    ${listHtml}
    <div class="a-meta">
      <button class="fb-btn" data-fb="up" aria-label="Hữu ích">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 14H3.5a1 1 0 01-1-1V8a1 1 0 011-1H6m0 7V7m0 7h6.2a1.5 1.5 0 001.47-1.8l-.9-4.5A1.5 1.5 0 0011.3 6.4H9V3.5a1.5 1.5 0 00-3 0V6L4.5 7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <button class="fb-btn" data-fb="down" aria-label="Không hữu ích">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="transform:rotate(180deg)"><path d="M6 14H3.5a1 1 0 01-1-1V8a1 1 0 011-1H6m0 7V7m0 7h6.2a1.5 1.5 0 001.47-1.8l-.9-4.5A1.5 1.5 0 0011.3 6.4H9V3.5a1.5 1.5 0 00-3 0V6L4.5 7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </div>`;

  turn.insertAdjacentHTML('beforeend', `
    <div class="followups">
      <button class="followup-btn" data-followup="shorter">Trả lời ngắn gọn hơn</button>
      <button class="followup-btn" data-followup="example">Cho ví dụ cụ thể</button>
      <button class="followup-btn" data-followup="more">Nói thêm chi tiết</button>
    </div>`);

  renderSources(result.sources);
  scrollToBottom();
}

function removeTurn(turn){ turn.remove(); }

function showError(kind){
  errorBannerText.textContent = kind === 'timeout'
    ? '⏱ Yêu cầu quá thời gian chờ (timeout). Máy chủ phản hồi chậm, vui lòng thử lại.'
    : '⚠ Không thể kết nối máy chủ. Vui lòng kiểm tra mạng và thử lại.';
  errorBanner.hidden = false;
}

// ---------- Core send flow ----------
async function sendQuestion(rawText){
  const text = (rawText || '').trim();

  // Validate câu hỏi rỗng
  if (!text){
    inputError.hidden = false;
    chatInput.classList.add('is-invalid');
    chatInput.focus();
    return;
  }
  inputError.hidden = true;
  chatInput.classList.remove('is-invalid');

  errorBanner.hidden = true;
  chatInput.value = '';
  sendBtn.disabled = true;

  const turn = buildTurn(text);

  try{
    const result = await apiClient.ask(text);
    resolveTurn(turn, result);
  } catch(err){
    removeTurn(turn);
    lastFailedQuestion = text;
    showError(err.kind || 'network');
  } finally{
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

// ---------- Events ----------
chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  sendQuestion(chatInput.value);
});

chatInput.addEventListener('input', () => {
  if (!inputError.hidden && chatInput.value.trim()){
    inputError.hidden = true;
    chatInput.classList.remove('is-invalid');
  }
});

retryBtn.addEventListener('click', () => {
  if (lastFailedQuestion) sendQuestion(lastFailedQuestion);
  else errorBanner.hidden = true;
});

// feedback + follow-up buttons (event delegation)
thread.addEventListener('click', async (e) => {
  const fb = e.target.closest('.fb-btn');
  if (fb){
    const group = fb.parentElement;
    group.querySelectorAll('.fb-btn').forEach(b => b.classList.remove('is-selected'));
    fb.classList.add('is-selected');

    const turn = fb.closest('.turn');
    const payload = {
      question: turn?.dataset.question || '',
      answer: turn?.dataset.answer || '',
      vote: fb.dataset.fb // 'up' | 'down'
    };
    try{
      await apiClient.sendFeedback(payload);
    } catch(err){
      // Không chặn UI vì feedback là phụ — chỉ log để debug
      console.warn('Gửi feedback thất bại:', err);
    }
    return;
  }

  const follow = e.target.closest('.followup-btn');
  if (follow){
    if (follow.dataset.q){
      sendQuestion(follow.dataset.q);
      return;
    }
    const kind = follow.dataset.followup;
    const prefixMap = {
      shorter: "(trả lời ngắn gọn hơn) ",
      example: "(cho ví dụ cụ thể) ",
      more: "(nói thêm chi tiết) "
    };
    const baseQuestion = follow.closest('.turn').querySelector('.q-pill span').textContent;
    sendQuestion((prefixMap[kind] || '') + baseQuestion);
  }
});
