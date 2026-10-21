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

# 1. 초세부 지역 리스트 (구/동 단위 순환)
REGIONS = [
    {"full": "부산 동래구 사직동·온천동·명륜동", "short": "동래구 사직동", "city": "부산"},
    {"full": "부산 금정구 부곡동·장전동·구서동", "short": "금정구 부곡동", "city": "부산"},
    {"full": "부산 해운대구 우동·좌동·재송동·반여동", "short": "해운대 재송동", "city": "부산"},
    {"full": "부산 부산진구 서면·부전동·양정동·개금동", "short": "부산진구 양정동", "city": "부산"},
    {"full": "부산 연제구 연산동·거제동", "short": "연제구 연산동", "city": "부산"},
    {"full": "부산 수영구 광안동·남천동·망미동", "short": "수영구 광안동", "city": "부산"},
    {"full": "부산 사상구 감전동·주례동·학장동·엄궁동", "short": "사상구 감전동", "city": "부산"},
    {"full": "부산 북구 덕천동·화명동·구포동·만덕동", "short": "북구 화명동", "city": "부산"},
    {"full": "부산 사하구 하단동·괴정동·장림동·다대동", "short": "사하구 하단동", "city": "부산"},
    {"full": "부산 남구 대연동·용호동·문현동", "short": "남구 대연동", "city": "부산"},
    {"full": "부산 동구 초량동·범일동 및 중구·서구", "short": "동구 범일동", "city": "부산"},
    {"full": "부산 강서구 명지동·녹산공단·대저동", "short": "강서구 명지동", "city": "부산"},
    {"full": "부산 기장군 정관읍·기장읍·일광읍", "short": "기장군 정관읍", "city": "부산"},
    {"full": "양산 물금읍·증산·석산·덕계·평산동", "short": "양산 물금·석산", "city": "양산"},
    {"full": "김해 장유·율하·내외동·삼계동·진영읍", "short": "김해 장유·내외동", "city": "김해"},
    {"full": "창원 성산구·의창구 및 마산·진해 일대", "short": "창원·마산·진해", "city": "경남"}
]

# 2. 초세부 타겟 아이템 (고객이 실제로 급하게 검색하는 알짜 롱테일 키워드 12종)
MICRO_TARGETS = [
    {
        "item": "가정집 묵은살림·대형폐기물(냉장고·세탁기·장롱·돌침대)",
        "kw": "가정집폐기물, 냉장고버리기, 세탁기처분, 돌침대철거, 장롱소파버리기, 빈집정리",
        "scene": "가정집이라고 쓰레기가 절대 작은게아닙니다. 적게는 수년 길게는 몇십년 사시면서 집에 크게 정리안하는이상 안쓰는 잡동사니 물건들이 정말 많이 쌓이기 마련이거든요.",
        "objects": "양문형 냉장고, 김치냉장고, 세탁기 같은 무거운 가전부터 안방 장롱, 무거운 돌침대, 소파, 그리고 베란다 깊숙이 박혀있던 주방용품이랑 화분들까지",
        "action": "안에 있는 쓰레기들과 살림들을 분류해서 정리하고 버리고! 꺼집어내고 또 1층까지 내리고.. 박스랑 마대자루 수십개에 담아가며 수많은 먼지와 사투를 벌입니다.!!",
        "tip": "특히 돌침대나 대형 양문형 냉장고는 일반인들이 괜히 혼자 옮기려다 허리 다치거나 문틀 다 찍혀먹기 일쑤거든요. 처음부터 숙련된 인력이랑 장비를 불러서 한방에 빼내는게 결국 돈 아끼는 길입니다."
    },
    {
        "item": "식당·고깃집 폐업 주방용품·업소용냉장고 및 내부 원상복구 철거",
        "kw": "식당폐업철거, 상가원상복구, 업소용냉장고처분, 주방용품폐기, 닥트철거, 방수턱하스리",
        "scene": "상가 계약기간이 끝나거나 부득이하게 식당·카페를 정리하실 때 가장 막막한게 바로 내부 철거랑 무거운 주방 집기들입니다. 눈앞이 살짝 아찔할 정도로 손갈 곳이 많죠.",
        "objects": "홀에 있는 가벽이나 천장 텍스, 바닥 데코타일 뜯어내는 건 기본이고, 주방 안에 꽉 찬 업소용 45박스 냉장고, 테이블냉장고, 제빙기, 스텐 싱크대랑 그릇들, 천장 환풍 닥트까지",
        "action": "전기랑 수도, 가스 라인 안 건드리게 조심조심 살피면서 주방 집기들 먼저 싹 끌어내고요. 주방 바닥에 콘크리트로 올라온 방수턱까지 뿌레카(파쇄기)로 시원하게 깨부수고 마대에 담아 나릅니다!",
        "tip": "식당 철거는 철거 따로, 폐기물 따로 부르면 인건비가 두배로 깨집니다. 가벽 철거부터 주방 고철·폐가전 정리, 마대 폐기물 반출까지 한 팀이 와서 원스톱으로 밀어버려야 시간도 빠르고 견적도 확 줄어들어요."
    },
    {
        "item": "부모님 유품정리·시골집·빈집 일괄 정리 및 생활쓰레기 수거",
        "kw": "유품정리, 빈집정리, 시골집정리, 쓰레기집청소, 생활폐기물수거, 이민이사폐기물",
        "scene": "살다 보면 부모님이 계시던 집의 유품정리나 오랫동안 비워둔 빈집, 혹은 이사 가면서 남긴 짐들을 한꺼번에 싹 비워야 할 때가 있죠. 가족분들이 직접 하려다가 하루 종일 먼지만 마시고 포기하시는 경우가 참 많아요.",
        "objects": "오래된 옷가지, 이불, 책, 고장난 소형 전자제품부터 찬장 속 그릇, 옥상이나 창고에 방치된 묵은 쓰레기들과 대형 가구들까지",
        "action": "귀중품이나 사진처럼 따로 챙겨드려야 할 물건은 미리 말씀해주시면 따로 빼두고요, 나머지 버려야 할 폐기물들은 마대자루와 박스에 꼼꼼하게 담아서 1톤·2.5톤 트럭에 빈틈없이 차곡차곡 싣습니다.",
        "tip": "엘리베이터가 없는 주택 2~3층이거나 골목이 좁아서 차 대기가 까다로운 곳이라도 걱정 마세요. 현장 여건에 맞춰서 인력이든 사다리차든 딱 맞게 배차해서 이웃분들 눈치 안 보이게 속전속결로 비워드립니다."
    },
    {
        "item": "학원·사무실·독서실 가벽 칸막이 원상복구 철거 및 사무집기 폐기",
        "kw": "사무실철거, 학원철거, 가벽철거, 칸막이철거, 천장텍스, 바닥데코타일철거, 사업장폐기물",
        "scene": "사무실이나 학원, 병원 같은 곳은 방을 여러 개로 쪼개서 쓰다 보니 나갈 때 건물주나 관리사무소에서 원상복구 기준을 꽤 까다롭게 봅니다.",
        "objects": "석고보드 가벽, 유리 칸막이, 나무 합판 구조물은 물론이고 바닥에 본드로 딱 붙어있는 데코타일, 카페트, 그리고 버리고 가는 사무용 책상, 회전의자, 철제 캐비닛, 파티션까지",
        "action": "철거와 동시에 폐기물 반출에 엄청 신경 씁니다! 가벽 부수고 나면 폐목재랑 석고 잔재가 산더미처럼 쌓이는데, 이걸 바로바로 안 빼내면 발 디딜 틈도 없고 작업 속도가 안 나거든요. 치우고 부수고 무한반복이죠.",
        "tip": "오피스 빌딩이나 상가 건물은 평일 낮에 소음 때문에 작업을 못 하게 막는 곳도 많습니다. 미리 엘리베이터 보양 조건이랑 작업 가능 시간대만 체크해주시면 야간이든 주말이든 일정 맞춰서 깔끔하게 통과시켜 드립니다."
    },
    {
        "item": "공장·창고·지하주차장 구조물 및 옥상 심야보일러·골대·조형물 철거",
        "kw": "공장철거, 창고철거, 지하주차장철거, 심야보일러철거, 골대철거, 조형물철거, 구조물철거",
        "scene": "일반 매장 철거랑은 차원이 다른 현장이 바로 무거운 설비나 특수 구조물 철거입니다. 이건 힘만 좋다고 되는게 아니라 30년 현장 노하우랑 장비 운용이 생명이에요.",
        "objects": "옥상에 흉물처럼 방치된 대형 심야보일러, 물탱크, 학교 운동장 축구골대, 오래된 조형물, 지하주차장 철골 구조물이나 공장·창고 안의 샌드위치판넬 가설건축물까지",
        "action": "그냥 통째로 못 들어내는 놈들은 주변에 불꽃 안 튀게 안전 조치 싹 해놓고 운반 가능한 크기로 정밀하게 절단합니다. 땅속에 콘크리트 기초가 박혀있는 골대나 조형물은 바닥 굴착해서 뿌리까지 파쇄하고 흙으로 평평하게 되메우기까지 끝내주죠.",
        "tip": "지하주차장처럼 층고가 낮아서 큰 트럭이 못 들어가거나, 옥상이라 계단으로 못 내리는 현장도 사진 몇 장만 찍어서 보내주시면 사다리차나 소형 장비를 어떻게 넣을지 바로 견적과 방법을 딱 잡아드립니다."
    }
]

# 3. 날씨/도입부 멘트 블록 (AI 티 전혀 안 나는 일상 구어체 6종)
WEATHER_INTROS = [
    "요즘 날씨가 참 변덕스럽죠? 아침저녁으론 선선한가 싶다가도 작업복 입고 현장에서 한바탕 땀 쏟고 나면 등줄기가 흠뻑 젖네요 ㅎㅎ 그래도 날씨와 상관없이 저희 대봉개발의 작업은 오늘도 계속 되어집니다!",
    "바람에 기분 좋은 선선함이 느껴지는 계절이네요. 다들 하시는 일이나 매장, 집안 정리 준비는 잘 되어가시는지 모르겠습니다. 현장에서 발로 뛰는 30년 베테랑 대봉개발입니다!",
    "이번주도 정신없이 현장을 뛰어다니다 보니 벌써 하루가 다 갔네요. 몸은 좀 고단해도 찾아주시는 손님들이 계시니 힘내서 일하고 있습니다. 반갑습니다 대봉개발입니다~",
    "막상 철거랑 폐기물 처리를 알아보려고 하면 부르는게 값이고 어디에 맡겨야 뒷탈이 없을지 참 막막하시죠? 사직동에서 시작해 30년째 현장을 지키고 있는 대봉개발이 속 시원하게 알려드릴게요.",
    "현장 일이라는게 말만 번지르르하게 한다고 되는게 아니거든요. 결국 처음 들어갈 때부터 마지막 빗자루질하고 나올 때까지 얼마나 양심적으로 깔끔하게 치우느냐가 핵심이죠!"
]

# 4. 중간 현장 추임새 블록 (사장님 실제 원고 말투 그대로 반영)
MID_REACTIONS = [
    "보시죠 엄청많죠 쓰레기? 처음 현장 문 열고 들어가면 다들 한숨부터 쉬시는데, 저희 눈에는 그냥 오늘 치워야 할 일거리일 뿐입니다 ㅎㅎ",
    "벌써부터 분주하고 바쁜 손길에 정신이 하나도 없습니다. 할 때는 '이걸 언제 다 빼지?' 싶어도 잠깐 놀라면 그뿐, 바로 정신 차리고 치우다 보면 언제나 끝은 보이기 마련입니다!",
    "이 힘든 걸 누가 하냐구요? 바로 저희 대봉개발에서 합니다! 남들이 힘들다고 피하는 까다로운 현장일수록 다 치우고 났을 때 그 쾌감이 진짜 장난 아니거든요.",
    "날씨도 만만치 않은데 먼지 뒤집어써가며 꺼집어내고 내리는게 정말 쉽지 않은 작업입니다. 하지만 손발이 척척 맞는 베테랑 팀원들이 있어서 그저 든든하기만 할 뿐입니다."
]

# 5. 마무리 멘트 블록 (다양화)
CLOSINGS = [
    "이렇게 싹 다 정리하고 나면 마지막에 바닥도 한번 시원하게 쓸어드리고요! 전문 입주청소 업체는 아니라 새집처럼 반짝반짝하게 만들어주지는 못하지만, 아무것도 없는 속 시원한 빈집·빈상가로는 확실하게 만들어 드립니다~~",
    "항상 작업이 끝나고 나면 손님들이 '사장님 정말 깔끔하게 해줬다고, 고생 많으셨다'고 시원한 음료수 하나 건네주시며 칭찬을 해주시곤 합니다. 솔직히 그 맛에 30년 동안 이 일 계속하고 있습니다 😎",
    "전부 철거하고 폐기물까지 트럭에 가득 싣고 나니 정말이지 넓고 깨끗해졌네요! 마무리까지 확실하게 하고 나야 그제서야 마음 편하게 발걸음을 돌릴 수 있답니다."
]

def apply_human_touch(text):
    """
    AI 판독기를 무력화하는 '사장님 타자 습관' 자연 반영 필터
    (문맥은 해치지 않으면서 너무 완벽한 기계식 띄어쓰기를 사람처럼 자연스럽게 완화)
    """
    replacements = [
        ("작은 게 아닙니다", "작은게아닙니다"),
        ("하는 게 ", "하는게 "),
        ("라는 게 ", "라는게 "),
        ("할 때", "할때"),
        ("하니까요", "하니깐요"),
        ("거든요.", "거든요~"),
    ]
    for old, new in replacements:
        if random.random() < 0.65:  # 65% 확률로 자연스럽게 섞음 (매번 패턴이 달라지게)
            text = text.replace(old, new, 1)
    return text

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
    os.makedirs(LOGS_DIR, exist_ok=True)

    now = datetime.now()
    today_str = now.strftime("%Y.%m.%d")
    month_day = f"{now.month}월 {now.day}일"

    # 날짜+시간 시드를 이용해 매일 전혀 다른 조합 생성
    seed_num = now.timetuple().tm_yday + now.hour
    reg = REGIONS[seed_num % len(REGIONS)]
    target = MICRO_TARGETS[(seed_num * 3) % len(MICRO_TARGETS)]

    weather_intro = random.choice(WEATHER_INTROS)
    mid_reaction = random.choice(MID_REACTIONS)
    closing_remark = random.choice(CLOSINGS)

    memo_path = os.path.join(INPUT_DIR, "memo.txt")
    memo_content = ""
    if os.path.exists(memo_path):
        with open(memo_path, "r", encoding="utf-8") as f:
            memo_content = f.read().strip()

    # [A] 실제 현장 메모가 있는 날 -> 생생한 현장 일기로 작성
    if memo_content:
        tag = f"실제 현장 작업일지 · {today_str}"
        title = f"{reg['short']} 철거 및 폐기물 처리 현장 다녀왔습니다! ({month_day} 작업)"
        raw_story = (
            f"{weather_intro}\n\n"
            f"오늘 다녀온 현장은 {reg['full']} 쪽인데요. 현장에서 직접 겪은 이야기 짧게 풀어볼게요.\n\n"
            f"{memo_content}\n\n"
            f"{mid_reaction}\n\n"
            f"{closing_remark}"
        )
        with open(os.path.join(LOGS_DIR, "memo_history.txt"), "a", encoding="utf-8") as bf:
            bf.write(f"[{today_str}]\n{memo_content}\n\n")
        with open(memo_path, "w", encoding="utf-8") as wf:
            wf.write("")
    # [B] 메모가 없는 날 -> 레고 블록 조합으로 100% 독창적인 현장 노하우 & 작업 이야기 생성
    else:
        tag = f"{reg['short']} · {target['item'].split('(')[0]}"
        title = f"{reg['short']} {target['item']} 시원하게 비워드립니다!"
        raw_story = (
            f"{weather_intro}\n\n"
            f"이번에 이야기해 볼 주제는 많은 분들이 전화로 물어보시는 【{reg['full']}】 지역의 {target['item']} 작업입니다.\n\n"
            f"{target['scene']}\n\n"
            f"막상 현장에 가보면 {target['objects']} 정말 끝도 없이 나옵니다.\n\n"
            f"{mid_reaction}\n\n"
            f"{target['action']}\n\n"
            f"💡 여기서 30년 경력 사장님이 알려드리는 꿀팁 하나!\n"
            f"{target['tip']}\n\n"
            f"{closing_remark}"
        )

    final_story = apply_human_touch(raw_story)
    html_paragraphs = "</p><p>".join(final_story.split("\n\n"))

    # 홈페이지 삽입용 아티클 (즉시 전화 걸기 전환 버튼 포함!)
    new_post_html = f"""<article class="auto-post">
  <span class="tag">{tag}</span>
  <h3>{title}</h3>
  <p>{html_paragraphs}</p>
  <div style="margin-top:14px;">
    <a href="tel:01085359787" style="display:inline-block;background:#174c42;color:#fff;padding:8px 16px;border-radius:4px;text-decoration:none;font-weight:700;font-size:14px;">📞 이 작업 바로 견적 물어보기 (010-8535-9787)</a>
  </div>
  <div class="meta">🏆 {COMPANY_INFO['badge']} | 📍 출장: {reg['full']} 및 경남 전역 | 🔎 세부품목: {target['kw']}</div>
</article>"""

    success = update_index_html(new_post_html)

    # 네이버 블로그 복사용 원고 (짧은 줄바꿈 호흡 + 인간미 있는 말투 적용)
    kw_list = [k.strip() for k in target["kw"].split(",")]
    hashtags = "#" + " #".join(kw_list) + f" #{reg['short'].replace(' ', '')}철거 #{reg['short'].replace(' ', '')}폐기물 #{reg['city']}철거 #{reg['city']}폐기물처리 #대봉개발"

    blog_text = (
        f"====================================================================\n"
        f" [네이버 블로그 AI 탐지 회피 & 상위노출 원고 - {today_str}]\n"
        f" * 사진 넣는 자리에 휴대폰에 있는 현장 사진을 3~4장만 툭툭 넣어주세요!\n"
        f"====================================================================\n\n"
        f"[제목]\n"
        f"{title}\n\n"
        f"--------------------------------------------------------------------\n"
        f"[본문]\n\n"
        f"안녕하십니까 대봉개발입니다. 😊\n\n"
        f"{weather_intro}\n\n"
        f"오늘은 【{reg['full']}】 쪽에서 문의가 정말 많은\n"
        f"{target['item']} 이야기를 좀 해볼까 합니다.\n"
        f"보시죠~!\n\n"
        f"[📸 여기에 현장 입구나 쌓여있는 폐기물/철거 전 사진 1장 넣기]\n\n"
        f"{apply_human_touch(target['scene'])}\n\n"
        f"안에서 나오는 물건들을 보면요,\n"
        f"{target['objects']}\n"
        f"엄청나죠 진짜?\n\n"
        f"{apply_human_touch(mid_reaction)}\n\n"
        f"[📸 여기에 마대자루 작업 중이거나 철거 중인 리얼한 사진 1~2장 넣기]\n\n"
        f"{apply_human_touch(target['action'])}\n\n"
        f"✨ 잠깐! 견적 알아보실 때 이건 꼭 기억하세요!\n"
        f"{apply_human_touch(target['tip'])}\n\n"
        f"[📸 여기에 트럭에 가득 실은 사진이나 빗자루질 끝난 빈 공간 사진 1장 넣기]\n\n"
        f"{apply_human_touch(closing_remark)}\n\n"
        f"이사철 이삿짐 정리, 사무실 정리, 식당 폐업 정리, 가정집 유품 정리, 각종 대형 폐기물 처리 등등!\n"
        f"저희가 직접 가서 견적 봐드리고 정말 양심적이고 합리적으로 처리해 드립니다!!\n\n"
        f"숨고(Soomgo)에서도 고객님들이 직접 뽑아주신 철거·폐기물 최고 평점 & 최고의 고수 업체니깐요,\n"
        f"부산, 양산, 김해, 경남 전 지역 어디든 편하게 연락 주세요~! 🤙\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 대봉개발 (30년 경력 / 숨고 최고의 고수 선정)\n"
        f"📍 출장 지역 : 부산 · 양산 · 김해 및 경남 전 지역 어디든 출발!\n"
        f"📞 직통 문의 : {COMPANY_INFO['phone']} (사진 문자로 보내주시면 빠른 견적 가능!)\n"
        f"🌐 공식 홈페이지 : https://daebong-busan.netlify.app/\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{hashtags}\n"
    )

    draft_path = os.path.join(OUTPUT_DIR, "blog_draft.txt")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(blog_text)

    if success:
        print(f"✓ [역검증 완료 버전] 업데이트 성공: {title}")

if __name__ == "__main__":
    run_automation()