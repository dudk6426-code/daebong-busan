# -*- coding: utf-8 -*-
import datetime
import hashlib
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def create_favicons():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">\n'
        '  <rect width="92" height="92" x="4" y="4" rx="18" fill="#ffffff" stroke="#1d4ed8" stroke-width="6"/>\n'
        '  <text x="50" y="64" font-family="Malgun Gothic, sans-serif" font-size="38" font-weight="900" fill="#1d4ed8" text-anchor="middle">대봉</text>\n'
        '</svg>\n'
    )
    (ROOT / "favicon.svg").write_text(svg, encoding="utf-8")
    png_p = str(ROOT / "favicon.png")
    ico_p = str(ROOT / "favicon.ico")
    ps = f"""
    Add-Type -AssemblyName System.Drawing
    $b = New-Object System.Drawing.Bitmap(192, 192)
    $g = [System.Drawing.Graphics]::FromImage($b)
    $g.SmoothingMode = 'AntiAlias'
    $g.Clear([System.Drawing.Color]::White)
    $p = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(29, 78, 216), 10)
    $g.DrawRectangle($p, 6, 6, 180, 180)
    $f = New-Object System.Drawing.Font('Malgun Gothic', 58, [System.Drawing.FontStyle]::Bold)
    $br = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(29, 78, 216))
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = 'Center'
    $sf.LineAlignment = 'Center'
    $rect = New-Object System.Drawing.RectangleF(0, 4, 192, 192)
    $g.DrawString('대봉', $f, $br, $rect, $sf)
    $b.Save('{png_p}', [System.Drawing.Imaging.ImageFormat]::Png)
    $b64 = New-Object System.Drawing.Bitmap($b, 64, 64)
    $b64.Save('{ico_p}', [System.Drawing.Imaging.ImageFormat]::Icon)
    $g.Dispose(); $b.Dispose(); $b64.Dispose()
    """
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)


def clean_robotic_phrases(html_text):
    html_text = html_text.replace(
        "(※ 아래 안내는 동일 유형의 작업을 알아보시는 분들을 위한 공통 참고 기준입니다.)",
        "",
    )
    html_text = html_text.replace(
        "안녕하십니까, 사직동 본점을 중심으로 현장에서 직접 뛰는 대봉개발입니다. 😊",
        "부산·양산·김해·경남 현장을 30년 경력 직영 기술진이 직접 발로 뛰며 시공하는 대봉개발입니다.",
    )
    return html_text


def trim_index_to_two_cards():
    idx_path = ROOT / "index.html"
    if not idx_path.exists():
        return None
    t = idx_path.read_text(encoding="utf-8", errors="ignore")

    # 이전 패치 흔적 정리
    t = re.sub(r"<!-- DAEBONG_FAV_START -->.*?<!-- DAEBONG_FAV_END -->\s*", "", t, flags=re.S)
    t = re.sub(r"<!-- DAEBONG_UI_START -->.*?<!-- DAEBONG_UI_END -->\s*", "", t, flags=re.S)
    t = re.sub(r"<!-- DAEBONG_FAVICON_START -->.*?<!-- DAEBONG_FAVICON_END -->\s*", "", t, flags=re.S)
    t = re.sub(r"<!-- DAEBONG_UI_PATCH_START -->.*?<!-- DAEBONG_UI_PATCH_END -->\s*", "", t, flags=re.S)
    t = re.sub(r"<!-- DAEBONG_ARCHIVE_BOX_START -->.*?<!-- DAEBONG_ARCHIVE_BOX_END -->\s*", "", t, flags=re.S)

    fav_block = (
        "<!-- DAEBONG_FAV_START -->\n"
        '<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=10"/>\n'
        '<link rel="icon" type="image/png" sizes="192x192" href="/favicon.png?v=10"/>\n'
        '<link rel="shortcut icon" href="/favicon.ico?v=10"/>\n'
        '<link rel="apple-touch-icon" href="/favicon.png?v=10"/>\n'
        "<!-- DAEBONG_FAV_END -->"
    )
    if "</head>" in t:
        t = t.replace("</head>", fav_block + "\n</head>", 1)

    t = clean_robotic_phrases(t)

    # auto-cases 폴더 내 전체 누적 개수 파악
    ac_dir = ROOT / "auto-cases"
    total_archived = 0
    if ac_dir.exists():
        total_archived = len([d for d in ac_dir.iterdir() if d.is_dir() and (d / "index.html").exists()])

    # 카드 블록(<article>...</article>) 찾기
    art_re = re.compile(r"<article\b[^>]*>.*?</article>", re.DOTALL)
    matches = [
        m for m in art_re.finditer(t)
        if ("이 글 전용 페이지" in m.group(0) or "/auto-cases/" in m.group(0))
    ]

    latest_card_html = matches[0].group(0) if matches else ""
    before_count = len(matches)

    if before_count > 2:
        # 3번째 카드부터는 index.html에서 물리적으로 완전히 제거하여 최신 2개만 남김
        for m in reversed(matches[2:]):
            t = t[: m.start()] + t[m.end() :]

        # 다시 상위 2개 위치 확인 후 2번째 카드 바로 뒤에 전체 목록 이동 박스 삽입
        matches_after = [
            m for m in art_re.finditer(t)
            if ("이 글 전용 페이지" in m.group(0) or "/auto-cases/" in m.group(0))
        ]
        for i in range(min(2, len(matches_after)) - 1, -1, -1):
            m = matches_after[i]
            cleaned_card = m.group(0).replace("db-hidden-case", "")
            cleaned_card = re.sub(r'\s*style="display:\s*none\s*!important;?"', "", cleaned_card)
            t = t[: m.start()] + cleaned_card + t[m.end() :]

        matches_final = [
            m for m in art_re.finditer(t)
            if ("이 글 전용 페이지" in m.group(0) or "/auto-cases/" in m.group(0))
        ]
        if len(matches_final) >= 2:
            second_end = matches_final[1].end()
            count_label = max(total_archived, before_count)
            archive_box = (
                "\n<!-- DAEBONG_ARCHIVE_BOX_START -->\n"
                '<div style="grid-column: 1 / -1; width: 100%; margin: 28px 0 12px; padding: 26px 20px; '
                'background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 16px; text-align: center;">\n'
                '  <p style="margin: 0 0 8px; font-size: 1.05rem; font-weight: 800; color: #0f172a;">\n'
                "    📌 메인 화면에는 가장 최근 업데이트된 안내 2건만 표시됩니다.\n"
                "  </p>\n"
                '  <p style="margin: 0 0 16px; font-size: 0.92rem; color: #475569;">\n'
                f"    이전 지역별·작업별 상세 안내 및 시공 기록(총 {count_label}건 누적)은 전용 목록 페이지에서 모두 확인하실 수 있습니다.\n"
                "  </p>\n"
                '  <a href="/auto-cases/" style="display: inline-block; background: #1d4ed8; color: #ffffff; '
                "padding: 14px 30px; border-radius: 999px; font-weight: 800; font-size: 0.98rem; "
                'text-decoration: none; box-shadow: 0 4px 12px rgba(29,78,216,0.25);">\n'
                f"    🗂️ 다른 지역·작업별 안내 및 누적 기록 전체 보기 ({count_label}건 목록 이동)\n"
                "  </a>\n"
                "</div>\n"
                "<!-- DAEBONG_ARCHIVE_BOX_END -->\n"
            )
            t = t[:second_end] + archive_box + t[second_end:]

    idx_path.write_text(t, encoding="utf-8")

    # 서브 페이지들의 로봇 문구 및 파비콘도 일괄 정리
    if ac_dir.exists():
        for sub_html in ac_dir.rglob("*.html"):
            st = sub_html.read_text(encoding="utf-8", errors="ignore")
            st = clean_robotic_phrases(st)
            if "favicon.svg" not in st and "</head>" in st:
                st = st.replace("</head>", fav_block + "\n</head>", 1)
            sub_html.write_text(st, encoding="utf-8")

    after_matches = [
        m for m in art_re.finditer(t)
        if ("이 글 전용 페이지" in m.group(0) or "/auto-cases/" in m.group(0))
    ]
    print(f"✓ [홈페이지 검증] 메인 안내 카드 개수: 기존 {before_count}개 -> 현재 {len(after_matches)}개로 물리적 축소 완료!")
    return latest_card_html


def generate_diversified_blog(latest_card_html):
    today_str = datetime.date.today().strftime("%Y.%m.%d")
    region = "부산·경남"
    topic = "상가·식당 내부 철거 및 폐기물 정리"
    memo_line = ""
    post_id = f"post-{datetime.date.today().strftime('%Y%m%d')}"

    if latest_card_html:
        m_id = re.search(r"/auto-cases/([^/\"']+)", latest_card_html)
        if m_id:
            post_id = m_id.group(1)
        m_h3 = re.search(r"<h3[^>]*>(.*?)</h3>", latest_card_html, re.S)
        if m_h3:
            raw_title = re.sub(r"<[^>]+>", "", m_h3.group(1)).strip()
            # 예: "수영구 광안·남천동 식당·치킨집... - 사진 문자 견적..."
            parts = raw_title.split(" - ")[0].strip()
            tokens = parts.split()
            if len(tokens) >= 3:
                region = " ".join(tokens[:2])
                topic = " ".join(tokens[2:])
            else:
                topic = parts
        m_memo = re.search(r'작업 메모\s*:\s*"([^"]+)"', latest_card_html)
        if m_memo:
            memo_line = m_memo.group(1).strip()

    # blog_post.txt에서 추가 단서 추출 (최신 실행 직후일 경우)
    bp = ROOT / "blog_post.txt"
    if bp.exists():
        raw_bp = bp.read_text(encoding="utf-8", errors="ignore")
        m_reg = re.search(r"([가-힣]+(?:구|시|군)\s+[가-힣·]+(?:동|읍|면))\s+일대에서\s+(.+?)\s+업체를", raw_bp)
        if m_reg:
            region = m_reg.group(1).strip()
            topic = m_reg.group(2).strip()
        m_m = re.search(r'작업 메모\s*:\s*"([^"]+)"', raw_bp)
        if m_m:
            memo_line = m_m.group(1).strip()

    # 매 실행마다 다른 스타일이 나오도록 시간+지역+주제 조합 시드 생성
    seed_str = f"{region}-{topic}-{memo_line}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    h = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16)

    # 업종별 맞춤 디테일 문장
    if any(k in (topic + memo_line) for k in ["식당", "치킨", "포차", "주방", "음식점", "카페", "고깃집"]):
        equip_detail = "업소용 냉장고, 스텐 싱크대와 작업대, 화구, 천장 환풍 후드·닥트 배관, 홀 붙박이 의자와 가벽"
        work_focus = "기름기가 많은 주방 설비 특성상 가스·수도·전기 마감 상태를 가장 먼저 차단하고, 바닥이나 출입구 손상 없이 중량 장비를 안전하게 빼내는 것"
        check_tip = "주방 장비와 집기류만 단품으로 비울지, 아니면 홀 가벽·천장 닥트 해체와 주방 바닥 방수턱 파쇄(하스리)까지 포함한 전체 원상복구인지"
        tag_extra = "#식당폐업철거 #주방집기처분 #식당원상복구 #업소용냉장고폐기 #닥트철거"
    elif any(k in (topic + memo_line) for k in ["사무실", "학원", "부동산", "점포", "가벽", "칸막이"]):
        equip_detail = "유리 가벽, 석고보드·목재 칸막이, 상담 데스크, 사무용 책상·파티션, 바닥 데코타일 및 천장 텍스"
        work_focus = "건물 관리실이나 임대인이 요구하는 퇴거 점검 기준에 맞춰 남겨둘 설비와 철거할 가벽 범위를 정확히 구분해 해체하는 것"
        check_tip = "철거할 칸막이의 대략적인 길이, 바닥 데코타일·강화마루 제거 포함 여부, 엘리베이터 사용 가능 시간대"
        tag_extra = "#사무실원상복구 #상가철거 #가벽철거 #칸막이철거 #점포원상복구"
    elif any(k in (topic + memo_line) for k in ["공장", "창고", "주차장", "하스리", "구조물", "보일러", "운동장", "조형물"]):
        equip_detail = "조립식 샌드위치판넬 가벽, 철제 앵글·선반, 콘크리트 기초·방수턱, 노후 보일러 및 대형 철구조물"
        work_focus = "출입구 층고와 차량 진입 폭을 미리 파악해 절단·파쇄 장비를 적재적소에 배치하고 해체물과 고철·폐기물을 신속히 분리 상차하는 것"
        check_tip = "해체할 구조물의 대략적인 크기와 재질, 차량 진입 여건(지하주차장 층고 제한 유무 등), 반출할 사업장 폐기물 종류"
        tag_extra = "#구조물철거 #하스리작업 #사업장폐기물 #창고정리 #철구조물해체"
    else:
        equip_detail = "내부 인테리어 가벽, 매립 구조물, 대형 폐가구 및 각종 혼합 폐기물"
        work_focus = "주변 상가나 이웃에 소음·분진 불편을 최소화하면서 숙련된 인력이 하루 만에 해체부터 폐기물 상차·바닥 정리까지 마치는 것"
        check_tip = "비워내야 할 공간의 현장 사진 2~3장과 층수(계단 또는 엘리베이터 유무), 희망하시는 작업 일정"
        tag_extra = "#상가원상복구 #내부철거 #대형폐기물수거 #폐기물처리 #점포정리"

    memo_sentence = f"\n(최근 진행 기록 : {memo_line})\n" if memo_line else "\n"
    reg_clean = re.sub(r"[^가-힣a-zA-Z0-9]", "", region)
    hashtags = f"#{reg_clean}철거 #{reg_clean}폐기물 #{reg_clean}원상복구 {tag_extra} #부산철거 #경남철거 #대봉개발"

    # 6가지 완전히 다른 글 양식 (홈페이지 문장과 겹치지 않는 블로그 전용 에세이/후기 구조)
    styles = [
        (
            "양식 1 : 현장 반장 실무 노트형",
            f"""현장마다 구조도 다르고 물건을 빼내는 동선도 제각각입니다.
{region} 일대에서 {topic} 작업을 준비하다 보면 어디서부터 손을 대야 할지 막막해하시는 분들을 자주 뵙습니다.{memo_sentence}
혼자서 정리하기 버거운 {equip_detail} 등은 전용 장비와 손발이 잘 맞는 베테랑 인력이 투입되어야 안전하고 빠르게 비워낼 수 있습니다.

특히 이번 공정에서 저희 대봉개발이 가장 중요하게 챙기는 기준은 '{work_focus}'입니다.

단순히 부수고 치우는 데 그치지 않고, 작업 후 임대인이나 관리실 퇴거 확인을 바로 받으실 수 있도록 바닥 잔해물 빗질까지 깔끔하게 마무리해 드리고 있습니다.

[상담 전 미리 확인해 두시면 좋은 점]
• {check_tip}를 먼저 파악해 두시면 견적 산출이 훨씬 정확해집니다.
• 사진에서 미처 보이지 않던 숨은 구조물이 현장에서 발견되더라도 임의로 진행하지 않고, 반드시 먼저 설명드리고 협의를 거친 뒤 작업합니다.

바쁘신 와중에 복잡한 설명 적으실 필요 없이, 현장 사진 몇 장과 [{region} / 층수]만 010-8535-9787 번으로 문자 남겨주세요.
30년 경력 직영 팀이 현장 여건에 맞는 가장 합리적인 방법과 일정을 친절히 안내해 드리겠습니다.
더 다양한 시공 사례는 공식 홈페이지(https://daebong-busan.kr/)에서도 확인하실 수 있습니다.

{hashtags}"""
        ),
        (
            "양식 2 : 단계별 공정 브리핑형",
            f"""{region} 현장에서 {topic} 업체를 알아보실 때, 작업이 어떤 순서로 진행되는지 궁금해하시는 분들을 위해 대봉개발의 실제 직영 작업 과정을 정리해 드립니다.{memo_sentence}
STEP 1. 사전 마감 점검 및 반출 동선 확보
현장에 도착하면 가장 먼저 인접 점포나 이웃에 불편이 없도록 차량 위치와 반출 경로를 확보합니다. {work_focus}이 첫 번째 원칙입니다.

STEP 2. {equip_detail} 해체 및 분리 반출
30년 손발을 맞춰온 직영 기술진이 순서대로 구조물과 설비를 해체합니다. 하청을 주지 않고 직접 시공하기 때문에 작업 속도가 빠르고 중간 거품 비용이 없습니다.

STEP 3. 폐기물 상차 및 바닥 정리 마감
발생한 폐기물을 차량에 빈틈없이 상차한 뒤, 현장에 남은 잔먼지와 부스러기까지 깨끗하게 정리하여 기분 좋게 인계해 드립니다.

💡 빠른 사진 견적 팁
현장 방문 전이라도 [{check_tip}] 내용을 현장 사진 2~3장과 함께 010-8535-9787 로 문자 주시면 대략적인 비용과 소요 시간을 바로 확인하실 수 있습니다.
부산·양산·김해·경남 어디든 성실하게 상담해 드립니다. (홈페이지 : https://daebong-busan.kr/)

{hashtags}"""
        ),
        (
            "양식 3 : 고객 고민 해결 & Q&A 에세이형",
            f""""철거까지 다 해야 할까요, 아니면 안에 있는 집기랑 폐기물만 비워도 될까요?"
{region}에서 {topic} 문의를 주시는 사장님들께서 가장 먼저 물어보시는 질문입니다.{memo_sentence}
결론부터 말씀드리면 현장 상황에 맞춰 꼭 필요한 만큼만 선택해서 진행하실 수 있습니다.

1) 내부 설비·집기류 단독 수거가 필요한 경우
인테리어 해체 없이 {equip_detail} 중 무거운 품목과 마대 폐기물만 깔끔하게 빼내는 작업만 단독으로 맡기실 수 있습니다.

2) 임대차 계약 만료에 따른 전체 원상복구인 경우
{work_focus}을 중심으로, 계약 조건에 맞춘 철거부터 폐기물 반출까지 한 번에 해결해 드립니다.

3) 비대면 진행이 필요하신 경우
생업으로 바쁘셔서 현장에 계속 계시기 어렵더라도 걱정하지 마세요. 사전 협의된 범위에 맞춰 작업 전·후 사진을 문자로 투명하게 공유해 드립니다.

문의하실 때는 {check_tip} 정도만 사진과 함께 010-8535-9787 로 편하게 문자 남겨주세요.
30년 경력의 대봉개발(https://daebong-busan.kr/)이 정직한 견적으로 도와드리겠습니다.

{hashtags}"""
        ),
        (
            "양식 4 : 견적 체크리스트 & 실패 방지 가이드형",
            f"""{region} 일대에서 {topic} 견적을 비교하실 때, 나중에 얼굴 붉히는 추가 비용 없이 깔끔하게 마무리하려면 아래 세 가지는 꼭 확인해 보시는 것이 좋습니다.{memo_sentence}
첫째, 하청 없는 직영 인력이 직접 시공하는가?
영업만 하고 외주를 주는 곳과 달리, 대봉개발은 30년 경력의 베테랑 직영 팀이 직접 현장에 투입되어 {equip_detail} 해체부터 상차까지 책임집니다.

둘째, 설비 마감과 안전 조치가 확실한가?
무작정 부수는 철거는 위험합니다. {work_focus}이 선행되어야 누수나 안전사고 없이 공정이 마무리됩니다.

셋째, 사전 견적 소통이 명확한가?
문자로 보내주시는 현장 사진과 함께 [{check_tip}]를 알려주시면, 현장 조건에 딱 맞는 투명한 견적을 안내해 드립니다. 혹시라도 사진에 보이지 않던 변수가 있으면 작업 전에 먼저 말씀드리고 협의합니다.

부산 사직동 본점을 중심으로 {region} 및 경남 전 지역을 발로 뛰고 있습니다.
편하게 010-8535-9787 로 사진 문자 남겨주시면 확인 즉시 연락드리겠습니다. (공식 안내 : https://daebong-busan.kr/)

{hashtags}"""
        ),
    ]

    style_name, body_text = styles[h % len(styles)]

    titles = [
        f"{region} {topic}, 현장 진행 순서와 사진 견적 체크포인트",
        f"{region} {topic} 비용 줄이는 실무 팁과 직영 작업 기록",
        f"{region} {topic} 상담 전 알아두면 좋은 체크리스트 (대봉개발)",
    ]

    # 클립보드에는 순수 본문(body_text)만 복사하여 블로그에 바로 붙여넣을 수 있게 함
    bp.write_text(body_text, encoding="utf-8")
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-Content -Path 'blog_post.txt' -Encoding UTF8 -Raw | Set-Clipboard",
        ],
        cwd=str(ROOT),
        check=False,
    )

    preview_box = f"""====================================================================
 [대봉개발 블로그 원고 (AI 유사문서 방지 다변화 엔진 적용)]
 • 적용된 양식 : {style_name} (매 실행 시 자동 변주)
 • 대상 문서 ID : {post_id}
 ★ 아래 [본문]이 클립보드에 새로 복사되었습니다! (블로그에 바로 Ctrl+V)
====================================================================

[블로그 맞춤형 추천 제목 3선]
후보 1 : {titles[0]}
후보 2 : {titles[1]}
후보 3 : {titles[2]}

--------------------------------------------------------------------
[새로 생성된 블로그 본문 미리보기]

{body_text}
===================================================================="""
    return preview_box


def hook_main_and_run_bat():
    # 1. automation/main.py 최상단에 atexit 훅 설치 (sys.exit으로 종료되어도 무조건 fix_daebong.py 실행)
    mp = ROOT / "automation" / "main.py"
    if mp.exists():
        mt = mp.read_text(encoding="utf-8", errors="ignore")
        # 예전 느슨한 하단 훅 제거
        mt = re.sub(r"\nimport subprocess, sys.*?fix_all\.py.*?\n", "\n", mt, flags=re.S)
        mt = re.sub(r"\nimport subprocess, sys.*?patch_blog\.py.*?\n", "\n", mt, flags=re.S)
        mt = re.sub(r"\nimport subprocess, sys.*?blog_variator\.py.*?\n", "\n", mt, flags=re.S)

        top_hook = (
            "# DAEBONG_ATEXIT_HOOK\n"
            "import atexit as _atexit, subprocess as _sp, sys as _sys\n"
            "from pathlib import Path as _P\n"
            "_atexit.register(lambda: _sp.run([_sys.executable, str(_P(__file__).resolve().parent.parent / 'fix_daebong.py')], check=False))\n"
        )
        if "DAEBONG_ATEXIT_HOOK" not in mt:
            lines = mt.splitlines(True)
            insert_idx = 0
            for i, line in enumerate(lines[:5]):
                if line.startswith("#") or "from __future__" in line:
                    insert_idx = i + 1
            lines.insert(insert_idx, top_hook)
            mt = "".join(lines)
        mp.write_text(mt, encoding="utf-8")

    # 2. CNAME 파일 고정
    (ROOT / "CNAME").write_text("daebong-busan.kr\n", encoding="utf-8")

    # 3. run.bat 내 git push가 충돌로 막히지 않도록 보강
    rb = ROOT / "run.bat"
    if rb.exists():
        rt = rb.read_text(encoding="utf-8", errors="ignore")
        if "git push origin main" in rt and "--force" not in rt:
            rt = rt.replace("git push origin main", "git push origin main --force")
            rb.write_text(rt, encoding="utf-8")


if __name__ == "__main__":
    create_favicons()
    hook_main_and_run_bat()
    latest_card = trim_index_to_two_cards()
    preview = generate_diversified_blog(latest_card)
    os.system("cls")
    print(preview)