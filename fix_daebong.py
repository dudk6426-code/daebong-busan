# -*- coding: utf-8 -*-
import datetime
import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
TRACKED_TAGS = {
    "div",
    "article",
    "section",
    "main",
    "ul",
    "ol",
    "li",
    "a",
    "details",
}


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
        for _ in range(len(self.stack) - 1, i - 1, -1):
          popped = self.stack.pop()
          if popped.end_idx is None:
            popped.end_idx = end_pos
        break


def strip_all_old_patches(html_text):
  """이전 패치 흔적을 제거하고, 기존에 접어둔 카드가 있다면 손실 없이 원래 위치로 복원합니다."""
  # 기존 접기 박스(DAEBONG_FOLD)가 있으면 내부 카드들만 살려서 밖으로 꺼냄
  fold_pattern = re.compile(
      r"<!-- DAEBONG_FOLD_START -->.*?<!-- DAEBONG_FOLD_CARDS_START -->(.*?)<!--"
      r" DAEBONG_FOLD_CARDS_END -->.*?<!-- DAEBONG_FOLD_END -->\s*",
      flags=re.S,
  )
  html_text = fold_pattern.sub(r"\1\n", html_text)

  # 혹시 카드 없는 구버전 DAEBONG_FOLD 블록이 있으면 제거
  html_text = re.sub(
      r"<!-- DAEBONG_FOLD_START -->.*?<!-- DAEBONG_FOLD_END -->\s*",
      "",
      html_text,
      flags=re.S,
  )

  # 이전 숨김 스크립트 및 구버전 패치 주석 제거
  html_text = re.sub(
      r"<style>\s*\.db-hidden-card\b.*?</script>\s*", "", html_text, flags=re.S
  )
  for marker in [
      "DAEBONG_FAV",
      "DAEBONG_UI",
      "DAEBONG_FAVICON",
      "DAEBONG_UI_PATCH",
      "DAEBONG_ARCHIVE_BOX",
  ]:
    html_text = re.sub(
        rf"<!-- {marker}_START -->.*?<!-- {marker}_END -->\s*",
        "",
        html_text,
        flags=re.S,
    )

  for cls_name in ["db-hidden-card", "db-hidden-case", "db-extra-hidden"]:
    html_text = html_text.replace(f" {cls_name}", "").replace(cls_name, "")

  html_text = re.sub(
      r'\s*style="display:\s*none\s*!important;?"', "", html_text
  )
  return html_text


def find_regional_guide_heading(html_text):
  """네비게이션이나 메타태그가 아닌 본문의 '지역별 · 세부 작업별 철거 및 폐기물 안내' 제목 위치를 찾습니다."""
  h_pat = re.compile(
      r"<h[1-4][^>]*>[^<]*지역별\s*(?:[·ㆍ.]|&middot;|&#183;)?\s*세부\s*작업별\s*철거\s*및\s*폐기물\s*안내[\s\S]*?</h[1-4]>",
      re.I,
  )
  m = h_pat.search(html_text)
  if m:
    return m

  fallback_pat = re.compile(
      r"지역별\s*(?:[·ㆍ.]|&middot;|&#183;)?\s*세부\s*작업별\s*철거\s*및\s*폐기물\s*안내"
  )
  matches = list(fallback_pat.finditer(html_text))
  return matches[-1] if matches else None


def count_cards_in_slice(s):
  """해당 HTML 조각 안에 들어있는 지역별 안내 카드의 개수를 판별합니다."""
  c1 = s.count("현장 작업 가이드")
  c2 = s.count("이 글 전용 페이지")
  c3 = len(re.findall(r"전화\s*상담\s*\(010-8535-9787\)", s))
  c4 = len(re.findall(r"이\s*작업\s*사진\s*문자로\s*견적상담", s))
  return max(c1, c2, c3, c4)


def is_single_card_slice(s):
  """단일 카드가 맞는지 검증 (제목 태그 + 상담/가이드 요소 동시 포함 & 카드 수 1개)"""
  if count_cards_in_slice(s) != 1:
    return False
  has_heading = bool(re.search(r"<h[234]\b", s, re.I))
  has_marker = any(
      k in s
      for k in [
          "현장 작업 가이드",
          "이 글 전용 페이지",
          "010-8535-9787",
          "문자로 견적상담",
      ]
  )
  return has_heading and has_marker


def find_guide_card_nodes(html_text):
  """전체 HTML을 파싱하여 '지역별 · 세부 작업별 안내' 섹션 내부의 개별 카드 노드 목록만 정확히 반환합니다."""
  m_guide = find_regional_guide_heading(html_text)
  if not m_guide:
    return None, []

  parser = OffsetTreeParser(html_text)
  parser.feed(html_text)

  # '지역별 안내' 제목을 감싸는 가장 안쪽 <section> (없으면 상위 컨테이너) 찾기
  enclosing_sections = [
      n
      for n in parser.all_nodes
      if n.tag == "section"
      and n.end_idx is not None
      and n.start_idx < m_guide.start()
      and n.end_idx > m_guide.end()
  ]
  if enclosing_sections:
    sec_node = max(enclosing_sections, key=lambda n: n.start_idx)
    sec_end = sec_node.end_idx
  else:
    next_sec = re.search(
        r"<(?:section|footer)\b", html_text[m_guide.end() :], re.I
    )
    sec_end = (
        (m_guide.end() + next_sec.start()) if next_sec else len(html_text)
    )

  # 제목(m_guide.end()) 이후 ~ 섹션 끝(sec_end) 사이에서 단일 카드 컨테이너 후보 탐색
  candidates = []
  for node in parser.all_nodes:
    if node.tag not in ("article", "div") or node.end_idx is None:
      continue
    if node.start_idx < m_guide.end() or node.end_idx > sec_end:
      continue
    s = html_text[node.start_idx : node.end_idx]
    if is_single_card_slice(s):
      candidates.append(node)

  # 카드 내부의 중첩 <div>가 중복 선택되지 않도록 가장 바깥쪽(최외곽) 단일 카드 노드만 추출
  cand_set = set(candidates)
  card_nodes = []
  for node in candidates:
    p = node.parent
    has_card_ancestor = False
    while p and p != parser.root:
      if p in cand_set:
        has_card_ancestor = True
        break
      p = p.parent
    if not has_card_ancestor:
      card_nodes.append(node)

  card_nodes.sort(key=lambda n: n.start_idx)
  return m_guide, card_nodes


def extract_card_title(card_html):
  mh = re.search(r"<h[234][^>]*>(.*?)</h[234]>", card_html, re.S | re.I)
  if mh:
    return re.sub(r"<[^>]+>", "", mh.group(1)).strip()
  return ""


def restore_from_git_if_needed(current_html):
  """1) 상단(작업분야 등)을 원본 상태로 보호하고

  2) 만약 이전 스크립트가 3번째 이후 카드를 아예 삭제했었다면 Git 기록에서 카드들을 복원해 접기 박스에 넣을 수 있게 합니다.
  """
  cleaned = strip_all_old_patches(current_html)
  m_curr, curr_cards = find_guide_card_nodes(cleaned)
  if not m_curr:
    return cleaned

  try:
    commits = subprocess.check_output(
        ["git", "log", "--format=%H", "-n", "30"],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="ignore",
    ).splitlines()

    # 상단 복구용 원본 및 과거 누적 카드 수집
    restored_upper = False
    collected_extra_cards = []
    seen_titles = {
        extract_card_title(cleaned[c.start_idx : c.end_idx]) for c in curr_cards
    }

    for c in commits:
      c = c.strip()
      if not c:
        continue
      old_raw = subprocess.check_output(
          ["git", "show", f"{c}:index.html"],
          cwd=str(ROOT),
          text=True,
          encoding="utf-8",
          errors="ignore",
      )
      old_clean = strip_all_old_patches(old_raw)
      m_old, old_cards = find_guide_card_nodes(old_clean)
      if not m_old:
        continue

      # 상단 섹션 원상복구 (최초 1회)
      if not restored_upper and "db-hidden-card" not in old_raw:
        old_sec_start = old_clean.rfind("<section", 0, m_old.start())
        curr_sec_start = cleaned.rfind("<section", 0, m_curr.start())
        if old_sec_start != -1 and curr_sec_start != -1:
          cleaned = old_clean[:old_sec_start] + cleaned[curr_sec_start:]
          m_curr, curr_cards = find_guide_card_nodes(cleaned)
          restored_upper = True

      # 만약 현재 파일에 카드가 2개 이하로 삭제되어 있다면 과거 커밋에서 누락된 카드 복원
      if len(curr_cards) <= 2 and len(old_cards) > 2:
        for oc in old_cards:
          oc_html = old_clean[oc.start_idx : oc.end_idx]
          t_str = extract_card_title(oc_html)
          if t_str and t_str not in seen_titles:
            seen_titles.add(t_str)
            collected_extra_cards.append(oc_html)
        if len(curr_cards) + len(collected_extra_cards) > 2:
          break

    # 복원된 이전 카드가 있다면 마지막 카드 바로 뒤에 이어붙임
    if collected_extra_cards and curr_cards:
      insert_pos = curr_cards[-1].end_idx
      extra_blob = "\n\n" + "\n\n".join(collected_extra_cards)
      cleaned = cleaned[:insert_pos] + extra_blob + cleaned[insert_pos:]
  except Exception:
    pass

  return strip_all_old_patches(cleaned)


def fix_index_regional_guide_only():
  idx_path = ROOT / "index.html"
  if not idx_path.exists():
    return None, 0, 0, 0, []

  raw_html = idx_path.read_text(encoding="utf-8", errors="ignore")
  t = restore_from_git_if_needed(raw_html)

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

  m_guide, card_nodes = find_guide_card_nodes(t)
  if not m_guide or not card_nodes:
    idx_path.write_text(t, encoding="utf-8")
    return None, 0, 0, 0, []

  total_found = len(card_nodes)
  latest_card_html = t[card_nodes[0].start_idx : card_nodes[0].end_idx]

  # auto-cases 폴더 기준 전체 누적 개수 확인
  ac_dir = ROOT / "auto-cases"
  total_archived = total_found
  if ac_dir.exists():
    dirs = [
        d
        for d in ac_dir.iterdir()
        if d.is_dir() and (d / "index.html").exists()
    ]
    total_archived = max(len(dirs), total_found)

  kept_titles = []
  for cnode in card_nodes[:2]:
    title_str = extract_card_title(t[cnode.start_idx : cnode.end_idx])
    if title_str:
      kept_titles.append(title_str)

  folded_cnt = max(0, total_found - 2)

  if total_found > 2:
    # 3번째 카드부터 마지막 카드까지 HTML을 추출하여 접기(펼쳐보기) 박스 안으로 이동
    hidden_cards_list = [t[c.start_idx : c.end_idx] for c in card_nodes[2:]]
    hidden_cards_joined = "\n\n".join(hidden_cards_list)

    # 기존 위치에서 3번째 이후 카드 제거 (뒤에서부터 제거하여 인덱스 유지)
    for cnode in reversed(card_nodes[2:]):
      t = t[: cnode.start_idx] + t[cnode.end_idx :]

    # 2번째 카드 바로 뒤에 '펼쳐보기/접기 토글 + 전용 목록 이동' 박스 삽입
    second_end = card_nodes[1].end_idx
    fold_box = f"""
<!-- DAEBONG_FOLD_START -->
<div id="db-regional-fold-wrap" style="grid-column: 1 / -1; width: 100%; margin: 24px 0 16px;">
  <div style="padding: 24px 20px; background: #ffffff; border: 2px solid #cbd5e1; border-left: 5px solid #14532d; border-radius: 14px; text-align: center; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);">
    <p style="margin: 0 0 6px; font-size: 1.04rem; font-weight: 800; color: #0f172a;">
      📌 메인 화면에는 최신 지역·작업별 안내 2건만 우선 표시됩니다.
    </p>
    <p style="margin: 0 0 18px; font-size: 0.92rem; color: #475569;">
      나머지 지역별 안내(<strong>+{folded_cnt}건</strong>)는 아래 버튼을 눌러 바로 펼쳐보시거나 전용 목록 페이지에서 확인하실 수 있습니다.
    </p>
    <div style="display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; align-items: center;">
      <button type="button" id="db-fold-toggle-btn"
        onclick="(function(){{
          var box = document.getElementById('db-more-guides-list');
          var btn = document.getElementById('db-fold-toggle-btn');
          if (!box || !btn) return;
          if (box.style.display === 'none') {{
            box.style.display = 'flex';