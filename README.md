# 한국항공대학교 전공 평점 자동 계산기 (KAU Major GPA Calculator)

한국항공대학교(KAU) 종합정보시스템(nportal) 성적 자동 크롤링 및 학년별 전공 학점/평점 분석 웹 애플리케이션입니다.

![Neo-brutalist Design](https://img.shields.io/badge/Design-Neo--Brutalist-ff5c2b?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright)

---

## 주요 기능

1. **학교 포털 성적 자동 수집 (Playwright 크롤러)**
   - 학번과 비밀번호를 입력하면 한국항공대 포털(`nportal.kau.ac.kr`)에 자동 로그인하여 전체 수강 내역을 안전하게 크롤링합니다.
   - 폐강 과목 및 P/NP(Pass/Fail) 과목을 자동으로 판별하여 평점 계산에서 정확히 분리합니다.

2. **학년별 전공 심층 분석 및 과목 리스트**
   - 1학년~4학년 연도별로 수강한 전공 과목 목록, 이수학점, 평점 반영학점, 전공 평점(GPA)을 한눈에 정리합니다.
   - P 과목(현장실습, 세미나 등)도 리스트에 명확하게 표기됩니다.

3. **성적표 텍스트 붙여넣기 및 수동 추가 지원**
   - 포털에서 복사한 텍스트를 붙여넣기만 해도 자동 정규식 파싱으로 성적표를 복원합니다.
   - 직접 과목 추가, 이수구분 변경(전공 ↔ 교양), 학점/성적 실시간 수정 및 시뮬레이션 지원.

4. **학년별 전공 성적 텍스트 내보내기**
   - 원하는 양식으로 정리된 학년별 전공 과목 성적 요약 텍스트(`.txt`) 파일 다운로드.



---

## 🚀 빠른 시작 가이드

### 사전 요구사항

- Python 3.10 이상
- Git
- Chromium을 다운로드할 수 있는 인터넷 연결

### Windows PowerShell

```powershell
git clone https://github.com/mintluv/kau_major_credit.git
cd kau_major_credit

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m playwright install chromium

python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

PowerShell에서 스크립트 실행이 차단되면 다음 명령을 한 번 실행하세요.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### macOS / Linux

```bash
git clone https://github.com/mintluv/kau_major_credit.git
cd kau_major_credit

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt
python -m playwright install chromium

python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

### 접속
웹 브라우저에서 `http://127.0.0.1:8000` 접속!

---

## 🌐 외부 접속 + Cloudflare Tunnel 자동 연동

내 컴퓨터를 호스트로 두고, 외부(스마트폰/다른 PC)에서 **`https://mintluv.github.io/kau_major_credit/`** 에 접속했을 때 내 컴퓨터 백엔드가 크롤링하도록 연동할 수 있습니다.

### 실행 방법

```bash
python start_public_server.py
```
- Cloudflare Tunnel이 자동 실행되며 최신 접속 주소가 GitHub에 실시간 동기화됩니다.
- 외부 어디서든 **`https://mintluv.github.io/kau_major_credit/`** 에 접속하면 100% 자동 직결됩니다!

---

## 💻 내 컴퓨터 로컬 전용 실행

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
웹 브라우저에서 `http://127.0.0.1:8000` 접속!

---

## 기술 스택

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Playwright (Async Chromium)
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3 (Neo-Brutalism Theme)
- **Fonts**: Baloo 2, Pretendard, JetBrains Mono
