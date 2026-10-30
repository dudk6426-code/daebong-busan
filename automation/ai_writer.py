import os, sys, json, urllib.request, urllib.error, re, html, difflib, datetime, pathlib, hashlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
TOPICS = ["상가 철거 견적 전 확인사항", "식당 주방 철거 준비", "사무실 원상복구 범위 확인", "폐기물 분류와 반출 동선", "창고 정리 전 준비사항", "부분 철거 전 주변 시설 보호", "엘리베이터 없는 건물 폐기물 반출", "카페 폐업 정리 체크리스트", "철거 현장 사진으로 견적 문의하기", "가벽 철거 전 확인사항", "폐기물 양과 작업 범위 정리", "철거 일정과 건물 관리규정 확인", "매장 집기와 철거 대상 구분", "작업 전 전기 가스 수도 확인", "공사 후 정리 범위 확인"]
SYSTEM = """한국의 철거 및 폐기물 정리 정보를 독자에게 설명하는 작가다.
사실로 확인되지 않은 현장 완료, 고객 후기, 가격, 경력, 허가, 자격, 실적을 절대 지어내지 마라.
가상의 현장은 반드시 '가상 예시'라고 표시한다. 법률·폐기물 처리 기준을 단정하지 말고 관할 기관이나 허가업체에 확인하라고 안내한다.
석면, 가스, 전기 등 위험 작업의 직접 시공 절차를 제공하지 말고 전문가 상담을 권한다.
키워드 반복이나 과장광고를 피하고 한국어로 유용하게 작성한다. 연락처와 상호를 지어내지 않는다."""
def ask(prompt):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key: raise RuntimeError("GEMINI_API_KEY가 없습니다. 설치 안내를 확인하세요.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", MODEL):
        raise RuntimeError("모델 이름이 올바르지 않습니다.")
    body = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 4096}
    }, ensure_ascii=False).encode("utf-8")
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"
    req = urllib.request.Request(url, data=body, headers={"x-goog-api-key": key, "Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp: data=json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError("구글 API 요청 실패 (HTTP %s). 키, 무료 사용 한도와 모델 접근 권한을 확인하세요." % e.code)
    except urllib.error.URLError:
        raise RuntimeError("구글 API에 연결할 수 없습니다. 인터넷 연결을 확인하세요.")
    candidates=data.get("candidates", [])
    if not candidates or candidates[0].get("finishReason") != "STOP":
        raise RuntimeError("AI 응답이 차단되었거나 완료되지 않아 중단했습니다.")
    text="".join(part.get("text", "") for part in candidates[0].get("content", {}).get("parts", []) if not part.get("thought")).strip()
    if len(text)<100: raise RuntimeError("AI 응답이 너무 짧습니다. 재시도하세요.")
    return text
def readmemo(path):
    b=path.read_bytes()
    for enc in ('utf-8-sig','cp949'):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    raise RuntimeError("메모 파일을 UTF-8로 저장해 주세요.")
def blog():
    memo=ROOT/"automation"/"memo.txt"
    if not memo.exists():
        memo.write_text("제목 또는 키워드: \n현장 정보(실제 사실만): \n",encoding="utf-8-sig")
        raise RuntimeError("automation/memo.txt에 제목과 내용을 먼저 입력하고 다시 실행하세요.")
    text=readmemo(memo).strip()
    if len(text)<20 or text=="제목 또는 키워드: \n현장 정보(실제 사실만):": raise RuntimeError("memo.txt에 제목과 내용을 먼저 입력하세요.")
    result=ask("네이버 블로그 원고를 작성해라. 첫 줄에 제목, 이후 본문. 다음 메모에 포함된 사실만 실제 현장으로 표현하고, 정보가 없으면 정보성 글로 작성하라. 확인이 필요한 내용은 [확인 필요]로 표시하라.\n\n메모:\n"+text[:6000])
    out=ROOT/"automation"/"output"; out.mkdir(exist_ok=True)
    filename=out/"blog_draft.txt"
    filename.write_text(result+"\n",encoding="utf-8-sig")
    print("블로그 초안 생성:",filename)
def website():
    path=ROOT/"index.html"; source=path.read_text(encoding="utf-8")
    start="<!-- AUTO_POSTS_START -->"; end="<!-- AUTO_POSTS_END -->"
    if source.count(start)!=1 or source.count(end)!=1 or source.index(start)>source.index(end):
        raise RuntimeError("게시판 표시 위치를 정확히 찾지 못해 중단했습니다.")
    today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()
    marker="ai-info-"+today.isoformat()
    if marker in source: print("오늘 글이 이미 있습니다."); return
    topic=TOPICS[today.toordinal()%len(TOPICS)]
    statepath=ROOT/"automation"/"ai_post_history.json"
    history=json.loads(statepath.read_text(encoding="utf-8")) if statepath.exists() else []
    prompt=f"""주제: {topic}
홈페이지용 정보 글을 작성하라. 실제 현장 사례는 절대 만들지 말 것. 특정 법령, 금액, 업체의 자격이나 실적을 단정하지 말 것.
JSON 객체만 반환: {{"title":"제목", "paragraphs":["문단1","문단2","문단3","문단4"]}}
각 문단은 독자에게 구체적인 확인 질문이나 준비 정보를 제공한다. 마크다운과 HTML을 사용하지 않는다."""
    result=ask(prompt)
    result=re.sub(r"^```(?:json)?\s*|\s*```$","",result.strip())
    try: obj=json.loads(result); title=obj["title"]; paragraphs=obj["paragraphs"]
    except (ValueError,KeyError,TypeError): raise RuntimeError("AI 응답 형식 오류로 발행하지 않았습니다.")
    if not isinstance(title,str) or not 5<=len(title)<=120 or not isinstance(paragraphs,list) or not 3<=len(paragraphs)<=8 or any(not isinstance(x,str) or not 20<=len(x)<=1000 for x in paragraphs):
        raise RuntimeError("글 형식 검증 실패로 발행하지 않았습니다.")
    combined=title+" "+" ".join(paragraphs)
    if len(combined)<300: raise RuntimeError("글이 너무 짧아 발행하지 않았습니다.")
    for old in history[-30:]:
        if difflib.SequenceMatcher(None,combined,old.get("text","")).ratio()>.72:
            raise RuntimeError("최근 생성 글과 유사하여 발행하지 않았습니다.")
    escape=html.escape
    article='\n<article class="auto-post" data-case-id="'+marker+'">\n<span class="tag">철거·폐기물 정보 안내</span>\n<h3>'+escape(title)+'</h3>\n'
    article+=''.join('<p>'+escape(q).replace('\n','<br/>')+'</p>\n' for q in paragraphs)
    article+='<p>현장 여건에 따라 작업 범위와 비용은 달라질 수 있습니다. 상담: <a href="tel:01085359787">010-8535-9787</a></p>\n</article>\n'
    updated=source.replace(start,start+article,1)
    # Preserve the rest of the page including the existing show-more script.
    path.write_text(updated,encoding="utf-8")
    history.append({"date":str(today),"topic":topic,"title":title,"text":combined})
    statepath.write_text(json.dumps(history[-90:],ensure_ascii=False,indent=2),encoding="utf-8")
    print("홈페이지 글 생성:", title)
if __name__=="__main__":
    try:
        if len(sys.argv)!=2 or sys.argv[1] not in ("blog","website"): raise RuntimeError("사용법: python ai_writer.py blog 또는 website")
        blog() if sys.argv[1]=="blog" else website()
    except Exception as exc:
        print("오류:",exc,file=sys.stderr); sys.exit(1)
