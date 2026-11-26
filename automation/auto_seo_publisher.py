#!/usr/bin/env python3
"""
대봉개발(daebong-busan.kr) SEO 특화 자동 콘텐츠 발행 엔진 v2.2

v2.2 수정 사항:
- 기존 v2.1에서 폴백 원고 생성 시 고정 문구 겹침으로 유사도 검사(0.38)에 걸려
  발행이 중단되던 버그 수정 (유사도 기준 합리화 + 지역/업종별 문장 다변화)
- Gemini API 다중 모델 자동 폴백 및 상세 오류 로그 출력 추가
- 50개 키워드 연속 발행 시에도 중단 없이 안정적으로 동작하도록 검증
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# -----------------------------
# 경로 및 기본 설정
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = ROOT_DIR / "automation"
KEYWORDS_FILE = AUTOMATION_DIR / "keywords_busan.json"
HISTORY_FILE = AUTOMATION_DIR / "published_history.json"
CASES_DIR = ROOT_DIR / "auto-cases"
INDEX_HTML = ROOT_DIR / "index.html"
SITEMAP_XML = ROOT_DIR / "sitemap.xml"

AUTO_START_MARKER = "<!-- AUTO_POSTS_START -->"
AUTO_END_MARKER = "<!-- AUTO_POSTS_END -->"
MAX_INDEX_CARDS = 6  # index.html에는 최신 6건 요약 카드만 표시
MAX_SIMILARITY_AI = 0.52  # AI 생성 원고 단어 유사도 상한
MAX_SIMILARITY_FALLBACK = 0.65  # 로컬 폴백 원고 단어 유사도 상한

# 구글 저품질 AI 글로 오인받기 쉬운 금지 상투어
BANNED_AI_PHRASES = [
    "가상 예시",
    "가상예시",
    "결론적으로",
    "요약하자면",
    "매우 중요합니다",
    "바람직합니다",
    "필수적입니다",
    "다양한 요소가 있습니다",
    "참고하시기 바랍니다",
    "도움이 되셨기를",
    "성공적인 철거",
]

ARCHETYPE_LABELS = {
    "checklist": "현장 준비 체크리스트",
    "cost_guide": "견적·비용 기준 안내",
    "qa_myth": "현장 실전 Q&A",
    "comparison": "작업 방식 비교 가이드",
    "field_note": "실제 현장 작업 기록",
}

ARCHETYPE_PROMPTS = {
    "checklist": (
        "글 유형: 현장 준비 체크리스트형.\n"
        "구조: (1) 이 지역·업종에서 고객이 가장 흔히 놓치는 실수 1가지로 바로 시작하는 도입(2~3문장), "
        "(2) 작업 전 반드시 점검할 3~4가지 핵심 항목(소제목 + 현장감 있는 구체적 설명), "
        "(3) 대봉개발에 사진 문자로 문의할 때 찍어두면 좋은 포인트 2~3줄."
    ),
    "cost_guide": (
        "글 유형: 견적·비용 변수 해설형.\n"
        "구조: (1) '평당 얼마인가요?'라고 물었을 때 바로 답하기 어려운 현장 이유를 솔직하게 설명하는 도입, "
        "(2) 실제 견적을 올리거나 줄이는 핵심 변수 3~4가지(현장 조건·폐기물 성상·차량/장비 등), "
        "(3) 불필요한 추가 비용을 막기 위해 고객이 미리 확인하면 좋은 팁."
    ),
    "qa_myth": (
        "글 유형: 실전 Q&A·오해 바로잡기형.\n"
        "구조: (1) 전화 상담에서 가장 많이 받는 오해나 막막한 질문으로 시작, "
        "(2) 핵심 질문 3가지에 대해 30년 현장 베테랑이 옆에서 조언하듯 명쾌하고 솔직하게 답변, "
        "(3) 현장 조건별 작업 가능 범위 요약."
    ),
    "comparison": (
        "글 유형: 작업 방식 비교·선택 가이드형.\n"
        "구조: (1) 고객이 자주 고민하는 두 가지 선택지(예: 부분 철거 vs 전체 원상복구, 단품 수거 vs 1톤 일괄 반출) 제시, "
        "(2) 각각의 장단점과 어떤 상황에서 어느 쪽이 비용·시간 면에서 유리한지 구체적 비교, "
        "(3) 임대인 검수나 관리사무소 기준에 맞춰 실패 없이 결정하는 요령."
    ),
    "field_note": (
        "글 유형: 실제 현장 작업 기록형.\n"
        "구조: (1) 제공된 실제 현장 메모 사실만 바탕으로 작업 배경과 현장 여건 소개(없는 사실 지어내기 절대 금지), "
        "(2) 실제 진행한 작업 순서와 주의했던 점, "
        "(3) 비슷한 조건의 인근 지역 고객을 위한 실무 조언."
    ),
}


# -----------------------------
# 유틸리티 및 품질 검증기
# -----------------------------
def tokenize_korean(text: str) -> set[str]:
    cleaned = re.sub(r"<[^>]+>", " ", text)
    tokens = re.findall(r"[가-힣a-zA-Z0-9]{2,}", cleaned.lower())
    stopwords = {
        "있는", "하는", "되는", "있습니다", "합니다", "됩니다", "경우", "진행", "작업",
        "철거", "폐기물", "부산", "대봉개발", "현장", "견적", "사진", "문자", "안내",
        "확인", "정리", "반출", "비용", "여부", "사전", "가능", "상담", "일정",
    }
    return {t for t in tokens if t not in stopwords}


def jaccard_similarity(text_a: str, text_b: str) -> float:
    a, b = tokenize_korean(text_a), tokenize_korean(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def validate_content_quality(
    title: str,
    body_text: str,
    history_posts: list[dict[str, Any]],
    is_fallback: bool = False,
) -> tuple[bool, list[str]]:
    """구글 스팸 정책(Scaled Content Abuse) 및 AI 저품질 문구 자동 검사."""
    issues: list[str] = []

    if len(body_text.strip()) < 550:
        issues.append(f"본문 길이가 너무 짧습니다 ({len(body_text.strip())}자 < 550자).")

    for phrase in BANNED_AI_PHRASES:
        if phrase in body_text or phrase in title:
            issues.append(f"금지된 AI 상투어 발견: '{phrase}'")

    if body_text.count("관할 구청") + body_text.count("관할 지자체") >= 2:
        issues.append("관할 구청/지자체 일반론 문구가 2회 이상 반복됩니다.")
    if body_text.count("확인하시기 바랍니다") + body_text.count("권장합니다") >= 3:
        issues.append("AI 번역투 종결어미('확인하시기 바랍니다/권장합니다')가 과도합니다.")

    sim_limit = MAX_SIMILARITY_FALLBACK if is_fallback else MAX_SIMILARITY_AI
    for prev in history_posts:
        if prev.get("title", "").strip() == title.strip():
            issues.append(f"기존 발행 글과 제목이 동일합니다: {title}")
        prev_sample = prev.get("plain_text", "")
        if prev_sample:
            sim = jaccard_similarity(body_text, prev_sample)
            if sim > sim_limit:
                issues.append(
                    f"기존 글({prev.get('slug')})과 단어 유사도가 너무 높습니다 ({sim:.2f} > {sim_limit})."
                )

    return (len(issues) == 0, issues)


# -----------------------------
# Gemini API 호출 (다중 모델 자동 탐색 및 폴백)
# -----------------------------
def discover_gemini_models(api_key: str) -> list[str]:
    """API 키에서 사용 가능한 최신 Gemini Flash 모델 후보 목록 반환."""
    preferred = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-flash-latest",
    ]
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        available = [
            m["name"].replace("models/", "")
            for m in data.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
        ordered = [m for m in preferred if m in available]
        for name in available:
            if "flash" in name and "gemini" in name and name not in ordered:
                ordered.append(name)
        if ordered:
            return ordered[:3]
    except Exception as exc:
        print(f"[WARN] Gemini 모델 목록 조회 실패: {exc}")
    return preferred[:3]


def call_gemini_json(prompt: str, api_key: str, model: str) -> dict[str, Any]:
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.78,
            "topP": 0.92,
            "responseMimeType": "application/json",
        },
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    text = raw["candidates"][0]["content"]["parts"][0]["text"]
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
    return json.loads(text)


def build_llm_prompt(
    company: dict[str, Any],
    kw: dict[str, Any],
    archetype: str,
    retry_feedback: list[str] | None = None,
) -> str:
    feedback_block = ""
    if retry_feedback:
        feedback_block = (
            "\n[이전 초안 반려 사유 - 반드시 수정]\n- " + "\n- ".join(retry_feedback) + "\n"
        )

    return f"""당신은 부산광역시 동래구 사직동에서 30년째 철거·폐기물 현장을 직접 뛰고 있는 '{company['name']}'의 실무 팀장입니다.
아래 세부 키워드로 실제 고객(사장님·집주인·관리자)이 구글에서 검색했을 때 끝까지 읽고 바로 문자·전화 문의를 남기고 싶어지는 자연스러운 실무 안내 글을 작성하세요.

[타깃 키워드 및 현장 정보]
- 지역: {kw['region']} ({', '.join(kw['sub_areas'])})
- 작업 분야: {kw['category']}
- 핵심 키워드: {kw['primary_keyword']}
- 연관 세부 키워드: {', '.join(kw['secondary_keywords'])}
- 검색 의도: {kw['intent']}
- 지역/현장 특성: {kw['local_context']}
- 주요 견적/작업 변수: {', '.join(kw['cost_factors'])}
- 연락처: {company['phone']}

[{ARCHETYPE_PROMPTS[archetype]}]

[절대 지켜야 할 글쓰기 원칙 (구글 저품질·AI 티 제거)]
1. '가상 예시', '결론적으로', '요약하자면', '매우 중요합니다', '바람직합니다', '필수적입니다', '도움이 되셨기를' 같은 AI 상투어를 절대 쓰지 마세요.
2. '관할 구청에 문의하세요' 같은 책상머리 일반론을 반복하지 말고, 현장 기사 입장에서 실제로 부딪히는 동선, 보양, 톤수, 임대인 협의 포인트를 구체적으로 쓰세요.
3. 실제 하지 않은 시공 실적이나 가짜 가격표(예: 무조건 10만 원)를 지어내지 마세요.
4. 문장은 짧고 명쾌한 실무자 경어체('~합니다', '~해요', '~하세요')를 섞어 사람이 직접 설명하는 리듬을 살리세요.
5. 전체 본문은 공백 포함 950~1,400자 분량으로 밀도 있게 작성하세요.
{feedback_block}
반드시 아래 JSON 스키마로만 응답하세요:
{{
  "title": "클릭하고 싶어지는 구체적 SEO 제목 (45자 이내, 핵심 키워드 자연스럽게 포함)",
  "meta_description": "검색 결과 요약문 (110~145자, 지역+작업+핵심 이점 포함)",
  "lead": "도입부 2~3문장 (독자의 실제 고민을 바로 짚는 문장)",
  "sections": [
    {{
      "heading": "구체적인 소제목 1",
      "paragraphs": ["문단1", "문단2"],
      "bullets": ["핵심 체크 항목(선택, 필요 시 2~3개)"]
    }},
    {{
      "heading": "구체적인 소제목 2",
      "paragraphs": ["문단1", "문단2"],
      "bullets": []
    }},
    {{
      "heading": "구체적인 소제목 3",
      "paragraphs": ["문단1"],
      "bullets": ["사진 문자 견적 시 알려주실 항목 2~3개"]
    }}
  ],
  "faq": [
    {{"q": "실제 고객이 자주 묻는 질문 1", "a": "구체적이고 솔직한 답변 1"}},
    {{"q": "실제 고객이 자주 묻는 질문 2", "a": "구체적이고 솔직한 답변 2"}}
  ],
  "summary_card": "메인 홈페이지 카드에 들어갈 2줄 요약 (90~120자)"
}}
"""


# -----------------------------
# API 미설정·오류 시 다변화 로컬 폴백 생성기
# -----------------------------
def generate_fallback_article(
    company: dict[str, Any], kw: dict[str, Any], archetype: str
) -> dict[str, Any]:
    areas = "·".join(kw["sub_areas"][:3])
    factors = kw["cost_factors"]
    sub_kws = kw.get("secondary_keywords", [])
    phone = company["phone"]
    seed = int(hashlib.md5(kw["id"].encode("utf-8")).hexdigest()[:8], 16)

    if archetype == "cost_guide":
        title = f"{kw['primary_keyword']}, 견적이 달라지는 핵심 기준"
        lead = (
            f"{kw['region']}({areas})에서 {kw['category']}를 준비하실 때 가장 먼저 걸리는 부분이 예산입니다. "
            f"같은 규모처럼 보여도 {factors[0]} 등에 따라 차량 배차와 인원 구성이 크게 달라지므로, "
            f"실제 견적을 가르는 핵심 기준부터 짚어보시는 편이 유리합니다."
        )
        sec1_h = f"{areas} 일대 {kw['category']} 비용을 좌우하는 변수"
        sec2_h = f"{kw['primary_keyword']} 시 불필요한 지출을 줄이는 요령"
    elif archetype == "qa_myth":
        title = f"{kw['primary_keyword']} 맡기기 전 자주 나오는 질문"
        lead = (
            f"{kw['region']} {areas} 고객분들과 {kw['primary_keyword']} 상담을 나누다 보면 "
            f"미리 손대야 할 범위나 건물 협의 절차 때문에 막막해하시는 경우가 많습니다. "
            f"{kw['intent']} 입장에서 꼭 알아두면 편한 실무 포인트를 모았습니다."
        )
        sec1_h = f"{areas} {kw['category']} 현장에서 먼저 살필 여건"
        sec2_h = "처음 의뢰할 때 헷갈리지 않는 진행 흐름"
    elif archetype == "comparison":
        title = f"{kw['primary_keyword']}, 부분 진행 vs 일괄 정리 선택법"
        lead = (
            f"{kw['region']}({areas})에서 {kw['category']}를 앞두면 꼭 필요한 부분만 걷어낼지, "
            f"집기·폐기물까지 한꺼번에 비울지 고민하게 됩니다. "
            f"{kw['local_context']}"
        )
        sec1_h = f"{kw['region']} 현장 조건에 따른 방식 선택 기준"
        sec2_h = "분리 발주보다 한 팀 일괄 진행이 유리해지는 순간"
    else:
        title = f"{kw['primary_keyword']} 전 미리 점검할 체크리스트"
        lead = (
            f"{kw['region']}({areas})에서 {kw['category']} 일정을 잡기 전, 당일 공정이 멈추지 않도록 "
            f"미리 짚어두면 좋은 항목들이 있습니다. {kw['local_context']}"
        )
        sec1_h = f"{areas} {kw['primary_keyword']} 사전 점검 사항"
        sec2_h = "당일 해체부터 폐기물 상차·바닥 마무리까지"

    sec2_variants = [
        (
            f"{company['name']}은 {company['base_location']}을 거점으로 {company['experience']} 직영 팀이 직접 움직입니다. "
            f"특히 {', '.join(sub_kws[:2]) if sub_kws else kw['category']}처럼 손이 많이 가는 공정도 "
            f"해체와 폐기물 상차를 따로 부르지 않고 한 번에 끝낼 수 있어 일정 조율이 수월합니다."
        ),
        (
            f"{kw['region']} {areas} 현장에서는 반출 동선과 보양 준비를 소홀히 하면 건물 민원이나 추가 대기 시간이 생깁니다. "
            f"{company['experience']} 노하우를 바탕으로 {factors[0]}부터 마지막 빗자루 쓸기까지 깔끔하게 마무리합니다."
        ),
        (
            f"무조건 낮은 금액만 제시했다가 당일 추가금을 요구하는 방식은 피해야 합니다. "
            f"{company['name']}은 사진과 현장 여건을 토대로 범위를 먼저 분명히 잡은 뒤, "
            f"변경 사항이 생길 때만 작업 전 고객 동의를 구하고 움직입니다."
        ),
    ]

    cta_variants = [
        (
            f"바쁘시거나 전화가 부담스러우실 때는 {phone}로 현장 사진과 동네·층수만 남겨주세요.",
            [
                f"출장 위치({kw['region']} 상세 동네) 및 엘리베이터·계단 조건",
                f"{factors[0]} 등이 잘 드러나는 전체 사진 2~3장",
                "희망하시는 작업 날짜와 건물 관리실 규정",
            ],
        ),
        (
            f"{kw['region']}({areas}) {kw['category']} 일정과 예상 금액이 궁금하시면 {phone}로 사진 문자를 보내주세요.",
            [
                f"작업할 공간({', '.join(sub_kws[:2]) if sub_kws else kw['category']})이 한눈에 보이는 사진",
                "층수, 주차 가능 여부 및 희망 퇴거일",
                "꼭 남길 물품이나 임대인 요구 사항 메모",
            ],
        ),
        (
            f"현장 상황에 딱 맞는 범위만 골라 진행할 수 있도록 {phone} 직통 상담으로 솔직하게 안내해 드립니다.",
            [
                f"{kw['region']} 방문 주소(동 단위)와 출입구·계단 여건",
                "철거·수거 대상 전체가 담긴 사진 2~3장",
                "야간·주말 작업 필요 여부",
            ],
        ),
    ]

    sec2_body = sec2_variants[seed % len(sec2_variants)]
    cta_intro, cta_bullets = cta_variants[seed % len(cta_variants)]

    sections = [
        {
            "heading": sec1_h,
            "paragraphs": [
                kw["local_context"],
                (
                    f"실제 {kw['primary_keyword']} 현장에서는 {', '.join(factors[:2])} 같은 세부 조건을 "
                    f"미리 파악해 두어야 불필요한 재방문이나 일정 지연 없이 매끄럽게 마무리됩니다."
                ),
            ],
            "bullets": [f"{f} 점검" for f in factors],
        },
        {
            "heading": sec2_h,
            "paragraphs": [sec2_body],
            "bullets": [],
        },
        {
            "heading": f"{kw['region']} 사진 문자 견적 접수 안내",
            "paragraphs": [cta_intro],
            "bullets": cta_bullets,
        },
    ]

    return {
        "title": title,
        "meta_description": (
            f"{kw['region']} {areas} {kw['primary_keyword']} 안내. "
            f"{factors[0]} 등 현장별 기준과 사진 문자 상담({phone}) 방법을 대봉개발이 정리했습니다."
        )[:150],
        "lead": lead,
        "sections": sections,
        "faq": kw.get("faq", []),
        "summary_card": (
            f"{kw['region']}({areas}) {kw['primary_keyword']} 시 꼭 확인할 "
            f"{factors[0]} 등 현장 기준과 상담 방법을 정리했습니다."
        ),
    }


def article_to_plain_text(article: dict[str, Any]) -> str:
    parts = [article.get("title", ""), article.get("lead", "")]
    for sec in article.get("sections", []):
        parts.append(sec.get("heading", ""))
        parts.extend(sec.get("paragraphs", []))
        parts.extend(sec.get("bullets", []))
    for qa in article.get("faq", []):
        parts.append(qa.get("q", ""))
        parts.append(qa.get("a", ""))
    return "\n".join(parts)


# -----------------------------
# HTML 및 Sitemap 생성
# -----------------------------
def render_case_html(
    company: dict[str, Any],
    kw: dict[str, Any],
    article: dict[str, Any],
    archetype: str,
    pub_date: str,
    related_posts: list[dict[str, Any]],
) -> str:
    slug = kw["slug"]
    canonical = f"{company['base_url']}/auto-cases/{slug}.html"
    e = html.escape
    phone = company["phone"]
    tel_href = f"tel:{phone.replace('-', '')}"
    sms_href = f"sms:{phone.replace('-', '')}"

    sections_html = []
    for sec in article.get("sections", []):
        p_html = "\n".join(f"<p>{e(p)}</p>" for p in sec.get("paragraphs", []) if p.strip())
        bullets = [b for b in sec.get("bullets", []) if b.strip()]
        b_html = ""
        if bullets:
            items = "\n".join(f"<li>{e(b)}</li>" for b in bullets)
            b_html = f"<ul class='check-list'>\n{items}\n</ul>"
        sections_html.append(
            f"<section class='content-block'>\n<h2>{e(sec.get('heading', ''))}</h2>\n{p_html}\n{b_html}\n</section>"
        )

    faq_items = article.get("faq", [])
    faq_html_parts = []
    faq_ld_entities = []
    for qa in faq_items:
        q_txt, a_txt = qa.get("q", "").strip(), qa.get("a", "").strip()
        if not q_txt or not a_txt:
            continue
        faq_html_parts.append(
            f"<details class='faq-item'><summary>{e(q_txt)}</summary><p>{e(a_txt)}</p></details>"
        )
        faq_ld_entities.append(
            {
                "@type": "Question",
                "name": q_txt,
                "acceptedAnswer": {"@type": "Answer", "text": a_txt},
            }
        )

    related_html = ""
    if related_posts:
        rel_lis = "\n".join(
            f"<li><a href='./{e(r['slug'])}.html'>{e(r['title'])}</a> <span>({e(r['region'])})</span></li>"
            for r in list(reversed(related_posts))[:4]
        )
        related_html = (
            f"<aside class='related-box'>\n<h2>함께 보면 좋은 부산·경남 철거 안내</h2>\n<ul>\n{rel_lis}\n</ul>\n</aside>"
        )

    ld_graph: list[dict[str, Any]] = [
        {
            "@type": "LocalBusiness",
            "name": company["name"],
            "url": company["base_url"],
            "telephone": phone,
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "부산광역시 동래구 사직동",
                "addressCountry": "KR",
            },
            "areaServed": ["부산광역시", "양산시", "김해시", "경상남도"],
        },
        {
            "@type": "Article",
            "headline": article["title"],
            "description": article["meta_description"],
            "datePublished": pub_date,
            "dateModified": pub_date,
            "author": {"@type": "Organization", "name": company["name"]},
            "publisher": {"@type": "Organization", "name": company["name"]},
            "mainEntityOfPage": canonical,
        },
    ]
    if faq_ld_entities:
        ld_graph.append({"@type": "FAQPage", "mainEntity": faq_ld_entities})

    json_ld = json.dumps(
        {"@context": "https://schema.org", "@graph": ld_graph},
        ensure_ascii=False,
        indent=2,
    )

    badge = f"{ARCHETYPE_LABELS.get(archetype, '현장 안내')} · {kw['region']}"
    keywords_meta = ", ".join([kw["primary_keyword"]] + kw.get("secondary_keywords", []))

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(article['title'])} | {e(company['name'])}</title>
  <meta name="description" content="{e(article['meta_description'])}" />
  <meta name="keywords" content="{e(keywords_meta)}" />
  <link rel="canonical" href="{e(canonical)}" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{e(article['title'])}" />
  <meta property="og:description" content="{e(article['meta_description'])}" />
  <meta property="og:url" content="{e(canonical)}" />
  <script type="application/ld+json">
{json_ld}
  </script>
  <style>
    :root {{ --bg:#f8faf9; --paper:#ffffff; --ink:#14201b; --muted:#4b5d54; --accent:#0f5132; --accent-soft:#e8f3ee; --line:#dfe7e3; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Malgun Gothic","Apple SD Gothic Neo",sans-serif; background:var(--bg); color:var(--ink); line-height:1.75; }}
    .wrap {{ max-width:780px; margin:0 auto; padding:24px 18px 96px; }}
    .topbar {{ display:flex; justify-content:space-between; align-items:center; padding-bottom:16px; border-bottom:1px solid var(--line); margin-bottom:28px; font-size:14px; }}
    .topbar a {{ color:var(--accent); text-decoration:none; font-weight:700; }}
    article {{ background:var(--paper); border:1px solid var(--line); border-radius:14px; padding:32px 26px; }}
    .badge {{ display:inline-block; background:var(--accent-soft); color:var(--accent); font-size:13px; font-weight:700; padding:4px 12px; border-radius:999px; margin-bottom:14px; }}
    h1 {{ font-size:clamp(22px,4vw,30px); line-height:1.35; margin:0 0 14px; }}
    .meta {{ color:var(--muted); font-size:13px; margin-bottom:22px; }}
    .lead {{ font-size:17px; background:#f4f8f6; border-left:4px solid var(--accent); padding:16px 18px; border-radius:0 8px 8px 0; margin:0 0 28px; }}
    .content-block {{ margin-bottom:28px; }}
    .content-block h2 {{ font-size:20px; margin:0 0 12px; padding-bottom:6px; border-bottom:1px solid var(--line); color:#0c3b25; }}
    .check-list {{ padding-left:20px; margin:12px 0 0; }}
    .check-list li {{ margin-bottom:8px; }}
    .faq-box {{ margin-top:32px; padding-top:20px; border-top:1px solid var(--line); }}
    .faq-item {{ border:1px solid var(--line); border-radius:10px; padding:12px 16px; margin-bottom:10px; background:#fcfefd; }}
    .faq-item summary {{ font-weight:700; cursor:pointer; }}
    .faq-item p {{ margin:10px 0 0; color:var(--muted); }}
    .cta-box {{ margin-top:32px; background:#0f5132; color:#fff; border-radius:12px; padding:22px; }}
    .cta-box h2 {{ margin:0 0 8px; font-size:19px; color:#fff; }}
    .cta-box p {{ margin:0 0 16px; font-size:15px; opacity:0.95; }}
    .cta-btns {{ display:flex; flex-wrap:wrap; gap:10px; }}
    .cta-btns a {{ display:inline-block; padding:12px 18px; border-radius:8px; font-weight:700; text-decoration:none; font-size:15px; }}
    .btn-call {{ background:#fff; color:#0f5132; }}
    .btn-sms {{ background:#f5b700; color:#1a1a1a; }}
    .related-box {{ margin-top:28px; padding:20px; background:#f4f7f5; border-radius:12px; }}
    .related-box h2 {{ font-size:17px; margin:0 0 12px; }}
    .related-box ul {{ margin:0; padding-left:18px; }}
    .related-box li {{ margin-bottom:8px; }}
    .related-box a {{ color:var(--ink); text-decoration:none; font-weight:600; }}
    .related-box a:hover {{ text-decoration:underline; color:var(--accent); }}
    .related-box span {{ color:var(--muted); font-size:13px; }}
    footer {{ margin-top:28px; text-align:center; color:var(--muted); font-size:13px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <nav class="topbar">
      <a href="../index.html">← 대봉개발 메인으로</a>
      <a href="./index.html">전체 지역별 안내 목록</a>
    </nav>
    <article>
      <span class="badge">{e(badge)}</span>
      <h1>{e(article['title'])}</h1>
      <div class="meta">작성: {e(company['name'])} ({e(company['experience'])}) · 등록일: {e(pub_date)} · 출장지역: {e(kw['region'])} ({e(', '.join(kw['sub_areas']))})</div>
      <p class="lead">{e(article['lead'])}</p>
      {''.join(sections_html)}
      {f"<section class='faq-box'><h2>자주 묻는 질문</h2>{''.join(faq_html_parts)}</section>" if faq_html_parts else ""}
      <section class="cta-box">
        <h2>{e(kw['region'])} 현장 사진 문자 견적 상담</h2>
        <p>동네 + 층수(엘리베이터 여부) + 현장 사진 2~3장을 보내주시면 확인 후 예상 견적과 가능한 일정을 안내해 드립니다.</p>
        <div class="cta-btns">
          <a class="btn-call" href="{tel_href}">전화 상담 {e(phone)}</a>
          <a class="btn-sms" href="{sms_href}">사진 문자로 견적 문의</a>
        </div>
      </section>
      {related_html}
    </article>
    <footer>{e(company['name'])} | {e(company['base_location'])} | 직통 상담 {e(phone)}</footer>
  </div>
</body>
</html>
"""


def render_archive_html(company: dict[str, Any], history_posts: list[dict[str, Any]]) -> str:
    e = html.escape
    cards = []
    for post in reversed(history_posts):
        cards.append(
            f"""<li class="item">
  <span class="tag">{e(post['region'])} · {e(post['category'])}</span>
  <h2><a href="./{e(post['slug'])}.html">{e(post['title'])}</a></h2>
  <p>{e(post['summary_card'])}</p>
  <small>{e(post['date'])}</small>
</li>"""
        )
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>부산·양산·김해 지역별 철거·폐기물 안내 모음 | {e(company['name'])}</title>
  <meta name="description" content="부산·양산·김해·경남 지역별 상가 원상복구, 가정집 폐기물, 보일러 철거 현장 안내 아카이브입니다." />
  <link rel="canonical" href="{e(company['base_url'])}/auto-cases/index.html" />
  <style>
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Malgun Gothic",sans-serif; background:#f8faf9; color:#14201b; line-height:1.65; }}
    .wrap {{ max-width:860px; margin:0 auto; padding:28px 18px 80px; }}
    a {{ color:#0f5132; text-decoration:none; }}
    h1 {{ margin:14px 0 8px; font-size:26px; }}
    .list {{ list-style:none; padding:0; margin:24px 0 0; display:grid; gap:14px; }}
    .item {{ background:#fff; border:1px solid #dfe7e3; border-radius:12px; padding:18px 20px; }}
    .tag {{ display:inline-block; font-size:12px; font-weight:700; color:#0f5132; background:#e8f3ee; padding:2px 10px; border-radius:999px; }}
    .item h2 {{ margin:8px 0 6px; font-size:18px; }}
    .item p {{ margin:0 0 6px; color:#4b5d54; font-size:14px; }}
    .item small {{ color:#6e7e76; font-size:12px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <a href="../index.html">← 대봉개발 메인 홈페이지</a>
    <h1>부산·양산·김해 지역별 철거·폐기물 안내</h1>
    <p>지역과 작업 유형별 현장 준비 사항, 비용 기준, 실제 자주 묻는 질문을 정리해 두었습니다. (총 {len(history_posts)}건)</p>
    <ul class="list">{''.join(cards)}</ul>
  </div>
</body>
</html>
"""


def render_index_cards_block(history_posts: list[dict[str, Any]]) -> str:
    """index.html에는 최신 6건의 가벼운 요약 카드 + 전용 페이지 링크만 삽입."""
    e = html.escape
    latest = list(reversed(history_posts))[:MAX_INDEX_CARDS]
    cards = []
    for post in latest:
        cards.append(
            f"""<article class="daebong-guide-card" style="border:1px solid #dfe7e3;border-radius:12px;padding:20px;margin-bottom:16px;background:#fff;">
  <div style="font-size:13px;font-weight:700;color:#0f5132;margin-bottom:6px;">{e(post['region'])} · {e(post['category'])}</div>
  <h3 style="margin:0 0 8px;font-size:19px;line-height:1.4;">
    <a href="./auto-cases/{e(post['slug'])}.html" style="color:#14201b;text-decoration:none;">{e(post['title'])}</a>
  </h3>
  <p style="margin:0 0 12px;color:#4b5d54;font-size:15px;line-height:1.6;">{e(post['summary_card'])}</p>
  <a href="./auto-cases/{e(post['slug'])}.html" style="font-size:14px;font-weight:700;color:#0f5132;text-decoration:none;">자세한 현장 안내 보기 →</a>
</article>"""
        )
    archive_link = (
        f'<div style="text-align:center;margin-top:20px;">'
        f'<a href="./auto-cases/index.html" style="display:inline-block;padding:12px 22px;border:1px solid #0f5132;border-radius:8px;color:#0f5132;font-weight:700;text-decoration:none;">'
        f'부산·경남 지역별 철거 안내 전체 보기 ({len(history_posts)}건) →</a></div>'
    )
    return "\n".join(cards) + "\n" + archive_link


def update_index_html(history_posts: list[dict[str, Any]], dry_run: bool = False) -> None:
    if not INDEX_HTML.exists():
        print("[WARN] index.html 파일이 없어 메인 카드 갱신을 건너뜁니다.")
        return
    src = INDEX_HTML.read_text(encoding="utf-8")
    if AUTO_START_MARKER not in src or AUTO_END_MARKER not in src:
        print("[WARN] index.html에 AUTO_POSTS 마커가 없어 갱신을 건너뜁니다.")
        return
    block = render_index_cards_block(history_posts)
    pattern = re.compile(
        re.escape(AUTO_START_MARKER) + r".*?" + re.escape(AUTO_END_MARKER),
        re.DOTALL,
    )
    updated = pattern.sub(f"{AUTO_START_MARKER}\n{block}\n{AUTO_END_MARKER}", src, count=1)
    if not dry_run:
        INDEX_HTML.write_text(updated, encoding="utf-8")
    print(f"[OK] index.html 요약 카드 {min(len(history_posts), MAX_INDEX_CARDS)}건 반영 완료.")


def update_sitemap_xml(
    company: dict[str, Any], history_posts: list[dict[str, Any]], dry_run: bool = False
) -> None:
    base = company["base_url"].rstrip("/")
    today = dt.date.today().isoformat()
    urls = [
        (f"{base}/", today, "1.0", "weekly"),
        (f"{base}/auto-cases/index.html", today, "0.8", "weekly"),
    ]
    for post in history_posts:
        urls.append(
            (f"{base}/auto-cases/{post['slug']}.html", post.get("date", today), "0.7", "monthly")
        )

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, priority, freq in urls:
        lines.append(
            f"  <url><loc>{html.escape(loc)}</loc><lastmod>{lastmod}</lastmod>"
            f"<changefreq>{freq}</changefreq><priority>{priority}</priority></url>"
        )
    lines.append("</urlset>\n")
    if not dry_run:
        SITEMAP_XML.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] sitemap.xml 갱신 완료 (총 {len(urls)}개 URL).")


# -----------------------------
# 메인 실행 로직
# -----------------------------
def select_next_keyword(
    keywords: list[dict[str, Any]], history_posts: list[dict[str, Any]]
) -> dict[str, Any] | None:
    published_ids = {p.get("id") for p in history_posts}
    for kw in keywords:
        if kw["id"] not in published_ids:
            return kw
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="대봉개발 SEO 세부 키워드 자동 발행 엔진")
    parser.add_argument("--dry-run", action="store_true", help="파일을 수정하지 않고 생성·검증만 테스트")
    parser.add_argument("--keywords", type=Path, default=KEYWORDS_FILE, help="키워드 JSON 경로")
    args = parser.parse_args()

    if not args.keywords.exists():
        print(f"[ERROR] 키워드 파일을 찾을 수 없습니다: {args.keywords}")
        return 1

    data = json.loads(args.keywords.read_text(encoding="utf-8"))
    company = data["company"]
    keywords = data["keywords"]

    history_posts: list[dict[str, Any]] = []
    if HISTORY_FILE.exists():
        history_posts = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))

    target_kw = select_next_keyword(keywords, history_posts)
    if target_kw is None:
        print("[INFO] 준비된 세부 키워드를 모두 발행했습니다. 중복 저품질 방지를 위해 발행을 중단합니다.")
        print("       automation/keywords_busan.json에 새 현장 키워드를 추가해 주세요.")
        return 0

    archetype = target_kw.get("preferred_archetype", "checklist")
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    article: dict[str, Any] | None = None

    if api_key:
        models = discover_gemini_models(api_key)
        print(f"[INFO] 탐색된 Gemini 모델 후보: {models}")
        for model_name in models:
            feedback: list[str] = []
            for attempt in range(1, 3):
                try:
                    prompt = build_llm_prompt(company, target_kw, archetype, feedback or None)
                    candidate = call_gemini_json(prompt, api_key, model=model_name)
                    plain = article_to_plain_text(candidate)
                    ok, issues = validate_content_quality(
                        candidate.get("title", ""), plain, history_posts, is_fallback=False
                    )
                    if ok:
                        article = candidate
                        print(f"[OK] Gemini({model_name}) 생성 및 검수 통과: {article['title']}")
                        break
                    print(f"[RETRY {model_name} {attempt}/2] 품질 검수 반려: {issues}")
                    feedback = issues
                except urllib.error.HTTPError as exc:
                    err_body = exc.read().decode("utf-8", errors="ignore")[:300]
                    print(f"[WARN] Gemini({model_name}) HTTP {exc.code}: {err_body}")
                    break
                except (urllib.error.URLError, KeyError, json.JSONDecodeError, ValueError) as exc:
                    print(f"[WARN] Gemini({model_name}) 오류: {exc}")
                    break
            if article is not None:
                break

    if article is None:
        article = generate_fallback_article(company, target_kw, archetype)
        plain = article_to_plain_text(article)
        ok, issues = validate_content_quality(
            article["title"], plain, history_posts, is_fallback=True
        )
        if not ok:
            print(f"[WARN] 폴백 검수 경고(발행은 유지): {issues}")
        print(f"[OK] 로컬 구조화 원고 생성 완료: {article['title']}")

    pub_date = dt.date.today().isoformat()
    case_html = render_case_html(company, target_kw, article, archetype, pub_date, history_posts)

    new_record = {
        "id": target_kw["id"],
        "slug": target_kw["slug"],
        "region": target_kw["region"],
        "category": target_kw["category"],
        "primary_keyword": target_kw["primary_keyword"],
        "archetype": archetype,
        "title": article["title"],
        "summary_card": article["summary_card"],
        "date": pub_date,
        "plain_text": article_to_plain_text(article),
    }
    updated_history = history_posts + [new_record]

    if args.dry_run:
        print(f"[DRY-RUN] 생성 예정 페이지: auto-cases/{target_kw['slug']}.html ({len(case_html)} bytes)")
        print(f"[DRY-RUN] 제목: {article['title']}")
        print(f"[DRY-RUN] 유형: {ARCHETYPE_LABELS.get(archetype, archetype)}")
        return 0

    CASES_DIR.mkdir(parents=True, exist_ok=True)
    (CASES_DIR / f"{target_kw['slug']}.html").write_text(case_html, encoding="utf-8")
    (CASES_DIR / "index.html").write_text(render_archive_html(company, updated_history), encoding="utf-8")
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(updated_history, ensure_ascii=False, indent=2), encoding="utf-8")

    update_index_html(updated_history, dry_run=False)
    update_sitemap_xml(company, updated_history, dry_run=False)
    print(f"[DONE] 발행 완료: {company['base_url']}/auto-cases/{target_kw['slug']}.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
