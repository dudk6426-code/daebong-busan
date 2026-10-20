import os
from datetime import datetime

# 1. 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

COMPANY_INFO = {
    "name": "대봉개발",
    "phone": "010-8535-9787",
    "location": "부산광역시 동래구 사직동",
    "experience": "30년 경력"
}

def log_event(status, message, cost_krw=0):
    log_file = os.path.join(LOGS_DIR, "execution.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{status}] 비용: {cost_krw}원 | {message}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)

def run_test_mode():
    print("[대봉개발 자동화 시스템 - 미리보기 생성 모드]")
    
    # 1. 입력 메모 확인
    memo_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    
    if memo_files:
        memo_path = os.path.join(INPUT_DIR, memo_files[0])
        with open(memo_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        title = "현장 시공 기록 (제공된 메모 기반)"
        body_text = f"대봉개발({COMPANY_INFO['location']}) 현장 작업 기록입니다.\n\n[확인된 작업 메모]\n{content}\n\n문의: {COMPANY_INFO['phone']}"
        html_content = f"""
        <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-top: 20px; background-color: #fafafa;">
            <h3 style="color: #2c3e50; margin-top: 0;">{title}</h3>
            <p style="white-space: pre-line; line-height: 1.6; color: #333;">{content}</p>
            <p style="color: #666; font-size: 0.9em; margin-bottom: 0;"><strong>소재지:</strong> {COMPANY_INFO['location']} | <strong>문의:</strong> {COMPANY_INFO['phone']}</p>
        </div>
        """
    else:
        title = "상가 원상복구 및 철거 상담 전 확인 사항"
        body_text = (
            f"안녕하세요, {COMPANY_INFO['experience']} 철거 전문 대봉개발입니다.\n\n"
            "상가 원상복구 및 내부 철거 상담 시 다음 사항을 미리 확인해 주시면 정확한 안내가 가능합니다:\n"
            "1. 철거 대상 공간의 전체 사진 및 바닥·천장 상태\n"
            "2. 건물 내 폐기물 반출 경로(엘리베이터 사용 여부 또는 계단 폭)\n"
            "3. 건물 관리사무소 원상복구 기준 확인\n\n"
            f"지역: 부산·양산·김해 (사직동 기준 1시간 이내)\n"
            f"상담 문의: {COMPANY_INFO['phone']}"
        )
        html_content = f"""
        <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-top: 20px; background-color: #fdfdfd;">
            <h3 style="color: #2c3e50; margin-top: 0;">{title}</h3>
            <p style="line-height: 1.6; color: #333;">{COMPANY_INFO['experience']} 철거 전문 대봉개발입니다. 상담 전 아래 사항을 확인해 주세요.</p>
            <ol style="line-height: 1.8; color: #444;">
                <li>철거 대상 공간의 전체 사진 및 바닥·천장 상태</li>
                <li>건물 내 폐기물 반출 경로(엘리베이터 사용 여부 또는 계단 폭)</li>
                <li>건물 관리사무소 원상복구 기준 확인</li>
            </ol>
            <p style="color: #666; font-size: 0.9em; margin-bottom: 0;"><strong>작업 가능 지역:</strong> 부산·양산·김해 (사직동 기준 1시간 이내) | <strong>문의:</strong> {COMPANY_INFO['phone']}</p>
        </div>
        """

    # 2. 블로그용 텍스트 저장
    blog_output_path = os.path.join(OUTPUT_DIR, "blog_draft.txt")
    with open(blog_output_path, "w", encoding="utf-8") as f:
        f.write(f"제목: {title}\n\n{body_text}")

    # 3. 로컬 안전 미리보기 HTML 파일 저장 (기존 index.html은 전혀 건드리지 않음)
    preview_path = os.path.join(OUTPUT_DIR, "preview.html")
    preview_full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>[미리보기] 대봉개발 홈페이지 반영 예정 초안</title>
</head>
<body style="font-family: sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px;">
    <div style="background-color: #e8f4fd; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 0.9em; color: #0c5460;">
        ℹ️ <strong>검토용 로컬 미리보기:</strong> 실제 홈페이지에 반영하기 전 확인하는 화면입니다.
    </div>
    <h2>대봉개발 시공/안내 추가 초안 미리보기</h2>
    {html_content}
</body>
</html>"""

    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(preview_full_html)

    log_event("SUCCESS", f"미리보기 및 초안 생성 완료: {title}", cost_krw=0)
    print("✓ 결과 생성 완료:")
    print("  - 블로그 초안: automation/output/blog_draft.txt")
    print("  - 웹 미리보기: automation/output/preview.html")

if __name__ == "__main__":
    run_test_mode()