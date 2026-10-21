@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================================
echo   [대봉개발] 홈페이지 & 네이버 블로그 원스톱 관리 시스템
echo ========================================================
echo.

:: 1. 파이썬으로 새로운 세부 키워드 글 생성 (또는 memo.txt 자동 살붙이기)
python automation\main.py

:: 2. 클라우드 서버 최신 상태 동기화 및 홈페이지·코드 즉시 반영
git checkout main
git pull --rebase origin main
git add index.html automation/main.py automation/run.bat automation/output/blog_draft.txt
git commit -m "auto: 홈페이지 및 자동 살붙이기 블로그 원고 업데이트"
git push origin main

:: 3. 안내문 제외한 '순수 본문'만 클립보드에 자동 복사 & 메모장 + 네이버 블로그 글쓰기 창 오픈!
if exist "automation\output\blog_clipboard.txt" (
    powershell -command "Get-Content -Path 'automation\output\blog_clipboard.txt' -Encoding UTF8 | Set-Clipboard"
)
if exist "automation\output\blog_draft.txt" (
    start notepad.exe "automation\output\blog_draft.txt"
    start "" "https://blog.naver.com/dudk6424?Redirect=Write"
)

echo.
echo ========================================================
echo   ✓ 1. 실제 홈페이지 업데이트 및 클라우드 동기화 완료!
echo   ✓ 2. 순수 블로그 본문이 클립보드에 [자동 복사] 되었습니다!
echo   ✓ 3. 열린 네이버 블로그 본문 칸에 바로 [Ctrl + V] 하세요!
echo ========================================================
timeout /t 7