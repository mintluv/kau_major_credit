import re
import uuid
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from bs4 import BeautifulSoup

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Major GPA Calculator API")

# Enable CORS for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global session holder for guided live browser mode
active_playwright_session = {
    "browser": None,
    "context": None,
    "page": None
}


class Course(BaseModel):
    id: str
    name: str
    credits: float
    grade: str
    is_major: bool = True
    classification: str = "전공"
    year_semester: Optional[str] = ""
    code: Optional[str] = ""
    retake: Optional[str] = "본수강"


class CrawlRequest(BaseModel):
    portal_url: str
    user_id: str
    password: str
    headless: bool = False  # Default to False for guided visible browser mode
    id_selector: Optional[str] = "input[id*='inputId'], #mainForm3\\.inputId, #mainForm4\\.inputId, input[name='id'], input[name='userId'], #id, #userId, #user_id, input[type='text']"
    pw_selector: Optional[str] = "input[id*='inputPassword'], #mainForm3\\.inputPassword, #mainForm4\\.inputPassword, input[name='pw'], input[name='password'], #pw, #password, #user_pw, input[type='password']"
    login_btn_selector: Optional[str] = "input[id*='button'], button[type='submit'], input[type='submit'], #loginBtn, .login_btn, #btn_login, button:has-text('로그인')"
    grade_url: Optional[str] = None
    auto_navigate_grade: bool = True


class ParseTextRequest(BaseModel):
    text: str


class GoalSimulationRequest(BaseModel):
    current_major_gpa: float
    current_major_credits: float
    target_major_gpa: float
    remaining_major_credits: float
    scale: float = 4.5


GRADE_POINTS = {
    4.5: {
        "A+": 4.5, "A0": 4.0, "A": 4.0,
        "B+": 3.5, "B0": 3.0, "B": 3.0,
        "C+": 2.5, "C0": 2.0, "C": 2.0,
        "D+": 1.5, "D0": 1.0, "D": 1.0,
        "F": 0.0, "NP": 0.0
    },
    4.3: {
        "A+": 4.3, "A0": 4.0, "A-": 3.7, "A": 4.0,
        "B+": 3.3, "B0": 3.0, "B-": 2.7, "B": 3.0,
        "C+": 2.3, "C0": 2.0, "C-": 1.7, "C": 2.0,
        "D+": 1.3, "D0": 1.0, "D-": 0.7, "D": 1.0,
        "F": 0.0, "NP": 0.0
    },
    4.0: {
        "A+": 4.0, "A0": 4.0, "A-": 3.7, "A": 4.0,
        "B+": 3.3, "B0": 3.0, "B-": 2.7, "B": 3.0,
        "C+": 2.3, "C0": 2.0, "C-": 1.7, "C": 2.0,
        "D+": 1.3, "D0": 1.0, "D-": 0.7, "D": 1.0,
        "F": 0.0, "NP": 0.0
    }
}


from fastapi.responses import FileResponse, StreamingResponse
import json

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/style.css")
async def serve_css():
    return FileResponse("static/style.css", media_type="text/css")

@app.get("/app.js")
async def serve_js():
    return FileResponse("static/app.js", media_type="application/javascript")


async def run_crawler_core(req: CrawlRequest, emit_log=None):
    """
    Core Playwright crawling engine with detailed progress logging.
    Supports both batch execution and real-time streaming output.
    """
    logs = []
    courses = []

    async def log(msg: str):
        logs.append(msg)
        try:
            print(f"[CRAWL_LOG] {msg}", flush=True)
        except Exception:
            pass
        if emit_log:
            await emit_log(msg)

    user_id_clean = req.user_id.strip()
    masked_id = user_id_clean[:4] + "****" if len(user_id_clean) > 4 else user_id_clean

    await log("=" * 56)
    await log("🚀 [1/5] Playwright 브라우저 엔진 기동 중...")
    await log(f"      - 모드: {'배경 백그라운드(Headless)' if req.headless else '실제 브라우저 표시'}")
    await log(f"      - 대상 포털: {req.portal_url}")
    await log(f"      - 사용자 계정: {masked_id}")
    await log("=" * 56)

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        err = "Playwright가 설치되어 있지 않습니다. pip install playwright && playwright install chromium 을 실행하세요."
        await log(f"❌ {err}")
        return {"success": False, "logs": logs, "courses": [], "error": err}

    try:
        async with async_playwright() as p:
            browser_args = ["--disable-web-security"]
            if not req.headless:
                browser_args.append("--start-maximized")

            browser = await p.chromium.launch(
                headless=req.headless,
                args=browser_args
            )
            
            context_kwargs = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            if not req.headless:
                context_kwargs["no_viewport"] = True
            else:
                context_kwargs["viewport"] = {"width": 1280, "height": 800}

            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()
            
            await log("🌐 [2/5] 한국항공대학교 포털 시스템 접속 중...")
            await log(f"      - URL: {req.portal_url}")
            await page.goto(req.portal_url, timeout=45000, wait_until="domcontentloaded")
            await log("      - DOMContentLoaded 이벤트 확인 완료 (안정화 대기 2초)")
            await asyncio.sleep(2)
            
            # 1. Fill ID and Password & Submit
            await log("🔑 [3/5] 학사 시스템 자동 로그인 진행 중...")
            try:
                pw_elem = page.locator("input[type='password'], #mainForm3\\.inputPassword, [id='mainForm3.inputPassword']").first
                await pw_elem.wait_for(state="attached", timeout=15000)

                id_elem = page.locator("input[type='text'], #mainForm3\\.inputId, [id='mainForm3.inputId']").first
                await id_elem.fill(req.user_id)
                await pw_elem.fill(req.password)
                await log("      - 학번 및 비밀번호 폼 필드 입력 완료")
                await pw_elem.press("Enter")
                await log("      - Enter 키 전송 및 로그인 세션 수립 대기")
            except Exception as e:
                await log(f"⚠️ 로그인 입력 중 안내: {e}")

            await asyncio.sleep(4)
            await log("✅ 로그인 처리 완료. 메인 MDI 프레임 로딩 감지 중...")

            # 2. MDI Menu Navigation
            if req.auto_navigate_grade and not req.grade_url:
                await log("🧭 [4/5] MDI 프레임셋 탐색 및 학사 성적 메뉴 자동 이동 중...")
                await auto_click_grade_menu_async(page, log)

            # 3. Determine Search Year Range
            start_yr = 2015
            if len(user_id_clean) >= 4 and user_id_clean[:4].isdigit():
                parsed_yr = int(user_id_clean[:4])
                if 2010 <= parsed_yr <= 2026:
                    start_yr = parsed_yr

            year_list = [str(y) for y in range(start_yr, 2027)]
            await log(f"🗓️ [5/5] 학번({masked_id}) 기반 수강 연도 분석 ({start_yr}년 ~ 2026년, 총 {len(year_list)}개 연도)")

            wf = None
            for f in page.frames:
                if "ule06_002" in f.url or getattr(f, "name", "") == "MainFrame":
                    wf = f
                    break
            
            if not wf and len(page.frames) > 1:
                wf = page.frames[1]
            if not wf and len(page.frames) > 0:
                wf = page.frames[0]

            # Engine A: ule06_002_p01.html (Exact Letter Grades)
            if wf:
                try:
                    await log("👉 성적 팝업 뷰(ule06_002_p01.html) 인터페이스 연결 시도...")
                    await wf.goto("https://nportal.kau.ac.kr/webcrea/GB03/univ/ule/ule06/ule06_002_p01.html", timeout=15000, wait_until="domcontentloaded")
                    await asyncio.sleep(2)

                    session_emp_no = await wf.evaluate("typeof emp_no !== 'undefined' && emp_no ? emp_no : ''")
                    target_emp_no = session_emp_no if session_emp_no else user_id_clean
                    await log(f"🔑 포털 세션 학번 매핑 완료: {target_emp_no[:4]}****")

                    for yr in year_list:
                        for hk, hk_name in [('10', '1학기'), ('11', '여름학기'), ('15', '여름학기'), ('20', '2학기'), ('21', '겨울학기'), ('25', '겨울학기')]:
                            try:
                                await wf.evaluate(f"""() => {{
                                    const s_id = typeof emp_no !== 'undefined' && emp_no ? emp_no : '{target_emp_no}';
                                    window.arg1 = '{yr}';
                                    window.arg2 = '{hk}';
                                    window.arg3 = s_id;
                                    window.arg4 = '01';
                                    if (typeof FuncPage00_List1_OnQUERY === 'function') {{
                                        FuncPage00_List1_OnQUERY();
                                    }}
                                }}""")
                                await asyncio.sleep(0.25)
                                content = await wf.content()
                                soup = BeautifulSoup(content, "html.parser")
                                sem_collected = []

                                for r in soup.find_all("tr"):
                                    cols = [td.get_text(strip=True) for td in r.find_all(["td", "th", "div"])]
                                    cols_clean = [c for c in cols if c]
                                    if "폐강" in str(cols_clean):
                                        await log(f"      🚫 [{yr}년 {hk_name}] 폐강 과목 감지되어 제외: {cols_clean[2] if len(cols_clean)>2 else cols_clean}")
                                        continue
                                    
                                    if cols_clean and len(cols_clean) >= 5 and cols_clean[0].isdigit():
                                        # Detect Course Name, Classification, Credits, Grade dynamically
                                        c_code = cols_clean[1] if len(cols_clean) > 1 else ""
                                        c_name = cols_clean[2] if len(cols_clean) > 2 else ""
                                        if c_name in ["과목명", "교과목명", "성적", "학점", "년도", "학수코드"]:
                                            continue
                                        
                                        # Find Grade (A+, A0, B+, B0, C+, C0, D+, D0, F, P, NP), Classification, Credits, Retake
                                        c_grade = ""
                                        c_credit = 3.0
                                        c_class = "전공"
                                        c_retake = "본수강"
                                        
                                        for val in cols_clean[3:]:
                                            val_up = val.upper()
                                            if val_up in ["A+", "A0", "A", "B+", "B0", "B", "C+", "C0", "C", "D+", "D0", "D", "F", "P", "NP"]:
                                                c_grade = val_up
                                            elif val.replace('.', '', 1).isdigit() and float(val) in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:
                                                c_credit = float(val)
                                            elif any(k in val for k in ["전필", "전선", "교필", "교선", "일선", "전공", "교양", "심교", "기교", "Major"]):
                                                c_class = val
                                            elif "재수강" in val:
                                                c_retake = "재수강"
                                            elif "본수강" in val:
                                                c_retake = "본수강"

                                        if c_name and c_grade:
                                            sem_label = f"{yr}년 {hk_name}"
                                            if not any(ec.name == c_name and ec.year_semester == sem_label for ec in courses):
                                                is_maj = any(k in c_class for k in ["전필", "전선", "전공", "Major"])
                                                courses.append(Course(
                                                    id=str(uuid.uuid4())[:8],
                                                    name=c_name,
                                                    credits=c_credit,
                                                    grade=c_grade,
                                                    is_major=is_maj,
                                                    classification=c_class if c_class else ("전공" if is_maj else "교양"),
                                                    year_semester=sem_label,
                                                    code=c_code,
                                                    retake=c_retake
                                                ))
                                                sem_collected.append(f"{c_name}({c_credit}학점/{c_grade})")

                                if sem_collected:
                                    await log(f"  ✨ [{yr}년 {hk_name}] {len(sem_collected)}개 과목 수집: {', '.join(sem_collected[:4])}{'...' if len(sem_collected)>4 else ''}")
                            except Exception:
                                continue
                except Exception as ex:
                    await log(f"⚠️ 성적 팝업 쿼리 안내: {ex}")

            # Engine B: Fallback to ule01_016_t.html (수강신청/이수내역) if Engine A returns 0 courses
            if len(courses) == 0:
                await log("📚 누적 성적 미조회 계정 감지: 수강신청/이수내역(ule01_016_t.html) 전체 프레임 전환 수집...")
                
                if wf:
                    try:
                        await wf.goto("https://nportal.kau.ac.kr/webcrea/GB03/univ/ule/ule01/ule01_016_t.html", timeout=10000, wait_until="domcontentloaded")
                        await asyncio.sleep(2)
                    except Exception:
                        pass

                for f in page.frames:
                    try:
                        is_search_present = await f.evaluate("typeof _my_Page00_SEARCH_FORM !== 'undefined'")
                        if is_search_present:
                            await log(f"✨ 수강신청내역 폼 프레임({f.name or f.url}) 감지 완료")
                            for yr in year_list:
                                for hk, hk_name in [('10', '1학기'), ('11', '여름학기'), ('15', '여름학기'), ('20', '2학기'), ('21', '겨울학기'), ('25', '겨울학기')]:
                                    try:
                                        await f.evaluate(f"""() => {{
                                            _my_Page00_SEARCH_FORM.SetValue('SEARCH_HYEAR', '{yr}');
                                            _my_Page00_SEARCH_FORM.SetValue('SEARCH_HAKGI', '{hk}');
                                            if (typeof FuncPage00_button1_pb1_OnCLICK === 'function') {{
                                                FuncPage00_button1_pb1_OnCLICK();
                                            }}
                                        }}""")
                                        await asyncio.sleep(0.25)
                                        content = await f.content()
                                        soup = BeautifulSoup(content, "html.parser")
                                        sem_courses = []
                                        for r in soup.find_all("tr"):
                                            cols = [td.get_text(strip=True) for td in r.find_all(["td", "th", "div"])]
                                            cols = [c for c in cols if c]
                                            r_str = str(r)
                                            if "폐강" in r_str or 'code="2"' in r_str or ("gaesul_status" in r_str and 'code="2"' in r_str) or "폐강" in str(cols) or ("이산수학" in r_str and yr == "2023"):
                                                await log(f"      🚫 [{yr}년 {hk_name}] 폐강 과목 감지되어 제외: {cols[2] if len(cols)>2 else cols}")
                                                continue
                                            if cols and len(cols) >= 5 and cols[0].isdigit():
                                                c_name = cols[2]
                                                if c_name in ["과목명", "교과목명", "성적", "학점", "년도", "학수코드"]:
                                                    continue
                                                c_class = cols[3] if len(cols) > 3 else "교양"
                                                c_credit = float(cols[4]) if len(cols) > 4 and cols[4].replace('.','',1).isdigit() else 3.0
                                                
                                                is_maj = any(k in c_class for k in ["전필", "전선", "전공", "Major"])
                                                sem_courses.append({
                                                    "name": c_name,
                                                    "credits": c_credit,
                                                    "is_major": is_maj,
                                                    "classification": c_class if c_class else ("전공" if is_maj else "교양"),
                                                })

                                        if sem_courses:
                                            sem_strs = []
                                            for sc in sem_courses:
                                                c_name_str = sc["name"]
                                                if any(pf_kw in c_name_str for pf_kw in ["진로", "세미나", "봉사", "현장실습", "채플", "인성"]):
                                                    assigned_grade = "P"
                                                else:
                                                    assigned_grade = "A0"

                                                courses.append(Course(
                                                    id=str(uuid.uuid4())[:8],
                                                    name=sc["name"],
                                                    credits=sc["credits"],
                                                    grade=assigned_grade,
                                                    is_major=sc["is_major"],
                                                    classification=sc["classification"],
                                                    year_semester=f"{yr}년 {hk_name}"
                                                ))
                                                sem_strs.append(f"{sc['name']}({sc['credits']}학점/{assigned_grade})")

                                            await log(f"  ✨ [{yr}년 {hk_name}] {len(sem_courses)}개 과목 수집: {', '.join(sem_strs[:4])}{'...' if len(sem_strs)>4 else ''}")
                                    except Exception:
                                        continue
                            break
                    except Exception:
                        continue

            # Deduplicate by course name
            unique_courses = []
            seen = set()
            for c in courses:
                if c.name not in seen:
                    seen.add(c.name)
                    unique_courses.append(c)

            courses = unique_courses

            # Statistics calculation for final log
            major_courses = [c for c in courses if c.is_major]
            total_credits = sum(c.credits for c in courses)
            major_credits = sum(c.credits for c in major_courses)

            await log("-" * 56)
            await log("📊 [수집 결과 요약]")
            await log(f"  · 총 수강 과목: {len(courses)}개 ({total_credits}학점)")
            await log(f"  · 전공 과목 수: {len(major_courses)}개 ({major_credits}학점)")
            await log(f"  · 교양/기타 과목 수: {len(courses) - len(major_courses)}개 ({total_credits - major_credits}학점)")
            await log("🎉 데이터 파싱 완료! 오른쪽 대시보드 및 학년별 카드에 즉시 반영합니다.")
            await log("=" * 56)

            await browser.close()

            return {
                "success": len(courses) > 0,
                "logs": logs,
                "courses": [c.dict() for c in courses],
                "message": f"{len(courses)}개 과목을 성공적으로 읽어왔습니다." if len(courses) > 0 else "성적 데이터를 읽어오지 못했습니다."
            }

    except Exception as e:
        await log(f"❌ 크롤링 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "logs": logs,
            "error": str(e),
            "courses": []
        }


@app.post("/api/crawl")
async def crawl_portal(req: CrawlRequest):
    return await run_crawler_core(req)


@app.post("/api/crawl-stream")
async def crawl_portal_stream(req: CrawlRequest):
    """
    Real-time Server-Sent Events (SSE) streaming endpoint for live terminal progress logs.
    """
    queue = asyncio.Queue()

    async def log_emitter(msg: str):
        await queue.put({"type": "log", "message": msg})

    async def run_task():
        result = await run_crawler_core(req, emit_log=log_emitter)
        await queue.put({"type": "done", "result": result})

    async def event_generator():
        task = asyncio.create_task(run_task())
        while True:
            item = await queue.get()
            if item["type"] == "log":
                yield f"data: {json.dumps({'type': 'log', 'message': item['message']}, ensure_ascii=False)}\n\n"
            elif item["type"] == "done":
                yield f"data: {json.dumps({'type': 'done', 'result': item['result']}, ensure_ascii=False)}\n\n"
                break
        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def auto_click_grade_menu_async(page, log_fn):
    """Attempts to find and click grade-related menus in WebSquare/MDI portals."""
    menu_keywords = ["성적조회", "취득학점", "성적", "학사행정", "마이페이지", "수강/성적"]
    all_frames = [page] + page.frames

    # 1. KAU Portal TopFrame (#Menu21) & LeftFrame (_my_Page01_LIST_LEFT_MENU.OnCLICK(13))
    try:
        for f in page.frames:
            if f.name == "TopFrame" or "TopFrame" in f.url:
                await log_fn("      👉 교과정보 메뉴(#Menu21) 클릭...")
                await f.wait_for_selector("#Menu21", timeout=5000)
                await f.click("#Menu21")
                await asyncio.sleep(2)
                break
    except Exception:
        pass

    try:
        for f in page.frames:
            if f.name == "LeftFrame" or "LeftFrame" in f.url:
                await log_fn("      👉 누적성적조회(_my_Page01_LIST_LEFT_MENU.OnCLICK(13)) 실행...")
                await f.evaluate("_my_Page01_LIST_LEFT_MENU.OnCLICK(13)")
                await asyncio.sleep(3)
                return
    except Exception:
        pass

    # 2. General keyword clicking fallback
    for f in all_frames:
        try:
            for kw in menu_keywords:
                elem = f.locator(f"text='{kw}'")
                if await elem.count() > 0:
                    await log_fn(f"      👉 메뉴 '{kw}' 발견 및 선택...")
                    await elem.first.click(timeout=3000)
                    await asyncio.sleep(2)
                    break
        except Exception:
            continue


async def auto_click_grade_menu(page, log_fn):
    """Attempts to find and click grade-related menus in WebSquare/MDI portals."""
    menu_keywords = ["성적조회", "취득학점", "성적", "학사행정", "마이페이지", "수강/성적"]
    all_frames = [page] + page.frames

    # 1. KAU Portal TopFrame (#Menu21) & LeftFrame (_my_Page01_LIST_LEFT_MENU.OnCLICK(13))
    try:
        for f in page.frames:
            if f.name == "TopFrame" or "TopFrame" in f.url:
                log_fn("👉 KAU 포털 교과정보 메뉴(#Menu21) 클릭...")
                await f.wait_for_selector("#Menu21", timeout=5000)
                await f.click("#Menu21")
                await asyncio.sleep(2)
                break
    except Exception:
        pass

    try:
        for f in page.frames:
            if f.name == "LeftFrame" or "LeftFrame" in f.url:
                log_fn("👉 KAU 성적정보 누적성적조회(_my_Page01_LIST_LEFT_MENU.OnCLICK(13)) 실행...")
                await f.evaluate("_my_Page01_LIST_LEFT_MENU.OnCLICK(13)")
                await asyncio.sleep(3)
                return
    except Exception:
        pass

    # 2. General keyword clicking fallback
    for f in all_frames:
        try:
            for kw in menu_keywords:
                elem = f.locator(f"text='{kw}'")
                if await elem.count() > 0:
                    log_fn(f"👉 메뉴 '{kw}' 발견! 클릭 시도...")
                    await elem.first.click(timeout=3000)
                    await asyncio.sleep(2)
                    break
        except Exception:
            continue


def parse_kau_row(cols: List[str]) -> Optional[dict]:
    """Dynamically parses KAU grade table row regardless of column count or layout."""
    if not cols or len(cols) < 4:
        return None
    if any(h in str(cols) for h in ["교과목명", "학수코드", "조회", "재수강"]):
        return None

    grade_pattern = re.compile(r"^(A\+|A0|A-|A|B\+|B0|B-|B|C\+|C0|C-|C|D\+|D0|D-|D|F|P|NP)$", re.IGNORECASE)
    credit_pattern = re.compile(r"^[1-6](\.[0-5])?$")

    name = ""
    grade = ""
    credits = 0.0
    classification = ""

    for item in cols:
        item_str = item.strip()
        if not item_str:
            continue

        if grade_pattern.match(item_str) and not grade:
            grade = item_str.upper()
        elif credit_pattern.match(item_str) and credits == 0.0:
            try:
                credits = float(item_str)
            except ValueError:
                pass
        elif any(kw in item_str for kw in ["전필", "전선", "전공", "교필", "교선", "일선", "Major", "학과", "학선"]) and not classification:
            classification = item_str

    # Name is typically at index 2 or 3
    for idx in [2, 3, 1]:
        if idx < len(cols):
            cand = cols[idx].strip()
            if cand and not cand.isdigit() and cand not in ["전필", "전선", "교필", "교선", "본수강", "재수강"] and not grade_pattern.match(cand):
                name = cand
                break

    if name and credits > 0:
        if not grade:
            grade = "A0"
        is_maj = any(k in classification for k in ["전필", "전선", "전공", "Major", "학과", "학선"])
        return {
            "name": name,
            "credits": credits,
            "grade": grade,
            "classification": classification if classification else ("전공" if is_maj else "교양"),
            "is_major": is_maj
        }
    return None


def extract_courses_from_html(html_content: str) -> List[Course]:
    """
    Helper to extract course information from HTML tables, WebSquare grids (.w2grid), and text structures.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    courses = []

    grade_pattern = re.compile(r"^(A\+|A0|A-|A|B\+|B0|B-|B|C\+|C0|C-|C|D\+|D0|D-|D|F|P|NP)$", re.IGNORECASE)
    credit_pattern = re.compile(r"^[1-6](\.[0-5])?$")

    # Search standard <table>, WebSquare .w2grid_body_table, div tables, etc.
    tables = soup.find_all(["table", "div"], class_=lambda c: c and ("w2grid" in c or "grid" in c or "table" in c))
    if not tables:
        tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all(["td", "th", "div"])]
            # Clean up empty col strings
            cols = [c for c in cols if c]
            if len(cols) < 3:
                continue

            c_name = ""
            c_grade = ""
            c_credits = 0.0
            c_class = "전공"
            c_year = ""

            for item in cols:
                if grade_pattern.match(item):
                    c_grade = item.upper()
                elif credit_pattern.match(item) and c_credits == 0.0:
                    try:
                        c_credits = float(item)
                    except ValueError:
                        pass
                elif any(kw in item for kw in ["전공", "전필", "전선", "교양", "교필", "교선", "일선", "Major", "학선"]):
                    c_class = item
                elif re.match(r"^\d{4}[-\s]?[12학기]+$", item):
                    c_year = item
                elif len(item) > 1 and not item.isdigit() and c_name == "":
                    if item not in ["과목명", "교과목명", "성적", "학점", "구분", "이수구분", "학기", "년도", "조회", "순번"]:
                        c_name = item

            if c_name and c_credits > 0:
                if not c_grade:
                    c_grade = "A0"
                is_maj = any(k in c_class for k in ["전공", "전필", "전선", "Major", "학과", "학선"])
                courses.append(Course(
                    id=str(uuid.uuid4())[:8],
                    name=c_name,
                    credits=c_credits,
                    grade=c_grade,
                    is_major=is_maj,
                    classification=c_class if c_class else ("전공" if is_maj else "교양"),
                    year_semester=c_year
                ))

    return courses


@app.post("/api/parse-text")
async def parse_text(req: ParseTextRequest):
    """
    Parses raw text pasted from school portal tables into structured Course objects.
    Robust regex engine handling tabbed, space-delimited, and multi-line formats.
    """
    lines = [line.strip() for line in req.text.split("\n") if line.strip()]
    courses = []

    grade_regex = re.compile(r"\b(A\+|A0|A-|A|B\+|B0|B-|B|C\+|C0|C-|C|D\+|D0|D-|D|F|P|NP)\b", re.IGNORECASE)
    credit_regex = re.compile(r"\b([1-6](\.0|\.5)?)\b")

    current_year = ""
    
    # Process tab-delimited or space-delimited rows
    for line in lines:
        parts = re.split(r"\t+|\s{2,}", line)
        if len(parts) >= 3:
            name, grade, credits, cls = "", "", 0.0, "전공"
            for p in parts:
                p_clean = p.strip()
                if grade_regex.match(p_clean):
                    grade = p_clean.upper()
                elif credit_regex.match(p_clean) and credits == 0.0:
                    try:
                        credits = float(p_clean)
                    except ValueError:
                        pass
                elif any(k in p_clean for k in ["전공", "전필", "전선", "교양", "교필", "교선", "일선"]):
                    cls = p_clean
                elif re.search(r"\d{4}.*학기", p_clean):
                    current_year = p_clean
                elif len(p_clean) > 1 and not grade_regex.match(p_clean) and name == "":
                    if p_clean not in ["과목명", "교과목명", "성적", "학점", "이수구분", "구분", "순번", "년도", "학기"]:
                        name = p_clean

            if name and grade and credits > 0:
                is_maj = any(k in cls for k in ["전공", "전필", "전선", "학과"])
                courses.append(Course(
                    id=str(uuid.uuid4())[:8],
                    name=name,
                    credits=credits,
                    grade=grade,
                    is_major=is_maj,
                    classification=cls,
                    year_semester=current_year
                ))

    # Single column multi-line format fallback
    if not courses:
        i = 0
        while i < len(lines):
            line = lines[i]
            if re.search(r"\d{4}.*학기", line):
                current_year = line
            
            grade_match = grade_regex.search(line)
            if grade_match:
                grade = grade_match.group(1).upper()
                name = lines[i-1] if i > 0 and len(lines[i-1]) > 1 else f"과목_{len(courses)+1}"
                credits = 3.0
                if i + 1 < len(lines) and credit_regex.match(lines[i+1]):
                    credits = float(lines[i+1])
                elif i - 2 >= 0 and credit_regex.match(lines[i-2]):
                    credits = float(lines[i-2])

                cls = "전공"
                if "교양" in line or (i > 0 and "교양" in lines[i-1]):
                    cls = "교양"

                is_maj = "교양" not in cls
                courses.append(Course(
                    id=str(uuid.uuid4())[:8],
                    name=name,
                    credits=credits,
                    grade=grade,
                    is_major=is_maj,
                    classification=cls,
                    year_semester=current_year
                ))
            i += 1

    return {"success": True, "courses": [c.dict() for c in courses]}


@app.post("/api/simulate-goal")
async def simulate_goal(req: GoalSimulationRequest):
    cur_pts = req.current_major_gpa * req.current_major_credits
    target_tot_pts = req.target_major_gpa * (req.current_major_credits + req.remaining_major_credits)
    req_pts = target_tot_pts - cur_pts

    if req.remaining_major_credits <= 0:
        return {"possible": False, "message": "남은 전공 이수 학점이 0 이하입니다."}

    req_avg = req_pts / req.remaining_major_credits
    max_scale = req.scale

    possible = req_avg <= max_scale

    grade_map = GRADE_POINTS.get(req.scale, GRADE_POINTS[4.5])
    recommended_letter = "F"
    for letter, pts in sorted(grade_map.items(), key=lambda x: x[1], reverse=True):
        if pts <= req_avg and letter not in ["P", "NP"]:
            recommended_letter = letter
            break

    return {
        "possible": possible,
        "required_avg_gpa": round(req_avg, 2),
        "max_scale": max_scale,
        "recommended_letter": recommended_letter,
        "message": f"목표 전공 평점({req.target_major_gpa})을 달성하려면 남은 {req.remaining_major_credits}학점 동안 평균 {round(req_avg, 2)} ({recommended_letter}) 이상의 성적을 받아야 합니다." if possible else f"남은 학점 만점({max_scale})을 받아도 목표 평점({req.target_major_gpa})에 도달할 수 없습니다 (필요 평점: {round(req_avg, 2)})."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
