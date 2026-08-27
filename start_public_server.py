import sys
import os
import re
import json
import time
import subprocess
import threading
import urllib.request

def download_cloudflared_if_needed():
    if not os.path.exists("cloudflared.exe"):
        print("[1/3] Cloudflare Tunnel (cloudflared.exe) 다운로드 중...")
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        urllib.request.urlretrieve(url, "cloudflared.exe")
        print("[OK] cloudflared.exe 다운로드 완료!")
    else:
        print("[1/3] cloudflared.exe 준비 완료.")

def update_and_push_url(tunnel_url):
    print(f"\n[2/3] 🚀 새 Cloudflare 터널 주소 감지: {tunnel_url}")
    print("      GitHub에 자동 동기화 푸시를 진행합니다 (약 2초 소요)...")
    
    data = {
        "backend_url": tunnel_url,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 1. Save JSON files
    for path in ["backend_url.json", "static/backend_url.json"]:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing {path}: {e}")

    # 2. Git commit & push
    try:
        subprocess.run(["git", "add", "backend_url.json", "static/backend_url.json"], capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", f"chore: sync live cloudflare tunnel URL ({tunnel_url})"], capture_output=True)
        push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
        if push_res.returncode == 0:
            print("      ✅ GitHub 동기화 성공!")
        else:
            print(f"      ⚠️ GitHub push 알림: {push_res.stderr.strip() or push_res.stdout.strip()}")
    except Exception as e:
        print(f"      ⚠️ Git 동기화 중 오류 (수동 입력 가능): {e}")

    print("\n" + "="*72)
    print("  🎉 [100% 자동 연동 완료!]")
    print(f"  🌐 웹사이트 주소: https://mintluv.github.io/kau_major_credit/")
    print(f"  🔗 내 컴퓨터 백엔드: {tunnel_url}")
    print("  👉 주소를 복사하거나 입력할 필요 없이 위 웹사이트에서 바로 이용하세요!")
    print("="*72 + "\n")

def main():
    os.system("chcp 65001 > nul")
    print("="*72)
    print("  🎓 한국항공대 전공 평점 계산기 - Cloudflare 자동 동기화 런처")
    print("="*72)
    
    # Ensure utf-8 encoding for standard outputs
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    download_cloudflared_if_needed()
    
    # 1. Start FastAPI backend
    print("\n[백엔드] FastAPI 로컬 서버 시작 중 (http://127.0.0.1:8000)...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )
    
    time.sleep(2)
    
    # 2. Start cloudflared
    print("[터널] Cloudflare Tunnel 시작 중...")
    tunnel_proc = subprocess.Popen(
        [os.path.abspath("cloudflared.exe"), "tunnel", "--url", "http://127.0.0.1:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )
    
    url_found = False
    
    # Monitor tunnel output
    try:
        for line in iter(tunnel_proc.stdout.readline, ''):
            if not line:
                break
            
            # Match trycloudflare.com URL
            match = re.search(r'(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)', line)
            if match and not url_found:
                url_found = True
                tunnel_url = match.group(1)
                threading.Thread(target=update_and_push_url, args=(tunnel_url,), daemon=True).start()
                
            # Print important lines
            if "Registered tunnel connection" in line or "error" in line.lower() or "fail" in line.lower():
                print(f"[Tunnel] {line.strip()}")
                
    except KeyboardInterrupt:
        print("\n서버를 종료합니다...")
    finally:
        tunnel_proc.terminate()
        backend_proc.terminate()

if __name__ == "__main__":
    main()
