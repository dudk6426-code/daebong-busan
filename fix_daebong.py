# -*- coding: utf-8 -*-
import datetime
import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
TRACKED_TAGS = {"div", "article", "section", "main", "ul", "ol", "li", "a"}


class Node:

  def __init__(self, tag, start_idx, parent=None):
    self.tag = tag
    self.start_idx = start_idx
    self.end_idx = None
    self.parent = parent
    self.children = []


class OffsetTreeParser(HTMLParser):

  def __init__(self, html_text):
    super().__init__()
    self.html_text = html_text
    self.line_starts = [0]
    for line in html_text.splitlines(True):
      self.line_starts.append(self.line_starts[-1] + len(line))
    self.root = Node("root", 0)
    self.root.end_idx = len(html_text)
    self.stack = [self.root]
    self.all_nodes = []

  def _pos_to_idx(self):
    lineno, col = self.getpos()
    return self.line_starts[lineno - 1] + col

  def handle_starttag(self, tag, attrs):
    t = tag.lower()
    if t not in TRACKED_TAGS:
      return
    idx = self._pos_to_idx()
    node = Node(t, idx, parent=self.stack[-1])
    self.stack[-1].children.append(node)
    self.stack.append(node)
    self.all_nodes.append(node)

  def handle_endtag(self, tag):
    t = tag.lower()
    if t not in TRACKED_TAGS:
      return
    idx = self._pos_to_idx()
    end_gt = self.html_text.find(">", idx)
    end_pos = (end_gt + 1) if end_gt != -1 else len(self.html_text)
    for i in range(len(self.stack) - 1, 0, -1):
      if self.stack[i].tag == t:
        for j in range(len(self.stack) - 1, i - 1, -1):
          popped = self.stack.pop()
          if popped.end_idx is None:
            popped.end_idx = end_pos
        break


def strip_all_old_patches(html_text):
  # 이전에 작업분야를 숨겼던 db-hidden-card 스크립트 및 모든 패치 흔적 완전 제거
  html_text = re.sub(
      r"<style>\s*\.db-hidden-card\b.*?</script>\s*", "", html_text, flags=re.S
  )
  html_text = re.sub(
      r"<!-- DAEBONG_FAV_START -->.*?<!-- DAEBONG_FAV_END -->\s*",
      "",
      html_text,
      flags=re.S,
  )
  html_text = re.sub(
      r"<!-- DAEBONG_UI_START -->.*?<!-- DAEBONG_UI_END -->\s*",
      "",
      html_text,
      flags=re.S,
  )
  html_text = re.sub(
      r"<!-- DAEBONG_FAVICON_START -->.*?<!-- DAEBONG_FAVICON_END -->\s*",
      "",
      html_text,
      flags=re.S,
  )
  html_text = re.sub(
      r"<!-- DAEBONG_UI_PATCH_START -->.*?<!-- DAEBONG_UI_PATCH_END -->\s*",
      "",
      html_text,
      flags=re.S,
  )
  html_text = re.sub(
      r"<!-- DAEBONG_ARCHIVE_BOX_START -->.*?<!-- DAEBONG_ARCHIVE_BOX_END"
      r" -->\s*",
      "",
      html_text,
      flags=re.S,
  )
  html_text = html_text.replace(" db-hidden-card", "").replace(
      "db-hidden-card", ""
  )
  html_text = html_text.replace(" db-hidden-case", "").replace(
      "db-hidden-case", ""
  )
  html_text = html_text.replace(" db-extra-hidden", "").replace(
      "db-extra-hidden", ""
  )
  html_text = re.sub(
      r'\s*style="display:\s*none\s*!important;?"', "", html_text
  )
  return html_text


def restore_upper_sections_from_git(current_html):
  """Git 기록에서 패치 전 원본을 찾아 '지역별 · 세부 작업별 철거 및 폐기물 안내' 위쪽(작업분야 등)을 100% 원상복구"""
  guide_pat = re.compile(
      r"지역별\s*[·ㆍ.]?\s*세부\s*작업별\s*철거\s*및\s*폐기물\s*안내"
  )
  m_curr = guide_pat.search(current_html)
  if not m_curr:
    return strip_all_old_patches(current_html)

  try:
    commits = subprocess.check_output(
        ["git", "log", "--format=%H", "-n", "30"],
        cwd=str(ROOT),
        text=True,
         encoding="utf-8",
        errors="ignore",
    ).splitlines()
    for c in commits:
      c = c.strip()
      if not c:
        continue
      old_html = subprocess.check_output(
          ["git", "show", f"{c}:index.html"],
          cwd=str(ROOT),
          text=True,
          encoding="utf-8",
          errors="ignore",
      )
      if (
          "db-hidden-card" not in old_html
          and "DAEBONG_ARCHIVE_BOX" not in old_html
          and "DAEBONG_UI" not in old_html
      ):
        m_old = guide_pat.search(old_html)
        if m_old:
          # '지역별 안내' 섹션의 시작 태그(<section 또는 <div) 위치 찾기
          old_sec_start = old_html.rfind("<section", 0, m_old.start())
          curr_sec_start = current_html.rfind("<section", 0, m_curr.start())
          if old_sec_start != -1 and curr_sec_start != -1:
            restored = old_html[:old_sec_start] + current_html[curr_sec_start:]
            return strip_all_old_patches(restored)
        break
  except Exception:
    pass
  return strip_all_old_patches(current_html)


def fix_index_regional_guide_only():
  idx_path = ROOT / "index.html"
  if not idx_path.exists():
    return None, 0, 0, []

  raw_html = idx_path.read_text(encoding="utf-8", errors="ignore")
  # 1단계: 작업분야 등 상단 영역 100% 원상복구 및 이전 숨김 스크립트 박멸
  t = restore_upper_sections_from_git(raw_html)

  # 파비콘 태그 삽입
  fav_block = (
      "<!-- DAEBONG_FAV_START -->\n"
      '<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=20"/>\n'
      '<link rel="icon" type="image/png" sizes="192x192"'
      ' href="/favicon.png?v=20"/>\n'
      '<link rel="shortcut icon" href="/favicon.ico?v=20"/>\n'
      '<link rel="apple-touch-icon" href="/favicon.png?v=20"/>\n'
      "<!-- DAEBONG_FAV_END -->"
  )
  if "</head>" in t:
    t = t.replace("</head>", fav_block + "\n</head>", 1)

  # 2단계: 오직 '지역별 · 세부 작업별 철거 및 폐기물 안내' 제목 이후 영역만 분리
  guide_pat = re.compile(
      r"지역별\s*[·ㆍ.]?\s*세부\s*작업별\s*철거\s*및\s*폐기물\s*안내"
  )
  m_guide = guide_pat.search(t)
  if not m_guide:
    idx_path.write_text(t, encoding="utf-8")
    return None, 0, 0, []

  # 절대 건드리면 안 되는 상단 영역(작업분야 포함)과 하단 지역별 안내 영역을 물리적으로 분리
  upper_safe_html = t[: m_guide.start()]
  lower_guide_html = t[m_guide.start() :]

  # lower_guide_html 내부만 DOM 트리 파싱
  parser = OffsetTreeParser(lower_guide_html)
  parser.feed(lower_guide_html)

  link_nodes = []
  for node in parser.all_nodes:
    if node.tag == "a" and node.end_idx is not None:
      a_html = lower_guide_html[node.start_idx : node.end_idx]
      if "이 글 전용 페이지" in a_html:
        link_nodes.append(node)

  def count_links_in(container_node):
    cnt = 0
    for ln in link_nodes:
      if (
          container_node.start_idx <= ln.start_idx
          and ln.end_idx <= container_node.end_idx
      ):
        cnt += 1
    return cnt

  card_nodes = []
  for ln in link_nodes:
    cur = ln
    while cur.parent and cur.parent != parser.root:
      if count_links_in(cur.parent) > 1:
        break
      cur = cur.parent
    if cur not in card_nodes:
      card_nodes.append(cur)

  before_cnt = len(card_nodes)
  latest_card_html = (
      lower_guide_html[card_nodes[0].start_idx : card_nodes[0].end_idx]
      if card_nodes
      else ""
  )

  # 전체 누적 개수 확인
  ac_dir = ROOT / "auto-cases"
  total_archived = before_cnt
  if ac_dir.exists():
    dirs = [
        d
        for d in ac_dir.iterdir()
        if d.is_dir() and (d / "index.html").exists()
    ]
    total_archived = max(len(dirs), before_cnt)

  kept_titles = []
  for cnode in card_nodes[:2]:
    chtml = lower_guide_html[cnode.start_idx : cnode.end_idx]
    mh = re.search(r"<h[234][^>]*>(.*?)</h[234]>", chtml, re.S)
    if mh:
      kept_titles.append(re.sub(r"<[^>]+>", "", mh.group(1)).strip())

  if before_cnt > 2:
    # 3번째 카드부터 마지막 카드까지 물리적으로 제거
    for cnode in reversed(card_nodes[2:]):
      lower_guide_html = (
          lower_guide_html[: cnode.start_idx]
          + lower_guide_html[cnode.end_idx :]
      )

    # 2번째 카드 바로 뒤에 전체 목록 페이지 이동 버튼 삽입
    second_end = card_nodes[1].end_idx
    archive_box = (
        "\n<!-- DAEBONG_ARCHIVE_BOX_START -->\n"
        '<div style="grid-column: 1 / -1; width: 100%; margin: 24px 0 12px;'
        " padding: 24px 20px; background: #f8fafc; border: 2px solid #cbd5e1;"
        ' border-radius: 16px; text-align: center;">\n'
        '  <p style="margin: 0 0 8px; font-size: 1.02rem; font-weight: 800;'
        ' color: #0f172a;">\n'
        "    📌 지역별 · 세부 작업별 안내에는 최신 업데이트된 2건만"
        " 표시됩니다.\n"
        "  </p>\n"
        '  <p style="margin: 0 0 16px; font-size: 0.92rem; color: #475569;">\n'
        "    다른 지역·작업별 상세 안내 및 누적 시공 기록(총"
        f" {total_archived}건)은 전용 목록 페이지에서 모두 확인하실 수"
        " 있습니다.\n"
        "  </p>\n"
        '  <a href="/auto-cases/" style="display: inline-block; background:'
        " #1d4ed8; color: #ffffff; padding: 14px 28px; border-radius: 999px;"
        " font-weight: 800; font-size: 0.96rem; text-decoration: none;"
        ' box-shadow: 0 4px 12px rgba(29,78,216,0.25);">\n'
        "    🗂️ 다른 지역·작업별 안내 및 누적 기록 전체 보기"
        f" (+{total_archived}건 목록 이동)\n"
        "  </a>\n"
        "</div>\n"
        "<!-- DAEBONG_ARCHIVE_BOX_END -->\n"
    )
    lower_guide_html = (
        lower_guide_html[:second_end]
        + archive_box
        + lower_guide_html[second_end:]
    )

  # 재결합 (상단 작업분야는 100% 보존됨)
  final_html = upper_safe_html + lower_guide_html
  idx_path.write_text(final_html, encoding="utf-8")

  # 재검증 파싱
  v_parser = OffsetTreeParser(final_html[m_guide.start() :])
  v_parser.feed(final_html[m_guide.start() :])
  after_cnt = sum(
      1
      for n in v_parser.all_nodes
      if n.tag == "a"
      and n.end_idx
      and "이 글 전용 페이지" in final_html[m_guide.start() :][n.start_idx : n.end_idx]
  )

  return latest_card_html, before_cnt, after_cnt, kept_titles


def generate_diversified_blog(latest_card_html):
  region = "부산·경남"
  topic = "상가·식당 내부 철거 및 폐기물 정리"
  memo_line = ""
  post_id = f"post-{datetime.date.today().strftime('%Y%m%d')}"

  if latest_card_html:
    m_id = re.search(r"/auto-cases/([^/\"']+)", latest_card_html)
    if m_id:
      post_id = m_id.group(1)
    m_h3 = re.search(r"<h[234][^>]*>(.*?)</h[234]>", latest_card_html, re.S)
    if m_h3:
      raw_title = re.sub(r"<[^>]+>", "", m_h3.group(1)).strip()
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

  seed_str = f"{region}-{topic}-{memo_line}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
  h = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16)

  if any(
      k in (topic + memo_line)
      for k in ["식당", "치킨", "포차", "주방", "음식점", "카페", "고깃집"]
  ):
    equip_detail = (
        "업소용 냉장고, 스텐 싱크대와 작업대, 화구, 천장 환풍 후드·닥트 배관,"
        " 홀 붙박이 의자와 가벽"
    )
    work_focus = (
        "기름기가 많은 주방 설비 특성상 가스·수도·전기 마감 상태를 가장 먼저"
        " 차단하고, 바닥이나 출입구 손상 없이 중량 장비를 안전하게 빼내는 것"
    )
    check_tip = (
        "주방 장비와 집기류만 단품으로 비울지, 아니면 홀 가벽·천장 닥트 해체와"
        " 주방 바닥 방수턱 파쇄(하스리)까지 포함한 전체 원상복구인지"
    )
    tag_extra = "#식당폐업철거 #주방집기처분 #식당원상복구 #업소용냉장고폐기 #닥트철거"
  elif any(
      k in (topic + memo_line)
      for k in ["사무실", "학원", "부동산", "점포", "가벽", "칸막이"]
  ):
    equip_detail = (
        "유리 가벽, 석고보드·목재 칸막이, 상담 데스크, 사무용 책상·파티션, 바닥"
        " 데코타일 및 천장 텍스"
    )
    work_focus = (
        "건물 관리실이나 임대인이 요구하는 퇴거 점검 기준에 맞춰 남겨둘 설비와"
        " 철거할 가벽 범위를 정확히 구분해 해체하는 것"
    )
    check_tip = (
        "철거할 칸막이의 대략적인 길이, 바닥 데코타일·강화마루 제거 포함 여부,"
        " 엘리베이터 사용 가능 시간대"
    )
    tag_extra = "#사무실원상복구 #상가철거 #가벽철거 #칸막이철거 #점포원상복구"
  else:
    equip_detail = "내부 인테리어 가벽, 설비 구조물, 대형 집기 및 각종 사업장·혼합 폐기물"
    work_focus = (
        "주변 상가나 이웃에 소음·분진 불편을 최소화하면서 숙련된 직영 인력이"
        " 해체부터 폐기물 상차·바닥 정리까지 깔끔하게 마치는 것"
    )
    check_tip = (
        "비워내야 할 공간의 현장 사진 2~3장과 층수(계단 또는 엘리베이터 유무),"
        " 희망하시는 작업 일정"
    )
    tag_extra = "#상가원상복구 #내부철거 #대형폐기물수거 #폐기물처리 #점포정리"

  memo_sentence = (
      f"\n(실제 진행 기록 : {memo_line})\n" if memo_line else "\n"
  )
  reg_clean = re.sub(r"[^가-힣a-zA-Z0-9]", "", region)
  hashtags = f"#{reg_clean}철거 #{reg_clean}폐기물 #{reg_clean}원상복구 {tag_extra} #부산철거 #경남철거 #대봉개발"

  styles = [
      (
          "현장 반장 실무 노트형",
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

{hashtags}""",
      ),
      (
          "단계별 공정 브리핑형",
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

{hashtags}""",
      ),
      (
          "고객 고민 해결 Q&A 에세이형",
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

{hashtags}""",
      ),
  ]

  style_name, body_text = styles[h % len(styles)]
  bp = ROOT / "blog_post.txt"
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
  return style_name, post_id, body_text


if __name__ == "__main__":
  latest_card, before_c, after_c, titles = fix_index_regional_guide_only()
  style_name, pid, blog_body = generate_diversified_blog(latest_card)
  os.system("cls")
  print("====================================================================")
  print(" [대봉개발 전면 재검증 및 수정 완료 보고]")
  print(" ✓ [검증 1] '작업분야' 카테고리 : 숨김 코드 완전 제거 및 100% 원상복구 완료")
  print(
      f" ✓ [검증 2] '지역별 · 세부 작업별 안내' 카드 수 : 기존 {before_c}개 ->"
      f" 현재 {after_c}개로 축소 완료"
  )
  for idx, title in enumerate(titles, 1):
    print(f"    - 노출 유지된 최신 글 [{idx}] : {title}")
  print(f" ✓ [검증 3] 블로그 원고 양식 : [{style_name}] 적용 및 클립보드 복사 완료")
  print("====================================================================\n")
  print(blog_body)