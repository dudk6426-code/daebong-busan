import os
import re
import sys
import json
import hashlib
from urllib.parse import quote
from html import escape
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
INDEX_FILE = PROJECT_DIR / "index.html"
CASES_DIR = PROJECT_DIR / "auto-cases"
SITEMAP_FILE = PROJECT_DIR / "sitemap.xml"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
STATE_FILE = LOGS_DIR / "last_processed_memo.json"
PROCESSED_MEMOS_FILE = LOGS_DIR / "processed_memos.txt"

SITE_URL = "https://daebong-busan.netlify.app"

COMPANY_INFO = {
    "name": "대봉개발",
    "phone": "010-8535-9787",
    "phone_link": "01085359787",
    "location": "부산광역시 동래구 사직동",
    "area": "부산 · 양산 · 김해 및 경남 지역",
    "badge": "30년 경력 철거·폐기물 직영 · 숨고(Soomgo) 고수 프로필 운영"
}

# 1. 시·구·동 계층형 지역 사전 (메모에 적힌 실제 동 이름을 그대로 보존)
BUSAN_GU_MAP = {
    "사직동": "동래구", "온천동": "동래구", "명륜동": "동래구", "안락동": "동래구", "수안동": "동래구", "낙민동": "동래구", "복천동": "동래구", "칠산동": "동래구", "명장동": "동래구",
    "거제동": "연제구", "연산동": "연제구",
    "부곡동": "금정구", "장전동": "금정구", "구서동": "금정구", "남산동": "금정구", "금사동": "금정구", "서동": "금정구", "청룡동": "금정구", "회동동": "금정구",
    "부전동": "부산진구", "전포동": "부산진구", "양정동": "부산진구", "개금동": "부산진구", "가야동": "부산진구", "당감동": "부산진구", "부암동": "부산진구", "초읍동": "부산진구", "범천동": "부산진구",
    "재송동": "해운대구", "반여동": "해운대구", "석대동": "해운대구", "좌동": "해운대구", "중동": "해운대구", "송정동": "해운대구",
    "광안동": "수영구", "남천동": "수영구", "망미동": "수영구", "민락동": "수영구", "수영동": "수영구",
    "대연동": "남구", "용호동": "남구", "문현동": "남구", "감만동": "남구", "우암동": "남구", "용당동": "남구",
    "화명동": "북구", "덕천동": "북구", "구포동": "북구", "만덕동": "북구", "금곡동": "북구",
    "감전동": "사상구", "주례동": "사상구", "학장동": "사상구", "엄궁동": "사상구", "괘법동": "사상구", "모라동": "사상구", "삼락동": "사상구", "덕포동": "사상구",
    "하단동": "사하구", "괴정동": "사하구", "장림동": "사하구", "다대동": "사하구", "당리동": "사하구", "신평동": "사하구", "감천동": "사하구", "구평동": "사하구",
    "범일동": "동구", "초량동": "동구", "수정동": "동구", "좌천동": "동구",
    "중앙동": "중구", "남포동": "중구", "광복동": "중구", "부평동": "중구", "영주동": "중구", "보수동": "중구", "대청동": "중구",
    "대신동": "서구", "충무동": "서구", "토성동": "서구", "암남동": "서구", "아미동": "서구", "남부민동": "서구",
    "동삼동": "영도구", "청학동": "영도구", "남항동": "영도구", "봉래동": "영도구", "대교동": "영도구", "신선동": "영도구",
    "명지동": "강서구", "대저동": "강서구", "신호동": "강서구", "지사동": "강서구", "녹산동": "강서구", "미음동": "강서구",
    "정관읍": "기장군", "기장읍": "기장군", "일광읍": "기장군", "장안읍": "기장군", "철마면": "기장군"
}

GYEONGNAM_DONG_MAP = {
    "용원동": ("경남", "창원 진해구 용원동", "창원시 진해구 용원동"),
    "용원": ("경남", "창원 진해구 용원", "창원시 진해구 용원"),
    "석동": ("경남", "창원 진해구 석동", "창원시 진해구 석동"),
    "풍호동": ("경남", "창원 진해구 풍호동", "창원시 진해구 풍호동"),
    "상남동": ("경남", "창원 성산구 상남동", "창원시 성산구 상남동"),
    "팔용동": ("경남", "창원 의창구 팔용동", "창원시 의창구 팔용동"),
    "합성동": ("경남", "창원 마산 합성동", "창원시 마산회원구 합성동"),
    "양덕동": ("경남", "창원 마산 양덕동", "창원시 마산회원구 양덕동"),
    "장유": ("김해", "김해 장유", "김해시 장유"),
    "율하동": ("김해", "김해 율하동", "김해시 율하동"),
    "율하": ("김해", "김해 장유·율하", "김해시 장유·율하"),
    "내외동": ("김해", "김해 내외동", "김해시 내외동"),
    "삼계동": ("김해", "김해 삼계동", "김해시 삼계동"),
    "구산동": ("김해", "김해 구산동", "김해시 구산동"),
    "어방동": ("김해", "김해 어방동", "김해시 어방동"),
    "삼방동": ("김해", "김해 삼방동", "김해시 삼방동"),
    "부원동": ("김해", "김해 부원동", "김해시 부원동"),
    "봉황동": ("김해", "김해 봉황동", "김해시 봉황동"),
    "진영읍": ("김해", "김해 진영읍", "김해시 진영읍"),
    "주촌면": ("김해", "김해 주촌면", "김해시 주촌면"),
    "진례면": ("김해", "김해 진례면", "김해시 진례면"),
    "물금읍": ("양산", "양산 물금읍", "양산시 물금읍"),
    "물금": ("양산", "양산 물금읍", "양산시 물금읍"),
    "증산": ("양산", "양산 물금·증산", "양산시 물금읍 증산"),
    "석산리": ("양산", "양산 석산", "양산시 동면 석산리"),
    "석산": ("양산", "양산 석산", "양산시 동면 석산리"),
    "덕계동": ("양산", "양산 덕계동", "양산시 덕계동"),
    "덕계": ("양산", "양산 덕계동", "양산시 덕계동"),
    "평산동": ("양산", "양산 평산동", "양산시 평산동"),
    "서창동": ("양산", "양산 서창동", "양산시 서창동"),
    "웅상": ("양산", "양산 웅상", "양산시 웅상(덕계·평산·서창)"),
    "산막공단": ("양산", "양산 산막공단", "양산시 산막공단"),
    "어곡공단": ("양산", "양산 어곡공단", "양산시 어곡공단"),
    "고현동": ("경남", "경남 거제시 고현동", "경남 거제시 고현동"),
    "옥포동": ("경남", "경남 거제시 옥포동", "경남 거제시 옥포동"),
    "장승포": ("경남", "경남 거제시 장승포", "경남 거제시 장승포")
}

AREA_LEVEL_MAP = [
    ("해운대 우동", ("부산", "해운대구 우동", "부산 해운대구 우동")),
    ("해운대구 우동", ("부산", "해운대구 우동", "부산 해운대구 우동")),
    ("센텀시티", ("부산", "해운대 센텀시티", "부산 해운대구 센텀시티")),
    ("센텀", ("부산", "해운대 센텀", "부산 해운대구 센텀")),
    ("광안리", ("부산", "수영구 광안리", "부산 수영구 광안리")),
    ("온천장", ("부산", "동래구 온천장", "부산 동래구 온천장")),
    ("다대포", ("부산", "사하구 다대포", "부산 사하구 다대포")),
    ("녹산공단", ("부산", "강서구 녹산공단", "부산 강서구 녹산공단")),
    ("정관", ("부산", "기장군 정관읍", "부산 기장군 정관읍")),
    ("서면", ("부산", "부산진구 서면", "부산 부산진구 서면")),
    ("사직", ("부산", "동래구 사직동", "부산 동래구 사직동")),
    ("거제시", ("경남", "경남 거제시", "경남 거제시")),
    ("거제도", ("경남", "경남 거제시", "경남 거제시")),
    ("진해구", ("경남", "창원 진해구", "창원시 진해구")),
    ("진해", ("경남", "창원 진해구", "창원시 진해구")),
    ("마산합포구", ("경남", "창원 마산합포구", "창원시 마산합포구")),
    ("마산회원구", ("경남", "창원 마산회원구", "창원시 마산회원구")),
    ("마산", ("경남", "창원 마산", "창원시 마산")),
    ("성산구", ("경남", "창원 성산구", "창원시 성산구")),
    ("의창구", ("경남", "창원 의창구", "창원시 의창구")),
    ("창원시", ("경남", "창원시", "창원시 일대")),
    ("창원", ("경남", "창원시", "창원시 일대")),
    ("김해시", ("김해", "김해시", "김해시 일대")),
    ("김해", ("김해", "김해시", "김해시 일대")),
    ("양산시", ("양산", "양산시", "양산시 일대")),
    ("양산", ("양산", "양산시", "양산시 일대")),
    ("진주시", ("경남", "경남 진주시", "경남 진주시")),
    ("진주", ("경남", "경남 진주시", "경남 진주시")),
    ("통영시", ("경남", "경남 통영시", "경남 통영시")),
    ("통영", ("경남", "경남 통영시", "경남 통영시")),
    ("밀양시", ("경남", "경남 밀양시", "경남 밀양시")),
    ("밀양", ("경남", "경남 밀양시", "경남 밀양시")),
    ("함안군", ("경남", "경남 함안군", "경남 함안군")),
    ("함안", ("경남", "경남 함안군", "경남 함안군")),
    ("창녕군", ("경남", "경남 창녕군", "경남 창녕군")),
    ("창녕", ("경남", "경남 창녕군", "경남 창녕군")),
    ("동래구", ("부산", "부산 동래구", "부산 동래구")),
    ("동래", ("부산", "부산 동래구", "부산 동래구")),
    ("연제구", ("부산", "부산 연제구", "부산 연제구")),
    ("금정구", ("부산", "부산 금정구", "부산 금정구")),
    ("부산진구", ("부산", "부산 부산진구", "부산 부산진구")),
    ("해운대구", ("부산", "부산 해운대구", "부산 해운대구")),
    ("해운대", ("부산", "부산 해운대구", "부산 해운대구")),
    ("수영구", ("부산", "부산 수영구", "부산 수영구")),
    ("사상구", ("부산", "부산 사상구", "부산 사상구")),
    ("사하구", ("부산", "부산 사하구", "부산 사하구")),
    ("영도구", ("부산", "부산 영도구", "부산 영도구")),
    ("영도", ("부산", "부산 영도구", "부산 영도구")),
    ("강서구", ("부산", "부산 강서구", "부산 강서구")),
    ("기장군", ("부산", "부산 기장군", "부산 기장군")),
    ("기장", ("부산", "부산 기장군", "부산 기장군")),
    ("부산 남구", ("부산", "부산 남구", "부산 남구")),
    ("부산 북구", ("부산", "부산 북구", "부산 북구")),
    ("부산 동구", ("부산", "부산 동구", "부산 동구")),
    ("부산 중구", ("부산", "부산 중구", "부산 중구")),
    ("부산 서구", ("부산", "부산 서구", "부산 서구"))
]

ROTATION_LOCATIONS = [
    {"city": "부산", "short": "동래구 사직동", "full": "부산 동래구 사직동·온천동"},
    {"city": "부산", "short": "연제구 거제동·연산동", "full": "부산 연제구 거제동·연산동"},
    {"city": "부산", "short": "금정구 부곡·장전동", "full": "부산 금정구 부곡동·장전동·구서동"},
    {"city": "부산", "short": "부산진구 서면·양정동", "full": "부산 부산진구 서면·부전동·양정동"},
    {"city": "부산", "short": "동래구 명륜·안락동", "full": "부산 동래구 명륜동·안락동·수안동"},
    {"city": "부산", "short": "해운대 우동·재송동", "full": "부산 해운대구 우동·재송동·좌동"},
    {"city": "부산", "short": "수영구 광안·남천동", "full": "부산 수영구 광안동·남천동·망미동"},
    {"city": "부산", "short": "북구 화명·덕천동", "full": "부산 북구 화명동·덕천동·구포동"},
    {"city": "부산", "short": "남구 대연·문현동", "full": "부산 남구 대연동·문현동·용호동"},
    {"city": "부산", "short": "사상구 감전·주례동", "full": "부산 사상구 감전동·주례동·학장동"},
    {"city": "부산", "short": "사하구 하단·괴정동", "full": "부산 사하구 하단동·괴정동·장림동"},
    {"city": "부산", "short": "동구 범일동·중구 남포동", "full": "부산 동구 범일동·중구 중앙동·남포동"},
    {"city": "부산", "short": "강서구 명지·기장 정관", "full": "부산 강서구 명지동 및 기장군 정관읍"},
    {"city": "양산", "short": "양산 물금·석산·덕계", "full": "양산시 물금읍·석산·덕계·웅상"},
    {"city": "김해", "short": "김해 장유·내외동·삼계", "full": "김해시 장유·율하·내외동·삼계동"},
    {"city": "경남", "short": "창원·마산·진해", "full": "창원시 성산·의창구 및 마산·진해 일대"}
]

# 2. 12대 세부 작업 카탈로그
TARGET_JOBS = [
    {
        "id": "office_realtor_restore",
        "triggers": ["부동산", "공인중개사", "사무실", "오피스", "점포", "파티션", "책상", "캐비닛"],
        "name": "사무실·부동산·점포 가벽 철거 및 퇴거 원상복구",
        "short_name": "사무실·점포 원상복구 철거",
        "kw": "사무실철거, 상가원상복구, 가벽철거, 유리칸막이철거, 사업장폐기물, 사무용가구처분",
        "items_detail": "유리 칸막이, 석고보드 가벽, 상담 데스크, 바닥 데코타일, 사무용 책상·회전의자·파티션·철제 캐비닛",
        "situation": "계약 만료를 앞두고 임대인이나 관리사무소와 협의된 기준에 맞춰 내부 칸막이를 해체하고 남은 사무 집기를 비워야 하는 상황",
        "process_guide": "전기·통신선을 먼저 안전하게 정리한 뒤 가벽과 바닥재를 순서대로 해체하고, 발생한 인테리어 잔재물과 폐가구를 차량으로 함께 반출합니다.",
        "check_points": "철거할 가벽의 대략적인 길이, 바닥 데코타일 제거 포함 여부, 반출할 사무 집기 물량과 엘리베이터 사용 조건",
        "faq_q": "관리사무소 기준이 까다로운 건물인데 주말이나 야간 작업도 조율 가능한가요?",
        "faq_a": "네, 건물 관리 규정에 맞춘 엘리베이터 보양과 작업 가능 시간대(주말·야간 등)를 사전에 확인하여 일정을 맞춰드립니다."
    },
    {
        "id": "restaurant_kitchen_close",
        "triggers": ["식당", "치킨", "고깃집", "고기집", "음식점", "주방", "횟집", "국밥", "분식", "중국집", "술집", "호프", "포차", "튀김기", "화구", "닥트", "방수턱"],
        "name": "식당·치킨집·음식점 폐업 주방설비 처분 및 내부 철거",
        "short_name": "식당 폐업 주방·내부 철거",
        "kw": "식당폐업철거, 치킨집철거, 업소용냉장고처분, 주방집기폐기, 닥트철거, 식당원상복구",
        "items_detail": "업소용 냉장고, 테이블냉장고, 튀김기, 가스 화구, 스텐 싱크대·작업대, 환풍 후드·닥트 배관, 홀 붙박이 의자·가벽",
        "situation": "식당이나 치킨집 등 요식업 매장을 정리하면서 기름기가 많은 주방 장비와 홀 인테리어를 함께 철거·반출해야 하는 상황",
        "process_guide": "가스·수도·전기 마감 상태를 먼저 확인한 후 무거운 스텐 주방 설비를 빼내고, 계약 조건에 따라 홀 가벽 해체나 주방 바닥 정리를 진행합니다.",
        "check_points": "주방 집기만 수거할지 또는 홀 가벽·천장 닥트·바닥 방수턱 파쇄(하스리)까지 포함된 원상복구인지 여부",
        "faq_q": "내부 철거는 안 하고 주방에 있는 업소용 냉장고랑 싱크대, 그릇만 비울 수도 있나요?",
        "faq_a": "네, 가능합니다. 철거 공정 없이 주방 설비와 집기류, 마대 폐기물만 일괄 수거하는 작업도 별도로 진행합니다."
    },
    {
        "id": "cafe_bakery_equipment",
        "triggers": ["카페", "커피", "베이커리", "빵집", "디저트", "제빙기", "쇼케이스", "업소용냉장고", "테이블냉장고", "싱크대", "카운터"],
        "name": "카페·베이커리 업소용냉장고·제빙기·쇼케이스 처분 및 카운터 철거",
        "short_name": "카페 철거 및 냉장설비 처분",
        "kw": "카페철거, 업소용냉장고폐기, 제빙기처분, 쇼케이스버리기, 카운터철거, 상가원상복구",
        "items_detail": "케이크·음료 쇼케이스, 제빙기, 업소용 냉장고, 스텐 싱크대, 급배수관이 연결된 커피 바(Bar) 카운터 및 홀 가벽",
        "situation": "카페나 빵집을 정리하면서 무거운 냉장·제빙 설비를 빼내고 급배수 배관이 연결된 카운터 바를 해체해야 하는 상황",
        "process_guide": "배수관 누수가 없도록 마감 처리한 뒤 무거운 쇼케이스와 냉장 설비를 먼저 반출하고, 목재·타일 카운터 구조물을 해체해 상차합니다.",
        "check_points": "처분할 냉장·제빙 설비 품목과 카운터 바·바닥 타일 철거 포함 여부, 매장 출입문 폭 및 계단 유무",
        "faq_q": "고장 난 업소용 냉장고나 쇼케이스 1~2대만 따로 수거 요청해도 되나요?",
        "faq_a": "네, 매장 전체 철거가 아니더라도 처분이 까다로운 업소용 대형 냉장고·제빙기 단품 수거도 출장 가능합니다."
    },
    {
        "id": "academy_hospital_partition",
        "triggers": ["학원", "독서실", "교습소", "스터디카페", "병원", "의원", "약국", "미용실", "네일", "헬스장", "필라테스", "칸막이", "가벽", "석고보드", "유리칸막이", "천장텍스", "데코타일"],
        "name": "학원·독서실·병원 다수 룸 칸막이 해체 및 원상복구 철거",
        "short_name": "학원·병원 칸막이 원상복구",
        "kw": "학원철거, 독서실철거, 병원철거, 가벽철거, 칸막이철거, 바닥데코타일철거, 천장텍스",
        "items_detail": "강의실·진료실 석고보드 가벽, 유리 칸막이와 도어, 바닥 데코타일·카페트, 천장 마감재, 강의용 책걸상·사물함·베드",
        "situation": "여러 개의 방으로 쪼개어 쓰던 학원, 독서실, 병원 등의 칸막이를 해체하고 대량의 폐목재·석고보드와 집기를 반출해야 하는 상황",
        "process_guide": "구역별로 가벽을 안전하게 해체하면서 동시에 폐자재를 마대에 담아 엘리베이터나 사다리차로 반출하여 현장 동선이 막히지 않게 관리합니다.",
        "check_points": "전용 면적(평수), 나뉘어 있는 방 개수, 천장·바닥 원상복구 범위, 건물 엘리베이터 또는 사다리차 작업 여건",
        "faq_q": "같은 건물에 다른 학원이나 매장이 영업 중인데 소음 시간대 조율이 되나요?",
        "faq_a": "네, 소음이 발생하는 파쇄·해체 작업은 관리실 및 주변 매장과 협의된 시간대에 집중하여 진행합니다."
    },
    {
        "id": "stone_bed_disassembly",
        "triggers": ["돌침대", "흙침대", "돌소파", "흙소파", "옥침대", "온돌침대"],
        "name": "가정집 무거운 돌침대·흙침대 방문 분해 및 수거",
        "short_name": "돌침대·흙침대 분해 수거",
        "kw": "돌침대버리기, 돌침대철거수거, 흙침대버리기, 돌소파처분, 무거운가구수거, 대형폐기물대행",
        "items_detail": "2인용(퀸/킹)·1인용(싱글) 돌침대 및 흙침대, 두꺼운 석재판·황토판, 온열 보료, 원목 프레임",
        "situation": "이사나 방 정리를 앞두고 일반인이 절대 혼자 들 수 없는 무거운 돌침대·흙침대를 안방에서 분해해 1층까지 내려야 하는 상황",
        "process_guide": "작업자들이 집 안으로 직접 들어가 돌판과 보료, 목재 프레임을 순서대로 안전하게 분해한 뒤, 마루나 문틀이 손상되지 않게 운반해 수거합니다.",
        "check_points": "돌침대/흙침대 크기(1인용/2인용), 건물 층수와 엘리베이터 유무(또는 계단 작업 여부)",
        "faq_q": "집 안에 놓인 돌침대를 제가 미리 밖에 내놓지 않아도 알아서 분해해 가시나요?",
        "faq_a": "네, 방 안에 있는 그대로 두시면 방문하여 분해부터 1층 반출, 수거 처리까지 일괄 진행해 드립니다."
    },
    {
        "id": "wardrobe_sofa_furniture",
        "triggers": ["장롱", "붙박이장", "소파", "침대", "매트리스", "피아노", "식탁", "서랍장", "장식장", "대형가구", "가구"],
        "name": "대형 장롱·붙박이장·소파·침대 해체 및 방문 수거",
        "short_name": "장롱·붙박이장·대형가구 수거",
        "kw": "장롱해체수거, 붙박이장철거, 소파버리기, 침대매트리스처분, 대형가구버리기, 가구수거업체",
        "items_detail": "10자·12자 대형 장롱, 안방 붙박이장, 가죽·리클라이너 소파, 침대 프레임과 매트리스, 식탁, 서랍장, 피아노",
        "situation": "부피가 커서 현관문을 그대로 통과하지 못하는 장롱이나 붙박이장, 무거운 소파·침대를 해체해 버려야 하는 상황",
        "process_guide": "방 안에서 장롱과 붙박이장, 침대 프레임을 운반 가능한 크기로 해체한 뒤 벽지나 바닥 찍힘에 유의하며 수거 차량까지 안전하게 반출합니다.",
        "check_points": "처분할 가구 종류와 수량(장롱 자수 등), 다른 잔짐 포함 여부, 엘리베이터 또는 계단 반출 조건",
        "faq_q": "붙박이장이나 큰 장롱 하나만 해체해서 버리는 것도 가능한가요?",
        "faq_a": "네, 집 전체 정리가 아니더라도 혼자 해체하기 어려운 대형 장롱·붙박이장 단품 철거 및 수거도 가능합니다."
    },
    {
        "id": "home_appliances_pots",
        "triggers": ["냉장고", "김치냉장고", "세탁기", "건조기", "에어컨", "가전", "화분", "도자기화분", "항아리"],
        "name": "가정집 대형가전(냉장고·세탁기) 및 무거운 베란다 화분·살림 수거",
        "short_name": "냉장고·세탁기·베란다 화분 수거",
        "kw": "냉장고버리기, 김치냉장고처분, 세탁기폐기, 화분버리기, 베란다정리, 가정집대형폐기물",
        "items_detail": "양문형 냉장고, 스탠드·뚜껑형 김치냉장고, 드럼·통돌이 세탁기, 흙이 가득 든 대형 화분·항아리, 베란다 묵은 살림",
        "situation": "고장 나거나 교체 후 남은 무거운 냉장고·세탁기, 혹은 흙 무게 때문에 엄두가 안 나는 다수의 베란다 화분과 잡동사니를 치워야 하는 상황",
        "process_guide": "좁은 다용도실이나 베란다 문틀 조건을 확인해 무거운 가전을 안전하게 끌어내고, 흙 화분과 잡동사니는 마대 및 전용 용기에 담아 깔끔히 반출합니다.",
        "check_points": "수거할 가전·화분 종류와 대략적인 개수, 함께 버릴 생활 잡동사니 유무, 층수 및 엘리베이터 여부",
        "faq_q": "흙이 들어있는 무거운 도자기 화분이랑 베란다 잡동사니도 그대로 치워주시나요?",
        "faq_a": "네, 흙과 화분을 일일이 따로 분리하실 필요 없이 있는 상태 그대로 방문하여 수거해 드립니다."
    },
    {
        "id": "moving_leftover_waste",
        "triggers": ["이사", "이삿짐", "남은짐", "잔짐", "버리기", "살림처분", "이사폐기물"],
        "name": "이사 전후 남은 짐·가구·생활폐기물 일괄 수거 및 집 비우기",
        "short_name": "이사 후 남은 짐·폐기물 정리",
        "kw": "이사폐기물, 이사후남은짐, 가정집폐기물처리, 살림처분, 생활폐기물수거, 집비우기",
        "items_detail": "이사 가면서 두고 가는 헌 가구, 소형 가전, 이불·헌 옷·책·주방 그릇, 베란다·창고에 남은 각종 생활 잡동사니",
        "situation": "이삿날 당일이나 이사 전후에 미처 처분하지 못한 가구와 잔짐을 퇴거 시간 전에 한꺼번에 비워야 하는 상황",
        "process_guide": "고객님이 일일이 분류하실 필요 없이 작업자들이 마대자루와 박스를 준비해 들어가 잔짐부터 큰 가구까지 전량 상차하고 바닥을 쓸어드립니다.",
        "check_points": "남은 짐의 대략적인 양(방 1칸 분량, 1톤 트럭 반 차·한 차 등), 이사/퇴거 희망 날짜와 시간대, 건물 층수",
        "faq_q": "이삿날 시간 맞춰서 바로 와주실 수 있나요?",
        "faq_a": "네, 이사 일정과 희망 시간을 미리 알려주시면 이삿짐 차량이 빠진 직후나 약속된 시간에 맞춰 방문합니다."
    },
    {
        "id": "parents_estate_empty_house",
        "triggers": ["유품", "유품정리", "빈집", "시골집", "촌집", "부모님", "집정리", "일괄정리", "묵은짐", "옥상짐", "쓰레기집"],
        "name": "부모님 유품정리·빈집·시골집 묵은 살림 일괄 정리 및 수거",
        "short_name": "부모님 집 비우기·빈집 유품정리",
        "kw": "유품정리업체, 빈집정리, 부모님집비우기, 시골집정리, 가정집일괄정리, 묵은살림처분",
        "items_detail": "안방·거실의 오래된 가구와 가전, 주방 찬장 속 그릇·살림살이, 다락방·창고·마당·옥상에 쌓인 묵은 짐과 생활폐기물 일체",
        "situation": "오랫동안 거주하던 부모님 댁이나 비워둔 주택의 살림 전체를 처음부터 끝까지 비워 빈집 상태로 만들어야 하는 상황",
        "process_guide": "보관해야 할 중요 물품(사진, 서류, 귀중품 등)을 먼저 확인해 따로 챙겨드린 뒤, 나머지 가구·가전 해체와 마대 포장, 차량 상차를 체계적으로 진행합니다.",
        "check_points": "주택 형태(아파트·빌라·단독주택), 평수와 방 개수, 골목길 차량 진입 여건 및 대략적인 물량 사진",
        "faq_q": "집 안에 짐이 너무 많아서 어디서부터 손대야 할지 모르겠는데 사진으로 상담이 되나요?",
        "faq_a": "네, 거실·방·주방·베란다를 휴대폰으로 한 장씩 찍어 문자로 보내주시면 예상 차량 대수와 작업 범위를 안내해 드립니다."
    },
    {
        "id": "boiler_water_tank_roof",
        "triggers": ["보일러", "심야보일러", "전기보일러", "물탱크", "옥상", "냉각탑", "배관"],
        "name": "옥상·지하실 노후 심야보일러·대형 물탱크 해체 및 반출 철거",
        "short_name": "심야보일러·옥상 물탱크 철거",
        "kw": "심야보일러철거, 옥상물탱크철거, 보일러해체수거, 물탱크철거비용, 고철설비철거",
        "items_detail": "노후 심야 전기보일러, 기름·가스보일러, 옥상 대형 FRP·스텐·철제 물탱크, 보온재 및 부속 배관",
        "situation": "고장 나거나 사용하지 않는 무거운 심야보일러나 대형 물탱크가 옥상·지하 보일러실에 방치되어 공간을 차지하고 있는 상황",
        "process_guide": "전기·배관 차단 확인과 주변 안전 보양을 먼저 실시한 뒤, 통째로 나오지 않는 설비는 현장에서 운반 가능한 크기로 정밀 절단·분할하여 반출합니다.",
        "check_points": "설비 종류(심야보일러/물탱크)와 규격 사진, 설치 위치(옥상·지하·1층), 계단 또는 사다리차 반출 여건",
        "faq_q": "보일러실 문이 좁아서 보일러가 통째로 안 나오는데 철거가 가능한가요?",
        "faq_a": "네, 실내에서 안전하게 분할 절단·해체하여 좁은 문이나 계단으로도 파손 없이 반출해 드립니다."
    },
    {
        "id": "goalpost_sculpture_outdoor",
        "triggers": ["골대", "축구골대", "농구골대", "조형물", "기념비", "철구조물", "간판", "어닝", "펜스", "휀스", "철제"],
        "name": "운동장 축구골대·야외 조형물·철구조물 절단 해체 및 기초 파쇄",
        "short_name": "축구골대·조형물·철구조물 철거",
        "kw": "축구골대철거, 골대철거, 조형물철거, 철구조물해체, 기초콘크리트파쇄, 야외구조물철거",
        "items_detail": "학교·체육시설 노후 축구골대·농구골대, 야외 조형물·안내판, 철제 캐노피·펜스, 땅속 콘크리트 고정 기초부",
        "situation": "부식되거나 흔들려 위험한 운동장 골대, 야외 조형물, 철구조물을 절단 해체하고 바닥 고정부까지 안전하게 제거해야 하는 상황",
        "process_guide": "불꽃·파편 방지 안전 조치를 한 뒤 철구조물을 절단 해체하고, 바닥이나 땅속에 콘크리트로 고정된 기초부는 파쇄(하스리) 후 평탄하게 마감합니다.",
        "check_points": "구조물 사진과 대략적인 크기, 바닥 콘크리트 기초 파쇄 포함 여부, 작업 차량 진입 가능 여부",
        "faq_q": "골대 기둥이 땅속 콘크리트에 묻혀 있는데 튀어나온 부분 없이 평평하게 마무리되나요?",
        "faq_a": "네, 지상 구조물 절단뿐만 아니라 기초 콘크리트 굴착·파쇄 및 되메우기 평탄화 작업까지 요청 범위대로 진행합니다."
    },
    {
        "id": "factory_parking_concrete",
        "triggers": ["공장", "창고", "주차장", "지하주차장", "판넬", "샌드위치", "컨테이너", "가설건축물", "하스리", "파쇄", "컷팅", "완파", "건물철거", "산업폐기물"],
        "name": "공장·창고·지하주차장 구조물 철거 및 콘크리트 파쇄(하스리)·폐기물 반출",
        "short_name": "공장·창고·주차장 철거 및 폐기물",
        "kw": "공장철거, 창고철거, 지하주차장철거, 샌드위치판넬철거, 가설건축물철거, 하스리작업, 사업장폐기물",
        "items_detail": "공장·창고 내 조립식 샌드위치판넬 가벽·가설건축물, 적재 랙·선반, 지하주차장 구조물, 콘크리트 방수턱·바닥 파쇄, 산업·사업장 폐기물",
        "situation": "공장·창고 퇴거를 위해 가설 판넬 구조물과 묵은 자재를 정리하거나, 층고가 낮은 지하주차장 내 구조물·폐기물을 반출해야 하는 상황",
        "process_guide": "현장 층고와 출입구 폭에 맞는 차량·장비를 투입해 판넬과 철골 구조물을 안전하게 해체하고, 폐목재·고철·혼합 폐기물을 분리 상차합니다.",
        "check_points": "철거할 구조물 면적/높이, 지하주차장 층고 제한 여부, 반출할 사업장 폐기물 종류와 사진",
        "faq_q": "지하주차장 높이 제한 때문에 큰 차가 못 들어가는데 폐기물 반출이 가능한가요?",
        "faq_a": "네, 지하주차장 진입이 가능한 저상·소형 작업 차량을 투입하여 높이 제한 구역에서도 원활하게 반출합니다."
    }
]

GENERAL_MEMO_JOB = {
    "id": "general_field_work",
    "triggers": [],
    "name": "현장 맞춤 철거 및 폐기물 정리 수거",
    "short_name": "철거 및 폐기물 정리",
    "kw": "부산철거, 부산폐기물처리, 상가원상복구, 가정집폐기물, 대형폐기물수거, 사업장폐기물",
    "items_detail": "현장 내 해체가 필요한 내부 시설물·칸막이·집기류 및 반출해야 할 각종 대형폐기물과 마대 잔재물",
    "situation": "현장 여건과 일정에 맞춰 불필요한 구조물을 안전하게 해체하고 발생한 폐기물을 깔끔하게 비워내야 하는 상황",
    "process_guide": "사전에 작업 범위와 반출 동선을 꼼꼼히 확인한 뒤, 주변 보양과 안전을 챙기며 철거부터 차량 상차, 기본적인 바닥 정리까지 책임지고 진행합니다.",
    "check_points": "작업할 동네와 층수(엘리베이터 유무), 철거·처분할 대상이 보이는 현장 사진 2~3장, 희망 작업 일정",
    "faq_q": "정확한 견적과 작업 가능 날짜는 어떻게 확인할 수 있나요?",
    "faq_a": "현장 사진 몇 장과 동네, 층수, 엘리베이터 유무를 문자로 보내주시면 확인 후 예상 견적과 일정을 안내해 드립니다."
}

# 3. 5가지 안내 글 양식
ARTICLE_ARCHETYPES = [
    {
        "type_name": "투명한 견적 기준 안내형",
        "badge_label": "견적·비용 기준 안내",
        "build": lambda reg, job, memo_block: [
            f"📌 {reg['short']} {job['short_name']}, 예상 비용과 작업 가능 여부가 궁금하신가요?\n"
            f"번거롭게 긴 설명을 적으실 필요 없이 【동네 + 층수(엘리베이터 유무) + 희망 날짜 + 현장 사진 2~3장】을 {COMPANY_INFO['phone']} 로 문자 보내주세요.\n"
            f"확인 후 예상 견적과 가능한 일정을 안내해 드립니다. 사진에서 확인되지 않은 작업이나 조건 변경이 있으면, 작업 전에 먼저 설명드리고 동의를 구한 뒤 진행합니다.",

            memo_block if memo_block else (
                f"■ {reg['full']} {job['short_name']}, 어떤 점을 먼저 살펴봐야 할까요?\n"
                f"{job['situation']}에서는 무작정 작업을 시작하기보다 작업 범위와 반출 조건을 정확히 짚어보는 것이 중요합니다.\n"
                f"주로 다루는 대상은 {job['items_detail']} 등이며, 현장 여건에 따라 가장 효율적인 인력과 차량 배치가 달라집니다."
            ),

            f"■ 대봉개발의 직영 작업 절차\n"
            f"{job['process_guide']}\n"
            f"30년 현장 경험을 가진 작업자들이 직접 현장을 살피고 해체부터 폐기물 상차, 기본적인 바닥 정리까지 차분하고 꼼꼼하게 마무리합니다.",

            f"■ 사진 문자 상담 시 함께 알려주시면 좋은 내용\n"
            f"✔ 확인 사항 : {job['check_points']}\n"
            f"단품 수거부터 전체 정리까지 {COMPANY_INFO['area']} 어디든 상담 가능하니 편하게 연락 주세요."
        ]
    },
    {
        "type_name": "30년 경력 현장 기록·과정 설명형",
        "badge_label": "현장 작업 가이드",
        "build": lambda reg, job, memo_block: [
            f"안녕하십니까, 사직동 본점을 중심으로 현장에서 직접 뛰는 대봉개발입니다. 😊\n"
            f"{reg['short']} 일대에서 {job['short_name']} 업체를 알아보고 계신다면 【동네 + 층수 + 현장 사진】을 {COMPANY_INFO['phone']} 로 편하게 문자 남겨주세요.\n"
            f"반출 조건을 확인한 뒤 작업 방법과 예상 견적을 친절히 안내해 드립니다.",

            memo_block if memo_block else (
                f"■ 현장에서 자주 마주하는 작업 상황\n"
                f"{job['situation']}이 생기면 혼자서 처리하기에는 무게나 폐기물 양 때문에 엄두가 나지 않는 경우가 많습니다.\n"
                f"특히 {job['items_detail']} 등은 전용 공구와 숙련된 반출 요령이 있어야 시설물 손상 없이 안전하게 비워낼 수 있습니다."
            ),

            f"■ 시작부터 마무리 바닥 정리까지 꼼꼼하게\n"
            f"{job['process_guide']}\n"
            f"작업 중 혹시라도 사진으로 보이지 않던 추가 작업이 필요한 경우에는 임의로 진행하지 않고, 반드시 사전에 설명드리고 협의를 거친 뒤 진행합니다.",

            f"■ 빠르고 정확한 상담을 위한 체크포인트\n"
            f"✔ 체크 포인트 : {job['check_points']}\n"
            f"{COMPANY_INFO['area']} 일대 어디든 현장 여건에 맞춰 성실하게 상담해 드리겠습니다."
        ]
    },
    {
        "type_name": "퇴거·일정 맞춤 상담형",
        "badge_label": "일정·절차 상담",
        "build": lambda reg, job, memo_block: [
            f"📅 정해진 퇴거일이나 계약 만료일에 맞춰 {reg['short']} {job['short_name']} 일정을 잡아야 하시나요?\n"
            f"희망하시는 작업 날짜와 함께 【동네 + 층수(엘리베이터 유무) + 현장 사진】을 {COMPANY_INFO['phone']} 로 문자로 보내주세요.\n"
            f"현재 배차 가능한 일정과 예상 소요 시간, 견적을 확인하여 신속히 답변해 드립니다.",

            memo_block if memo_block else (
                f"■ 일정이 정해진 현장일수록 사전 동선 파악이 중요합니다\n"
                f"{job['situation']}에서는 엘리베이터 사용 조건이나 차량 정차 공간, 관리실 작업 시간대 등을 미리 조율해야 당일 작업이 매끄럽게 진행됩니다.\n"
                f"주요 정리 대상인 {job['items_detail']}의 물량에 맞춰 알맞은 차량과 인원을 배정합니다."
            ),

            f"■ 철거와 폐기물 반출의 체계적인 연계\n"
            f"{job['process_guide']}\n"
            f"해체 작업과 폐기물 상차를 한 흐름으로 진행하여 불필요한 대기 시간을 줄이고 약속된 일정을 지킬 수 있도록 집중합니다.",

            f"■ 일정 문의 전 확인해 주실 사항\n"
            f"✔ 필수 체크 : {job['check_points']}\n"
            f"주말이나 특정 시간대 작업이 필요한 경우에도 미리 말씀해 주시면 {COMPANY_INFO['area']} 현장에 맞춰 조율해 드립니다."
        ]
    },
    {
        "type_name": "계단·좁은 공간 등 반출 조건 해결형",
        "badge_label": "반출 조건·현장 맞춤",
        "build": lambda reg, job, memo_block: [
            f"❓ \"엘리베이터가 없는 층인데 가능할까요?\", \"문이 좁아 안 빠지는데 어떻게 내리죠?\"\n"
            f"{reg['short']}에서 반출 조건이 까다로운 {job['short_name']} 때문에 고민 중이시라면 【동네 + 층수/계단 여부 + 현장 사진】을 {COMPANY_INFO['phone']} 로 보내주세요.\n"
            f"현장 출입문 폭과 이동 동선을 확인해 가장 알맞은 해체·반출 방법과 예상 비용을 안내해 드립니다.",

            memo_block if memo_block else (
                f"■ 까다로운 반출 여건에서 확인해야 할 점\n"
                f"{job['situation']} 중에서도 계단 작업이나 골목길, 지하·옥상 현장은 일반 작업보다 안전과 보양에 훨씬 더 신경을 써야 합니다.\n"
                f"{job['items_detail']} 등을 무리하게 옮기려다 문틀이나 벽면이 상하지 않도록 사전 분해·절단 계획이 필요합니다."
            ),

            f"■ 현장 여건에 맞춘 분해·해체 및 반출\n"
            f"{job['process_guide']}\n"
            f"계단 인력 반출, 사다리차 이용, 소형 차량 진입 등 현장 구조에 맞는 방식을 선택하며, 조건 변경이 필요한 경우 작업 전 미리 안내하고 동의받습니다.",

            f"■ 반출 조건 확인을 위해 알려주실 내용\n"
            f"✔ 확인 포인트 : {job['check_points']}\n"
            f"혼자 옮기기 위험한 무거운 짐이나 구조물이 있다면 {COMPANY_INFO['area']} 대봉개발로 편하게 문의해 주세요."
        ]
    },
    {
        "type_name": "자주 묻는 질문 Q&A 정리형",
        "badge_label": "핵심 Q&A 안내",
        "build": lambda reg, job, memo_block: [
            f"📞 {reg['short']} {job['short_name']}, 처음 문의하셔서 어떤 것부터 확인해야 할지 막막하신가요?\n"
            f"통화가 어려우셔도 괜찮습니다. 【동네 + 층수 + 엘리베이터 여부 + 사진 2~3장】을 {COMPANY_INFO['phone']} 로 문자로 보내주시면 확인 후 예상 견적과 일정을 안내해 드립니다.",

            memo_block if memo_block else (
                f"■ Q1. 어떤 물건과 작업까지 한 번에 맡길 수 있나요?\n"
                f"A. {job['situation']}에서 필요한 {job['items_detail']} 해체 및 수거를 함께 다루고 있습니다.\n"
                f"현장 조건에 따라 단품 수거부터 전체 원상복구 및 폐기물 반출까지 필요한 범위만 선택해 맡기실 수 있습니다."
            ),

            f"■ Q2. 작업은 어떤 순서로 진행되며 추가 비용 걱정은 없나요?\n"
            f"A. {job['process_guide']}\n"
            f"보내주신 사진과 조건을 바탕으로 예상 견적을 먼저 안내해 드리며, 현장에서 사진에 없던 추가 작업이 필요한 경우에는 반드시 작업 전에 먼저 설명하고 동의를 구합니다.",

            f"■ Q3. 견적 문의할 때 무엇을 알려주면 되나요?\n"
            f"A. 【{job['check_points']}】를 사진과 함께 문자로 남겨주시면 가장 정확합니다.\n"
            f"{COMPANY_INFO['area']} 전 지역 상담 가능하니 언제든 편하게 연락 주세요."
        ]
    }
]

def read_text_safe(filepath, *, required=False):
    path = Path(filepath)
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        if required:
            raise
        return ""
    if not data:
        return ""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ("utf-16",)
    else:
        encodings = ("utf-8-sig", "utf-8", "cp949", "euc-kr")
    for enc in encodings:
        try:
            return data.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"지원하지 않는 파일 인코딩입니다: {path}")

def write_text_atomic(filepath, content):
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8", newline="\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

def find_valid_token_pos(text, token):
    pattern = re.compile(re.escape(token))
    for m in pattern.finditer(text):
        start, end = m.start(), m.end()
        if start > 0 and ("가" <= text[start - 1] <= "힣"):
            prefix_2 = text[max(0, start - 2):start]
            if not prefix_2.endswith(("시", "구", "군", "산", "해", "원")):
                continue
        after_char = text[end:end + 1]
        if token in ("서면", "사직", "동래", "양산", "김해", "창원", "마산", "진해") and after_char in ("서", "집", "국", "면"):
            continue
        return start
    return -1

def detect_location_and_job_from_memo(memo_text):
    candidates = []
    for dong, gu in BUSAN_GU_MAP.items():
        pos = find_valid_token_pos(memo_text, dong)
        if pos != -1:
            candidates.append((1, pos, {"city": "부산", "short": f"{gu} {dong}", "full": f"부산 {gu} {dong}"}))

    for dong_key, (city, short_name, full_name) in GYEONGNAM_DONG_MAP.items():
        pos = find_valid_token_pos(memo_text, dong_key)
        if pos != -1:
            candidates.append((1, pos, {"city": city, "short": short_name, "full": full_name}))

    for area_key, (city, short_name, full_name) in AREA_LEVEL_MAP:
        pos = find_valid_token_pos(memo_text, area_key)
        if pos != -1:
            candidates.append((2, pos, {"city": city, "short": short_name, "full": full_name}))

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]))
        matched_reg = candidates[0][2]
    else:
        matched_reg = {"city": "부산", "short": "부산·경남", "full": "부산 · 양산 · 김해 및 경남 지역"}

    matched_job = None
    best_score = 0
    for job in TARGET_JOBS:
        score = sum(len(trig) for trig in job["triggers"] if trig in memo_text)
        if score > best_score:
            best_score = score
            matched_job = job

    if matched_job is None:
        matched_job = GENERAL_MEMO_JOB

    return matched_reg, matched_job

def classify_memo_status(memo_text):
    if any(w in memo_text for w in ["문의", "견적", "상담", "얼마", "질문", "알아보"]):
        return "inquiry"
    if any(w in memo_text for w in ["예정", "내일", "모레", "다음주", "예약", "방문할", "가기로"]):
        return "scheduled"
    return "completed"

def select_archetype_for_memo(memo_text, status):
    if status == "inquiry":
        return ARTICLE_ARCHETYPES[0]
    if status == "scheduled":
        return ARTICLE_ARCHETYPES[2]
    if any(w in memo_text for w in ["계단", "옥상", "지하", "좁은", "사다리차", "엘리베이터"]):
        return ARTICLE_ARCHETYPES[3]
    return ARTICLE_ARCHETYPES[1]

def build_three_titles(reg, job, memo_content="", status="completed"):
    if memo_content:
        first_line = memo_content.splitlines()[0].strip()
        short_memo = first_line if len(first_line) <= 26 else first_line[:26] + "..."
        if status == "inquiry":
            return [
                f"{reg['short']} {job['short_name']} 견적 상담 및 작업 조건 안내 - {short_memo}",
                f"{reg['short']} 철거·폐기물 상담 기록 [{short_memo}] 및 체크포인트",
                f"{reg['short']} {job['short_name']}, 반출 조건별 예상 견적 확인 방법"
            ]
        if status == "scheduled":
            return [
                f"{reg['short']} {job['short_name']} 작업 일정 및 사전 현장 체크 - {short_memo}",
                f"{reg['short']} 철거·폐기물 방문 예정 안내 [{short_memo}] (대봉개발)",
                f"{reg['short']} {job['short_name']}, 원활한 반출을 위한 사전 준비 사항"
            ]
        return [
            f"{reg['short']} {job['short_name']} 현장 작업 기록 - {short_memo} (대봉개발)",
            f"{reg['short']} 철거·폐기물 작업 일지 [{short_memo}] 및 사진 견적 안내",
            f"{reg['short']} {job['short_name']}, 반출 조건 확인 및 직영 작업 기록"
        ]
    return [
        f"{reg['short']} {job['name']} - 사진 문자 견적 및 작업 절차 안내",
        f"{reg['short']} {job['short_name']}, 견적이 달라지는 조건과 사전 체크리스트",
        f"{reg['short']} {job['short_name']} 상담 안내 (동네·층수·사진 문자 접수)"
    ]

def render_permanent_case_page(post_data):
    """각 글마다 고유 URL(/auto-cases/{case_id}/index.html)을 가진 영구 웹페이지를 생성"""
    case_id = post_data["case_id"]
    title = post_data["title"]
    tag = post_data["tag"]
    date_str = post_data["date"]
    reg_full = post_data["reg_full"]
    reg_short = post_data["reg_short"]
    job_short = post_data["job_short"]
    kw = post_data["kw"]
    paragraphs = post_data["paragraphs"]
    faq_q = post_data["faq_q"]
    faq_a = post_data["faq_a"]

    page_url = f"{SITE_URL}/auto-cases/{case_id}/"
    sms_raw = (
        f"[대봉개발 견적상담]\n"
        f"▶ 문의번호: {case_id}\n"
        f"▶ 확인한 글: {reg_short} {job_short}\n"
        f"1. 동네/층수(엘리베이터 유무): \n"
        f"2. 희망 날짜: \n"
        f"3. 현장 사진 2~3장을 첨부해 보내주세요."
    )
    sms_href = f"sms:{COMPANY_INFO['phone_link']}?body={quote(sms_raw, safe='')}"
    meta_desc = f"{reg_full} {job_short} ({tag}). 동네·층수·현장 사진 문자 상담 {COMPANY_INFO['phone']}"

    body_html = "\n".join(
        f"<p>{escape(p).replace(chr(10), '<br/>' + chr(10))}</p>"
        for p in paragraphs if p.strip()
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(meta_desc, quote=True)}">
  <link rel="canonical" href="{escape(page_url, quote=True)}">
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; color: #1f2d28; background: #f4f7f5;
      font-family: -apple-system, BlinkMacSystemFont, "Malgun Gothic", sans-serif;
      line-height: 1.8; padding-bottom: 92px;
    }}
    main {{
      max-width: 820px; margin: 24px auto; padding: 28px 24px;
      background: #ffffff; border-radius: 10px;
      box-shadow: 0 4px 18px rgba(0,0,0,0.06);
    }}
    .nav-links {{ font-size: 14px; margin-bottom: 14px; }}
    .nav-links a {{ color: #174c42; font-weight: 700; text-decoration: none; }}
    .tag {{
      display: inline-block; background: #e6f0ed; color: #174c42;
      padding: 4px 10px; border-radius: 4px; font-size: 13px; font-weight: 700;
    }}
    h1 {{ font-size: 24px; line-height: 1.45; margin: 12px 0; color: #12241e; }}
    .meta {{ color: #5c6e66; font-size: 13px; border-bottom: 1px solid #e3ebe7; padding-bottom: 14px; margin-bottom: 20px; }}
    p {{ margin: 0 0 18px 0; font-size: 16px; }}
    details {{ background: #f4f7f5; padding: 12px 16px; border-radius: 6px; margin: 18px 0; }}
    summary {{ font-weight: 700; color: #174c42; cursor: pointer; }}
    .copy-box {{
      background: #f9fbf9; border: 1px solid #d5e2dc; border-radius: 8px;
      padding: 16px; margin-top: 24px;
    }}
    textarea {{
      width: 100%; min-height: 135px; padding: 10px; font: inherit;
      font-size: 14px; border: 1px solid #c2d4cc; border-radius: 6px; margin-top: 8px;
    }}
    .sticky-cta {{
      position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999;
      display: flex; gap: 8px; padding: 10px 12px;
      background: rgba(18, 28, 24, 0.96); box-shadow: 0 -4px 16px rgba(0,0,0,0.25);
    }}
    .sticky-cta a {{
      flex: 1; text-align: center; padding: 14px 8px; border-radius: 6px;
      font-weight: 800; font-size: 15px; text-decoration: none;
    }}
    .btn-call {{ background: #174c42; color: #ffffff; border: 1px solid #287a6a; }}
    .btn-sms {{ background: #ffcc00; color: #111111; }}
  </style>
</head>
<body>
  <main>
    <div class="nav-links">
      <a href="/">← 대봉개발 메인 홈페이지</a> &nbsp;|&nbsp; <a href="/auto-cases/">📚 전체 작업·안내 기록 목록</a>
    </div>
    <span class="tag">{escape(tag)}</span>
    <h1>{escape(title)}</h1>
    <div class="meta">
      📅 작성일: {escape(date_str)} &nbsp;|&nbsp; 📍 지역: {escape(reg_full)} &nbsp;|&nbsp; 🔎 문의번호: {escape(case_id)}
    </div>
    {body_html}
    <details open>
      <summary>💡 자주 묻는 질문: {escape(faq_q)}</summary>
      <p style="margin-top:10px;margin-bottom:0;font-size:15px;">{escape(faq_a)}</p>
    </details>
    <div class="copy-box">
      <strong>📸 사진 문자 상담 안내 ({COMPANY_INFO['phone']})</strong>
      <div style="font-size:14px;color:#4a5a53;margin-top:4px;">
        아래 [사진 문자 견적상담] 버튼을 누르시거나, 문자 자동 입력이 안 되는 기기에서는 아래 내용을 복사해 사진과 함께 보내주세요.
      </div>
      <textarea readonly aria-label="복사할 견적 문의 양식">{escape(sms_raw)}</textarea>
    </div>
    <div class="meta" style="margin-top:20px;border:none;">
      🏆 {escape(COMPANY_INFO['badge'])} | 관련키워드: {escape(kw)}
    </div>
  </main>
  <nav class="sticky-cta" aria-label="하단 상담 연결">
    <a class="btn-call" href="tel:{COMPANY_INFO['phone_link']}">📞 전화 상담 ({COMPANY_INFO['phone']})</a>
    <a class="btn-sms" href="{escape(sms_href, quote=True)}">📸 사진 문자 견적상담</a>
  </nav>
</body>
</html>
"""

def save_permanent_archive_and_sitemap(post_data):
    """
    1) /auto-cases/{case_id}/post.json 및 index.html 영구 저장
    2) 지금까지 쌓인 모든 글(무제한)을 모아 /auto-cases/index.html 전체 보관함 생성
    3) 검색엔진 로봇용 /sitemap.xml 자동 갱신
    """
    case_id = post_data["case_id"]
    case_folder = CASES_DIR / case_id
    case_folder.mkdir(parents=True, exist_ok=True)

    write_text_atomic(case_folder / "post.json", json.dumps(post_data, ensure_ascii=False, indent=2))
    write_text_atomic(case_folder / "index.html", render_permanent_case_page(post_data))

    # 저장된 모든 영구 글 읽기 (개수 제한 없이 100% 영구 누적)
    all_posts = []
    for jf in CASES_DIR.glob("*/post.json"):
        try:
            item = json.loads(read_text_safe(jf, required=False))
            if item.get("case_id") and item.get("title"):
                all_posts.append(item)
        except Exception:
            continue

    all_posts.sort(key=lambda x: (x.get("date", ""), x.get("case_id", "")), reverse=True)

    cards_html = []
    for item in all_posts:
        cid = escape(item["case_id"])
        cards_html.append(
            f'<article style="background:#fff;padding:18px 20px;border-radius:8px;margin-bottom:14px;border:1px solid #dce6e1;">'
            f'<div style="font-size:13px;color:#174c42;font-weight:700;">{escape(item.get("tag", ""))} · {escape(item.get("date", ""))}</div>'
            f'<h2 style="font-size:19px;margin:8px 0;"><a href="/auto-cases/{cid}/" style="color:#12241e;text-decoration:none;">{escape(item["title"])}</a></h2>'
            f'<div style="font-size:14px;color:#55665e;">📍 {escape(item.get("reg_full", ""))} &nbsp;|&nbsp; <a href="/auto-cases/{cid}/" style="color:#174c42;font-weight:700;">자세히 보기 →</a></div>'
            f'</article>'
        )

    archive_index_html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>부산·경남 철거·폐기물 전체 작업 및 안내 기록 | 대봉개발</title>
  <meta name="description" content="대봉개발의 부산·양산·김해·경남 지역별 철거 및 폐기물 처리 현장 기록과 견적 안내 전체 보관함입니다.">
  <link rel="canonical" href="{SITE_URL}/auto-cases/">
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f4f7f5; color: #1f2d28; font-family: -apple-system, BlinkMacSystemFont, "Malgun Gothic", sans-serif; line-height: 1.7; padding-bottom: 80px; }}
    main {{ max-width: 860px; margin: 24px auto; padding: 0 16px; }}
    h1 {{ font-size: 24px; color: #12241e; }}
  </style>
</head>
<body>
  <main>
    <p><a href="/" style="color:#174c42;font-weight:700;text-decoration:none;">← 대봉개발 메인 홈페이지로 돌아가기</a></p>
    <h1>📚 대봉개발 작업 기록 및 지역별 안내 전체 보관함 (총 {len(all_posts)}건 누적)</h1>
    <p style="color:#4f6159;font-size:15px;">부산·양산·김해·경남 지역의 철거 및 폐기물 수거 기록이 삭제 없이 차곡차곡 영구 보관되는 페이지입니다.</p>
    {"".join(cards_html)}
  </main>
</body>
</html>
"""
    write_text_atomic(CASES_DIR / "index.html", archive_index_html)

    # 검색엔진(구글·네이버) 자동 수집용 sitemap.xml 생성
    today_iso = datetime.now(KST).strftime("%Y-%m-%d")
    sitemap_urls = [
        f"  <url><loc>{SITE_URL}/</loc><lastmod>{today_iso}</lastmod></url>",
        f"  <url><loc>{SITE_URL}/auto-cases/</loc><lastmod>{today_iso}</lastmod></url>"
    ]
    for item in all_posts:
        cid = escape(item["case_id"])
        d_iso = item.get("date", today_iso).replace(".", "-")
        sitemap_urls.append(f"  <url><loc>{SITE_URL}/auto-cases/{cid}/</loc><lastmod>{escape(d_iso)}</lastmod></url>")

    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(sitemap_urls) + "\n"
        '</urlset>\n'
    )
    write_text_atomic(SITEMAP_FILE, sitemap_xml)
    return len(all_posts)

def ensure_mobile_sticky_cta(html):
    sms_body = quote(
        "[대봉개발 사진견적 문의]\n"
        "1. 동네 : \n"
        "2. 층수 / 엘리베이터 유무 : \n"
        "3. 희망 날짜 : \n"
        "4. 현장 사진 2~3장을 함께 보내주세요."
    )
    sticky_bar_html = f"""<!-- DAEBONG_STICKY_START -->
<style>
  .daebong-sticky-cta {{
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999;
    display: flex; gap: 8px; padding: 10px 12px;
    background: rgba(18, 28, 24, 0.96);
    box-shadow: 0 -4px 16px rgba(0,0,0,0.25);
  }}
  .daebong-sticky-cta a {{
    flex: 1; text-align: center; padding: 14px 8px; border-radius: 6px;
    font-weight: 800; font-size: 15px; text-decoration: none; letter-spacing: -0.3px;
  }}
  .daebong-btn-call {{ background: #174c42; color: #ffffff; border: 1px solid #287a6a; }}
  .daebong-btn-sms {{ background: #ffcc00; color: #111111; }}
  body {{ padding-bottom: 78px !important; }}
</style>
<div class="daebong-sticky-cta">
  <a class="daebong-btn-call" href="tel:01085359787">📞 전화 상담</a>
  <a class="daebong-btn-sms" href="sms:01085359787?body={sms_body}">📸 사진 문자 견적상담</a>
</div>
<!-- DAEBONG_STICKY_END -->"""

    if "<!-- DAEBONG_STICKY_START -->" in html and "<!-- DAEBONG_STICKY_END -->" in html:
        return re.sub(
            r"<!-- DAEBONG_STICKY_START -->.*?<!-- DAEBONG_STICKY_END -->",
            sticky_bar_html,
            html,
            flags=re.DOTALL
        )
    if "daebong-sticky-cta" in html:
        return re.sub(
            r"(?:<!-- 대봉개발 모바일.*?-->\s*)?<style>\s*\.daebong-sticky-cta.*?</div\s*>",
            sticky_bar_html,
            html,
            flags=re.DOTALL
        )
    if "</body>" in html:
        return html.replace("</body>", sticky_bar_html + "\n</body>", 1)
    return html + sticky_bar_html

def is_legacy_exaggerated_post(post_html):
    bad_phrases = ["클릭당 만 원", "수수료(20~30%)", "억지 추가금을 요구하는 일이 비일비재", "3초 사진 견적", "3초 견적받기", "{short}"]
    return any(bp in post_html for bp in bad_phrases)

def update_index_html(new_post_html, case_id, total_archived_count):
    html = read_text_safe(INDEX_FILE, required=True)
    start_marker = "<!-- AUTO_POSTS_START -->"
    end_marker = "<!-- AUTO_POSTS_END -->"

    if html.count(start_marker) != 1 or html.count(end_marker) != 1:
        raise ValueError("index.html 내에 AUTO_POSTS 마커가 없거나 중복되어 있습니다.")
    if html.index(start_marker) >= html.index(end_marker):
        raise ValueError("index.html 내의 AUTO_POSTS 마커 순서가 잘못되었습니다.")

    before, rest = html.split(start_marker, 1)
    middle, after = rest.split(end_marker, 1)

    existing_posts = re.findall(r'<article class="auto-post".*?</article>', middle, flags=re.DOTALL)

    updated_posts = [new_post_html.strip()]
    for post in existing_posts:
        if f'data-case-id="{case_id}"' in post or post.strip() == new_post_html.strip():
            continue
        if is_legacy_exaggerated_post(post):
            continue
        updated_posts.append(post.strip())

    # 메인 페이지에도 최신 20개 글의 전체 본문이 차곡차곡 쌓이며, 하단 버튼으로 영구 보관함 전체 글과 연결됩니다.
    updated_posts = updated_posts[:20]

    archive_banner = (
        f'<div class="auto-archive-link" style="text-align:center;margin:20px 0 8px 0;">'
        f'<a href="/auto-cases/" style="display:inline-block;background:#e6f0ed;color:#174c42;padding:12px 22px;border-radius:6px;font-weight:800;text-decoration:none;border:1px solid #b8d4cb;">'
        f'📚 지금까지 차곡차곡 누적된 전체 작업·안내 기록 모두 보기 (총 {total_archived_count}건 영구 보관) →'
        f'</a></div>'
    )

    new_middle = "\n" + "\n".join(updated_posts) + "\n" + archive_banner + "\n"
    new_html = before + start_marker + new_middle + end_marker + after
    new_html = ensure_mobile_sticky_cta(new_html)
    write_text_atomic(INDEX_FILE, new_html)

def compute_memo_hash(memo_content):
    normalized = " ".join(memo_content.split())
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]

def is_memo_already_processed(memo_hash):
    if not PROCESSED_MEMOS_FILE.exists():
        return False
    recorded = read_text_safe(PROCESSED_MEMOS_FILE, required=False).splitlines()
    return any(line.startswith(memo_hash) for line in recorded)

def clear_processed_memo():
    memo_path = INPUT_DIR / "memo.txt"
    current_memo = read_text_safe(memo_path, required=False)
    if not current_memo:
        return

    if not STATE_FILE.exists():
        print("ℹ [메모 보존] 처리 대기 상태 파일이 없어 현재 memo.txt를 그대로 보존합니다.")
        return

    try:
        state = json.loads(read_text_safe(STATE_FILE, required=False) or "{}")
    except Exception:
        state = {}

    current_hash = compute_memo_hash(current_memo)
    if state.get("memo_hash") != current_hash:
        print("ℹ [새 메모 감지] 실행 도중 memo.txt 내용이 변경되었으므로 삭제하지 않고 보존합니다.")
        return

    now = datetime.now(KST)
    today_str = now.strftime("%Y.%m.%d %H:%M")
    case_id = state.get("case_id", f"memo-{current_hash}")

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOGS_DIR / "memo_history.txt", "a", encoding="utf-8") as bf:
        bf.write(f"[{today_str}] [{case_id}]\n{current_memo}\n\n")
    with open(PROCESSED_MEMOS_FILE, "a", encoding="utf-8") as pf:
        pf.write(f"{current_hash}\t{today_str}\t{case_id}\n")

    write_text_atomic(memo_path, "")
    try:
        STATE_FILE.unlink()
    except OSError:
        pass
    print(f"✓ [메모 안전 보관 및 초기화 완료] ID: {case_id}")

def run_automation():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    CASES_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(KST)
    today_str = now.strftime("%Y.%m.%d")
    today_compact = now.strftime("%Y%m%d")

    day_count = (now.date() - date(2026, 1, 1)).days
    num_locs = len(ROTATION_LOCATIONS)  # 16
    num_jobs = len(TARGET_JOBS)         # 12
    num_archs = len(ARTICLE_ARCHETYPES) # 5

    job_idx = day_count % num_jobs
    loc_idx = (day_count + (day_count // num_jobs)) % num_locs
    arch_idx = day_count % num_archs

    memo_path = INPUT_DIR / "memo.txt"
    memo_content = read_text_safe(memo_path, required=False)

    if memo_content:
        memo_hash = compute_memo_hash(memo_content)
        if is_memo_already_processed(memo_hash):
            print(f"ℹ 이미 처리된 메모({memo_hash})이므로 중복 생성하지 않고 비웁니다.")
            write_text_atomic(memo_path, "")
            memo_content = ""

    if memo_content:
        memo_hash = compute_memo_hash(memo_content)
        reg, job = detect_location_and_job_from_memo(memo_content)
        status = classify_memo_status(memo_content)
        archetype = select_archetype_for_memo(memo_content, status)
        # URL 및 폴더 이름으로 100% 안전한 영문·숫자 고유 ID 생성
        case_id = f"memo-{memo_hash}"

        if status == "inquiry":
            memo_block = (
                f"■ 【{reg['full']}】 견적·작업 상담 내용 ({today_str})\n"
                f"👉 문의 메모 : \"{memo_content}\"\n\n"
                f"고객님께서 문의주신 현장 여건과 관련하여 작업 범위 및 반출 조건별 체크포인트를 안내해 드립니다."
            )
            tag = f"견적·상담 기록 · {reg['short']} ({today_str})"
        elif status == "scheduled":
            memo_block = (
                f"■ 【{reg['full']}】 작업 예정 및 사전 확인 사항 ({today_str})\n"
                f"👉 일정 메모 : \"{memo_content}\"\n\n"
                f"원활하고 안전한 작업을 위해 사전에 현장 반출 동선과 장비·차량 배치를 점검한 기록입니다."
            )
            tag = f"작업 예정 안내 · {reg['short']} ({today_str})"
        else:
            memo_block = (
                f"■ 【{reg['full']}】 실제 현장 작업 기록 ({today_str})\n"
                f"👉 작업 메모 : \"{memo_content}\"\n\n"
                f"현장 여건에 맞춰 반출 동선과 안전 조치를 확인한 뒤 작업을 진행한 기록입니다.\n"
                f"(※ 아래 안내는 동일 유형의 작업을 알아보시는 분들을 위한 공통 참고 기준입니다.)"
            )
            tag = f"실제 현장 기록 · {reg['short']} ({today_str})"

        write_text_atomic(STATE_FILE, json.dumps({
            "memo_hash": memo_hash,
            "case_id": case_id,
            "created_at": today_str
        }, ensure_ascii=False))
    else:
        status = "guide"
        reg = ROTATION_LOCATIONS[loc_idx]
        job = TARGET_JOBS[job_idx]
        archetype = ARTICLE_ARCHETYPES[arch_idx]
        guide_hash = hashlib.sha1(f"{today_str}:{reg['short']}:{job['id']}".encode("utf-8")).hexdigest()[:8]
        case_id = f"guide-{today_compact}-{guide_hash}"
        memo_block = ""
        tag = f"{archetype['badge_label']} · {reg['short']}"

    titles = build_three_titles(reg, job, memo_content, status=status)
    primary_title = titles[0]
    paragraphs = archetype["build"](reg, job, memo_block)

    faq_section_text = (
        f"💬 상담 전 자주 물어보시는 질문 (Q&A)\n"
        f"Q. {job['faq_q']}\n"
        f"A. {job['faq_a']}\n\n"
        f"Q. 사진으로 먼저 견적을 확인한 뒤 결정해도 되나요?\n"
        f"A. 네, 사진과 동네·층수·희망 날짜를 문자로 보내주시면 예상 견적과 일정을 안내해 드립니다. 사진에서 확인되지 않은 작업이나 조건 변경이 있으면 작업 전에 비용을 설명하고 동의받겠습니다."
    )
    paragraphs.append(faq_section_text)

    # 1. 개별 영구 웹페이지(/auto-cases/{case_id}/index.html) 및 전체 보관함 + 사이트맵 누적 저장!
    post_data = {
        "case_id": case_id,
        "date": today_str,
        "tag": tag,
        "title": primary_title,
        "reg_short": reg["short"],
        "reg_full": reg["full"],
        "job_id": job["id"],
        "job_short": job["short_name"],
        "kw": job["kw"],
        "paragraphs": paragraphs[:-1],
        "faq_q": job["faq_q"],
        "faq_a": job["faq_a"]
    }
    total_archived_count = save_permanent_archive_and_sitemap(post_data)

    # 2. 메인 홈페이지(index.html)에도 최신 글 본문이 차곡차곡 쌓이고 개별 영구 페이지 링크 연결!
    safe_tag = escape(tag)
    safe_title = escape(primary_title)
    safe_case_id = escape(case_id)
    safe_meta_loc = escape(reg["full"])
    safe_meta_kw = escape(job["kw"])
    safe_faq_q = escape(job["faq_q"])
    safe_faq_a = escape(job["faq_a"])

    tracked_sms_body = quote(
        f"[대봉개발 견적상담]\n"
        f"▶ 문의번호: {case_id}\n"
        f"▶ 확인한 글: {reg['short']} {job['short_name']}\n"
        f"1. 동네/층수(엘리베이터 유무): \n"
        f"2. 희망 날짜: \n"
        f"3. 현장 사진 2~3장을 첨부해 보내주세요."
    )

    html_paragraphs = "</p>\n  <p>".join(
        escape(p).replace("\n", "<br/>\n") for p in paragraphs[:-1] if p.strip()
    )

    new_post_html = f"""<article class="auto-post" data-case-id="{safe_case_id}">
  <span class="tag">{safe_tag}</span>
  <h3><a href="/auto-cases/{safe_case_id}/" style="color:inherit;text-decoration:none;">{safe_title}</a></h3>
  <p>{html_paragraphs}</p>
  <details style="margin-top:12px;background:#f4f7f5;padding:10px 14px;border-radius:6px;cursor:pointer;">
    <summary style="font-weight:700;color:#174c42;">💡 자주 묻는 질문: {safe_faq_q}</summary>
    <p style="margin-top:8px;font-size:14px;color:#333;">{safe_faq_a}</p>
  </details>
  <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">
    <a href="tel:01085359787" style="display:inline-block;background:#174c42;color:#fff;padding:10px 16px;border-radius:4px;text-decoration:none;font-weight:700;font-size:14px;">📞 전화 상담 ({COMPANY_INFO['phone']})</a>
    <a href="sms:01085359787?body={tracked_sms_body}" style="display:inline-block;background:#ffcc00;color:#111;padding:10px 16px;border-radius:4px;text-decoration:none;font-weight:800;font-size:14px;">📸 이 작업 사진 문자로 견적상담</a>
    <a href="/auto-cases/{safe_case_id}/" style="display:inline-block;background:#e6f0ed;color:#174c42;padding:10px 14px;border-radius:4px;text-decoration:none;font-weight:700;font-size:13px;">🔗 이 글 전용 페이지</a>
  </div>
  <div class="meta">🏆 {escape(COMPANY_INFO['badge'])} | 📍 출장: {safe_meta_loc} 및 {escape(COMPANY_INFO['area'])} | 🔎 관련품목: {safe_meta_kw}</div>
</article>"""

    update_index_html(new_post_html, case_id, total_archived_count)

    # 3. 네이버 블로그용 해시태그 및 순수 본문 생성
    kw_list = [k.strip() for k in job["kw"].split(",") if k.strip()]
    clean_short = re.sub(r"[^가-힣a-zA-Z0-9]", "", reg["short"])
    hashtags = "#" + " #".join(kw_list) + f" #{clean_short}철거 #{clean_short}폐기물 #{reg['city']}철거 #{reg['city']}폐기물처리 #대봉개발"

    footer_block = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 {COMPANY_INFO['name']} ({COMPANY_INFO['badge']})\n"
        f"📍 출장 지역 : {COMPANY_INFO['area']} (일정 및 작업 여건 협의)\n"
        f"📩 문자 상담 : [동네 + 층수(엘리베이터 유무) + 희망 날짜 + 현장 사진] 문자 전송\n"
        f"📞 직통 문의 : {COMPANY_INFO['phone']}\n"
        f"🌐 공식 홈페이지 : https://daebong-busan.netlify.app/\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{hashtags}"
    )

    pure_blog_body = "\n\n\n".join(paragraphs) + "\n\n\n" + footer_block

    draft_display_text = (
        f"====================================================================\n"
        f" [대봉개발 블로그 원고 | 글 양식: {archetype['type_name']} | ID: {case_id}]\n"
        f" ★ 아래 [본문]은 이미 클립보드에 자동 복사되었습니다! (블로그 본문에 바로 Ctrl+V)\n"
        f" ★ 아래 [제목 후보 3개] 중 하나를 골라 블로그 제목 칸에 복사해 넣으세요.\n"
        f"====================================================================\n\n"
        f"[추천 제목 후보 3선]\n"
        f"후보 1 : {titles[0]}\n"
        f"후보 2 : {titles[1]}\n"
        f"후보 3 : {titles[2]}\n\n"
        f"--------------------------------------------------------------------\n"
        f"[본문 미리보기 (이미 클립보드에 복사됨)]\n\n"
        f"{pure_blog_body}\n"
    )

    write_text_atomic(OUTPUT_DIR / "blog_draft.txt", draft_display_text)
    write_text_atomic(OUTPUT_DIR / "blog_clipboard.txt", pure_blog_body)

    print(f"✓ [원고 생성 및 영구 페이지 누적 완료] (총 {total_archived_count}건 보관) {primary_title}")

if __name__ == "__main__":
    try:
        if "--clear-memo" in sys.argv:
            clear_processed_memo()
        else:
            run_automation()
    except Exception as exc:
        print(f"✗ [오류 중단] 자동화 실행 중 문제가 발생했습니다: {exc}", file=sys.stderr)
        sys.exit(1)