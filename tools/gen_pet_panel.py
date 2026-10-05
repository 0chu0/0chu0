# -*- coding: utf-8 -*-
"""
生成 README 首图 pet-panel.svg
—— 1:1 复刻 index.html 里的「猫猫桌面 · 像素风」看板（.pet），
   猫/电脑像素网格、代码滚动、颜色、边框、字号全部从 index.html 抽取，
   仅把下拉框/按钮等交互件画成静态外观。
"""
import re, json, os, sys

# 路径自适应：以本脚本所在位置为基准推仓库根目录，Actions 里 checkout 后可直接跑
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
SRC = os.path.join(ROOT, 'index.html')
DECOR = os.path.join(_HERE, 'decor.json')   # 星光 / 爱心装饰片段，随仓库走，免得依赖已删除的旧图

# 血条格数：5 = 满格 happy，0~4 = sad（与 index.html 的 JS 逻辑一致：只有满格才 happy）
FILL = int(sys.argv[1]) if len(sys.argv) > 1 else 5
assert 0 <= FILL <= 5, FILL
PCT = FILL * 20
STATE = 'happy' if FILL >= 5 else 'sad'
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    ROOT, 'pet-panel.svg' if FILL == 5 else 'pet-panel-%d.svg' % FILL)

html = open(SRC, encoding='utf-8').read()

def js_str_array(name):
    line = [l for l in html.split('\n') if l.strip().startswith('var %s=[' % name)]
    assert len(line) == 1, (name, len(line))
    return re.findall(r'"([^"]*)"', line[0])

CAT = js_str_array('CAT')
PC  = js_str_array('PC')
CODE_W = [int(x) for x in re.findall(r'\d+', re.search(r'var CODE_W=\[([^\]]*)\]', html).group(1))]
CODE_C = re.findall(r'"(#[0-9A-Fa-f]{6})"', re.search(r'var CODE_C=\[([^\]]*)\]', html).group(1))
SCRPX = re.search(r'var SCRPX=\{x:(\d+),y:(\d+),w:(\d+),h:(\d+)\};', html)
SCRPX = dict(zip('xywh', [int(v) for v in SCRPX.groups()]))
# index.html 里 SCRPX 定义了两次，draw() 用到的是最后一次
allpx = re.findall(r'var SCRPX=\{x:(\d+),y:(\d+),w:(\d+),h:(\d+)\};', html)
SCRPX = dict(zip('xywh', [int(v) for v in allpx[-1]]))
PAL = dict(re.findall(r"(\w):'(#[0-9A-Fa-f]{6})'", html))
PX, CX, CY, QX, QY, VW, VH = 4, 31, 1, 1, 12, 248, 128

# 文案（严格取自 index.html）
title = re.search(r'<span class="pet-title">(.*?)</span>', html, re.S).group(1).strip()
note  = re.search(r'<span class="pet-note" id="petNote">(.*?)</span>', html, re.S).group(1)
note_lines = [re.sub(r'<[^>]+>', '', p).strip() for p in note.split('<br>')]
note_lines = [l for l in note_lines if l]
btn_labels = re.findall(r'data-act="(\w+)"><span class="ic">&#(\d+);</span>(\w+)</button>', html)
acts = [(chr(int(code)), lab) for _a, code, lab in btn_labels]
sel_status = re.search(r'<select id="selStatus">(.*?)</select>', html, re.S).group(1)
status_opts = re.findall(r'<option[^>]*>([^<]+)</option>', sel_status)
sel_mood = re.search(r'<select id="selMood">(.*?)</select>', html, re.S).group(1)
mood_opts = [re.sub(r'\s+', ' ', m).strip() for m in re.findall(r'<option[^>]*>([^<]+)</option>', sel_mood)]
META_LABELS = re.findall(r'<span>(我的[^<]+)</span>', html)

# ---- 旧 SVG 里可复用的装饰（星光 / 爱心）----
_decor = json.load(open(DECOR, encoding='utf-8'))
SPK = {c: _decor['spk'][c] for c in 'abcd'}
HRT = {c: _decor['hrt'][c] for c in 'ab'}

# ---------- 绘图工具 ----------
DARK   = '#3A2F35'
CREAM  = '#F6EEE9'
TBG    = '#B9A7AE'
COFF   = '#8E7C85'
CON    = '#F4A6C0'
FLOOR  = '#E4C9B4'
PINK   = '#E0578A'
MUTED  = '#8E7C85'
MONO   = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W = 680
BAR_T, BAR_PAD = 3, 9
BAR_H = BAR_PAD * 2 + 19          # 37
BAR_BOT = BAR_T + BAR_H + 3       # 43
PAD = 14
X0, X1 = 3 + PAD, W - 3 - PAD     # 17 .. 663
CW = X1 - X0                      # 646
TRACK_H = 3 + 5 + 21 + 5 + 3      # 37
Y_TRACK = BAR_BOT + PAD           # 57
Y_STAT_BASE = Y_TRACK + TRACK_H + 10 + 12.5
Y_MAIN = Y_TRACK + TRACK_H + 10 + 16 + 12     # 132
MAIN_H = 224
Y_MAIN_B = Y_MAIN + MAIN_H        # 356
Y_SEL = Y_MAIN_B + 3 + 12         # 371
SEL_H = 34
Y_NOTE = Y_SEL + SEL_H + 20
H = int(Y_NOTE + 16.5 * len(note_lines) + 12)

def R(x, y, w, h, fill, sw=0, stroke=DARK, extra=''):
    s = '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"' % (x, y, w, h, fill)
    if sw:
        s += ' stroke="%s" stroke-width="%s"' % (stroke, sw)
    if extra:
        s += ' ' + extra
    return s + '/>'

def T(x, y, s, size, fill, anchor='middle', weight='normal', cls='', ls='0'):
    esc = (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    return ('<text x="%.2f" y="%.2f" font-size="%s" fill="%s" text-anchor="%s" '
            'font-weight="%s"%s%s>%s</text>') % (
        x, y, size, fill, anchor, weight,
        (' letter-spacing="%s"' % ls) if ls != '0' else '',
        (' class="%s"' % cls) if cls else '', esc)

def est_w(s, size):
    """粗略估算文本宽度（ASCII 0.6em / CJK 1.0em / emoji 1.15em）"""
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o > 0x1F000:
            w += size * 1.15
        elif o > 0x2E80:
            w += size
        else:
            w += size * 0.6
    return w

out = []
out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="Taroll 的猫猫看板（像素风 · 动态）">' % (W, H, W, H))
out.append('''<defs>
<linearGradient id="pbar" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#7FD4C1"/><stop offset="1" stop-color="#5FBFAB"/>
</linearGradient>
<clipPath id="pscr"><rect x="%d" y="%d" width="%d" height="%d"/></clipPath>
</defs>''' % (SCRPX['x'], SCRPX['y'], SCRPX['w'], SCRPX['h']))

out.append('''<style>
  /* 猫猫轻轻呼吸浮动 */
  @keyframes pbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}
  .bob{animation:pbob 2.9s ease-in-out infinite}
  /* 屏幕里代码向上滚动 */
  @keyframes pcode{0%{transform:translateY(0)}100%{transform:translateY(-64px)}}
  .codeScroll{animation:pcode 2.6s linear infinite}
  /* 光标闪烁 */
  @keyframes pblink{0%,49%{opacity:1}50%,100%{opacity:0}}
  .cur{animation:pblink 1.05s steps(1) infinite}
  /* 爱心升起 */
  @keyframes prise{0%{transform:translate(0,10px);opacity:0}22%{opacity:1}100%{transform:translate(0,-26px);opacity:0}}
  .hrt{animation:prise 3.1s ease-in-out infinite}
  .hrt.b{animation-delay:1.55s}
  /* 星光闪烁 */
  @keyframes ptw{0%,100%{transform:scale(.72);opacity:.55}50%{transform:scale(1.1);opacity:1}}
  .spk{animation:ptw 2.7s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
  .spk.b{animation-delay:.7s} .spk.c{animation-delay:1.4s} .spk.d{animation-delay:2.1s}
  /* 爱心血条上的小爱心跳动 */
  @keyframes pbeat{0%,100%{transform:scale(1)}30%{transform:scale(1.16)}60%{transform:scale(.96)}}
  .beat{animation:pbeat 1.5s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
  text{font-family:__MONO__}
  @media (prefers-reduced-motion:reduce){
    .bob,.codeScroll,.cur,.hrt,.spk,.beat{animation:none}
    .hrt,.spk{opacity:0}
  }
</style>'''.replace('__MONO__', MONO))

# ---------- 1. 面板外框 ----------
out.append(R(1.5, 1.5, W - 3, H - 3, CREAM, 3))

# ---------- 2. 标题栏 ----------
out.append(R(3, BAR_T, W - 6, BAR_H, 'url(#pbar)'))
out.append(R(3, BAR_T + BAR_H, W - 6, 3, DARK))
out.append(T(15, BAR_T + BAR_PAD + 13.5, title, 11.5, 'rgba(58,47,53,0.45)', 'start', 'bold'))
out.append(T(13, BAR_T + BAR_PAD + 11.5, title, 11.5, '#FFFFFF', 'start', 'bold'))
# 窗口三个按钮
bx = W - 3 - 12 - (19 * 3 + 6 * 2)
for i in range(3):
    x = bx + i * 25
    out.append(R(x, BAR_T + BAR_PAD, 19, 19, CREAM, 2))
    cx, cy = x + 9.5, BAR_T + BAR_PAD + 9.5
    if i == 0:      # _
        out.append(R(cx - 4, cy + 2.5, 8, 2, DARK))
    elif i == 1:    # □
        out.append(R(cx - 3.5, cy - 3.5, 7, 7, 'none', 2))
    else:           # ×
        out.append('<path d="M%.1f %.1f L%.1f %.1f M%.1f %.1f L%.1f %.1f" stroke="%s" stroke-width="2"/>'
                   % (cx - 3.5, cy - 3.5, cx + 3.5, cy + 3.5, cx + 3.5, cy - 3.5, cx - 3.5, cy + 3.5, DARK))

# ---------- 3. 顶部 5 格进度条 ----------
out.append(R(X0, Y_TRACK, CW, TRACK_H, TBG, 3))
gap, n = 4, 5
iw = CW - 6 - 10
cwid = (iw - gap * (n - 1)) / n
for i in range(n):
    x = X0 + 3 + 5 + i * (cwid + gap)
    out.append(R(x, Y_TRACK + 3 + 5, cwid, 21, CON if i < FILL else COFF, 2))

# ---------- 4. 状态文字 ----------
out.append(T(W / 2, Y_STAT_BASE, '%d%%  ·  %d / 5  ·  %s' % (PCT, FILL, STATE), 12.5, DARK))

# ---------- 5. 主体：左血条 / 中舞台 / 右按钮 ----------
COL_L, COL_R, GAPC = 52, 104, 12
STAGE_X = X0 + COL_L + GAPC
STAGE_W = CW - COL_L - COL_R - GAPC * 2
ACTION_X = X0 + CW - COL_R

# 左：爱心 + 竖血条 + 100%
out.append(T(X0 + COL_L / 2, Y_MAIN + 15, '\u2665', 19, PINK, 'middle', 'normal', 'beat'))
VB_Y, VB_H = Y_MAIN + 21 + 6, MAIN_H - 21 - 6 - 15 - 6
out.append(R(X0 + 12, VB_Y, 28, VB_H, TBG, 3))
in_h = VB_H - 6 - 6
cell_h = (in_h - 3 * 4) / 5
for i in range(5):
    y = VB_Y + 3 + 3 + (4 - i) * (cell_h + 3)
    out.append(R(X0 + 12 + 3 + 3, y, 28 - 12, cell_h, CON if i < FILL else COFF, 2))
out.append(T(X0 + COL_L / 2, Y_MAIN + MAIN_H - 3, '%d%%' % PCT, 11, DARK))

# 中：舞台
out.append(R(STAGE_X, Y_MAIN, STAGE_W, MAIN_H, CREAM, 3))
out.append(R(STAGE_X + 3, Y_MAIN + MAIN_H - 3 - 36, STAGE_W - 6, 36, FLOOR))
out.append(R(STAGE_X + 3, Y_MAIN + MAIN_H - 3 - 36, STAGE_W - 6, 3, DARK))

# 中：猫 + 电脑（像素网格直接照搬 index.html 的 draw()）
def rects(rows, ox, oy):
    o = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '.' or ch not in PAL:
                continue
            o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>'
                     % ((ox + c) * PX, (oy + r) * PX, PX, PX, PAL[ch]))
    return ''.join(o)

def code_lines():
    o = []
    n = len(CODE_W)
    for i in range(n * 2):
        k = i % n
        o.append('<rect x="%d" y="%d" width="%d" height="4" fill="%s"/>'
                 % (SCRPX['x'] + PX, SCRPX['y'] + i * 2 * PX, CODE_W[k] * PX, CODE_C[k]))
    return ''.join(o)

SPR_W = 250.0
SPR_H = SPR_W * VH / VW
spr_x = STAGE_X + 3 + ((STAGE_W - 6) - SPR_W) / 2
spr_y = Y_MAIN + MAIN_H - 3 - SPR_H
out.append('<svg x="%.2f" y="%.2f" width="%.2f" height="%.2f" viewBox="0 0 %d %d" '
           'shape-rendering="crispEdges" overflow="visible">' % (spr_x, spr_y, SPR_W, SPR_H, VW, VH))
out.append('<g class="bob">')
out.append('<g>' + rects(PC, QX, QY) + '</g>')
out.append('<g clip-path="url(#pscr)"><g class="codeScroll">' + code_lines() + '</g></g>')
out.append('<rect class="cur" x="%d" y="%d" width="4" height="8" fill="#E0578A"/>'
           % (SCRPX['x'] + PX, SCRPX['y'] + 4))
out.append('<g>' + rects(CAT, CX, CY) + '</g>')
out.append(SPK['a'] + SPK['b'] + SPK['c'] + SPK['d'])
out.append(HRT['a'] + HRT['b'])
out.append('</g></svg>')

# 中：气泡（满格 = 表白；未满/破功 = 页面里的 😢）
bub_txt = 'i love you! \U0001F497 剩 21h 9m' if FILL >= 5 else '\U0001F622'
bw = est_w(bub_txt, 11.5) + 20 + 6
bh = 11.5 * 1.35 + 10 + 6
bub_x, bub_y = STAGE_X + 3 + 12, Y_MAIN + 3 + 10
out.append(R(bub_x + 3, bub_y + 3, bw, bh, 'rgba(58,47,53,0.22)', 0, DARK))
out.append(R(bub_x, bub_y, bw, bh, '#FFFFFF', 3))
out.append(T(bub_x + 3 + 10, bub_y + 3 + 5 + 12, bub_txt, 11.5, DARK, 'start', 'bold'))

# 右：Feed / Water / Play
btn_h = (MAIN_H - 10 * 2) / 3
for i, (ico, lab) in enumerate(acts):
    y = Y_MAIN + i * (btn_h + 10)
    out.append(R(ACTION_X + 3, y + 3, COL_R, btn_h, 'rgba(58,47,53,0.28)', 0, DARK))
    out.append(R(ACTION_X, y, COL_R, btn_h, TBG, 3))
    out.append(T(ACTION_X + COL_R / 2, y + btn_h / 2 - 2, ico, 20, DARK))
    out.append(T(ACTION_X + COL_R / 2, y + btn_h / 2 + 17, lab, 11, DARK, 'middle', 'bold'))

# ---------- 6. 底部：我的状态 / 我的心情 + 说明 ----------
out.append(R(3, Y_MAIN_B, W - 6, 3, DARK))
sel_base = Y_SEL + SEL_H / 2 + 4.5
x = X0
for lab, val in [(META_LABELS[0], status_opts[1]), (META_LABELS[1], mood_opts[-1])]:
    out.append(T(x, sel_base, lab, 12, DARK, 'start', 'bold'))
    x += est_w(lab, 12) + 8
    boxw = est_w(val, 12) + 18 + 6 + 16
    out.append(R(x, Y_SEL, boxw, SEL_H, '#FFFFFF', 3))
    out.append(T(x + 3 + 9, sel_base, val, 12, DARK, 'start', 'bold'))
    ax = x + boxw - 3 - 14
    out.append('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f" fill="none" stroke="%s" stroke-width="2" '
               'stroke-linecap="round" stroke-linejoin="round"/>'
               % (ax, sel_base - 6, ax + 6, sel_base, ax + 12, sel_base - 6, DARK))
    x += boxw + 14

for i, line in enumerate(note_lines):
    out.append(T(X0, Y_NOTE + 11 + i * 16.5, line, 11, MUTED, 'start'))

out.append('</svg>')

svg = '\n'.join(out) + '\n'
open(OUT, 'w', encoding='utf-8').write(svg)
print('WROTE', OUT, len(svg), 'bytes   H=%d' % H)
print('title:', title)
print('acts:', acts)
print('status:', status_opts, '| mood:', mood_opts)
print('note:', note_lines)
print('SCRPX:', SCRPX, 'PAL:', PAL)
