# -*- coding: utf-8 -*-
"""
查 Taroll 在 GitHub 上最近一次 push 是几天前，换算成宠物看板的血条格数。

输出（CI 里写 $GITHUB_OUTPUT，本地直接打印到 stdout）：
  days  上次 push 距今多少天（UTC，向下取整；查不到时为 -1）
  fill  血条格数 0~5
  state happy / sad
  msg  一句人话，用作 commit message 和 workflow summary
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

USER = os.environ.get('PET_USER', '0chu0')
TOKEN = os.environ.get('GH_TOKEN', '') or os.environ.get('GITHUB_TOKEN', '')


def last_push_days():
    """返回最近一次真实 push 距今的天数；查不到返回 None。"""
    url = 'https://api.github.com/users/%s/events/public?per_page=100' % USER
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'taroll-pet-panel',
    }
    if TOKEN:
        headers['Authorization'] = 'Bearer ' + TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        events = json.load(r)

    # /events/public 返回的是精简 payload（只有 before/head/ref，没有 commits 字段），
    # 而 PushEvent 本身就代表真的推了代码，所以直接按 type 过滤即可。
    stamps = [e['created_at'] for e in events if e.get('type') == 'PushEvent']
    if not stamps:
        return None

    latest = max(stamps)
    then = datetime.strptime(latest, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - then
    return int(delta.total_seconds() // 86400)


def fill_for(days):
    """天數 → 血条格数。改这里的数字就能调规则。"""
    if days is None:      # 90 天内查不到任何 push
        return 0
    if days <= 0:
        return 5
    if days <= 2:
        return 4
    if days <= 6:
        return 2
    return 0


def main():
    days = last_push_days()
    fill = fill_for(days)
    state = 'happy' if fill >= 5 else 'sad'
    shown = '查不到近期 push' if days is None else ('%d 天前' % days)
    msg = 'pet panel %d/5 · %s · 上次 push %s' % (fill, state, shown)

    out = {'days': -1 if days is None else days, 'fill': fill,
           'state': state, 'msg': msg}
    print(msg)

    steps = os.environ.get('GITHUB_OUTPUT')
    if steps:
        with open(steps, 'a', encoding='utf-8') as f:
            for k, v in out.items():
                f.write('%s=%s\n' % (k, v))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write('### 猫猫状态刷新\n\n')
            f.write('| 上次 push | 血条 | 状态 |\n|---|---|---|\n')
            f.write('| %s | %d / 5 | %s |\n' % (shown, fill, state))


if __name__ == '__main__':
    main()
