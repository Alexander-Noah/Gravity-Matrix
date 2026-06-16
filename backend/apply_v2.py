#!/usr/bin/env python3
"""Apply character recognition fixes to llm.py using regex matching."""

import re

path = 'app/services/llm.py'
with open(path, 'rb') as f:
    raw = f.read()

# The file is UTF-8 encoded. Let's work with it.
# Let's read it as text to find patterns, but use bytes for replacement
text = raw.decode('utf-8')

# 1. Replace name-list pattern
# Find the exact pattern: for match in re.finditer(r"...", text):
# where the pattern has exactly 3 groups of 2-char CJK separated by 、
old_name_list = re.compile(
    r'(\s+)for match in re\.finditer\(r"\(\[\\u4e00-\\u9fff\]\{2\}\)、\(\[\\u4e00-\\u9fff\]\{2\}\)、\(\[\\u4e00-\\u9fff\]\{2\}\)", text\):'
)
m = old_name_list.search(text)
if m:
    indent = m.group(1)
    replacement = indent + 'for match in re.finditer(r"[\\u4e00-\\u9fff]{2,4}(?:[\\u4e00-\\u9fff]{2,4}|[、，]\\s*[\\u4e00-\\u9fff]{2,4})+", text):\n'
    replacement += indent + '    candidates.extend(re.findall(r"[\\u4e00-\\u9fff]{2,4}", match.group(0)))'
    text = text[:m.start()] + replacement + text[m.end()+1+len(indent+'        candidates.extend(match.groups())'):]
    print("Replaced name-list pattern")
else:
    print("FAIL: name-list pattern not found")

# 2. Replace action verb pattern
old_action = (
    r'name_action_pattern = \(\n'
    r'\s+r"\(\?\<\!\[\\\\u4e00-\\\\u9fff\]\)\(\[\\\\u4e00-\\\\u9fff\]\{2,4\}\)\\\\s\*"\n'
    r'\s+r"\(\?\:'
)
m2 = re.search(old_action, text)
if m2:
    idx = m2.start()
    # Find the end of this block: the line after 'candidates.append(match.group(1))'
    end_marker = 'candidates.append(match.group(1))'
    end_idx = text.find(end_marker, idx)
    if end_idx >= 0:
        end_idx += len(end_marker)
        new_action = (
            'name_action_pattern = (\n'
            '        r"(?<![\\\\u4e00-\\\\u9fff])([\\\\u4e00-\\\\u9fff]{2,4})\\\\s*"\n'
            '        r"(?:'
            '握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|没有|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)'
            '"\n'
            '    )\n'
            '    for match in re.finditer(name_action_pattern, text):\n'
            '        candidates.append(match.group(1))'
        )
        text = text[:idx] + new_action + text[end_idx:]
        print("Replaced action verb pattern")
    else:
        print("FAIL: end of action block not found")
else:
    print("FAIL: action pattern not found")

# 3. Replace stopwords
old_stopwords = (
    'stopwords = \{\n'
    '        "[一-鿿]\+",\n'
    '        "[一-鿿]\+",\n'
    '        "[一-鿿]\+",\n'
)
# Better: find by marker
sw_marker = '    stopwords = {\n'
sw_start = text.find(sw_marker)
if sw_start >= 0:
    # count braces to find end
    depth = 0
    found_open = False
    sw_end = sw_start
    for i in range(sw_start, len(text)):
        if text[i] == '{':
            depth += 1
            found_open = True
        elif text[i] == '}':
            depth -= 1
            if found_open and depth == 0:
                sw_end = i + 1
                break
    if sw_end > sw_start:
        new_stopwords = '''    stopwords = {
        "天下", "大势", "东汉", "朝政", "群雄", "乱世", "黄巾", "朝廷", "豪杰",
        "国家", "黎庶", "小说", "章节", "事情", "表面", "立刻", "众人", "他们",
        "这里", "那里", "忽然", "突然", "已经", "现在", "当时", "以后",
        "什么", "怎么", "如何", "为何", "然后", "于是", "接着", "继续",
        "一起", "一个", "也是", "因为", "但是", "不过", "面前", "旁边", "周围",
        "看见", "听见", "知道", "觉得", "想到", "感到", "发现", "明白",
        "一切", "一样", "一阵", "一声", "一下", "一眼", "刚才", "过后", "下来",
        "上去", "起来", "进去", "出来", "过去", "过来", "只是", "只见",
        "年代", "岁月", "心中", "眼里", "手中", "之中", "瞬息",
        "分久必合", "合久必分", "三顾茅庐",
    }'''
        text = text[:sw_start] + new_stopwords + text[sw_end:]
        print("Replaced stopwords")
    else:
        print(f"FAIL: stopwords end not found (sw_end={sw_end})")
else:
    print("FAIL: stopwords start not found")

with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(text)
print("Done writing file")
