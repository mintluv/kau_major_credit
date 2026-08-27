// State management
let state = {
  courses: [],
  scale: 4.5
};

// Standard Grade Point Maps
const GRADE_MAPS = {
  4.5: {
    "A+": 4.5, "A0": 4.0, "A": 4.0,
    "B+": 3.5, "B0": 3.0, "B": 3.0,
    "C+": 2.5, "C0": 2.0, "C": 2.0,
    "D+": 1.5, "D0": 1.0, "D": 1.0,
    "F": 0.0, "P": null, "NP": null
  },
  4.3: {
    "A+": 4.3, "A0": 4.0, "A-": 3.7, "A": 4.0,
    "B+": 3.3, "B0": 3.0, "B-": 2.7, "B": 3.0,
    "C+": 2.3, "C0": 2.0, "C-": 1.7, "C": 2.0,
    "D+": 1.3, "D0": 1.0, "D-": 0.7, "D": 1.0,
    "F": 0.0, "P": null, "NP": null
  },
  4.0: {
    "A+": 4.0, "A0": 4.0, "A-": 3.7, "A": 4.0,
    "B+": 3.3, "B0": 3.0, "B-": 2.7, "B": 3.0,
    "C+": 2.3, "C0": 2.0, "C-": 1.7, "C": 2.0,
    "D+": 1.3, "D0": 1.0, "D-": 0.7, "D": 1.0,
    "F": 0.0, "P": null, "NP": null
  }
};

// Dynamic Backend API URL Resolver for GitHub Pages & Cloudflare Tunnel
let autoDetectedBackendUrl = "";

async function loadAutoBackendUrl() {
  try {
    const res = await fetch(`backend_url.json?t=${Date.now()}`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.backend_url) {
        autoDetectedBackendUrl = data.backend_url.trim().replace(/\/+$/, "");
        console.log("🔗 Auto-detected live backend URL:", autoDetectedBackendUrl);
        updateServerBadge();
      }
    }
  } catch (e) {
    // ignore
  }
}

function updateServerBadge() {
  const badge = document.getElementById("server-status-badge");
  const activeUrl = localStorage.getItem("kau_gpa_backend_url") || autoDetectedBackendUrl;
  if (badge) {
    if (activeUrl) {
      badge.innerHTML = `<span style="color:#22c55e;">●</span> 서버 연동됨`;
      badge.title = `연결 주소: ${activeUrl}`;
    } else {
      badge.innerHTML = `<span style="color:#94a3b8;">○</span> 로컬 모드`;
    }
  }
}

function getApiUrl(endpoint) {
  let serverUrl = localStorage.getItem("kau_gpa_backend_url") || autoDetectedBackendUrl || "";
  serverUrl = serverUrl.trim().replace(/\/+$/, "");

  if (serverUrl) {
    return `${serverUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
  }
  return endpoint;
}

document.addEventListener("DOMContentLoaded", () => {
  loadAutoBackendUrl();
  initPresets();
  initTabs();
  initAdvancedToggle();
  initForms();
  initToolbar();
  initSimulator();
  initServerConfig();
});

// Server Config Dialog
function initServerConfig() {
  const dialog = document.getElementById("server-config-dialog");
  const btnOpen = document.getElementById("btn-server-config");
  const btnClose = document.getElementById("btn-close-server-config");
  const btnSave = document.getElementById("btn-save-server-config");
  const inputUrl = document.getElementById("input-backend-url");

  const currentUrl = localStorage.getItem("kau_gpa_backend_url") || "";
  if (inputUrl) inputUrl.value = currentUrl;

  if (btnOpen && dialog) {
    btnOpen.addEventListener("click", () => {
      dialog.style.display = "block";
      if (typeof dialog.showModal === "function") {
        try { dialog.showModal(); } catch (e) {}
      }
    });
  }

  const closeDialog = () => {
    dialog.style.display = "none";
    if (typeof dialog.close === "function") {
      try { dialog.close(); } catch (e) {}
    }
  };

  if (btnClose) btnClose.addEventListener("click", closeDialog);

  if (btnSave && inputUrl) {
    btnSave.addEventListener("click", () => {
      const val = inputUrl.value.trim().replace(/\/+$/, "");
      if (val) {
        localStorage.setItem("kau_gpa_backend_url", val);
        alert(`✅ 백엔드 서버 주소가 저장되었습니다:\n${val}`);
      } else {
        localStorage.removeItem("kau_gpa_backend_url");
        alert("ℹ️ 기본 로컬 상대 경로로 재설정되었습니다.");
      }
      closeDialog();
    });
  }
}

// Preset Buttons
function initPresets() {
  const btnKau = document.getElementById("btn-preset-kau");
  const btnGeneric = document.getElementById("btn-preset-generic");
  const portalUrlInput = document.getElementById("portal_url");
  const idSelInput = document.getElementById("id_selector");
  const pwSelInput = document.getElementById("pw_selector");
  const loginBtnSelInput = document.getElementById("login_btn_selector");

  btnKau.addEventListener("click", () => {
    btnKau.classList.add("active");
    btnGeneric.classList.remove("active");
    portalUrlInput.value = "https://nportal.kau.ac.kr/webcrea/GB03/mdi/login.html";
    idSelInput.value = "input[id*='inputId'], #mainForm3\\.inputId, #mainForm4\\.inputId, input[type='text']";
    pwSelInput.value = "input[id*='inputPassword'], #mainForm3\\.inputPassword, #mainForm4\\.inputPassword, input[type='password']";
    loginBtnSelInput.value = "input[id*='button'], button[type='submit'], input[type='submit'], #btn_login, .login_btn";
  });

  btnGeneric.addEventListener("click", () => {
    btnGeneric.classList.add("active");
    btnKau.classList.remove("active");
    portalUrlInput.value = "";
    portalUrlInput.placeholder = "https://portal.university.ac.kr/login";
  });
}

// Tab Switching
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      
      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      document.getElementById(tabId).classList.add("active");
    });
  });
}

// Advanced Selector Toggle
function initAdvancedToggle() {
  const toggleBtn = document.getElementById("toggle-advanced");
  const section = document.getElementById("advanced-section");
  const chevron = document.getElementById("adv-chevron");

  toggleBtn.addEventListener("click", () => {
    const isHidden = section.classList.contains("hidden");
    if (isHidden) {
      section.classList.remove("hidden");
      chevron.style.transform = "rotate(180deg)";
    } else {
      section.classList.add("hidden");
      chevron.style.transform = "rotate(0deg)";
    }
  });
}

// Forms initialization
function initForms() {
  // Global submit prevention across all forms
  document.querySelectorAll("form").forEach(f => {
    f.addEventListener("submit", (e) => e.preventDefault());
  });

  // Crawl Form Submit & Button Click
  const crawlForm = document.getElementById("crawl-form");
  const btnSubmitCrawl = document.getElementById("btn-submit-crawl");

  const runCrawl = async (e) => {
    if (e) e.preventDefault();
    await handleCrawl();
  };

  if (crawlForm) crawlForm.addEventListener("submit", runCrawl);
  if (btnSubmitCrawl) btnSubmitCrawl.addEventListener("click", runCrawl);

  // Text Paste Parse Submit
  const btnParseText = document.getElementById("btn-parse-text");
  if (btnParseText) {
    btnParseText.addEventListener("click", async (e) => {
      e.preventDefault();
      const text = document.getElementById("paste-text").value.trim();
      if (!text) {
        alert("성적표 텍스트를 먼저 입력해 주세요!");
        return;
      }

      try {
        const res = await fetch(getApiUrl("/api/parse-text"), {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "69420"
          },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        if (data.success && data.courses.length > 0) {
          addCourses(data.courses);
          alert(`🎉 ${data.courses.length}개 과목이 자동으로 파싱되어 추가되었습니다!`);
        } else {
          alert("⚠️ 텍스트에서 과목 및 성적 정보를 파싱하지 못했습니다. 수동 입력을 이용해 보세요.");
        }
      } catch (err) {
        alert("오류가 발생했습니다: " + err.message);
      }
    });
  }

  // Manual Input Submit & Button Click
  const manualForm = document.getElementById("manual-form");
  const btnManualAdd = document.getElementById("btn-manual-add");

  const runManualAdd = (e) => {
    if (e) e.preventDefault();
    const nameInput = document.getElementById("m-name");
    const name = nameInput ? nameInput.value.trim() : "";
    const credits = parseFloat(document.getElementById("m-credits").value);
    const grade = document.getElementById("m-grade").value;
    const classification = document.getElementById("m-class").value;
    const isMajor = document.getElementById("m-is-major").checked;

    if (!name) {
      alert("과목명을 입력해 주세요!");
      return;
    }

    const newCourse = {
      id: Math.random().toString(36).substring(2, 9),
      name,
      credits,
      grade,
      is_major: isMajor,
      classification
    };

    addCourses([newCourse]);
    if (nameInput) nameInput.value = "";
  };

  if (manualForm) manualForm.addEventListener("submit", runManualAdd);
  if (btnManualAdd) btnManualAdd.addEventListener("click", runManualAdd);
}

// Crawling Execution Handler (Real-time Streaming with Fallback)
let isCrawling = false;

window.handleCrawl = async function() {
  if (isCrawling) return; // Prevent double execution
  
  const userIdInput = document.getElementById("user_id");
  const passwordInput = document.getElementById("password");
  const portalUrlInput = document.getElementById("portal_url");

  const userId = userIdInput ? userIdInput.value.trim() : "";
  const password = passwordInput ? passwordInput.value : "";
  const portalUrl = portalUrlInput ? portalUrlInput.value.trim() : "";

  if (!userId) {
    alert("학번(아이디)을 입력해 주세요!");
    if (userIdInput) userIdInput.focus();
    return;
  }

  if (!password) {
    alert("비밀번호를 입력해 주세요!");
    if (passwordInput) passwordInput.focus();
    return;
  }

  isCrawling = true;

  const terminalCard = document.getElementById("terminal-card");
  const terminalBody = document.getElementById("terminal-body");
  const statusIndicator = document.getElementById("status-indicator");
  const submitBtn = document.getElementById("btn-submit-crawl");

  if (terminalCard) {
    terminalCard.classList.remove("hidden");
    terminalCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  if (terminalBody) {
    terminalBody.textContent = "🚀 서버 연결 및 Playwright 웹 크롤러 세션 준비 중...\n";
  }

  if (statusIndicator) {
    statusIndicator.textContent = "진행 중...";
    statusIndicator.style.background = "var(--sun)";
    statusIndicator.style.color = "var(--on-sun)";
  }

  if (submitBtn) submitBtn.disabled = true;

  // 기존 성적 리스트 즉시 초기화
  state.courses = [];
  renderApp();

  const payload = {
    portal_url: portalUrl || "https://nportal.kau.ac.kr/webcrea/GB03/mdi/login.html",
    user_id: userId,
    password: password,
    headless: true,
    id_selector: document.getElementById("id_selector") ? document.getElementById("id_selector").value : "",
    pw_selector: document.getElementById("pw_selector") ? document.getElementById("pw_selector").value : "",
    login_btn_selector: document.getElementById("login_btn_selector") ? document.getElementById("login_btn_selector").value : "",
    grade_url: (document.getElementById("grade_url") && document.getElementById("grade_url").value) || null
  };

  function appendLog(text) {
    if (terminalBody) {
      terminalBody.textContent += text + "\n";
      terminalBody.scrollTop = terminalBody.scrollHeight;
    }
  }

  try {
    // Attempt real-time SSE streaming
    const response = await fetch(getApiUrl("/api/crawl-stream"), {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "69420"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok || !response.body) {
      throw new Error(`HTTP ${response.status}: 스트리밍 응답 대기 중`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let finalResult = null;

    if (terminalBody) terminalBody.textContent = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data:")) continue;

        try {
          const jsonStr = trimmed.replace(/^data:\s*/, "");
          const ev = JSON.parse(jsonStr);

          if (ev.type === "log") {
            appendLog(ev.message);
          } else if (ev.type === "done") {
            finalResult = ev.result;
          }
        } catch (e) {
          // ignore
        }
      }
    }

    if (finalResult) {
      if (finalResult.success) {
        if (statusIndicator) {
          statusIndicator.textContent = "수집 완료";
          statusIndicator.style.background = "#b8f0ca";
          statusIndicator.style.color = "#164a25";
        }
        if (finalResult.courses && finalResult.courses.length > 0) {
          addCourses(finalResult.courses);
        }
      } else {
        if (statusIndicator) {
          statusIndicator.textContent = "오류 발생";
          statusIndicator.style.background = "var(--rose)";
          statusIndicator.style.color = "var(--on-rose)";
        }
        appendLog(`\n❌ 크롤링 실패: ${finalResult.error || "알 수 없는 오류"}`);
      }
    }

  } catch (err) {
    // Fallback to standard /api/crawl endpoint
    appendLog(`ℹ️ 실시간 스트림 대신 표준 방식으로 전환하여 조회합니다...`);
    try {
      const fbRes = await fetch(getApiUrl("/api/crawl"), {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "69420"
        },
        body: JSON.stringify(payload)
      });
      const data = await fbRes.json();
      if (data.logs) {
        if (terminalBody) terminalBody.textContent = data.logs.join("\n") + "\n";
      }
      if (data.success) {
        if (statusIndicator) {
          statusIndicator.textContent = "수집 완료";
          statusIndicator.style.background = "#b8f0ca";
          statusIndicator.style.color = "#164a25";
        }
        if (data.courses && data.courses.length > 0) {
          addCourses(data.courses);
        }
      } else {
        if (statusIndicator) {
          statusIndicator.textContent = "오류 발생";
          statusIndicator.style.background = "var(--rose)";
          statusIndicator.style.color = "var(--on-rose)";
        }
        appendLog(`\n❌ 크롤링 실패: ${data.error || "알 수 없는 오류"}`);
      }
    } catch (fbErr) {
      if (statusIndicator) {
        statusIndicator.textContent = "통신 에러";
        statusIndicator.style.background = "var(--rose)";
        statusIndicator.style.color = "var(--on-rose)";
      }
      appendLog(`\n❌ 서버 통신 오류: ${fbErr.message}`);
    }
  } finally {
    isCrawling = false;
    if (submitBtn) submitBtn.disabled = false;
  }
};

// Add Courses to State
function addCourses(newCourses) {
  const processed = newCourses.map(c => {
    const cls = c.classification || c.type || "";
    const name = c.name || "";
    // Any item containing '전공', '전필', '전선' is strictly treated as Major
    const isMajor = c.is_major || 
                    cls.includes("전공") || cls.includes("전필") || cls.includes("전선") || 
                    name.includes("전공필수") || name.includes("전공선택");
    return {
      ...c,
      is_major: isMajor,
      classification: cls || (isMajor ? "전공" : "교양")
    };
  });
  state.courses = [...state.courses, ...processed];
  renderApp();
}

// Toolbar & Controls
// Toolbar & Controls
function initToolbar() {
  const scaleSelect = document.getElementById("scale-select");
  if (scaleSelect) {
    scaleSelect.addEventListener("change", (e) => {
      state.scale = parseFloat(e.target.value);
      document.getElementById("scale-display-1").textContent = `/ ${state.scale.toFixed(2)}`;
      document.getElementById("scale-display-2").textContent = `/ ${state.scale.toFixed(2)}`;
      renderApp();
    });
  }

  // Clear all
  const btnClearAll = document.getElementById("btn-clear-all");
  if (btnClearAll) {
    btnClearAll.addEventListener("click", (e) => {
      if (e) e.preventDefault();
      if (confirm("등록된 모든 과목 성적을 삭제하시겠습니까?")) {
        state.courses = [];
        renderApp();
      }
    });
  }

  // Load KAU Student Example Sample Data
  const btnLoadSample = document.getElementById("btn-load-sample");
  if (btnLoadSample) {
    btnLoadSample.addEventListener("click", (e) => {
      if (e) e.preventDefault();
      state.courses = [];
      addCourses([
        // 2018-2 (1학년)
        { id: "k1", name: "물리및실험II", credits: 3.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2018년 2학기" },
        { id: "k2", name: "선형대수학", credits: 3.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2018년 2학기" },
        { id: "k3", name: "영어커뮤니케이션Ⅱ", credits: 2.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2018년 2학기" },
        { id: "k4", name: "항공우주산업개론", credits: 2.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2018년 2학기" },
        { id: "k5", name: "기초공학설계", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2018년 2학기" },
        { id: "k6", name: "컴퓨터프로그래밍", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2018년 2학기" },

        // 2019-1 (2학년)
        { id: "k7", name: "교양글쓰기", credits: 2.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2019년 1학기" },
        { id: "k8", name: "항공우주학개론", credits: 2.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2019년 1학기" },
        { id: "k9", name: "미분적분학", credits: 3.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2019년 1학기" },
        { id: "k10", name: "물리및실험I", credits: 3.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2019년 1학기" },
        { id: "k11", name: "컴퓨팅적 사고와 문제해결", credits: 3.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2019년 1학기" },
        { id: "k12", name: "천체와 우주의 이해", credits: 3.0, grade: "A+", is_major: false, classification: "교양선택", year_semester: "2019년 1학기" },
        { id: "k13", name: "영어커뮤니케이션Ⅰ", credits: 2.0, grade: "A+", is_major: false, classification: "교양필수", year_semester: "2019년 1학기" },

        // 2022-1 & 2학기 (3학년)
        { id: "k14", name: "사회봉사", credits: 1.0, grade: "P", is_major: false, classification: "교양선택", year_semester: "2022년 1학기" },
        { id: "k15", name: "글로벌문화와 소통", credits: 3.0, grade: "A+", is_major: false, classification: "교양선택", year_semester: "2022년 1학기" },
        { id: "k16", name: "공학수학Ⅱ", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2022년 1학기" },
        { id: "k17", name: "전자기학Ⅰ", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2022년 1학기" },
        { id: "k18", name: "회로이론Ⅰ", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2022년 1학기" },
        { id: "k19", name: "디지털논리회로", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2022년 1학기" },
        { id: "k20", name: "이산수학", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2022년 1학기" },

        { id: "k21", name: "현대사회와 윤리문제", credits: 3.0, grade: "A+", is_major: false, classification: "교양선택", year_semester: "2022년 2학기" },
        { id: "k22", name: "사회봉사", credits: 1.0, grade: "P", is_major: false, classification: "교양선택", year_semester: "2022년 2학기" },
        { id: "k23", name: "항공전자정보 세미나", credits: 1.0, grade: "P", is_major: true, classification: "전공필수", year_semester: "2022년 2학기" },
        { id: "k24", name: "기초회로및디지털실험", credits: 2.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2022년 2학기" },
        { id: "k25", name: "회로이론Ⅱ", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2022년 2학기" },
        { id: "k26", name: "물리전자공학", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2022년 2학기" },
        { id: "k27", name: "자료구조", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2022년 2학기" },
        { id: "k28", name: "디지털시스템설계", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2022년 2학기" },

        // 2023-1 & 2학기 (4학년)
        { id: "k29", name: "동양철학의 이해", credits: 3.0, grade: "A+", is_major: false, classification: "교양선택", year_semester: "2023년 1학기" },
        { id: "k30", name: "전자회로Ⅰ", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2023년 1학기" },
        { id: "k31", name: "전자회로실험", credits: 2.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2023년 1학기" },
        { id: "k32", name: "신호 및 시스템", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2023년 1학기" },
        { id: "k33", name: "반도체소자", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2023년 1학기" },
        { id: "k34", name: "마이크로프로세서", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2023년 1학기" },

        { id: "k35", name: "현대감성의 디자인과 예술", credits: 3.0, grade: "A+", is_major: false, classification: "교양선택", year_semester: "2023년 2학기" },
        { id: "k36", name: "기업가정신과 취창업전략", credits: 2.0, grade: "P", is_major: false, classification: "교양선택", year_semester: "2023년 2학기" },
        { id: "k37", name: "공학수학 I", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2023년 2학기" },
        { id: "k38", name: "창업형 종합설계 I", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2023년 2학기" },
        { id: "k39", name: "운영체제", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2023년 2학기" },
        { id: "k40", name: "전자HW설계", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2023년 2학기" },

        // 2024-1 & 2학기
        { id: "k41", name: "골프", credits: 2.0, grade: "A+", is_major: false, classification: "교양선택", year_semester: "2024년 1학기" },
        { id: "k42", name: "창업형 종합설계 II", credits: 3.0, grade: "A+", is_major: true, classification: "전공필수", year_semester: "2024년 1학기" },
        { id: "k43", name: "VLSI 시스템", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2024년 1학기" },
        { id: "k44", name: "고급시스템프로그래밍", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2024년 1학기" },
        { id: "k45", name: "빅데이터 응용", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2024년 1학기" },

        { id: "k46", name: "자기 계발과 표현", credits: 3.0, grade: "A+", is_major: false, classification: "교양선택", year_semester: "2024년 2학기" },
        { id: "k47", name: "멀티미디어공학", credits: 3.0, grade: "A+", is_major: true, classification: "전공선택", year_semester: "2024년 2학기" }
      ]);
    });
  }

  // Export Text File (2-semester counter per academic year)
  const btnExport = document.getElementById("btn-export-json");
  if (btnExport) {
    btnExport.addEventListener("click", (e) => {
      if (e) e.preventDefault();
      if (!state.courses || state.courses.length === 0) {
        alert("내보낼 성적 데이터가 없습니다.");
        return;
      }

      const gradeMap = GRADE_MAPS[state.scale] || GRADE_MAPS[4.5];
      const yearGroupList = getAcademicYearGroups(state.courses, state.scale);
      const lines = [];
      const today = new Date().toLocaleDateString("ko-KR");

      lines.push(`학년별 전공 성적 요약 (${today} / ${state.scale.toFixed(1)}점 만점)`);

      yearGroupList.forEach(data => {
        const gpa = data.majorCreditsGpa > 0
          ? (data.majorPoints / data.majorCreditsGpa).toFixed(2)
          : "0.00";

        lines.push("");
        lines.push(`${data.yearLabel} (${data.semesterRangeStr}) (전공 평점: ${gpa} / ${state.scale.toFixed(2)})`);

        if (data.majorCourses.length === 0) {
          lines.push("전공 과목 없음");
        } else {
          const courseStr = data.majorCourses.map(c => `${c.name} (${c.grade})`).join("  ");
          lines.push(courseStr);
        }
      });

      let totalMajorPoints = 0, totalMajorCredits = 0;
      state.courses.forEach(c => {
        if (c.is_major) {
          const pts = gradeMap[c.grade];
          if (pts !== null && pts !== undefined) {
            totalMajorPoints += pts * c.credits;
            totalMajorCredits += c.credits;
          }
        }
      });
      const totalGpa = totalMajorCredits > 0 ? (totalMajorPoints / totalMajorCredits).toFixed(2) : "0.00";

      lines.push("");
      lines.push(`총 전공 평점: ${totalGpa} / ${state.scale.toFixed(2)}  (반영학점 ${totalMajorCredits}학점)`);

      const text = lines.join("\n");
      const blob = new Blob(["\uFEFF" + text], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `전공성적요약_${new Date().toISOString().slice(0, 10)}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  // Import JSON
  const fileInput = document.getElementById("file-import");
  const btnImport = document.getElementById("btn-import-json");
  if (btnImport && fileInput) {
    btnImport.addEventListener("click", (e) => {
      if (e) e.preventDefault();
      fileInput.click();
    });
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const imported = JSON.parse(event.target.result);
          if (Array.isArray(imported)) {
            state.courses = [];
            addCourses(imported);
            alert("🎉 성적 데이터를 성공적으로 불러왔습니다.");
          }
        } catch (err) {
          alert("올바르지 않은 JSON 파일입니다.");
        }
      };
      reader.readAsText(file);
    });
  }
}

// Goal Simulator Logic
function initSimulator() {
  const btnRun = document.getElementById("btn-run-simulation");
  btnRun.addEventListener("click", async (e) => {
    e.preventDefault();
    const targetGpa = parseFloat(document.getElementById("sim-target-gpa").value);
    const remainingCredits = parseFloat(document.getElementById("sim-remaining-credits").value);

    // Calculate current major GPA
    const majorCourses = state.courses.filter(c => c.is_major);
    let curPoints = 0;
    let curCredits = 0;
    const gradeMap = GRADE_MAPS[state.scale] || GRADE_MAPS[4.5];

    majorCourses.forEach(c => {
      const pts = gradeMap[c.grade];
      if (pts !== null && pts !== undefined) {
        curPoints += pts * c.credits;
        curCredits += c.credits;
      }
    });

    const curMajorGpa = curCredits > 0 ? (curPoints / curCredits) : 0;

    try {
      const res = await fetch(getApiUrl("/api/simulate-goal"), {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "69420"
        },
        body: JSON.stringify({
          current_major_gpa: curMajorGpa,
          current_major_credits: curCredits,
          target_major_gpa: targetGpa,
          remaining_major_credits: remainingCredits,
          scale: state.scale
        })
      });

      const data = await res.json();
      const resultBox = document.getElementById("sim-result-box");
      const resultText = document.getElementById("sim-result-text");

      resultBox.classList.remove("hidden");
      resultText.textContent = data.message;
      if (data.possible) {
        resultBox.style.borderColor = "#10b981";
      } else {
        resultBox.style.borderColor = "#ef4444";
      }
    } catch (err) {
      alert("시뮬레이션 중 오류가 발생했습니다.");
    }
  });
}

// Render Application UI & Calculate GPA
function renderApp() {
  const gradeMap = GRADE_MAPS[state.scale] || GRADE_MAPS[4.5];

  let majorPoints = 0;
  let majorCreditsForGpa = 0;
  let majorTotalCredits = 0;

  let overallPoints = 0;
  let overallCreditsForGpa = 0;
  let overallTotalCredits = 0;

  state.courses.forEach(c => {
    const pts = gradeMap[c.grade];
    const isP = c.grade === "P";

    // Count credits towards total completed credits if not F/NP
    if (c.grade !== "F" && c.grade !== "NP") {
      overallTotalCredits += c.credits;
      if (c.is_major) majorTotalCredits += c.credits;
    }

    if (pts !== null && pts !== undefined) {
      overallPoints += pts * c.credits;
      overallCreditsForGpa += c.credits;

      if (c.is_major) {
        majorPoints += pts * c.credits;
        majorCreditsForGpa += c.credits;
      }
    }
  });

  const majorGpa = majorCreditsForGpa > 0 ? (majorPoints / majorCreditsForGpa) : 0;
  const overallGpa = overallCreditsForGpa > 0 ? (overallPoints / overallCreditsForGpa) : 0;

  // Update UI Counters
  document.getElementById("val-major-gpa").textContent = majorGpa.toFixed(2);
  document.getElementById("val-overall-gpa").textContent = overallGpa.toFixed(2);

  document.getElementById("val-major-credits-info").innerHTML = `전공 이수: <strong>${majorTotalCredits}</strong> 학점 (평점 반영 ${majorCreditsForGpa}학점)`;
  document.getElementById("val-overall-credits-info").innerHTML = `총 이수: <strong>${overallTotalCredits}</strong> 학점 (평점 반영 ${overallCreditsForGpa}학점)`;

  document.getElementById("course-count").textContent = state.courses.length;

  // Render Academic Year Major Breakdown
  renderYearBreakdown();

  // Render Table Rows
  const tbody = document.getElementById("course-table-body");
  if (state.courses.length === 0) {
    tbody.innerHTML = `
      <tr class="empty-row">
        <td colspan="6">
          <div class="empty-state">
            <i class="fa-solid fa-folder-open"></i>
            <p>등록된 과목이 없습니다.<br>왼쪽에서 포털 성적 수집, 텍스트 붙여넣기 또는 과목을 직접 추가해 보세요!</p>
          </div>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = state.courses.map(c => `
    <tr>
      <td>
        <button type="button" class="toggle-major-btn ${c.is_major ? 'is-major' : 'not-major'}" onclick="toggleMajor('${c.id}')">
          ${c.is_major ? '🌸 전공' : '📘 교양'}
        </button>
      </td>
      <td><strong>${escapeHtml(c.name)}</strong></td>
      <td>
        <select onchange="updateCredits('${c.id}', this.value)">
          ${[1.0, 2.0, 3.0, 4.0].map(cr => `<option value="${cr}" ${cr === c.credits ? 'selected' : ''}>${cr}</option>`).join('')}
        </select>
      </td>
      <td>
        <select onchange="updateGrade('${c.id}', this.value)">
          ${Object.keys(gradeMap).map(g => `<option value="${g}" ${g === c.grade ? 'selected' : ''}>${g}</option>`).join('')}
        </select>
      </td>
      <td><span class="badge ${c.is_major ? 'badge-pink' : 'badge-purple'}">${escapeHtml(c.classification || (c.is_major ? '전공' : '교양'))}</span></td>
      <td>
        <button type="button" class="btn btn-danger btn-sm" onclick="deleteCourse('${c.id}')">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>
  `).join('');
}


// Academic Year Counter Helper (Counts 1 academic year for every 2 completed semesters)
function getAcademicYearGroups(courses, scale) {
  const gradeMap = GRADE_MAPS[scale] || GRADE_MAPS[4.5];

  // 1. Group courses by unique semester
  const semesterMap = {};
  courses.forEach(c => {
    const semKey = c.year_semester && c.year_semester.trim() ? c.year_semester.trim() : "미지정";
    if (!semesterMap[semKey]) {
      semesterMap[semKey] = [];
    }
    semesterMap[semKey].push(c);
  });

  // 2. Sort semesters chronologically
  function parseSemesterOrder(semStr) {
    if (!semStr || semStr === "미지정") return 999999;
    const yrMatch = semStr.match(/(\d{4})/);
    const yr = yrMatch ? parseInt(yrMatch[1], 10) : 2099;
    let semWeight = 1;
    if (semStr.includes("2학기")) semWeight = 2;
    else if (semStr.includes("여름")) semWeight = 1.5;
    else if (semStr.includes("겨울")) semWeight = 2.5;
    return yr * 10 + semWeight;
  }

  const validSems = Object.keys(semesterMap)
    .filter(k => k !== "미지정")
    .sort((a, b) => parseSemesterOrder(a) - parseSemesterOrder(b));

  const unassignedSems = Object.keys(semesterMap).filter(k => k === "미지정");

  const yearGroupList = [];
  const yearLabels = ["1학년", "2학년", "3학년", "4학년", "5학년 (초과학기)", "6학년 (초과학기)"];

  // 3. Group semesters by 2 regular semesters (1학기, 2학기) per academic year, including seasonal semesters
  const yearBuckets = [];
  let currentBucket = { regularCount: 0, sems: [] };

  validSems.forEach(sk => {
    const isRegular = sk.includes("1학기") || sk.includes("2학기");
    currentBucket.sems.push(sk);

    if (isRegular) {
      currentBucket.regularCount += 1;
    }

    // When 2 regular semesters are completed, finalize this academic year bucket
    if (currentBucket.regularCount >= 2) {
      yearBuckets.push(currentBucket);
      currentBucket = { regularCount: 0, sems: [] };
    }
  });

  if (currentBucket.sems.length > 0) {
    yearBuckets.push(currentBucket);
  }

  yearBuckets.forEach((bucket, groupIdx) => {
    const semList = bucket.sems;
    const yearLabel = groupIdx < yearLabels.length ? yearLabels[groupIdx] : `${groupIdx + 1}학년`;
    const semesterRangeStr = semList.length > 1 ? `${semList[0]} ~ ${semList[semList.length - 1]}` : (semList[0] || "");

    const groupCourses = [];
    semList.forEach(sk => {
      groupCourses.push(...semesterMap[sk]);
    });

    const g = {
      yearLabel,
      semesterRangeStr,
      majorCreditsTotal: 0,
      majorCreditsGpa: 0,
      majorPoints: 0,
      overallCreditsTotal: 0,
      overallCreditsGpa: 0,
      overallPoints: 0,
      majorCourses: []
    };

    groupCourses.forEach(c => {
      const pts = gradeMap[c.grade];
      if (c.grade !== "F" && c.grade !== "NP") {
        g.overallCreditsTotal += c.credits;
        if (c.is_major) g.majorCreditsTotal += c.credits;
      }
      if (pts !== null && pts !== undefined) {
        g.overallPoints += pts * c.credits;
        g.overallCreditsGpa += c.credits;
        if (c.is_major) {
          g.majorPoints += pts * c.credits;
          g.majorCreditsGpa += c.credits;
          g.majorCourses.push({ name: c.name, credits: c.credits, grade: c.grade, pts, classification: c.classification || "" });
        }
      } else {
        if (c.is_major) {
          g.majorCourses.push({ name: c.name, credits: c.credits, grade: c.grade, pts: null, classification: c.classification || "" });
        }
      }
    });

    yearGroupList.push(g);
  }

  // Handle unassigned courses
  if (unassignedSems.length > 0) {
    const unassignedCourses = semesterMap["미지정"] || [];
    if (unassignedCourses.length > 0) {
      const g = {
        yearLabel: "기타/미지정 학기",
        semesterRangeStr: "학기 정보 없음",
        majorCreditsTotal: 0,
        majorCreditsGpa: 0,
        majorPoints: 0,
        overallCreditsTotal: 0,
        overallCreditsGpa: 0,
        overallPoints: 0,
        majorCourses: []
      };
      unassignedCourses.forEach(c => {
        const pts = gradeMap[c.grade];
        if (c.grade !== "F" && c.grade !== "NP") {
          g.overallCreditsTotal += c.credits;
          if (c.is_major) g.majorCreditsTotal += c.credits;
        }
        if (pts !== null && pts !== undefined) {
          g.overallPoints += pts * c.credits;
          g.overallCreditsGpa += c.credits;
          if (c.is_major) {
            g.majorPoints += pts * c.credits;
            g.majorCreditsGpa += c.credits;
            g.majorCourses.push({ name: c.name, credits: c.credits, grade: c.grade, pts, classification: c.classification || "" });
          }
        } else {
          if (c.is_major) {
            g.majorCourses.push({ name: c.name, credits: c.credits, grade: c.grade, pts: null, classification: c.classification || "" });
          }
        }
      });
      yearGroupList.push(g);
    }
  }

  return yearGroupList;
}

// Render Academic Year Major Breakdown Cards (2-semester counter per year)
function renderYearBreakdown() {
  const grid = document.getElementById("year-breakdown-grid");
  if (!grid) return;

  if (!state.courses || state.courses.length === 0) {
    grid.innerHTML = `
      <div class="empty-year-state">
        <p>등록된 과목이 없어 학년별 분석 데이터가 표시되지 않습니다.</p>
      </div>
    `;
    return;
  }

  const yearGroupList = getAcademicYearGroups(state.courses, state.scale);
  if (yearGroupList.length === 0) {
    grid.innerHTML = `<div class="empty-year-state"><p>학년별 데이터가 없습니다.</p></div>`;
    return;
  }

  // 레이아웃: 학년별 카드를 세로 전체폭으로 나열
  grid.style.gridTemplateColumns = "1fr";

  grid.innerHTML = yearGroupList.map(data => {
    const majGpa = data.majorCreditsGpa > 0 ? (data.majorPoints / data.majorCreditsGpa).toFixed(2) : "0.00";
    const overallGpa = data.overallCreditsGpa > 0 ? (data.overallPoints / data.overallCreditsGpa).toFixed(2) : "0.00";

    // 전공 과목 테이블 행 생성
    const courseRows = data.majorCourses.length > 0
      ? data.majorCourses.map(mc => {
          const gradeClass = mc.grade && mc.grade[0] ? `grade-${mc.grade[0]}` : "grade-P";
          const ptsDisplay = mc.pts !== null ? mc.pts.toFixed(1) : "-";
          const clsLabel = mc.classification ? `<span class="yr-cls-badge">${escapeHtml(mc.classification)}</span>` : "";
          return `
            <tr>
              <td>${escapeHtml(mc.name)} ${clsLabel}</td>
              <td style="text-align:center;">${mc.credits}</td>
              <td style="text-align:center;"><span class="grade-badge ${gradeClass}">${escapeHtml(mc.grade)}</span></td>
              <td style="text-align:center; font-weight:700; color:var(--ink);">${ptsDisplay}</td>
            </tr>`;
        }).join('')
      : `<tr><td colspan="4" style="text-align:center; color:var(--ink-3); padding:10px;">해당 학년 전공 과목 없음</td></tr>`;

    return `
      <div class="year-card year-card-full">
        <div class="year-card-header">
          <div>
            <span class="year-title">🎓 ${data.yearLabel}</span>
            <span style="font-family:var(--font-mono); font-size:11.5px; color:var(--ink-2); margin-left:8px;">(${data.semesterRangeStr})</span>
          </div>
          <div style="display:flex; gap:10px; align-items:center;">
            <span style="font-size:0.8rem; color:var(--ink-2);">전체 평점 <strong style="color:var(--ink); font-family:var(--font-mono);">${overallGpa}</strong></span>
            <span class="year-gpa-tag">전공 ${majGpa} / ${state.scale.toFixed(2)}</span>
          </div>
        </div>
        <!-- 요약 배지 행 -->
        <div class="year-summary-row">
          <div class="year-stat-chip">
            <span class="chip-lbl">전공 이수학점</span>
            <span class="chip-val">${data.majorCreditsTotal}<small>학점</small></span>
          </div>
          <div class="year-stat-chip">
            <span class="chip-lbl">평점 반영</span>
            <span class="chip-val">${data.majorCreditsGpa}<small>학점</small></span>
          </div>
          <div class="year-stat-chip highlight-chip">
            <span class="chip-lbl">전공 평점</span>
            <span class="chip-val" style="color:var(--ink);">${majGpa}</span>
          </div>
          <div class="year-stat-chip">
            <span class="chip-lbl">전공 과목 수</span>
            <span class="chip-val">${data.majorCourses.length}<small>개</small></span>
          </div>
        </div>
        <!-- 전공 과목 상세 테이블 -->
        <div class="year-course-table-wrap">
          <table class="year-course-table">
            <thead>
              <tr>
                <th>과목명</th>
                <th style="width:60px; text-align:center;">학점</th>
                <th style="width:70px; text-align:center;">성적</th>
                <th style="width:70px; text-align:center;">평점</th>
              </tr>
            </thead>
            <tbody>
              ${courseRows}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }).join('');
}

// Action helpers
window.toggleMajor = function(id) {
  state.courses = state.courses.map(c => c.id === id ? { ...c, is_major: !c.is_major } : c);
  renderApp();
};

window.updateCredits = function(id, val) {
  state.courses = state.courses.map(c => c.id === id ? { ...c, credits: parseFloat(val) } : c);
  renderApp();
};

window.updateGrade = function(id, val) {
  state.courses = state.courses.map(c => c.id === id ? { ...c, grade: val } : c);
  renderApp();
};

window.deleteCourse = function(id) {
  state.courses = state.courses.filter(c => c.id !== id);
  renderApp();
};

function escapeHtml(str) {
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
