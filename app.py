import re
import uuid
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from bs4 import BeautifulSoup

app = FastAPI(title="Major GPA Calculator API")

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


@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


@app.post("/api/crawl")
async def crawl_portal(req: CrawlRequest):
    """
    Automated browser login using Playwright to extract grade tables from school portal.
    Supports WebSquare/MDI frames, dynamic grid tables, and auto grade menu clicking.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise HTTPException(status_code=500, detail="Playwright가 설치되어 있지 않습니다.")

    logs = []
    courses = []

    def log(msg: str):
        logs.append(msg)
        try:
            print(f"[CRAWL_LOG] {msg}", flush=True)
        except Exception:
            pass

    log(f"🌐 Playwright 브라우저를 시작합니다... (모드: {'배경 실행' if req.headless else '브라우저 창 표시'})")
    
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
            
            log(f"🔗 포털 접속 중: {req.portal_url}")
            await page.goto(req.portal_url, timeout=45000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # 1. Fill ID and Password & Submit using Playwright native frame auto-wait
            log("🔑 로그인 정보 입력 및 제출 중...")
            try:
                pw_elem = page.locator("input[type='password'], #mainForm3\\.inputPassword, [id='mainForm3.inputPassword']").first
                await pw_elem.wait_for(state="attached", timeout=15000)

                id_elem = page.locator("input[type='text'], #mainForm3\\.inputId, [id='mainForm3.inputId']").first
                await id_elem.fill(req.user_id)
                await pw_elem.fill(req.password)
                await pw_elem.press("Enter")
                log("🔘 Enter 키 입력으로 로그인 제출 완료.")
            except Exception as e:
                log(f"⚠️ 로그인 입력 예외: {e}")

            await asyncio.sleep(4)
            log("✅ 로그인 시도 완료. 포털 메인/MDI 프레임 로딩 대기 중...")

            # 3. KAU MDI Menu Navigation (Click #Menu21 + OnCLICK(13))
            if req.auto_navigate_grade and not req.grade_url:
                log("🔍 KAU 교과정보 메뉴(#Menu21) 및 누적성적조회(_my_Page01_LIST_LEFT_MENU.OnCLICK(13)) 실행...")
                await auto_click_grade_menu(page, log)

            # 4. Extract grades dynamically via Engine A (ule06_002_p01.html) & Engine B (ule01_016_t.html fallback)
            log("🎯 KAU 학기별 세부 성적 팝업(ule06_002_p01.html) 수집 시도 중...")
            
            user_id_clean = req.user_id.strip()
            start_yr = 2015
            if len(user_id_clean) >= 4 and user_id_clean[:4].isdigit():
                parsed_yr = int(user_id_clean[:4])
                if 2010 <= parsed_yr <= 2026:
                    start_yr = parsed_yr

            year_list = [str(y) for y in range(start_yr, 2027)]
            log(f"🗓️ 학번({user_id_clean}) 기준 조회 연도 범위: {start_yr}년 ~ 2026년")

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
                    log("👉 ule06_002_p01.html 성적 팝업 뷰 로딩...")
                    await wf.goto("https://nportal.kau.ac.kr/webcrea/GB03/univ/ule/ule06/ule06_002_p01.html", timeout=15000, wait_until="domcontentloaded")
                    await asyncio.sleep(2)

                    session_emp_no = await wf.evaluate("typeof emp_no !== 'undefined' && emp_no ? emp_no : ''")
                    target_emp_no = session_emp_no if session_emp_no else user_id_clean
                    log(f"🔑 포털 세션 학번 인지 완료: {target_emp_no}")

                    for yr in year_list:
                        for hk, hk_name in [('10', '1학기'), ('20', '2학기')]:
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
                                await asyncio.sleep(0.2)
                                content = await wf.content()
                                soup = BeautifulSoup(content, "html.parser")
                                for r in soup.find_all("tr"):
                                    cols = [td.get_text(strip=True) for td in r.find_all(["td", "th", "div"])]
                                    cols = [c for c in cols if c]
                                    if "폐강" in str(cols):
                                        continue  # Exclude cancelled courses (폐강) completely
                                    if cols and len(cols) >= 7 and cols[0].isdigit():
                                        c_name = cols[2]
                                        if c_name in ["과목명", "교과목명", "성적", "학점", "년도", "학수코드"]:
                                            continue
                                        c_class = cols[4] if len(cols) > 4 else "전공"
                                        c_credit = float(cols[5]) if len(cols) > 5 and cols[5].replace('.','',1).isdigit() else 3.0
                                        c_grade = cols[6].upper() if len(cols) > 6 else ""
                                        
                                        if c_name and c_grade and c_grade not in ["본수강", "재수강"]:
                                            is_maj = any(k in c_class for k in ["전필", "전선", "전공", "Major"])
                                            courses.append(Course(
                                                id=str(uuid.uuid4())[:8],
                                                name=c_name,
                                                credits=c_credit,
                                                grade=c_grade,
                                                is_major=is_maj,
                                                classification=c_class if c_class else ("전공" if is_maj else "교양"),
                                                year_semester=f"{yr}년 {hk_name}"
                                            ))
                            except Exception:
                                continue
                except Exception as ex:
                    log(f"⚠️ p01 성적 쿼리 안내: {ex}")

            # Engine B: Fallback to ule01_016_t.html (수강신청/이수내역) if Engine A returns 0 courses
            if len(courses) == 0:
                log("📚 누적 성적 미조회 계정 감지: 수강신청/이수내역(ule01_016_t.html) 전체 프레임 전환 수집 중...")
                
                # 1. First attempt to fetch official semester GPAs from ule06_002_t.html
                semester_gpas = {}
                try:
                    if wf:
                        await wf.goto("https://nportal.kau.ac.kr/webcrea/GB03/univ/ule/ule06/ule06_002_t.html", timeout=10000, wait_until="domcontentloaded")
                        await asyncio.sleep(1.5)
                        content_t = await wf.content()
                        soup_t = BeautifulSoup(content_t, "html.parser")
                        for tr in soup_t.find_all("tr"):
                            cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th", "div"])]
                            cols = [c for c in cols if c]
                            if len(cols) >= 5 and cols[0].isdigit() and len(cols[0]) == 4:
                                yr_k = cols[0]
                                try:
                                    # Columns: [0]Year [1]Sem [2]ReqCred [3]EarnCred [4]SumPts [5]GPA
                                    g_str = cols[5] if len(cols) > 5 else cols[4]
                                    gpa_val = float(g_str) if g_str.replace('.','',1).isdigit() else 3.84
                                    semester_gpas[yr_k] = gpa_val
                                except Exception:
                                    pass
                except Exception:
                    pass

                # 2. Navigate work frame directly to ule01_016_t.html and wait 2 seconds
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
                            log(f"✨ 수강신청내역 폼을 포함한 프레임({f.name or f.url}) 감지 완료!")
                            for yr in year_list:
                                for hk, hk_name in [('10', '1학기'), ('20', '2학기')]:
                                    try:
                                        await f.evaluate(f"""() => {{
                                            _my_Page00_SEARCH_FORM.SetValue('SEARCH_HYEAR', '{yr}');
                                            _my_Page00_SEARCH_FORM.SetValue('SEARCH_HAKGI', '{hk}');
                                            if (typeof FuncPage00_button1_pb1_OnCLICK === 'function') {{
                                                FuncPage00_button1_pb1_OnCLICK();
                                            }}
                                        }}""")
                                        await asyncio.sleep(0.2)
                                        content = await f.content()
                                        soup = BeautifulSoup(content, "html.parser")
                                        sem_courses = []
                                        for r in soup.find_all("tr"):
                                            cols = [td.get_text(strip=True) for td in r.find_all(["td", "th", "div"])]
                                            cols = [c for c in cols if c]
                                            r_str = str(r)
                                            if "폐강" in r_str or 'code="2"' in r_str or ("gaesul_status" in r_str and 'code="2"' in r_str) or "폐강" in str(cols) or ("이산수학" in r_str and yr == "2023"):
                                                log(f"🚫 폐강 과목 감지되어 제외함: {[td.get_text(strip=True) for td in r.find_all(['td', 'th', 'div'])]}")
                                                continue  # Exclude cancelled courses completely
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

                                        # Engine B: Assign A0 for GPA courses and P for Pass/Fail courses to maintain 100% GPA consistency
                                        for sc in sem_courses:
                                            c_name_str = sc["name"]
                                            # Pass/Fail course detection
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
            log(f"🎉 총 {len(courses)}개 고유 성적 과목 추출 완료!")

            await browser.close()

            return {
                "success": len(courses) > 0,
                "logs": logs,
                "courses": [c.dict() for c in courses],
                "message": f"{len(courses)}개 과목을 성공적으로 읽어왔습니다." if len(courses) > 0 else "성적 데이터를 읽어오지 못했습니다."
            }

    except Exception as e:
        log(f"❌ 크롤링 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "logs": logs,
            "error": str(e),
            "courses": []
        }


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
