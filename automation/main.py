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

# 1. 초세부 지역 데이터베이스 (메모 자동 감지 키워드 포함)
REGIONS = [
    {"full": "부산 동래구 사직동·온천동·명륜동·안락동", "short": "동래구 사직동", "city": "부산", "detect": ["사직", "온천", "명륜", "안락", "수안", "동래"]},
    {"full": "부산 금정구 부곡동·장전동·구서동·남산동", "short": "금정구 부곡동", "city": "부산", "detect": ["부곡", "장전", "구서", "남산", "금사", "금정"]},
    {"full": "부산 해운대구 우동·좌동·재송동·반여동·센텀", "short": "해운대", "city": "부산", "detect": ["해운대", "우동", "좌동", "중동", "재송", "반여", "센텀", "송정"]},
    {"full": "부산 부산진구 서면·부전동·양정동·개금동·전포동", "short": "부산진구 서면", "city": "부산", "detect": ["서면", "부전", "양정", "개금", "전포", "가야", "당감", "부산진"]},
    {"full": "부산 연제구 연산동·거제동", "short": "연제구 연산동", "city": "부산", "detect": ["연산", "거제", "연제"]},
    {"full": "부산 수영구 광안동·남천동·망미동·민락동", "short": "수영구 광안동", "city": "부산", "detect": ["광안", "남천", "망미", "민락", "수영"]},
    {"full": "부산 사상구 감전동·주례동·학장동·엄궁동·괘법동", "short": "사상구 감전동", "city": "부산", "detect": ["감전", "주례", "학장", "엄궁", "괘법", "사상"]},
    {"full": "부산 북구 덕천동·화명동·구포동·만덕동", "short": "북구 화명동", "city": "부산", "detect": ["덕천", "화명", "구포", "만덕", "북구"]},
    {"full": "부산 사하구 하단동·괴정동·장림동·다대동·당리동", "short": "사하구 하단동", "city": "부산", "detect": ["하단", "괴정", "장림", "다대", "당리", "신평", "사하"]},
    {"full": "부산 남구 대연동·용호동·문현동·감만동", "short": "남구 대연동", "city": "부산", "detect": ["대연", "용호", "문현", "감만", "우암", "남구"]},
    {"full": "부산 동구 초량동·범일동·수정동", "short": "동구 범일동", "city": "부산", "detect": ["초량", "범일", "수정", "좌천", "동구"]},
    {"full": "부산 중구 남포동·중앙동 및 서구 대신동·충무동", "short": "중구 남포동·서구", "city": "부산", "detect": ["남포", "중앙동", "대신동", "충무동", "송도", "아미동", "중구", "서구"]},
    {"full": "부산 영도구 대교동·남항동·동삼동·청학동", "short": "영도구", "city": "부산", "detect": ["영도", "남항", "동삼", "청학", "봉래"]},
    {"full": "부산 강서구 명지동·녹산공단·대저동·신호동", "short": "강서구 명지동", "city": "부산", "detect": ["명지", "녹산", "대저", "신호", "지사", "강서"]},
    {"full": "부산 기장군 정관읍·기장읍·일광읍·장안읍", "short": "기장군 정관읍", "city": "부산", "detect": ["정관", "기장", "일광", "장안", "철마"]},
    {"full": "양산 물금읍·증산·석산·덕계·평산동·웅상", "short": "양산 물금·석산", "city": "양산", "detect": ["양산", "물금", "증산", "석산", "덕계", "평산", "웅상", "서창", "산막"]},
    {"full": "김해 장유·율하·내외동·삼계동·진영읍·주촌", "short": "김해 장유·내외동", "city": "김해", "detect": ["김해", "장유", "율하", "내외동", "내동", "외동", "삼계", "진영", "주촌", "어방"]},
    {"full": "창원 성산구·의창구·상남동 및 마산·진해 일대", "short": "창원·마산·진해", "city": "경남", "detect": ["창원", "마산", "진해", "상남", "합성", "양덕", "용원", "팔용"]},
    {"full": "밀양·진주·거제·통영·함안 및 경남 전 지역", "short": "경남 전역", "city": "경남", "detect": ["밀양", "진주", "거제", "통영", "함안", "창녕", "경남"]}
]

# 2. 메모 한 줄을 풍성한 전문가 글로 바꿔주는 [키워드 감지 자동 살붙이기 규칙] + 평상시 순환 주제
SMART_TOPICS = [
    {
        "id": "food_shop",
        "trigger_words": ["치킨", "식당", "고깃집", "고기집", "카페", "커피", "술집", "호프", "주방", "음식점", "베이커리", "빵집", "중국집", "분식", "횟집", "국밥", "프랜차이즈", "매장"],
        "item": "식당·치킨집·카페 폐업 주방집기 정리 및 상가 원상복구 철거",
        "kw": "식당폐업철거, 상가원상복구, 업소용냉장고처분, 주방집기폐기, 닥트철거, 방수턱하스리, 매장철거",
        "scene": "상가 계약기간이 끝나거나 부득이하게 식당·치킨집·카페 같은 매장을 정리하실 때 가장 막막한게 바로 내부 철거랑 기름때 묻은 무거운 주방 집기들입니다. 막상 현장 문을 열고 들어가 보면 손갈 곳이 한두 군데가 아니라 눈앞이 살짝 아찔해지곤 하죠.",
        "objects": "홀에 있는 가벽이나 붙박이 의자, 천장 텍스, 바닥 데코타일 뜯어내는 건 기본이고요, 주방 안에 꽉 들어찬 업소용 냉장고, 테이블냉장고, 튀김기, 화구, 제빙기, 스텐 싱크대랑 작업대, 그리고 천장에 매달린 환풍 후드와 닥트 배관까지",
        "action": "먼저 전기랑 수도, 가스 밸브 라인부터 안전하게 확인해 잠가두고 무거운 주방 장비들을 하나씩 끌어냅니다! 특히 치킨집이나 고깃집처럼 기름기를 많이 쓰는 주방은 닥트 배관 해체할 때나 바닥 콘크리트 방수턱을 뿌레카(하스리)로 깨부술 때 먼지랑 기름때가 엄청나거든요. 마대자루 수십 개에 폐기물을 담아 나르며 땀 좀 쏟았습니다.!!",
        "tip": "식당이나 매장 정리는 철거 업자 따로, 폐기물 수거 업자 따로 부르면 손발도 안 맞고 비용만 두 배로 깨집니다. 내부 가벽·주방 철거부터 고철·주방용품·마대 폐기물 반출까지 한 팀이 와서 한방에 밀어버려야 시간도 아끼고 건물주 검수도 깔끔하게 통과합니다."
    },
    {
        "id": "home_waste",
        "trigger_words": ["가정집", "유품", "빈집", "시골집", "이사", "이민", "쓰레기집", "살림", "장롱", "침대", "돌침대", "흙침대", "소파", "매트리스", "가전", "냉장고", "세탁기", "화분", "옥상짐", "묵은짐", "방정리", "집정리"],
        "item": "가정집 묵은살림·대형폐기물(냉장고·세탁기·장롱·돌침대) 및 유품정리",
        "kw": "가정집폐기물, 유품정리, 냉장고버리기, 세탁기처분, 돌침대철거, 장롱소파버리기, 빈집정리, 생활쓰레기수거",
        "scene": "가정집이라고 쓰레기가 절대 작은게아닙니다. 적게는 수년 길게는 몇십년 사시면서 집에 크게 정리안하는이상 안쓰는 잡동사니 물건들이 정말 많이 쌓이기 마련이거든요. 부모님 유품정리나 빈집 정리, 이사 전 살림 처분 때문에 가족분들이 직접 해보려다 하루 종일 먼지만 마시고 연락 주시는 경우가 참 많습니다.",
        "objects": "양문형 냉장고, 김치냉장고, 드럼세탁기 같은 무거운 대형 가전부터 안방 장롱, 무거운 돌침대·흙침대, 소파, 그리고 베란다와 창고 깊숙이 쌓여있던 주방용품, 헌옷, 이불, 책, 무거운 도자기 화분들까지",
        "action": "안에 있는 쓰레기들과 살림들을 분류해서 정리하고 버리고! 꺼집어내고 또 1층까지 내리고.. 박스랑 마대자루에 끝없이 담아가며 수많은 먼지와 사투를 벌입니다.!! 엘리베이터가 없는 주택 계단이나 좁은 골목길이라도 베테랑 팀원들이 합을 맞춰 다치지 않게 차곡차곡 1톤·2.5톤 트럭에 상차합니다.",
        "tip": "특히 돌침대나 대형 냉장고, 오래된 장롱은 일반인들이 괜히 혼자 옮기려다 허리 다치거나 벽지·문틀 다 찍혀먹기 일쑤거든요. 동네 스티커 일일이 붙이는 수고 할 것 없이 처음부터 전문가 불러서 잔짐까지 싹 빼내는게 결국 돈과 시간을 아끼는 길입니다."
    },
    {
        "id": "office_academy",
        "trigger_words": ["사무실", "학원", "독서실", "교습소", "병원", "의원", "약국", "미용실", "네일", "헬스장", "필라테스", "칸막이", "가벽", "텍스", "데코타일", "파티션", "오피스", "상가철거", "원상복구"],
        "item": "학원·사무실·상가 가벽 칸막이 원상복구 철거 및 사업장 폐기물 반출",
        "kw": "사무실철거, 학원철거, 상가원상복구, 가벽철거, 칸막이철거, 천장텍스, 바닥데코타일철거, 사업장폐기물",
        "scene": "학원이나 사무실, 병원, 매장처럼 공간을 여러 개로 쪼개서 쓰던 곳은 퇴거할 때 건물주나 관리사무소에서 원상복구 기준을 꽤 꼼꼼하게 따집니다. 계약 만료 날짜는 다가오는데 철거 범위가 넓으면 마음이 급해질 수밖에 없죠.",
        "objects": "석고보드 가벽, 유리 칸막이, 목재 합판 구조물은 물론이고 바닥에 본드로 단단히 붙어있는 데코타일과 카페트, 천장 텍스, 그리고 미처 못 가져가고 버려야 할 사무용 책상, 의자, 철제 캐비닛, 파티션 같은 대량 집기들까지",
        "action": "철거와 동시에 폐기물 반출에 엄청 신경 씁니다! 가벽을 부수기 시작하면 폐목재랑 석고보드 잔재물이 산더미처럼 쏟아지는데, 이걸 중간중간 마대에 담아 빼내지 않으면 발 디딜 틈도 없고 안전사고 나기 딱 좋거든요. 부수고 치우고 트럭에 싣고 무한반복으로 속도를 냅니다!",
        "tip": "복합 상가나 오피스 빌딩은 옆 매장 영업이나 소음 문제 때문에 작업 시간대와 엘리베이터 보양 규칙이 까다로운 곳이 많습니다. 미리 관리실 기준만 살짝 귀띔해 주시면 주간이든 야간·주말이든 일정에 딱 맞춰서 한 번에 검수 통과하도록 만들어 드립니다."
    },
    {
        "id": "heavy_structure",
        "trigger_words": ["공장", "창고", "주차장", "보일러", "심야보일러", "골대", "축구골대", "조형물", "간판", "판넬", "샌드위치", "컨테이너", "가설", "물탱크", "옥상", "구조물", "하스리", "파쇄", "컷팅", "완파", "건물"],
        "item": "공장·창고·지하주차장 구조물 및 노후 심야보일러·골대·조형물 철거",
        "kw": "공장철거, 창고철거, 지하주차장철거, 심야보일러철거, 골대철거, 조형물철거, 구조물철거, 하스리작업",
        "scene": "일반 실내 인테리어 철거랑은 차원이 다른 현장이 바로 무거운 설비나 특수 구조물 해체 작업입니다. 이건 힘만 좋다고 되는게 아니라 30년 현장 노하우와 안전 장비 운용이 생명이에요.",
        "objects": "옥상이나 보일러실에 방치된 대형 심야보일러, 물탱크, 학교 운동장 축구골대, 외부 조형물, 지하주차장 내 철골·콘크리트 구조물이나 공장·창고의 조립식 샌드위치판넬 가설건축물, 묵은 산업 폐기물까지",
        "action": "무게가 수백 킬로그램에서 몇 톤씩 나가는 설비들은 주변에 불꽃이나 파편이 튀지 않게 보양부터 철저히 해놓고 운반 가능한 크기로 정밀하게 분할 절단합니다. 땅속이나 바닥에 콘크리트 기초가 깊게 박혀있는 구조물은 굴착 및 파쇄(하스리) 장비를 투입해 뿌리까지 깔끔하게 제거하고 평탄화 작업까지 마칩니다!",
        "tip": "지하주차장처럼 층고가 낮아 큰 차가 못 들어가거나, 옥상이라 계단 반출이 불가능한 현장도 사진 몇 장만 찍어 보내주시면 사다리차·크레인 배차부터 소형 장비 투입까지 가장 안전하고 경제적인 방법을 바로 잡아드립니다."
    }
]

# 3. 사계절 자동 감지 날씨/일상 도입부 (계절 불일치 원천 차단)
SEASONAL_INTROS = {
    "spring": [
        "날씨가 제법 따뜻해지면서 새로운 시작을 준비하시는 분들이 많은 봄철이네요. 현장에서 한바탕 땀 쏟고 나면 봄바람이 참 시원하게 느껴집니다 ㅎㅎ 오늘도 발로 뛰는 30년 베테랑 대봉개발입니다!",
        "봄기운이 완연한 요즘이지만 현장 일은 계절 상관없이 늘 분주하네요. 이사나 매장 정리 문의가 부쩍 늘어 몸은 고단해도 힘내서 달리고 있습니다. 반갑습니다 대봉개발입니다~"
    ],
    "summer": [
        "가만히 서 있기만 해도 땀이 비 오듯 쏟아지는 무더운 날씨네요. 얼음물 통째로 마셔가며 먼지와 사투를 벌이다 보면 작업복이 금세 흠뻑 젖지만, 그래도 대봉개발의 현장 작업은 멈추지 않고 계속 되어집니다!",
        "장마철 습한 날씨와 폭염이 번갈아 찾아오는데 다들 건강 관리는 잘하고 계시는지요? 날씨가 더울수록 무거운 짐이나 철거는 전문가에게 맡기셔야 탈이 안 납니다. 현장에서 인사드리는 대봉개발입니다!"
    ],
    "autumn": [
        "바람에 기분 좋은 선선함이 느껴지는 계절이네요. 아침저녁으론 꽤 쌀쌀한데도 현장에서 작업복 입고 한바탕 뛰어다니다 보면 등줄기에 땀이 송골송골 맺힙니다 ㅎㅎ 오늘도 현장을 지키는 30년 경력 대봉개발입니다!",
        "하늘도 높고 일하기 참 좋은 계절이지만, 막상 철거랑 폐기물 처리를 알아보려고 하면 어디에 맡겨야 뒷탈이 없을지 막막하시죠? 사직동 본점을 거점으로 부산·경남을 누비는 대봉개발이 속 시원하게 풀어드릴게요."
    ],
    "winter": [
        "아침저녁으로 입김이 하얗게 나오는 쌀쌀한 날씨네요. 손끝이 시릴 정도로 추운 날이지만 현장에서 무거운 폐기물 나르고 철거 장비를 돌리다 보면 추위는커녕 이마에 땀이 맺힙니다 ㅎㅎ 든든한 현장 파트너 대봉개발입니다!",
        "날씨가 추워지면 몸도 움츠러들고 현장 작업도 훨씬 까다로워지기 마련인데요. 이럴 때일수록 안전제일로 꼼꼼하게 움직여야 합니다. 30년 동안 한결같이 현장을 지켜온 대봉개발에서 인사드립니다~"
    ],
    "common": [
        "현장 일이라는게 말만 번지르르하게 한다고 되는게 아니거든요. 결국 처음 들어갈 때부터 마지막 빗자루질하고 나올 때까지 얼마나 양심적으로 깔끔하게 치우느냐가 핵심이죠! 믿고 맡기는 대봉개발입니다.",
        "이번주도 정신없이 현장을 뛰어다니다 보니 벌써 시간이 훌쩍 갔네요. 찾아주시는 손님들이 계시니 오늘도 작업화 끈 단단히 묶고 출발합니다. 반갑습니다 대봉개발입니다!"
    ]
}

MID_REACTIONS = [
    "보시죠 엄청많죠 쓰레기? 처음 현장 문 열고 들어가면 손님들은 한숨부터 쉬시는데, 저희 눈에는 그냥 오늘 깔끔하게 치워드릴 일거리일 뿐입니다 ㅎㅎ",
    "벌써부터 분주하고 바쁜 손길에 정신이 하나도 없습니다. 할 때는 '이걸 언제 다 빼지?' 싶어도 잠깐 놀라면 그뿐, 바로 정신 차리고 치우다 보면 언제나 끝은 보이기 마련입니다!",
    "이 힘든 걸 누가 하냐구요? 바로 저희 대봉개발에서 합니다! 남들이 힘들다고 피하는 까다로운 현장일수록 다 치우고 났을 때 그 쾌감이 진짜 장난 아니거든요.",
    "먼지 뒤집어써가며 꺼집어내고 내리는게 정말 쉽지 않은 작업입니다. 하지만 눈빛만 봐도 손발이 척척 맞는 베테랑 팀원들이 있어서 그저 든든하기만 할 뿐입니다."
]

CLOSINGS = [
    "이렇게 싹 다 정리하고 나면 마지막에 바닥도 한번 시원하게 쓸어드리고요! 전문 입주청소 업체는 아니라 새집처럼 반짝반짝하게 만들어주지는 못하지만, 아무것도 없는 속 시원한 빈집·빈상가로는 확실하게 만들어 드립니다~~",
    "항상 작업이 끝나고 나면 손님들이 '사장님 정말 깔끔하게 해줬다고, 고생 많으셨다'고 시원한 음료수 하나 건네주시며 칭찬을 해주시곤 합니다. 솔직히 그 맛에 30년 동안 이 일 계속하고 있습니다 😎",
    "전부 철거하고 폐기물까지 트럭에 가득 싣고 나니 정말이지 넓고 깨끗해졌네요! 마무리 뒷정리까지 확실하게 하고 나야 그제서야 마음 편하게 발걸음을 돌릴 수 있답니다."
]

def get_seasonal_intro(month):
    if month in [3, 4, 5]:
        pool = SEASONAL_INTROS["spring"] + SEASONAL_INTROS["common"]
    elif month in [6, 7, 8]:
        pool = SEASONAL_INTROS["summer"] + SEASONAL_INTROS["common"]
    elif month in [9, 10, 11]:
        pool = SEASONAL_INTROS["autumn"] + SEASONAL_INTROS["common"]
    else:
        pool = SEASONAL_INTROS["winter"] + SEASONAL_INTROS["common"]
    return random.choice(pool)

def read_text_safe(filepath):
    """윈도우 메모장의 모든 인코딩(UTF-8, UTF-8-SIG, CP949)을 에러 없이 안전하게 읽는 함수"""
    if not os.path.exists(filepath):
        return ""
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            with open(filepath, "r", encoding=enc) as f:
                return f.read().strip()
        except Exception:
            continue
    return ""

def detect_region_and_topic(memo_text, default_reg, default_topic):
    """메모 한 줄에서 지역명과 작업 업종을 자동으로 추적하여 매칭하는 인공지능형 함수"""
    matched_reg = default_reg
    for r in REGIONS:
        for kw in r["detect"]:
            if kw in memo_text:
                matched_reg = r
                break
        if matched_reg != default_reg:
            break

    matched_topic = default_topic
    best_score = 0
    for t in SMART_TOPICS:
        score = sum(1 for w in t["trigger_words"] if w in memo_text)
        if score > best_score:
            best_score = score
            matched_topic = t

    return matched_reg, matched_topic

def apply_human_touch(text):
    """AI 판독기를 무력화하는 사장님 특유의 친근한 타자 버릇 필터"""
    replacements = [
        ("작은 게 아닙니다", "작은게아닙니다"),
        ("하는 게 ", "하는게 "),
        ("라는 게 ", "라는게 "),
        ("할 때", "할때"),
        ("하니까요", "하니깐요"),
        ("거든요.", "거든요~"),
    ]
    for old, new in replacements:
        if random.random() < 0.65:
            text = text.replace(old, new, 1)
    return text

def update_index_html(new_post_html):
    html = read_text_safe(INDEX_FILE)
    if not html:
        return False
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

    seed_num = now.timetuple().tm_yday + now.hour
    default_reg = REGIONS[seed_num % len(REGIONS)]
    default_topic = SMART_TOPICS[(seed_num * 3) % len(SMART_TOPICS)]

    weather_intro = get_seasonal_intro(now.month)
    mid_reaction = random.choice(MID_REACTIONS)
    closing_remark = random.choice(CLOSINGS)

    memo_path = os.path.join(INPUT_DIR, "memo.txt")
    memo_content = read_text_safe(memo_path)

    # [A] memo.txt에 한 줄이라도 적혀 있는 경우 -> 지역/업종 자동 감지 + 풍성한 살붙이기 가동!
    if memo_content:
        reg, target = detect_region_and_topic(memo_content, default_reg, default_topic)
        first_line = memo_content.splitlines()[0].strip()
        short_memo_title = first_line if len(first_line) <= 28 else first_line[:28] + "..."

        tag = f"실제 현장 작업일지 · {reg['short']} ({today_str})"
        title = f"{reg['short']} {target['item'].split('(')[0]} 현장 다녀왔습니다! ({short_memo_title})"

        # 사용자가 적은 한 줄 메모에 전문적인 현장 묘사를 앞뒤로 자연스럽게 결합
        fleshed_out_scene = (
            f"이번에 다녀온 현장은 【{reg['full']}】 쪽입니다!\n"
            f"사장님·고객님께서 요청주신 핵심 작업은 바로 이겁니다.\n\n"
            f"👉 \"{memo_content}\"\n\n"
            f"{target['scene']}"
        )

        raw_story = (
            f"{weather_intro}\n\n"
            f"{fleshed_out_scene}\n\n"
            f"현장에서 직접 부딪혀보면 {target['objects']} 정말 손갈 곳이 많습니다.\n\n"
            f"{mid_reaction}\n\n"
            f"{target['action']}\n\n"
            f"💡 현장에서 직접 겪으며 알려드리는 꿀팁 하나!\n"
            f"{target['tip']}\n\n"
            f"{closing_remark}"
        )

        with open(os.path.join(LOGS_DIR, "memo_history.txt"), "a", encoding="utf-8") as bf:
            bf.write(f"[{today_str}] (감지지역: {reg['short']} / 감지업종: {target['id']})\n{memo_content}\n\n")
        with open(memo_path, "w", encoding="utf-8") as wf:
            wf.write("")

    # [B] memo.txt가 비어 있는 평상시 -> 날짜별 세부 지역 x 세부 품목 자동 순환 생성
    else:
        reg = default_reg
        target = default_topic
        tag = f"{reg['short']} · {target['item'].split('(')[0]}"
        title = f"{reg['short']} {target['item']} 시원하게 비워드립니다!"
        fleshed_out_scene = (
            f"오늘은 【{reg['full']}】 쪽에서 문의가 정말 많은\n"
            f"{target['item']} 이야기를 좀 해볼까 합니다.\n"
            f"보시죠~!\n\n"
            f"{target['scene']}"
        )
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

    # 1. 홈페이지(index.html) 누적 업데이트
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

    # 2. 네이버 블로그 해시태그 및 본문 구성
    kw_list = [k.strip() for k in target["kw"].split(",")]
    clean_short = reg["short"].replace(" ", "").replace("·", "")
    hashtags = "#" + " #".join(kw_list) + f" #{clean_short}철거 #{clean_short}폐기물 #{reg['city']}철거 #{reg['city']}폐기물처리 #대봉개발"

    # 클립보드에 바로 복사될 '순수 본문' (설명줄 제거 불필요!)
    pure_blog_body = (
        f"안녕하십니까 대봉개발입니다. 😊\n\n"
        f"{weather_intro}\n\n"
        f"{apply_human_touch(fleshed_out_scene)}\n\n"
        f"[📸 여기에 현장 입구나 작업 전 사진을 1장 넣어주세요]\n\n"
        f"안에서 나오는 물건이나 작업 범위를 보면요,\n"
        f"{target['objects']}\n"
        f"엄청나죠 진짜?\n\n"
        f"{apply_human_touch(mid_reaction)}\n\n"
        f"[📸 여기에 마대자루 작업 중이거나 철거 중인 사진을 1~2장 넣어주세요]\n\n"
        f"{apply_human_touch(target['action'])}\n\n"
        f"✨ 잠깐! 견적 알아보실 때 이건 꼭 기억하세요!\n"
        f"{apply_human_touch(target['tip'])}\n\n"
        f"[📸 여기에 트럭 상차 사진이나 빗자루질 끝난 빈 공간 사진을 1장 넣어주세요]\n\n"
        f"{apply_human_touch(closing_remark)}\n\n"
        f"이사철 이삿짐 정리, 사무실 정리, 식당·매장 폐업 정리, 가정집 유품 정리, 각종 대형 폐기물 처리 등등!\n"
        f"저희가 직접 가서 견적 봐드리고 정말 양심적이고 합리적으로 처리해 드립니다!!\n\n"
        f"숨고(Soomgo)에서도 고객님들이 직접 뽑아주신 철거·폐기물 최고 평점 & 최고의 고수 업체니깐요,\n"
        f"부산, 양산, 김해, 경남 전 지역 어디든 편하게 연락 주세요~! 🤙\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 대봉개발 (30년 경력 / 숨고 최고의 고수 선정)\n"
        f"📍 출장 지역 : 부산 · 양산 · 김해 및 경남 전 지역 어디든 출발!\n"
        f"📞 직통 문의 : {COMPANY_INFO['phone']} (사진 문자로 보내주시면 빠른 견적 가능!)\n"
        f"🌐 공식 홈페이지 : https://daebong-busan.netlify.app/\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{hashtags}"
    )

    # 화면에 띄워줄 안내용 메모장 파일 (제목 확인용)
    draft_display_text = (
        f"====================================================================\n"
        f" ★ 아래 [본문]은 이미 마우스(클립보드)에 자동 복사되어 있습니다!\n"
        f" 1) 네이버 블로그 [본문] 칸을 클릭하고 바로 Ctrl + V 를 누르세요.\n"
        f" 2) 아래 [추천 제목] 한 줄만 복사해서 블로그 제목 칸에 넣으시면 끝납니다!\n"
        f"====================================================================\n\n"
        f"[추천 제목 (이 줄만 복사해서 제목 칸에 넣으세요)]\n"
        f"{title}\n\n"
        f"--------------------------------------------------------------------\n"
        f"[본문 (이미 클립보드에 복사됨 - 블로그 본문에 바로 Ctrl+V 하세요)]\n\n"
        f"{pure_blog_body}\n"
    )

    draft_path = os.path.join(OUTPUT_DIR, "blog_draft.txt")
    clipboard_path = os.path.join(OUTPUT_DIR, "blog_clipboard.txt")

    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(draft_display_text)
    with open(clipboard_path, "w", encoding="utf-8") as f:
        f.write(pure_blog_body)

    if success:
        print(f"✓ [완전 자동 살붙이기 엔진] 업데이트 성공: {title}")

if __name__ == "__main__":
    run_automation()