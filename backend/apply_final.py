#!/usr/bin/env python3
"""Apply character extraction fixes using a clean byte-for-byte approach.

Works by matching exact portions of the original function and replacing them.
Uses unicode escapes to avoid terminal/encoding issues.
"""

import os

path = 'app/services/llm.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# All old/new blocks use only ASCII-safe programming text.
# Chinese characters are referenced via their positions in the file.

# ---------------------------------------------------------------------------
# 1. REPLACE name-list pattern (currently lines 603-604)
# OLD: for match in re.finditer(r"([一-鿿]{2})、([一-鿿]{2})、([一-鿿]{2})", text):
#      /     candidates.extend(match.groups())
# NEW: match runs of 2+ CJK names separated by 、or ，
# ---------------------------------------------------------------------------
old_name_list_start = '    for match in re.finditer(r"([\\u4e00-\\u9fff]{2})'
old_name_list_end   = '        candidates.extend(match.groups())'

new_name_list = (
    '    for match in re.finditer(r"[\\u4e00-\\u9fff]{2,4}(?:[、，]\\s*[\\u4e00-\\u9fff]{2,4})+", text):\n'
    '        candidates.extend(re.findall(r"[\\u4e00-\\u9fff]{2,4}", match.group(0)))'
)

idx1 = content.find(old_name_list_start)
if idx1 < 0:
    raise SystemExit("FAIL: could not find old_name_list_start")
idx2 = content.find(old_name_list_end, idx1)
if idx2 < 0:
    raise SystemExit("FAIL: could not find old_name_list_end")
idx2 += len(old_name_list_end)
content = content[:idx1] + new_name_list + content[idx2:]
print("Replaced name-list pattern")

# ---------------------------------------------------------------------------
# 2. REPLACE action verb pattern (currently lines 606-611)
# Remove 从/率/与/和/同/向 — these are NOT action verbs
# Add more common dialogue/action verbs
# Keep 没有 as it can catch character names in "XX没有..." pattern
# ---------------------------------------------------------------------------
old_action_start = '    name_action_pattern = ('
old_action_end   = '        candidates.append(match.group(1))\n'  # must include newline

new_action = (
    '    name_action_pattern = (\n'
    '        r"(?<![\\u4e00-\\u9fff])([\\u4e00-\\u9fff]{2,4})\\s*"\n'
    '        r"(?:'
    # action verbs with clear character-agent semantics:
    '握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|'
    '点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上|'
    # keep 没有 as it captures names in "XX没-有..." pattern
    '没有'
    ')"\n'
    '    )\n'
    '    for match in re.finditer(name_action_pattern, text):\n'
    '        candidates.append(match.group(1))\n'
)

idx3 = content.find(old_action_start)
if idx3 < 0:
    raise SystemExit("FAIL: could not find old_action_start")
idx4 = content.find(old_action_end, idx3)
if idx4 < 0:
    raise SystemExit("FAIL: could not find old_action_end")
idx4 += len(old_action_end)
content = content[:idx3] + new_action + content[idx4:]
print("Replaced action verb pattern")

# ---------------------------------------------------------------------------
# 3. REPLACE stopwords set (currently lines 613-632)
# Expand with common narrative/functional 2-char phrases that are never names
# ---------------------------------------------------------------------------
old_sw_start = '    stopwords = {'
# Find the closing } of the set
idx5 = content.find(old_sw_start)
if idx5 < 0:
    raise SystemExit("FAIL: could not find stopwords start")
# Count braces
depth = 0
found_open = False
idx6 = idx5
for i in range(idx5, len(content)):
    if content[i] == '{':
        depth += 1
        found_open = True
    elif content[i] == '}':
        depth -= 1
        if found_open and depth == 0:
            idx6 = i + 1
            break
if idx6 <= idx5:
    raise SystemExit("FAIL: could not find stopwords end")

new_stopwords = (
    '    stopwords = {\n'
    '        "天下", "大势", "东汉", "朝政", "群雄", "乱世", "黄巾", "朝廷", "豪杰",\n'
    '        "国家", "黎庶", "小说", "章节", "事情", "表面", "立刻", "众人", "他们",\n'
    '        "这里", "那里", "忽然", "突然", "已经", "现在", "当时", "以后",\n'
    '        "什么", "怎么", "如何", "为何", "然后", "于是", "接着", "继续",\n'
    '        "一起", "一个", "也是", "因为", "但是", "不过", "面前", "旁边", "周围",\n'
    '        "看见", "听见", "知道", "觉得", "想到", "感到", "发现", "明白",\n'
    '        "一切", "一样", "一阵", "一声", "一下", "一眼", "刚才", "过后", "下来",\n'
    '        "上去", "起来", "进去", "出来", "过去", "过来", "只是", "只见",\n'
    '        "年代", "岁月", "心中", "眼里", "手中", "之中", "瞬息",\n'
    '        "分久必合", "合久必分", "三顾茅庐",\n'
    '    }'
)
content = content[:idx5] + new_stopwords + content[idx6:]
print("Replaced stopwords")

# ---------------------------------------------------------------------------
# Write back
# ---------------------------------------------------------------------------
with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(content)

# Verify syntax
import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax check: OK")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")
    raise SystemExit(1)
