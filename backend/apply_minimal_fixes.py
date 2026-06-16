#!/usr/bin/env python3
"""Apply minimal character recognition fixes to llm.py.

Fixes:
1. Name-list pattern: support 2+ names (not just exactly 3), mixed 、and ，
2. Action verbs: remove prepositions 从/与/和/同 that cause false positives
3. Expand stopwords significantly
"""

with open('app/services/llm.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Name-list pattern (lines 603-604)
old_list = '''    for match in re.finditer(r"([\\u4e00-\\u9fff]{2})、([\\u4e00-\\u9fff]{2})、([\\u4e00-\\u9fff]{2})", text):
        candidates.extend(match.groups())'''

new_list = '''    for match in re.finditer(r"[\\u4e00-\\u9fff]{2,4}(?:[、，]\\s*[\\u4e00-\\u9fff]{2,4})+", text):
        candidates.extend(re.findall(r"[\\u4e00-\\u9fff]{2,4}", match.group(0)))'''

assert old_list in content, "old_list not found"
content = content.replace(old_list, new_list)

# Fix 2: Action verbs — remove 从/与/和/同, keep 没有, add more genuine action verbs
old_action = r"""    name_action_pattern = (
        r"(?<![一-鿿])([一-鿿]{2,4})\s*"
        r"(?:握着|说|低声道|道|问|答|没有|从|提醒|看着|率|与|和|同|向)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))"""

new_action = r"""    name_action_pattern = (
        r"(?<![一-鿿])([一-鿿]{2,4})\s*"
        r"(?:握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|没有|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))"""

assert old_action in content, "old_action not found"
content = content.replace(old_action, new_action)

# Fix 3: Expand stopwords
old_sw = '''    stopwords = {
        "天下",
        "大势",
        "东汉",
        "朝政",
        "群雄",
        "乱世",
        "黄巾",
        "朝廷",
        "豪杰",
        "国家",
        "黎庶",
        "小说",
        "章节",
        "事情",
        "表面",
        "立刻",
        "众人",
        "他们",
    }'''

new_sw = '''    stopwords = {
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

assert old_sw in content, "old_stopwords not found"
content = content.replace(old_sw, new_sw)

with open('app/services/llm.py', 'w', encoding='utf-8', newline='') as f:
    f.write(content)
print("All fixes applied successfully")
