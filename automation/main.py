import os
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
INDEX_FILE = os.path.join(PROJECT_DIR, "index.html")
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

COMPANY_INFO = {
    "name": "대봉개발",
    "phone": "010-8535-9787",
    "location": "부산광역시 동래구 사직동",
    "area": "부산 · 양산 · 김해 및 경남 전 지역 어디든",
    "badge": "숨고(Soomgo) 선정 철거·폐기물 분야 최고 평점 & 최고의 고수"
}

# 고객이 실제 검색하는 [지역 + 세부 작업] 롱테일 키워드 템플릿 (허위 후기가 아닌 100% 사실 기반 전문 안내)
SEO_TEMPLATES = [
    {
        "tag": "부산 동래구·금정구·연제구 | 상가 원상복구",
        "title": "상가·식당·카페 퇴거 시 내부 가벽·천장·바닥 원상복구 철거 가이드",
        "body": "임대차 계약 종료로 인한 상가 원상복구 시 관리사무소 및 임대인과의 사전 협의가 필수입니다. 대봉개발은 사직동 본점을 거점으로 동래구, 금정구, 연제구 등 부산 전역의 식당 주방 설비 해체, 석고보드 가벽 철거, 천장 텍스 및 바닥 데코타일 철거부터 폐기물 반출까지 30년 경력의 노하우로 깔끔하게 원상복구를 진행합니다."
    },
    {
        "tag": "양산 물금·석산·덕계 | 상가·사무실 철거 및 폐기물",
        "title": "양산 지역 상가·학원·사무실 칸막이 철거 및 대량 폐기물 신속 수거 안내",
        "body": "양산 물금신도시, 석산, 덕계 등 상가 밀집 지역의 학원·사무실 이전 및 폐업 시 발생하는 내부 인테리어 철거와 대형 집기·폐기물 처리를 일괄 상담합니다. 엘리베이터 양중 또는 사다리차 작업 여건을 미리 파악하여 주변 매장의 영업 피해를 최소화하고 신속하게 폐기물을 반출합니다."
    },
    {
        "tag": "김해 장유·내외동·삼계 | 폐기물 처리·유품정리",
        "title": "김해 전 지역 사업장 폐기물, 인테리어 잔재물 및 가정집 생활폐기물·유품정리",
        "body": "김해 장유, 내외동, 삼계동 및 인근 공단·사업장에서 발생하는 혼합 폐기물, 건설·인테리어 잔재물, 창고 정리 폐기물과 가정집 이사·유품정리 시 나오는 대형 생활폐기물을 1톤·2.5톤 차량으로 신속하게 수거합니다. 철거 없이 폐기물 수거만 필요한 현장도 합리적인 비용으로 안내해 드립니다."
    },
    {
        "tag": "부산 해운대구·수영구·남구 | 매장·오피스 철거",
        "title": "해운대·수영·남구 상가 인테리어 부분 철거 및 바닥·천장 해체 작업 안내",
        "body": "신규 창업을 위한 매장 리모델링 전 기존 인테리어 부분 철거부터 전체 철거까지 현장 조건에 맞춰 작업합니다. 소음과 분진 관리가 중요한 복합 상가나 오피스 빌딩에서도 30년 현장 경험을 바탕으로 안전하게 구조물을 해체하고 뒷정리까지 완벽하게 마무리합니다."
    },
    {
        "tag": "부산 사상구·북구·강서구 | 공장·창고·구조물 철거",
        "title": "사상·북구·강서구 공장·창고 내부 구조물, 노후 보일러 및 대형 설비 해체",
        "body": "공장, 창고, 옥상 등에 방치된 노후 심야보일러, 철골 구조물, 가설 건축물 및 지하주차장 구조물 해체 작업을 전문 장비와 인력으로 안전하게 처리합니다. 무거운 설비의 분할 절단부터 반출, 현장 청소까지 원스톱으로 해결해 드립니다."
    },
    {
        "tag": "창원·마산·진해·경남 전역 | 철거·폐기물 출장 상담",
        "title": "부산·양산·김해부터 창원·경남 어디든 달려가는 숨고 '최고의 고수' 대봉개발",
        "body": "어디에 맡겨야 할지 막막한 철거와 폐기물 처리, 숨고(Soomgo) 철거·폐기물 분야 최고 평점 및 '최고의 고수'로 선정된 대봉개발에 문의하세요. 현장 사진과 위치, 층수만 알려주시면 경남 어디든 거품 없는 정직한 견적과 깔끔한 시공으로 보답합니다."
    }
]

def log_event(status, message):
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, "execution.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{status}] {message}\n")

def update_index_html(new_post_html):
    if not os.path.exists(INDEX_FILE):
        print("[오류] index.html 파일을 찾을 수 없습니다.")
        return False

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    start_marker = "<!-- AUTO_POSTS_START -->"
    end_marker = "<!-- AUTO_POSTS_END -->"

    if start_marker not in html or end_marker not in html:
        print("[오류] index.html에 자동 업데이트 구역 표식이 없습니다.")
        return False

    before, rest = html.split(start_marker, 1)
    middle, after = rest.split(end_marker, 1)

    # 기존 게시물들을 추출하여 최대 5개까지만 유지 (최신 글이 맨 위로 오도록 누적)
    existing_posts = re.findall(r'<article class="auto-post">.*?</article>', middle, flags=re.DOTALL)
    
    # 방금 만든 글과 완전히 똑같은 제목이 이미 맨 위에 있다면 중복 삽입 방지, 아니면 맨 앞에 추가
    updated_posts = [new_post_html.strip()]
    for post in existing_posts:
        if post.strip() != new_post_html.strip():
            updated_posts.append(post.strip())
    
    # 홈페이지가 너무 길어지지 않게 최신 6개 글만 유지
    updated_posts = updated_posts[:6]

    new_middle = "\n" + "\n".join(updated_posts) + "\n"
    new_html = before + start_marker + new_middle + end_marker + after

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)
    return True

def run_automation():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    today_str = datetime.now().strftime("%Y.%m.%d")
    memo_path = os.path.join(INPUT_DIR, "memo.txt")
    memo_content = ""

    if os.path.exists(memo_path):
        with open(memo_path, "r", encoding="utf-8") as f:
            memo_content = f.read().strip()

    # 1. memo.txt에 현장 메모가 적혀 있는 날 -> 실제 현장 기록으로 생성 후 메모 비우기
    if memo_content:
        tag = f"실제 현장 기록 · {today_str}"
        title = f"[{datetime.now().strftime('%m월 %d일')}] 대봉개발 철거·폐기물 정리 현장 작업 안내"
        body = memo_content
        # 사용 완료한 메모는 다음 날 중복 올라가지 않도록 백업 후 비움
        with open(os.path.join(LOGS_DIR, "memo_history.txt"), "a", encoding="utf-8") as bf:
            bf.write(f"[{today_str}]\n{memo_content}\n\n")
        with open(memo_path, "w", encoding="utf-8") as wf:
            wf.write("")
    # 2. 메모가 없는 날 -> 날짜별로 세부 지역+작업 키워드 템플릿 자동 선택
    else:
        idx = datetime.now().timetuple().tm_yday % len(SEO_TEMPLATES)
        selected = SEO_TEMPLATES[idx]
        tag = selected["tag"]
        title = selected["title"]
        body = selected["body"]

    # 홈페이지(index.html)에 삽입할 HTML 조각
    new_post_html = f"""<article class="auto-post">
  <span class="tag">{tag}</span>
  <h3>{title}</h3>
  <p>{body}</p>
  <div class="meta">🏆 {COMPANY_INFO['badge']} | 📍 출장: {COMPANY_INFO['area']} | 📞 직통 문의: {COMPANY_INFO['phone']}</div>
</article>"""

    # 실제 index.html 업데이트 실행
    success = update_index_html(new_post_html)

    # 네이버 블로그 복사용 원고(blog_draft.txt) 생성
    blog_text = (
        f"[블로그 제목]\n{title} - {COMPANY_INFO['name']}\n\n"
        f"[블로그 본문 (Ctrl+A 전체선택 후 Ctrl+C 복사해서 블로그에 붙여넣으세요)]\n"
        f"안녕하세요! {COMPANY_INFO['badge']}에 빛나는 30년 경력 철거·폐기물 전문 【{COMPANY_INFO['name']}】입니다.\n\n"
        f"■ 핵심 분야: {tag}\n\n"
        f"{body}\n\n"
        f"저희 대봉개발은 부산 사직동 본점을 거점으로 부산 전 지역, 양산, 김해 및 경남 어디든 현장 여건에 맞춰 신속하게 달려갑니다.\n\n"
        f"✔ 상가·식당·카페·사무실·학원 내부 철거 및 원상복구\n"
        f"✔ 심야보일러·옥상 구조물·지하주차장 철거\n"
        f"✔ 건설·인테리어 폐기물, 사업장 대량 폐기물, 가정집 생활폐기물·유품정리\n\n"
        f"현장 지역, 대략적인 면적, 현장 사진, 층수와 엘리베이터 유무를 문자나 전화로 알려주시면 거품 없는 합리적인 견적을 빠르게 안내해 드립니다!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 {COMPANY_INFO['name']} ({COMPANY_INFO['badge']})\n"
        f"📍 출장 지역: {COMPANY_INFO['area']}\n"
        f"📞 직통 전화상담: {COMPANY_INFO['phone']}\n"
        f"🌐 공식 홈페이지: https://daebong-busan.netlify.app/\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"#부산철거 #양산철거 #김해철거 #경남철거 #상가원상복구 #부산폐기물처리 #양산폐기물 #김해폐기물 #식당철거 #사무실원상복구 #유품정리 #대봉개발"
    )

    draft_path = os.path.join(OUTPUT_DIR, "blog_draft.txt")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(blog_text)

    if success:
        log_event("SUCCESS", f"index.html 및 블로그 원고 자동 업데이트 완료: {title}")
        print(f"✓ [성공] 홈페이지 및 블로그 초안 업데이트 완료: {title}")
    else:
        log_event("ERROR", "index.html 업데이트 실패")

if __name__ == "__main__":
    run_automation()