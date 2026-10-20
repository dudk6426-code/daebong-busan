@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================
echo   대봉개발 자동화 시스템 실행 중...
echo ==============================================
echo.

python main.py

if exist "output\preview.html" (
    echo.
    echo [완료] 검토용 미리보기 화면을 브라우저로 엽니다.
    start "" "output\preview.html"
) else (
    echo.
    echo [안내] 미리보기 파일이 생성되지 않았습니다.
)

echo.
echo 작업을 마치려면 아무 키나 누르세요...
pause >nul