import os
import re
import random
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

# 1. 세부 지역 리스트 (구/동 및 경남 거점 순환)
REGIONS = [
    {"area": "부산 동래구(사직동·온천동·명륜동·안락동)", "short": "동래구 사직동·온천동"},
    {"area": "부산 금정구(부곡동·장전동·구서동·남산동)", "short": "금정구 부곡동·구서동"},
    {"area": "부산 해운대구(우동·좌동·재송동·반여동·센텀)", "short": "해운대 우동·재송동"},
    {"area": "부산 부산진구(서면·부전동·양정동·개금동·가야동)", "short": "부산진구 서면·양정동"},
    {"area": "부산 연제구(연산동·거제동) 및 수영구(광안동·망미동)", "short": "연제구 연산동·수영구"},
    {"area": "부산 사상구(감전동·주례동·학장동·엄궁동)", "short": "사상구 감전동·학장동"},
    {"area": "부산 북구(덕천동·화명동·구포동·만덕동)", "short": "북구 화명동·덕천동"},
    {"area": "부산 사하구(하단동·괴정동·장림동·다대동)", "short": "사하구 하단동·괴정동"},
    {"area": "부산 남구(대연동·용호동·문현동) 및 동구(초량·범일동)", "short": "남구 대연동·동구 범일동"},
    {"area": "부산 강서구(명지동·녹산공단·대저동) 및 기장군(정관·일광)", "short": "강서구 명지·기장 정관"},
    {"area": "양산(물금·증산·석산·덕계·평산·웅상·산막공단)", "short": "양산 물금·석산·덕계"},
    {"area": "김해(장유·율하·내외동·삼계동·진영·주촌·어방동)", "short": "김해 장유·내외동·삼계"},
    {"area": "창원(성산·의창)·마산(합성·양덕)·진해(용원) 및 경남 전역", "short": "창원·마산·진해·경남"}
]

# 2. 세부 철거 & 폐기물 주제 리스트 (롱테일 키워드 + 실제 현장 노하우 어조)
TOPICS = [
    {
        "category": "식당·카페 폐업철거 및 주방용품·가전 폐기",
        "sub_kw": "상가철거, 식당폐업철거, 업소용냉장고, 주방집기처분, 닥트철거, 원상복구",
        "title_tpl": "{short} 식당·카페 상가 원상복구 철거 및 주방용품·업소용냉장고 폐기물 정리",
        "story": (
            "상가 계약 기간이 끝나가거나 부득이하게 식당·카페를 정리하실 때 가장 막막한 게 바로 내부 철거와 무거운 주방 집기들입니다. "
            "현장에 나가보면 홀 쪽의 석고보드 가벽이나 천장 텍스, 바닥 데코타일 철거뿐만 아니라 주방 안에 들어찬 대형 업소용 냉장고, 테이블 냉장고, 제빙기, 스테인리스 싱크대와 작업대, 그리고 천장에 매달린 후드와 닥트 배관까지 손갈 곳이 한두 군데가 아니거든요.\n\n"
            "특히 건물주나 관리사무소에서 요구하는 원상복구 기준이 까다로운 곳은 처음에 지어졌던 상태 그대로 깔끔하게 비워줘야 보증금 문제없이 퇴거하실 수 있습니다. "
            "저희 대봉개발은 30년 동안 수많은 매장을 정리해 본 경험으로, 철거 시작 전 엘리베이터 보양 작업이나 사다리차 진입 여건부터 꼼꼼히 체크해서 옆 가게에 소음이나 분진 피해가 가지 않도록 속전속결로 작업을 마무리해 드립니다."
        ),
        "checklist": [
            "주방 내 콘크리트 방수턱(하스리 작업) 파쇄 포함 여부 확인",
            "업소용 냉장고, 제빙기, 식기세척기, 그릇 등 주방용품 일괄 폐기 및 정리 범위",
            "외부 돌출 간판 및 어닝, 에어컨 실외기 철거 동시 진행 여부"
        ]
    },
    {
        "category": "가정집 대형폐기물·유품정리·가전제품 수거",
        "sub_kw": "유품정리, 가정집폐기물, 냉장고버리기, 세탁기폐기, 장롱소파처분, 빈집정리, 생활쓰레기",
        "title_tpl": "{short} 가정집 생활폐기물·유품정리 및 냉장고·세탁기·대형가구 일괄 수거",
        "story": (
            "살면서 집안을 한번 싹 비워야 할 때가 있죠. 부모님이 계시던 집의 유품정리나 빈집 정리, 혹은 이사를 앞두고 오래된 살림살이를 한꺼번에 버려야 할 때 혼자서 스티커 붙이고 밖으로 꺼내는 건 사실상 불가능에 가깝습니다. "
            "양문형 냉장고나 김치냉장고, 드럼세탁기 같은 무거운 가전제품부터 장롱, 돌침대, 흙침대, 소파, 매트리스, 그리고 베란다와 창고에 수십 년간 쌓여 있던 주방용품과 잔짐들까지 막상 꺼내놓으면 1톤 트럭 몇 대 분량이 훌쩍 넘어가곤 합니다.\n\n"
            "엘리베이터가 없는 주택 2~3층이거나 골목이 좁은 현장이라도 걱정하실 필요 없습니다. 현장 여건에 맞춰 숙련된 인력과 1톤·2.5톤 차량, 필요시 사다리차까지 동원해서 집안에 손상 없이 깔끔하게 반출하고 빗자루질까지 해드리고 나옵니다."
        ),
        "checklist": [
            "버리실 대형 가전(냉장고·세탁기·TV 등)과 가구(장롱·침대·소파) 대략적인 개수",
            "옷가지, 이불, 책, 그릇 등 마대자루에 담아야 할 잔짐(생활폐기물)의 양",
            "건물 층수 및 엘리베이터 유무(또는 계단 작업·사다리차 사용 가능 여부)"
        ]
    },
    {
        "category": "주차장·공장·창고·특수 구조물 및 골대·보일러 철거",
        "sub_kw": "지하주차장철거, 공장철거, 건물철거, 심야보일러철거, 조형물철거, 골대철거",
        "title_tpl": "{short} 공장·창고·지하주차장 철거 및 노후 심야보일러·조형물·골대 해체 작업",
        "story": (
            "일반 상가 인테리어 철거와 달리 공장이나 창고, 지하주차장 구조물, 혹은 옥상에 방치된 대형 심야보일러나 운동장 축구골대·조형물 철거는 안전과 장비 운용이 생명입니다. "
            "무게가 수백 킬로그램에서 몇 톤씩 나가는 철골 구조물이나 보일러 본체는 그냥 들어낼 수가 없기 때문에, 불꽃이 튀지 않게 주변 보양을 철저히 한 뒤 운반 가능한 크기로 정밀하게 분할 절단해야 하거든요.\n\n"
            "또 학교 운동장 골대나 외부 조형물처럼 땅속에 콘크리트 기초가 깊게 묻혀 있는 경우에는 바닥을 굴착해서 지중 고정부까지 뿌리째 파쇄(하스리)하고 평탄하게 되메우기까지 해줘야 사고 위험이 없습니다. "
            "지하주차장처럼 층고가 낮아 큰 차가 못 들어가는 곳도 현장 조건에 딱 맞는 소형 장비와 차량을 투입해 군더더기 없이 해결해 드립니다."
        ),
        "checklist": [
            "철거할 구조물(보일러, 골대, 조형물, 샌드위치판넬 가설건축물 등)의 사진 및 위치",
            "바닥 콘크리트 고정부 파쇄(굴착) 및 평탄화 마감 필요 여부",
            "옥상·지하 등 특수 공간의 경우 장비 진입 폭과 사다리차·크레인 작업 공간 확인"
        ]
    },
    {
        "category": "학원·사무실·오피스 칸막이 철거 및 사업장 폐기물",
        "sub_kw": "사무실철거, 학원철거, 가벽철거, 천장텍스철거, 바닥데코타일철거, 사업장폐기물, 1톤트럭폐기물",
        "title_tpl": "{short} 사무실·학원 가벽 칸막이 원상복구 철거 및 사업장 대량 폐기물 반출",
        "story": (
            "학원이나 사무실, 독서실처럼 방을 여러 개로 쪼개서 쓰던 공간은 퇴거할 때 칸막이(가벽) 철거와 바닥 본드 제거, 천장 원상복구가 핵심입니다. "
            "유리 칸막이나 래핑 가벽을 뜯어내고 나면 천장 텍스가 손상된 곳이 없는지, 바닥 데코타일이나 카페트를 걷어낸 자리에 단차가 생기지 않는지 꼼꼼하게 봐야 관리실 검수를 한 번에 통과할 수 있습니다.\n\n"
            "철거하면서 쏟아져 나오는 폐목재, 석고보드, 유리, 폐합성수지 같은 인테리어 혼합 폐기물부터 미처 못 챙기고 버려야 할 사무용 책상, 회전의자, 파티션, 철제 캐비닛, 창고 적치물까지 차종(1톤, 2.5톤, 집게차)에 맞춰 한 번에 싹 실어 나릅니다. "
            "주말이나 야간에만 작업이 가능한 오피스 빌딩도 일정에 맞춰 유연하게 작업해 드립니다."
        ),
        "checklist": [
            "칸막이(석고·목재·유리) 총 길이와 천장 텍스·조명 원상복구 포함 여부",
            "바닥재(데코타일, 카페트, OA플로어 등) 철거 범위 및 엘리베이터 양중 가능 시간",
            "함께 처분할 사무용 가구·집기류 등 사업장 폐기물 물량 확인"
        ]
    }
]

# 3. AI 티를 없애는 자연스러운 도입부 인사말 (랜덤 선택)
INTROS = [
    "날씨가 꽤 쌀쌀해졌는데 다들 현장 일이나 매장 정리 준비는 잘 되어가시는지 모르겠습니다. 현장에서 직접 땀 흘리며 발로 뛰는 30년 경력 철거·폐기물 전문 대봉개발입니다.",
    "요즘 상가 이전이나 집안 정리 때문에 전화 주시는 사장님, 고객님들이 부쩍 많으십니다. 숨고(Soomgo) 철거·폐기물 분야에서 고객님들이 직접 뽑아주신 최고 평점 & '최고의 고수' 대봉개발입니다.",
    "철거랑 폐기물 처리, 막상 알아보려고 하면 부르는 게 값이고 어디에 맡겨야 뒷탈이 없을지 고민되시죠? 사직동 본점을 거점으로 부산·양산·김해·경남 어디든 달려가는 30년 베테랑 대봉개발입니다.",
    "현장 일이라는 게 말만 번지르르하게 한다고 되는 게 아니라, 결국 시작부터 마지막 빗자루질까지 얼마나 깔끔하게 끝내느냐가 핵심이거든요. 믿고 맡길 수 있는 30년 경력의 대봉개발에서 오늘도 실전 팁을 하나 정리해 드립니다."
]

def log_event(status, message):
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, "execution.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{status}] {message}\n")

def update_index_html(new_post_html):
    if not os.path.exists(INDEX_FILE):
        return False

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    start_marker = "<!-- AUTO_POSTS_START -->"
    end_marker = "<!-- AUTO_POSTS_END -->"

    if start_marker not in html or end_marker not in html:
        return False

    before, rest = html.split(start_marker, 1)
    middle, after = rest.split(end_marker, 1)

    existing_posts = re.findall(r'<article class="auto-post">.*?</article>', middle, flags=re.DOTALL)
    
    updated_posts = [new_post_html.strip()]
    for post in existing_posts:
        if post.strip() != new_post_html.strip():
            updated_posts.append(post.strip())
    
    # 홈페이지에 최근 8개의 세부 키워드 글이 누적되어 검색 로봇이 풍부하게 수집하도록 유지
    updated_posts = updated_posts[:8]

    new_middle = "\n" + "\n".join(updated_posts) + "\n"
    new_html = before + start_marker + new_middle + end_marker + after

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)
    return True

def run_automation():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    today_str = datetime.now().strftime("%Y.%m.%d")
    day_num = datetime.now().timetuple().tm_yday

    memo_path = os.path.join(INPUT_DIR, "memo.txt")
    memo_content = ""
    if os.path.exists(memo_path):
        with open(memo_path, "r", encoding="utf-8") as f:
            memo_content = f.read().strip()

    # 날짜와 시간을 조합해 매일 다른 [세부 지역] x [세부 철거/폐기물 주제] 매칭
    reg_idx = day_num % len(REGIONS)
    top_idx = (day_num // 2 + datetime.now().hour) % len(TOPICS)
    
    region = REGIONS[reg_idx]
    topic = TOPICS[top_idx]
    intro = random.choice(INTROS)

    if memo_content:
        tag = f"실제 현장 작업 기록 · {today_str}"
        title = f"[{datetime.now().strftime('%m월 %d일')}] {region['short']} 철거 및 폐기물 정리 실제 현장 기록"
        story_body = memo_content
        checklist_items = topic["checklist"]
        with open(os.path.join(LOGS_DIR, "memo_history.txt"), "a", encoding="utf-8") as bf:
            bf.write(f"[{today_str}]\n{memo_content}\n\n")
        with open(memo_path, "w", encoding="utf-8") as wf:
            wf.write("")
    else:
        tag = f"{region['short']} · {topic['category']}"
        title = topic["title_tpl"].format(short=region["short"])
        story_body = topic["story"]
        checklist_items = topic["checklist"]

    check_html = "".join([f"<li>{item}</li>" for item in checklist_items])
    check_text = "\n".join([f"  ✔ {item}" for item in checklist_items])

    # 1. 홈페이지(index.html)에 누적될 SEO 최적화 아티클
    new_post_html = f"""<article class="auto-post">
  <span class="tag">{tag}</span>
  <h3>{title}</h3>
  <p>{story_body.replace(chr(10)+chr(10), '</p><p>')}</p>
  <p style="font-size:14px;color:#2c4a3e;background:#f4f7f5;padding:12px 16px;border-radius:4px;"><strong>💡 빠른 견적 상담 전 체크포인트:</strong><br/>{' / '.join(checklist_items)}</p>
  <div class="meta">📍 중점 출장지: {region['area']} 및 경남 전역 | 🔎 관련분야: {topic['sub_kw']} | 📞 직통 문의: {COMPANY_INFO['phone']}</div>
</article>"""

    success = update_index_html(new_post_html)

    # 2. 네이버 블로그 상위노출(DIA+ 로직 최적화: 1,200자 내외 구어체 + 키워드 과다반복 방지 + 체류시간 유도 구성)
    hashtags = "#" + " #".join([k.strip() for k in topic["sub_kw"].split(",")]) + f" #{region['short'].split()[0]}철거 #{region['short'].split()[0]}폐기물 #부산철거 #양산철거 #김해철거 #경남철거 #대봉개발"

    blog_text = (
        f"====================================================================\n"
        f" [네이버 블로그 상위노출(DIA+ 로직) 맞춤 원고 - {today_str}]\n"
        f" * 팁: 현장 사진 3~5장만 글 사이사이에 넣고 그대로 발행하시면 효과가 배가됩니다!\n"
        f"====================================================================\n\n"
        f"[제목 (그대로 복사해서 블로그 제목 칸에 넣으세요)]\n"
        f"{title} (30년 경력 대봉개발)\n\n"
        f"--------------------------------------------------------------------\n"
        f"[본문 (아래부터 끝까지 복사해서 블로그 본문에 붙여넣으세요)]\n\n"
        f"반갑습니다! {intro}\n\n"
        f"오늘은 많은 분들이 문의하시는 【{region['area']}】 일대의 {topic['category']} 작업 시 꼭 알아두셔야 할 현실적인 부분들을 짚어드리려고 합니다.\n\n"
        f"[여기에 현장 사진이나 명함 사진을 1장 넣어주시면 좋습니다]\n\n"
        f"■ 현장에서 직접 겪어보면 왜 경험이 중요할까요?\n\n"
        f"{story_body}\n\n"
        f"간혹 무조건 싸게 해준다는 곳에만 맡겼다가 작업 도중에 폐기물 양이 많다며 추가 비용을 과하게 요구하거나, 마감 정리가 덜 되어 건물주와 얼굴 붉히는 일들이 종종 생깁니다. 그래서 처음 상담할 때부터 현장 조건을 정확하게 짚어내는 베테랑과 상의하시는 게 결국 시간과 비용을 아끼는 지름길입니다.\n\n"
        f"■ 전화 주시기 전에 이것만 미리 확인해 주세요!\n\n"
        f"상담 전화(010-8535-9787)나 문자로 문의하실 때 아래 내용을 대략적으로라도 알려주시면, 현장 방문 전에도 훨씬 정확하고 거품 없는 견적을 바로 안내받으실 수 있습니다.\n\n"
        f"{check_text}\n\n"
        f"[여기에 작업 관련 사진을 1~2장 더 넣어주시면 체류시간이 올라갑니다]\n\n"
        f"■ 부산 · 양산 · 김해 · 경남 어디든 달려갑니다!\n\n"
        f"저희 대봉개발은 사직동 본점을 중심으로 {region['area']} 현장은 물론이고 부산 전역과 양산, 김해, 창원 등 경남 어디든 거리 제한 없이 신속하게 출장 상담을 도와드리고 있습니다.\n\n"
        f"작은 가정집 폐기물 하나, 고장 난 업소용 냉장고나 세탁기 처분, 유품정리부터 상가 원상복구, 공장·주차장·심야보일러·골대 철거까지! 막막한 현장이 있다면 언제든 편하게 사진 몇 장과 함께 연락 주십시오. 30년 현장 노하우와 숨고 최고 평점의 자부심으로 속 시원하게 해결해 드리겠습니다.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 대봉개발 (숨고 철거·폐기물 최고 평점 & 최고의 고수)\n"
        f"📍 출장 가능 지역: 부산 · 양산 · 김해 및 경남 전 지역 어디든\n"
        f"🛠 주요 업무: 상가·식당·사무실·학원 원상복구 / 공장·주차장·보일러·골대 철거 / 가정집·사업장 폐기물 및 유품정리\n"
        f"📞 직통 전화 및 문자 상담: {COMPANY_INFO['phone']}\n"
        f"🌐 공식 홈페이지: https://daebong-busan.netlify.app/\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{hashtags}\n"
    )

    draft_path = os.path.join(OUTPUT_DIR, "blog_draft.txt")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(blog_text)

    if success:
        log_event("SUCCESS", f"고품질 세부키워드 업데이트 완료: {title}")
        print(f"✓ [업데이트 성공] {title}")
    else:
        log_event("ERROR", "index.html 업데이트 실패")

if __name__ == "__main__":
    run_automation()