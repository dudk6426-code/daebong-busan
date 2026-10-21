@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================================
echo   [대봉개발] 홈페이지 & 네이버 블로그 원스톱 관리 시스템
echo ========================================================
echo.

:: 1. 클라우드 서버가 밤 9시에 업데이트해 둔 최신 상태 받아오기
git checkout main
git pull origin main

:: 2. 파이썬으로 새로운 세부 키워드 글 생성 (홈페이지 + 블로그 원고)
python automation\main.py

:: 3. 홈페이지 변경사항 즉시 반영
git add index.html automation/output/blog_draft.txt
git commit -m "auto: 홈페이지 및 네이버 블로그 원고 업데이트"
git push origin main

:: 4. 생성된 블로그 원고를 클립보드에 자동 복사 & 메모장 + 네이버 블로그 글쓰기 창 동시 오픈!
if exist "automation\output\blog_draft.txt" (
    powershell -command "Get-Content -Path 'automation\output\blog_draft.txt' -Encoding UTF8 | Set-Clipboard"
    start notepad.exe "automation\output\blog_draft.txt"
    start "" "https://blog.naver.com/dudk6424?Redirect=Write"
)

echo.
echo ========================================================
echo   ✓ 1. 실제 홈페이지 업데이트 완료!
echo   ✓ 2. 블로그 원고가 클립보드에 [자동 복사] 되었습니다!
echo   ✓ 3. 열린 네이버 블로그 글쓰기 창에서 [Ctrl + V]만 누르세요!
echo ========================================================
timeout /t 7