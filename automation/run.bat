@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================================
echo   [대봉개발] 홈페이지 및 네이버 블로그 안전 동기화 시스템
echo ========================================================
echo.

:: 1. 파이썬 원고 생성 및 홈페이지(index.html) 업데이트
python -X utf8 automation\main.py
if errorlevel 1 (
    echo [오류] 파이썬 원고 생성 실패
    pause
    exit /b 1
)

:: 2. 변경된 파일 스테이징 및 커밋
git add index.html automation/main.py automation/run.bat .github/workflows/daily_update.yml
git diff --staged --quiet
if %errorlevel% equ 1 (
    git commit -m "auto: 홈페이지 및 블로그 원고 업데이트"
)

:: 3. 클라우드 동기화 및 서버 전송
git pull --rebase origin main
if errorlevel 1 (
    echo [오류] 클라우드 동기화 실패
    pause
    exit /b 1
)

git push origin main
if errorlevel 1 (
    echo [오류] 클라우드 서버 전송 실패
    pause
    exit /b 1
)

:: 4. 전송 완료 후 안전하게 메모 정리
python -X utf8 automation\main.py --clear-memo

:: 5. 순수 본문 클립보드 복사 및 블로그 글쓰기 창 열기
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; Get-Content -LiteralPath 'automation\output\blog_clipboard.txt' -Raw -Encoding UTF8 | Set-Clipboard"
start notepad.exe "automation\output\blog_draft.txt"
start "" "https://blog.naver.com/dudk6424?Redirect=Write"

echo.
echo ========================================================
echo   [완료] 1. 홈페이지 클라우드 반영 및 메모 안전 처리 완료!
echo   [완료] 2. 순수 본문이 클립보드에 복사되었습니다! (Ctrl+V)
echo ========================================================
timeout /t 5