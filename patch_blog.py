# -*- coding: utf-8 -*-
import datetime, hashlib, re, subprocess
from pathlib import Path
root = Path(__file__).resolve().parent
def make_blog(memo, region, dt):
    seed = memo + dt + datetime.datetime.now().strftime('%H%M')
    h = int(hashlib.md5(seed.encode('utf-8')).hexdigest(), 16)
    intros = [
        f'반갑습니다. 부산 사직동을 거점으로 {region} 현장을 직접 발로 뛰는 대봉개발입니다.\n오늘은 최근 다녀온 [{memo}] 현장 진행 과정과 함께, 작업 전 알아두시면 도움 되는 실무 기준을 정리해 드립니다.',
        f'안녕하세요! 30년 현장 노하우로 철거부터 폐기물 반출까지 직접 책임지는 대봉개발입니다.\n얼마 전 {region}에서 진행한 [{memo}] 작업을 마치고 돌아왔는데요. 현장 여건에 맞춘 진행 과정을 공유합니다.',
        f'{region} 일대에서 상가 원상복구나 폐기물 정리를 고민 중이신가요?\n하청 없이 직영 팀이 직접 현장을 챙기는 대봉개발에서 [{memo}] 시공 기록을 전해드립니다.',
        f'현장마다 구조도 다르고 반출 동선도 제각각이죠. {region} 철거·폐기물 베테랑 대봉개발입니다.\n이번에 완료한 [{memo}] 현장을 바탕으로 깔끔한 정리 과정을 소개해 드릴게요.'
    ]
    bodies = [
        f'📌 사전 동선 확보와 안전한 설비 해체\n이번 {region} 현장은 주변 상가나 이웃에 불편을 주지 않도록 반출 경로를 먼저 확보한 뒤, 무거운 설비와 내부 구조물을 순서대로 안전하게 해체했습니다.\n\n특히 철거 작업은 단순히 부수는 것이 아니라 전기·수도·가스 마감 상태를 정확히 확인하고, 작업 후 바닥에 남는 잔해물까지 빗질하듯 깔끔하게 치워내는 것이 핵심입니다.',
        f'📌 투명한 견적 소통과 신속한 당일 반출\n[{memo}] 작업을 진행하면서 가장 신경 쓴 부분은 안전과 신속한 반출이었습니다. 층수와 차량 진입 여건을 미리 체크해 불필요한 시간 지체를 줄였습니다.\n\n현장에서 간혹 사진으로 미처 보이지 않던 숨은 구조물이나 추가 폐기물이 나오는 경우가 있는데요. 저희는 임의로 진행하지 않고 반드시 먼저 설명드리고 협의를 거친 후 투명하게 처리하고 있습니다.',
        f'📌 부분 수거부터 전체 원상복구까지 맞춤형 진행\n{region} 현장 도착 후 가장 먼저 철거 범위와 남겨두어야 할 시설물을 꼼꼼히 구분했습니다. 호흡이 잘 맞는 직영 베테랑 팀이 투입되어 설비 해체부터 폐기물 상차까지 막힘없이 마무리했습니다.\n\n내부 집기류만 부분 수거하는 작업부터 바닥·천장·가벽을 모두 비워내는 전체 원상복구까지 현장 상황에 딱 맞는 방식으로 진행해 드립니다.'
    ]
    qnas = [
        ('Q. 철거는 안 하고 내부 집기나 폐기물만 따로 치울 수도 있나요?', 'A. 물론입니다. 무거운 주방 설비, 사무용 가구, 대형 생활폐기물이나 마대 자루만 단독으로 수거하는 작업도 상시 진행하고 있습니다.'),
        ('Q. 바빠서 현장에 계속 있기 어려운데 비대면 진행도 가능한가요?', 'A. 사전에 비워야 할 품목과 범위만 정확히 알려주시면, 작업 전·후 사진을 문자로 보내드리기 때문에 현장에 계시지 않아도 안심하고 맡기실 수 있습니다.'),
        ('Q. 방문 견적 전에 대략적인 비용을 먼저 알 수 있을까요?', 'A. 네, 010-8535-9787 번호로 [동네 이름 + 층수 + 현장 사진 몇 장]만 문자로 보내주시면 물량과 동선을 파악해 예상 견적을 빠르게 안내해 드립니다.'),
        ('Q. 임대인이 요구하는 원상복구 기준이 까다로운데 맞춰주실 수 있나요?', 'A. 30년 경력 동안 수많은 상가·식당·사무실 원상복구를 처리해 왔습니다. 가벽 철거부터 천장, 바닥 정리까지 계약 조건에 맞춰 깔끔하게 마감해 드립니다.')
    ]
    q1 = qnas[h % len(qnas)]
    q2 = qnas[(h + 1) % len(qnas)]
    rc = region.replace(' ', '')
    tags = f'#{rc}철거 #{rc}폐기물 #{rc}원상복구 #부산철거 #경남철거 #상가원상복구 #식당폐업철거 #폐기물수거 #대봉개발'
    return f'{intros[h % len(intros)]}\n\n📍 현장 기록 : [{region}] {memo} ({dt})\n\n{bodies[(h // 2) % len(bodies)]}\n\n💡 상담 전 자주 묻는 질문\n{q1[0]}\n{q1[1]}\n\n{q2[0]}\n{q2[1]}\n\n📞 대봉개발 직통 상담 및 사진 견적 안내\n• 간편 문자 문의 : [동네 + 층수(엘리베이터 유무) + 현장 사진] 전송\n• 직통 전화 : 010-8535-9787 (30년 경력 직영 시공)\n• 공식 홈페이지 : https://daebong-busan.kr/\n\n{tags}\n'
memo_val = '김해시 진영읍 미야카세 포차 철거'
reg_val = '김해시 진영읍'
dt_val = datetime.date.today().strftime('%Y.%m.%d')
mf = root / 'memo.txt'
if mf.exists():
    lines = [l.strip() for l in mf.read_text(encoding='utf-8', errors='ignore').splitlines() if l.strip() and not l.strip().startswith('#')]
    if lines: memo_val = lines[-1]
for tf in list(root.glob('*.txt')) + list((root / 'automation').glob('*.txt')):
    if tf.name.lower() in ['memo.txt', 'robots.txt', 'requirements.txt']: continue
    raw = tf.read_text(encoding='utf-8', errors='ignore')
    m1 = re.search(r'작업 메모\s*:\s*"([^"]+)"', raw)
    m2 = re.search(r'【([^】]+)】', raw)
    if m1: memo_val = m1.group(1).strip()
    if m2: reg_val = m2.group(1).strip()
new_blog = make_blog(memo_val, reg_val, dt_val)
for tf in list(root.glob('*.txt')) + list((root / 'automation').glob('*.txt')):
    if tf.name.lower() in ['memo.txt', 'robots.txt', 'requirements.txt']: continue
    raw = tf.read_text(encoding='utf-8', errors='ignore')
    if '대봉개발' in raw or '010-8535-9787' in raw:
        tf.write_text(new_blog, encoding='utf-8')
(root / 'blog_post.txt').write_text(new_blog, encoding='utf-8')
subprocess.run(['powershell', '-NoProfile', '-Command', "Get-Content -Path 'blog_post.txt' -Encoding UTF8 -Raw | Set-Clipboard"], cwd=str(root), check=False)
mp = root / 'automation' / 'main.py'
if mp.exists():
    mt = mp.read_text(encoding='utf-8', errors='ignore')
    mt = mt.replace('(※ 아래 안내는 동일 유형의 작업을 알아보시는 분들을 위한 공통 참고 기준입니다.)', '')
    hook = '\nimport subprocess, sys; from pathlib import Path as _P; subprocess.run([sys.executable, str(_P(__file__).resolve().parent.parent / "patch_ui.py")], check=False); subprocess.run([sys.executable, str(_P(__file__).resolve().parent.parent / "patch_blog.py")], check=False)\n'
    if 'patch_blog.py' not in mt: mt = mt + hook
    mp.write_text(mt, encoding='utf-8')
print('✓ [3/3] 블로그 다변화 원고 생성 및 클립보드 자동 복사 완료!')
