@echo off
chcp 65001 >nul
setlocal
set "STEP=초기 폴더 이동"
cd /d "%~dp0\.."
if errorlevel 1 goto :fail

echo ========================================================
echo   [대봉개발] 홈페이지 ^& 네이버 블로그 안전 동기화 시스템
echo ========================================================
echo.

:: 1. 클라우드 최신 상태 먼저 동기화
set "STEP=Git 브랜치 확인 및 최신 동기화(pull)"
git checkout main
if errorlevel 1 goto :fail

git pull --rebase origin main
if errorlevel 1 goto :fail

:: 2. 파이썬 원고 생성 (이 시점에는 memo.txt를 삭제하지 않고 해시만 기록함)
set "STEP=파이썬 원고 생성 및 HTML 검증"
python -X utf8 automation\main.py
if errorlevel 1 goto :fail

:: 3. 변경 파일 스테이징 및 커밋
set "STEP=Git 변경 파일 스테이징(add)"
git add index.html automation/main.py automation/run.bat .github/workflows/daily_update.yml automation/output/blog_draft.txt automation/output/blog_clipboard.txt
if errorlevel 1 goto :fail

git diff --staged --quiet
if %errorlevel% equ 1 (
    set "STEP=Git 커밋(commit)"
    git commit -m "auto: 홈페이지 및 블로그 원고 업데이트"
    if errorlevel 1 goto :fail
) else if %errorlevel% gtr 1 (
    set "STEP=Git 변경 상태 확인(diff)"
    goto :fail
)

:: 4. 이전 미전송 커밋까지 포함하여 항상 push 성공 여부를 확인한 뒤에만 메모 정리!
set "STEP=클라우드 서버 전송(git push)"
git push origin main
if errorlevel 1 goto :fail

:: 5. 방금 처리한 메모 해시와 일치할 때만 memo.txt 비우기 및 이력 저장
set "STEP=처리 완료된 메모 정리(--clear-memo)"
python -X utf8 automation\main.py --clear-memo
if errorlevel 1 goto :fail

:: 6. 순수 본문 클립보드 복사 및 블로그 글쓰기 창 열기
set "STEP=클립보드 본문 복사"
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; Get-Content -LiteralPath 'automation\output\blog_clipboard.txt' -Raw -Encoding UTF8 | Set-Clipboard"
if errorlevel 1 goto :fail

start notepad.exe "automation\output\blog_draft.txt"
start "" "https://blog.naver.com/dudk6424?Redirect=Write"

echo.
echo ========================================================
echo   ✓ 1. 홈페이지 클라우드 반영 및 메모 안전 처리 완료!
echo   ✓ 2. 순수 본문이 클립보드에 복사되었습니다! (Ctrl+V)
echo ========================================================
timeout /t 7
exit /b 0

:fail
echo.
echo ========================================================
echo   ✗ [오류 중단] '%STEP%' 단계에서 문제가 발생하여 중단했습니다.
echo   ✗ 메모 상태는 automation\input\memo.txt 및 logs\memo_history.txt를 확인하세요.
echo ========================================================
pause
exit /b 1