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

# 지역 매트릭스
REGIONS = [
    {"area": "부산 동래구(사직동·온천동·명륜동·안락동)", "short": "동래구 사직동"},
    {"area": "부산 금정구(부곡동·장전동·구서동·남산동)", "short": "금정구 부곡동"},
    {"area": "부산 해운대구(우동·좌동·재송동·센텀)", "short": "해운대구 우동"},
    {"area": "부산 부산진구(서면·부전동·양정동·개금동)", "short": "부산진구 서면"},
    {"area": "부산 연제구(연산동) 및 수영구(광안동)", "short": "연제구·수영구"},
    {"area": "부산 사상구(감전동·주례동·학장동)", "short": "사상구 감전동"},
    {"area": "부산 북구(덕천동·화명동·구포동)", "short": "북구 화명동"},
    {"area": "부산 사하구(하단동·괴정동·장림동)", "short": "사하구 하단동"},
    {"area": "부산 남구(대연동·용호동) 및 동구(범일동)", "short": "남구 대연동"},
    {"area": "부산 강서구(명지동) 및 기장군(정관읍)", "short": "강서구 명지·기장"},
    {"area": "양산(물금읍·증산·석산·덕계·산막공단)", "short": "양산 물금·석산"},
    {"area": "김해(장유·율하·내외동·삼계동·진영)", "short": "김해 장유·내외동"},
    {"area": "창원(성산·의창)·마산·진해 및 경남 전역", "short": "창원·마산·경남"}
]

# 철거/폐기물 주제 리스트 (사장님의 구어체 경험담 스타일)
TOPICS = [
    {
        "category": "상가 원상복구 및 식당·카페 폐업 철거",
        "sub_kw": "상가철거, 식당폐업철거, 업소용냉장고처분, 주방집기, 원상복구, 닥트철거",
        "title_tpl": "{short} 상가 원상복구 철거 및 식당 폐업 업소용 냉장고·주방집기 정리 후기",
        "story": (
            "날씨가 선선해지긴 했는데, 현장에서 땀 흘리며 일하다 보면 그 소리가 그 소리죠 뭐 ㅎㅎ 땀 뻘뻘 흘리며 다녀온 현장 이야기 풀어볼게요.\n\n"
            "이번에 다녀온 곳은 {short}에 있는 상가예요. 면적이 꽤 넓어서 눈앞이 살짝 아찔하긴 했는데, 뭐 어쩌겠어요? 부딪혀야지!\n\n"
            "상가 철거랑 내부 원상복구는 생각보다 손이 진짜 많이 가거든요. 홀에 있는 가벽이나 천장 텍스 뜯어내는 건 기본이고, 주방 안에 처박혀 있던 무거운 업소용 냉장고랑 싱크대, 닥트까지 싹 다 비워내야 하니까요.\n\n"
            "현장에서 직접 일해보면 느끼는 거지만, 철거는 속도도 중요하지만 결국 뒷정리랑 폐기물 반출이 반 이상 먹고 들어가요. 가벽 부수고 나면 마대자루가 산더미처럼 쌓이는데, 이걸 중간중간 안 치우면 발 디딜 틈도 없고 안전사고 나기 딱 좋거든요.\n\n"
            "1톤 트럭 대놓고 마대에 담아서 내리고, 또 싣고.. 무한 반복입니다. 솔직히 쉽다면 거짓말이죠. 몸은 고단해도 다 끝내놓고 빗자루로 바닥 싹 쓸어드릴 때 그 희열이란!\n\n"
            "\"사장님, 덕분에 속이 다 시원하네요~\" 하고 손님이 음료수 하나 건네주실 때 그 맛에 이 일 합니다. 😎"
        ),
        "checklist": [
            "주방 내 콘크리트 방수턱(하스리) 파쇄 포함 여부",
            "업소용 냉장고, 제빙기, 식기세척기 등 주방 집기 일괄 폐기 범위",
            "건물 관리사무소 원상복구 기준 및 사다리차 진입 여건"
        ]
    },
    {
        "category": "가정집 대형폐기물·유품정리 및 가전 수거",
        "sub_kw": "유품정리, 가정집폐기물, 냉장고버리기, 세탁기폐기, 장롱소파처분, 빈집정리",
        "title_tpl": "{short} 가정집 대형폐기물 정리, 유품정리 및 냉장고·세탁기·장롱 일괄 수거",
        "story": (
            "연이은 날씨 변화 속에서도 현장 작업은 멈출 수 없죠! 이번에 다녀온 곳은 {short}의 한 가정집 폐기물 처리 현장입니다.\n\n"
            "보시죠 엄청 많죠 쓰레기? 가정집이라고 쓰레기가 절대 작은 게 아닙니다. 적게는 수년, 길게는 몇십 년 살시면서 크게 정리 안 하시면 안 쓰는 잡동사니와 대형 가구들이 정말 많이 쌓이기 마련이거든요.\n\n"
            "양문형 냉장고, 드럼세탁기, 무거운 장롱이랑 소파, 돌침대에다가 베란다와 방마다 가득 찬 잔짐들까지.. 박스랑 마대 정리해가며 수많은 먼지 속에서 꺼내고 또 1층까지 내리고 날씨도 더운데 정말 쉽지 않은 작업입니다.\n\n"
            "하지만 이걸 누가 합니까? 저희 대봉개발이 직접 갑니다! 정말 양심적으로 깔끔하게 일처리 해드리고요, 항상 작업 끝나고 나면 손님들이 \"정말 깔끔하게 해줬다\"고 칭찬을 아끼지 않으시죠.\n\n"
            "전문 청소업체처럼 새집처럼 만들어주지는 못해도, 아무것도 없는 깨끗한 빈집으로는 확실하게 만들어 드립니다~!"
        ),
        "checklist": [
            "버리실 대형 가전(냉장고·세탁기 등) 및 가구(장롱·침대·소파) 품목",
            "옷가지, 이불, 책 등 마대자루에 담아야 할 잔짐의 양",
            "건물 층수 및 엘리베이터 유무 (계단 작업 여부)"
        ]
    },
    {
        "category": "공장·창고·지하주차장·구조물 철거",
        "sub_kw": "공장철거, 창고철거, 지하주차장철거, 심야보일러철거, 골대철거, 구조물철거",
        "title_tpl": "{short} 공장·창고·지하주차장 철거 및 노후 심야보일러·구조물 해체 작업",
        "story": (
            "일반 상가랑은 또 다른 긴장감이 흐르는 특수 철거 현장 다녀왔습니다. 이번에 다녀온 곳은 {short}의 공장 및 구조물 철거 현장이에요.\n\n"
            "공장이나 창고, 지하주차장 구조물, 혹은 옥상에 방치된 무거운 심야보일러나 학교 운동장 축구골대 같은 철구조물 철거는 무작정 부수면 큰일 납니다. 안전이 최우선이니까요!\n\n"
            "무게가 수백 킬로그램씩 나가는 구조물은 주변 보양을 철저히 한 뒤 운반 가능한 크기로 정밀하게 절단하고, 땅속에 콘크리트 기초가 묻혀 있는 곳은 파쇄(하스리) 작업까지 완벽하게 병행해야 완벽합니다.\n\n"
            "할 때는 '이걸 언제 다하지?' 싶어도 다 하고 나면 그렇게 뿌듯할 수가 없어요. 대봉개발에 불가능이란 없습니다. 위험하고 손 많이 가는 철거 작업, 깔끔한 마무리까지 확실하게 책임집니다!"
        ),
        "checklist": [
            "철거할 구조물(보일러, 철골, 판넬, 골대 등)의 규격 및 사진",
            "바닥 콘크리트 고정부 파쇄(하스리) 및 평탄화 마감 필요 여부",
            "차량 진입 및 장비 작업 공간 확보 여부"
        ]
    },
    {
        "category": "사무실·학원 가벽 칸막이 철거 및 사업장 폐기물",
        "sub_kw": "사무실철거, 학원철거, 가벽철거, 천장텍스철거, 데코타일철거, 사업장폐기물",
        "title_tpl": "{short} 사무실·학원 가벽 칸막이 원상복구 철거 및 사업장 대량 폐기물 반출",
        "story": (
            "학원이나 사무실 원상복구 철거 건으로 {short}에 다녀왔습니다. 여러 개의 방으로 쪼개져 있던 가벽을 뜯어내고 원상복구를 해야 하는 현장이었어요.\n\n"
            "유리 칸막이나 래핑 가벽을 깔끔하게 해체하고 나면 천장 텍스나 바닥 데코타일에 손상이 없는지 꼼꼼하게 살펴야 관리실 검수를 한 번에 통과할 수 있습니다. 철거하면서 나오는 폐목재, 석고보드, 폐합성수지 잔재물들도 산더미처럼 쌓이죠.\n\n"
            "여기에 쓰던 책상, 의자, 파티션 같은 사무실 집기류까지 차종(1톤, 2.5톤)에 맞춰 한 번에 싹 싣고 나면 속이 다 시원합니다.\n\n"
            "이사철 사무실 정리, 폐업 정리, 각종 폐기물 처리까지 저희가 직접 가서 견적 봐드리고 합리적으로 처리해 드리니까요. 부산, 경남 전지역 어디든 편하게 연락 주세요!"
        ),
        "checklist": [
            "칸막이(석고·목재·유리) 철거 범위 및 천장·바닥 원상복구 여부",
            "처분할 사무용 가구 및 사업장 폐기물 대략적인 물량",
            "엘리베이터 양중 가능 여부 및 작업 시간대 확인"
        ]
    }
]

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

    reg_idx = day_num % len(REGIONS)
    top_idx = (day_num // 2 + datetime.now().hour) % len(TOPICS)
    region = REGIONS[reg_idx]
    topic = TOPICS[top_idx]

    if memo_content:
        tag = f"실제 현장 작업 기록 · {today_str}"
        title = f"[{datetime.now().strftime('%m월 %d일')] {region['short']} 철거 및 폐기물 정리 실제 현장 후기"
        story_body = memo_content
        checklist_items = topic["checklist"]
        with open(memo_path, "w", encoding="utf-8") as wf:
            wf.write("")
    else:
        tag = f"{region['short']} · {topic['category']}"
        title = topic["title_tpl"].format(short=region["short"])
        story_body = topic["story"]
        checklist_items = topic["checklist"]

    check_html = "".join([f"<li>{item}</li>" for item in checklist_items])
    check_text = "\n".join([f"  ✔ {item}" for item in checklist_items])

    new_post_html = f"""<article class="auto-post">
  <span class="tag">{tag}</span>
  <h3>{title}</h3>
  <p>{story_body.replace(chr(10)+chr(10), '</p><p>')}</p>
  <p style="font-size:14px;color:#2c4a3e;background:#f4f7f5;padding:12px 16px;border-radius:4px;"><strong>💡 빠른 견적 상담 전 체크포인트:</strong><br/>{' / '.join(checklist_items)}</p>
  <div class="meta">📍 중점 출장지: {region['area']} | 🔎 관련분야: {topic['sub_kw']} | 📞 직통 문의: {COMPANY_INFO['phone']}</div>
</article>"""

    success = update_index_html(new_post_html)

    hashtags = "#" + " #".join([k.strip() for k in topic["sub_kw"].split(",")]) + f" #{region['short'].split()[0]}철거 #{region['short'].split()[0]}폐기물 #부산철거 #양산철거 #김해철거 #경남철거 #대봉개발"

    blog_text = (
        f"====================================================================\n"
        f" [네이버 블로그 상위노출 맞춤 원고 - {today_str}]\n"
        f" * 팁: 현장 사진 3~5장만 글 사이사이에 넣고 그대로 발행하세요!\n"
        f"====================================================================\n\n"
        f"[제목 (그대로 복사해서 블로그 제목 칸에 넣으세요)]\n"
        f"{title} (30년 경력 대봉개발)\n\n"
        f"--------------------------------------------------------------------\n"
        f"[본문 (아래부터 끝까지 복사해서 블로그 본문에 붙여넣으세요)]\n\n"
        f"안녕하세요! 대봉개발입니다.\n\n"
        f"이번에 다녀온 현장은 [{region['area']}]에 있는 {topic['category']} 현장인데요.\n\n"
        f"[여기에 현장 사진이나 작업 사진을 1장 넣어주세요]\n\n"
        f"{story_body}\n\n"
        f"[여기에 철거 중간 또는 폐기물 상차 사진을 넣어주세요]\n\n"
        f"이렇게 깔끔하게 정리하고 나면 바닥도 싹 쓸어드립니다! 전문 청소업체처럼 새집처럼 만들어주지는 못해도, 아무것도 없는 깨끗한 빈집이나 원상복구된 공간으로는 확실하게 만들어 드립니다~\n\n"
        f"이사철 이사짐 정리, 사무실 정비, 폐업 정리, 가정집 정리, 폐기물 처리 등등!\n"
        f"저희가 직접 가서 견적 봐드리고 합리적으로 처리해 드립니다.\n\n"
        f"부산, 양산, 김해, 경남 전 지역 어디든 달려가니깐요! 편하게 연락 주세요~\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 대봉개발 (숨고 철거·폐기물 최고 평점 & 최고의 고수)\n"
        f"📍 출장 가능 지역: 부산 · 양산 · 김해 및 경남 전 지역 어디든\n"
        f"🛠 주요 업무: 상가·식당·사무실·학원 원상복구 / 공장·주차장·보일러 철거 / 가정집·사업장 폐기물 및 유품정리\n"
        f"📞 직통 전화 및 문자 상담: {COMPANY_INFO['phone']}\n"
        f"🌐 공식 홈페이지: https://daebong-busan.netlify.app/\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{hashtags}\n"
    )

    draft_path = os.path.join(OUTPUT_DIR, "blog_draft.txt")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(blog_text)

    if success:
        print(f"✓ 업데이트 성공: {title}")

if __name__ == "__main__":
    run_automation()