# -*- coding: utf-8 -*-
import datetime, hashlib, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def create_favicons():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">\n'
        '  <rect width="92" height="92" x="4" y="4" rx="18" fill="#ffffff" stroke="#1d4ed8" stroke-width="6"/>\n'
        '  <text x="50" y="64" font-family="Malgun Gothic, sans-serif" font-size="38" font-weight="900" fill="#1d4ed8" text-anchor="middle">대봉</text>\n'
        '</svg>\n'
    )
    (ROOT / 'favicon.svg').write_text(svg, encoding='utf-8')
    c1, c2 = ord('대'), ord('봉')
    png_p = str(ROOT / 'favicon.png')
    ico_p = str(ROOT / 'favicon.ico')
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
    $txt = [string][char]{c1} + [string][char]{c2}
    $g.DrawString($txt, $f, $br, $rect, $sf)
    $b.Save('{png_p}', [System.Drawing.Imaging.ImageFormat]::Png)
    $b64 = New-Object System.Drawing.Bitmap($b, 64, 64)
    $b64.Save('{ico_p}', [System.Drawing.Imaging.ImageFormat]::Icon)
    $g.Dispose(); $b.Dispose(); $b64.Dispose()
    """
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], check=False)
    print("✓ [1/3] 파란색 '대봉' 파비콘 생성 완료")

def patch_html():
    fav_tags = (
        '<!-- DAEBONG_FAV_START -->\n'
        '<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=5"/>\n'
        '<link rel="icon" type="image/png" sizes="192x192" href="/favicon.png?v=5"/>\n'
        '<link rel="shortcut icon" href="/favicon.ico?v=5"/>\n'
        '<link rel="apple-touch-icon" href="/favicon.png?v=5"/>\n'
        '<!-- DAEBONG_FAV_END -->'
    )
    ui_code = """<!-- DAEBONG_UI_START -->
<style>
.db-hidden-case { display: none !important; }
.db-more-bar {
  grid-column: 1 / -1; width: 100%; margin: 22px 0 12px; padding: 20px;
  background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 14px;
  text-align: center; display: flex; flex-wrap: wrap; justify-content: center; gap: 12px;
}
.db-btn-archive {
  background: #1d4ed8; color: #ffffff !important; padding: 13px 26px;
  border-radius: 999px; font-weight: 700; font-size: 0.96rem;
  text-decoration: none !important; display: inline-flex; align-items: center; gap: 6px;
}
.db-btn-toggle {
  background: #ffffff; color: #1e293b; border: 1px solid #94a3b8;
  padding: 12px 22px; border-radius: 999px; font-weight: 700;
  font-size: 0.94rem; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
}
</style>
<script>
(function(){
  function enforceTwoCards(){
    var links = Array.from(document.querySelectorAll("a")).filter(function(a){
      return (a.textContent || "").indexOf("이 글 전용 페이지") !== -1;
    });
    if (links.length <= 2) return;
    var cards = [];
    links.forEach(function(a){
      var el = a.closest("article");
      if (!el) {
        var cur = a;
        while (cur.parentElement && cur.parentElement !== document.body) {
          var cnt = links.filter(function(x){ return cur.parentElement.contains(x); }).length;
          if (cnt > 1) break;
          cur = cur.parentElement;
        }
        el = cur;
      }
      if (el && cards.indexOf(el) === -1) cards.push(el);
    });
    if (cards.length <= 2) return;
    cards.slice(0, 2).forEach(function(c){
      c.classList.remove("db-hidden-case");
      c.style.removeProperty("display");
    });
    var extras = cards.slice(2);
    extras.forEach(function(c){
      c.classList.add("db-hidden-case");
      c.style.setProperty("display", "none", "important");
    });
    var old = document.getElementById("db-more-bar");
    if (old) old.remove();
    var bar = document.createElement("div");
    bar.id = "db-more-bar";
    bar.className = "db-more-bar";
    var aBtn = document.createElement("a");
    aBtn.href = "/auto-cases/";
    aBtn.className = "db-btn-archive";
    aBtn.textContent = "🗂️ 다른 지역·작업별 안내 및 누적 기록 목록 보기 (+" + extras.length + "건)";
    var tBtn = document.createElement("button");
    tBtn.type = "button";
    tBtn.className = "db-btn-toggle";
    tBtn.textContent = "➕ 현재 화면에서 펼쳐보기";
    var open = false;
    tBtn.onclick = function(){
      open = !open;
      extras.forEach(function(c){
        if (open) {
          c.classList.remove("db-hidden-case");
          c.style.removeProperty("display");
        } else {
          c.classList.add("db-hidden-case");
          c.style.setProperty("display", "none", "important");
        }
      });
      tBtn.textContent = open ? "▲ 최신 2개만 남기고 접기" : "➕ 현재 화면에서 펼쳐보기";
    };
    bar.appendChild(aBtn);
    bar.appendChild(tBtn);
    cards[1].insertAdjacentElement("afterend", bar);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enforceTwoCards);
  } else {
    enforceTwoCards();
  }
  window.addEventListener("load", enforceTwoCards);
})();
</script>
<!-- DAEBONG_UI_END -->"""

    files = list(ROOT.glob('*.html')) + list((ROOT / 'auto-cases').rglob('*.html'))
    for f in files:
        if not f.is_file(): continue
        t = f.read_text(encoding='utf-8', errors='ignore')
        t = re.sub(r'<!-- DAEBONG_FAV_START -->.*?<!-- DAEBONG_FAV_END -->\s*', '', t, flags=re.S)
        t = re.sub(r'<!-- DAEBONG_UI_START -->.*?<!-- DAEBONG_UI_END -->\s*', '', t, flags=re.S)
        t = t.replace('(※ 아래 안내는 동일 유형의 작업을 알아보시는 분들을 위한 공통 참고 기준입니다.)', '')
        t = t.replace('안녕하십니까, 사직동 본점을 중심으로 현장에서 직접 뛰는 대봉개발입니다. 😊', '반갑습니다. 부산·경남 현장을 30년 경력 직영 팀이 직접 발로 뛰며 책임지는 대봉개발입니다.')
        t = t.replace('■ 시작부터 마무리 바닥 정리까지 꼼꼼하게', '■ 현장 여건에 맞춘 안전 해체 및 깔끔한 바닥 정리')
        if '</head>' in t:
            t = t.replace('</head>', fav_tags + '\n</head>', 1)
        if f.name == 'index.html' and f.parent == ROOT:
            art_re = re.compile(r'(<article\b[^>]*>)(.*?)(</article>)', re.DOTALL)
            cnt = 0
            def hide_extra(m):
                nonlocal cnt
                o, b, c = m.group(1), m.group(2), m.group(3)
                if '이 글 전용 페이지' in b:
                    cnt += 1
                    o = o.replace(' db-hidden-case', '').replace('db-hidden-case', '')
                    o = re.sub(r'\s*style="display:\s*none\s*!important;?"', '', o)
                    if cnt > 2:
                        if 'class="' in o:
                            o = o.replace('class="', 'class="db-hidden-case ', 1)
                        else:
                            o = o[:-1] + ' class="db-hidden-case">'
                        o = o[:-1] + ' style="display:none !important;">'
                return o + b + c
            t = art_re.sub(hide_extra, t)
            if '</body>' in t:
                t = t.replace('</body>', ui_code + '\n</body>', 1)
        f.write_text(t, encoding='utf-8')
    print("✓ [2/3] 홈페이지 최신 2개만 노출 고정 및 기존 문구 수정 완료")

def build_varied_blog():
    memo = "김해시 진영읍 미야카세 포차 철거"
    region = "김해시 진영읍"
    dt = datetime.date.today().strftime('%Y.%m.%d')
    mf = ROOT / 'memo.txt'
    if mf.exists():
        lines = [x.strip() for x in mf.read_text(encoding='utf-8', errors='ignore').splitlines() if x.strip() and not x.strip().startswith('#')]
        if lines: memo = lines[-1]
    for tf in list(ROOT.glob('*.txt')) + list((ROOT / 'automation').glob('*.txt')):
        if tf.name.lower() in ['memo.txt', 'robots.txt', 'requirements.txt']: continue
        raw = tf.read_text(encoding='utf-8', errors='ignore')
        m1 = re.search(r'작업 메모\s*:\s*"([^"]+)"', raw)
        m2 = re.search(r'【([^】]+)】', raw)
        if m1: memo = m1.group(1).strip()
        if m2: region = m2.group(1).strip()

    seed = memo + dt + datetime.datetime.now().strftime('%H%M%S')
    h = int(hashlib.md5(seed.encode('utf-8')).hexdigest(), 16)
    rc = re.sub(r'\s+', '', region)

    if any(k in memo for k in ['식당', '포차', '주방', '치킨', '카페', '고깃집']):
        wtype = "식당·점포 주방 설비 및 내부 철거"
        dline = "가스·수도·전기 마감 상태를 먼저 점검한 뒤 업소용 냉장고와 스텐 조리대 등 무거운 주방 집기를 안전하게 반출하고, 홀 가벽과 바닥까지 깔끔하게 정리했습니다."
        cline = "주방 설비와 집기만 비울지, 홀 가벽·천장 닥트·바닥 방수턱(하스리)까지 포함된 전체 원상복구인지 알려주시면 더욱 정확한 견적 안내가 가능합니다."
        tags = f"#{rc}철거 #{rc}식당철거 #{rc}폐기물 #{rc}원상복구 #식당폐업철거 #주방집기처분 #상가원상복구 #부산경남철거 #대봉개발"
    elif any(k in memo for k in ['사무실', '학원', '상가', '가벽', '칸막이']):
        wtype = "상가·사무실 칸막이 해체 및 원상복구"
        dline = "건물 내 이동 동선과 엘리베이터 사용 여건을 먼저 파악한 뒤, 내부 가벽과 바닥재·사무용 집기를 순서대로 해체하여 신속하게 상차까지 마쳤습니다."
        cline = "철거할 가벽 면적과 바닥 데코타일 제거 유무, 반출할 집기 물량을 사진과 함께 보내주시면 빠르게 비용을 산출해 드립니다."
        tags = f"#{rc}철거 #{rc}상가철거 #{rc}원상복구 #{rc}폐기물 #사무실원상복구 #가벽철거 #인테리어철거 #부산철거 #대봉개발"
    else:
        wtype = "현장 맞춤형 철거 및 폐기물 일괄 정리"
        dline = "현장 도착 후 주변 안전과 반출 경로를 먼저 확보하고, 30년 경력의 직영 베테랑 팀이 해체부터 폐기물 상차·바닥 빗질까지 하루 만에 깔끔히 마무리했습니다."
        cline = "처리할 현장 사진 2~3장과 동네·층수(엘리베이터 유무)를 문자로 남겨주시면 물량에 맞는 차량과 일정을 바로 안내해 드립니다."
        tags = f"#{rc}철거 #{rc}폐기물 #{rc}원상복구 #부산철거 #양산철거 #김해철거 #폐기물수거 #상가철거 #대봉개발"

    qnas = [
        ("Q. 내부 철거는 안 하고 무거운 집기나 폐기물만 따로 치울 수도 있나요?",
         "A. 물론입니다. 철거 공정 없이 주방 설비, 대형 가구, 마대 폐기물만 단독으로 수거하는 작업도 상시 진행하고 있습니다."),
        ("Q. 일 때문에 바빠서 현장에 계속 있기 어려운데 비대면 진행도 되나요?",
         "A. 사전에 작업 범위만 명확히 알려주시면 작업 전·후 사진을 문자로 상세히 보내드리므로 현장에 계시지 않아도 안심하고 맡기실 수 있습니다."),
        ("Q. 작업하다가 갑자기 추가 비용을 요구하지는 않나요?",
         "A. 보내주신 사진과 조건을 바탕으로 산출한 견적을 기준으로 하며, 사진에 보이지 않던 숨은 구조물 등이 나올 경우 임의로 진행하지 않고 반드시 먼저 설명드리고 협의합니다."),
        ("Q. 임대인이나 관리실의 원상복구 기준이 까다로운데 맞춰주실 수 있나요?",
         "A. 30년 현장 경험을 바탕으로 임대차 계약 조건과 퇴거 점검 기준에 맞춰 바닥 정리부터 배관 마감까지 깔끔하게 처리해 드립니다.")
    ]
    q1 = qnas[h % len(qnas)]
    q2 = qnas[(h + 1) % len(qnas)]

    templates = [
        f"""반갑습니다. 부산 사직동을 거점으로 {region} 현장을 직접 발로 뛰는 대봉개발입니다.
얼마 전 다녀온 [{memo}] 현장 진행 과정과 함께, {wtype} 의뢰 전 알아두시면 좋은 실무 팁을 정리해 드립니다.

📍 현장 작업 요약 ({dt})
• 위치 및 내용 : {region} / {memo}
• 중점 공정 : {wtype}

이번 현장에서 가장 신경 쓴 부분은 안전한 해체와 깔끔한 마무리였습니다.
{dline}

하청을 주지 않고 30년 경력의 직영 기술진이 직접 현장을 챙기기 때문에 작업 속도는 물론 마무리 청소 상태까지 믿고 맡기실 수 있습니다.

✔ 빠른 상담을 위한 체크 포인트
{cline}

💬 자주 물어보시는 질문
{q1[0]}
{q1[1]}

{q2[0]}
{q2[1]}

📞 대봉개발 간편 사진 견적 안내
• 문자 문의 : 010-8535-9787 (동네 + 층수 + 현장 사진 전송)
• 공식 홈페이지 : https://daebong-busan.kr/

{tags}""",
        f"""{region} 일대에서 {wtype} 업체를 알아보고 계신가요?
철거부터 폐기물 반출까지 직영 팀이 한 번에 해결하는 대봉개발에서 최근 완료한 [{memo}] 시공 기록을 전해드립니다.

[1] 사전 동선 파악 및 안전 조치 ({dt})
현장 기록 : {memo} ({region})
본격적인 해체에 앞서 인접 상가나 이웃에 불편이 없도록 반출 경로와 차량 위치를 먼저 확보했습니다.

[2] 숙련된 직영 팀의 해체 및 상차
{dline}

[3] 사진 견적 문의 시 참고사항
{cline}

💡 의뢰 전 궁금해하시는 점
{q1[0]}
{q1[1]}

{q2[0]}
{q2[1]}

📲 010-8535-9787 번으로 [동네 / 층수 / 현장 사진 2~3장]만 문자 주시면 확인 즉시 친절히 안내해 드립니다.
더 많은 시공 사례는 https://daebong-busan.kr/ 에서 확인하실 수 있습니다.

{tags}""",
        f"""안녕하세요! 30년 베테랑 직영 인력이 직접 시공하는 철거·폐기물 전문 대봉개발입니다.
오늘은 {region} 현장에서 마무리한 [{memo}] 작업 후기를 공유해 드릴게요.

현장마다 구조와 반출 조건이 다르기 때문에 경험 많은 작업자들의 호흡이 무엇보다 중요합니다.
{dline}

📌 작업 노트 ({dt})
- 현장명 : {memo}
- 사전 확인 사항 : {cline}

❓ 상담 시 자주 주시는 질문
{q1[0]}
{q1[1]}

{q2[0]}
{q2[1]}

복잡하게 설명하실 필요 없이 010-8535-9787 로 현장 사진과 위치만 편하게 문자 남겨주세요.
부산·양산·김해·경남 어디든 성실하게 상담해 드리겠습니다. (https://daebong-busan.kr/)

{tags}"""
    ]
    post = templates[h % len(templates)]
    (ROOT / 'blog_post.txt').write_text(post, encoding='utf-8')
    for tf in list(ROOT.glob('*.txt')) + list((ROOT / 'automation').glob('*.txt')):
        if tf.name.lower() in ['memo.txt', 'robots.txt', 'requirements.txt']: continue
        raw = tf.read_text(encoding='utf-8', errors='ignore')
        if '대봉개발' in raw or '010-8535-9787' in raw:
            tf.write_text(post, encoding='utf-8')
    subprocess.run(['powershell', '-NoProfile', '-Command', "Get-Content -Path 'blog_post.txt' -Encoding UTF8 -Raw | Set-Clipboard"], cwd=str(ROOT), check=False)

    mp = ROOT / 'automation' / 'main.py'
    if mp.exists():
        mt = mp.read_text(encoding='utf-8', errors='ignore')
        mt = mt.replace('(※ 아래 안내는 동일 유형의 작업을 알아보시는 분들을 위한 공통 참고 기준입니다.)', '')
        hook = '\nimport subprocess, sys\nfrom pathlib import Path as _P\nsubprocess.run([sys.executable, str(_P(__file__).resolve().parent.parent / "fix_all.py")], check=False)\n'
        if 'fix_all.py' not in mt:
            mt += hook
        mp.write_text(mt, encoding='utf-8')
    print("✓ [3/3] 블로그 원고 다변화 적용 및 클립보드 복사 완료!")

if __name__ == '__main__':
    create_favicons()
    patch_html()
    build_varied_blog()
