@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================================
echo   [대봉개발] 홈페이지 자동 업데이트 및 배포 시스템 가동
echo ========================================================
echo.

:: 1. 파이썬으로 index.html 세부 키워드 글 업데이트 및 블로그 원고 생성
python automation\main.py

:: 2. 변경된 홈페이지를 GitHub(실제 사이트)에 즉시 자동 반영
echo.
echo [진행 중] 실제 홈페이지(Netlify)로 변경 사항을 업로드합니다...
git checkout main
git pull origin main
git add index.html automation/main.py automation/run.bat
git commit -m "auto: 홈페이지 리모델링 및 세부 키워드 안내 자동 업데이트"
git push origin main

echo.
echo ========================================================
echo   ✓ 실제 홈페이지 자동 반영 완료! (약 30초 후 사이트 적용)
echo   ✓ 네이버 블로그 복사용 원고(blog_draft.txt)를 엽니다.
echo ========================================================

:: 3. 네이버 블로그에 바로 붙여넣을 수 있게 메모장 원고 자동 팝업
if exist "automation\output\blog_draft.txt" (
    start notepad.exe "automation\output\blog_draft.txt"
)

timeout /t 5