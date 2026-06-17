#!/usr/bin/env python3
"""Apply all character recognition fixes to llm.py."""
import sys

target = 'app/services/llm.py'

with open(target, 'r', encoding='utf-8') as f:
    content = f.read()

helper = '''
def _looks_like_narrative(word: str) -> bool:
    """Heuristic: filter narrative/functional phrases that look like names."""
    narrative = {"突然", "忽然", "已经", "现在", "当时", "然后", "于是",
                 "接着", "继续", "因为", "但是", "只见", "只是", "原来",
                 "起来", "下来", "上去", "进去", "出来", "过去", "过来",
                 "之后", "之前", "以后", "过后", "的时候"}
    return word in narrative


'''

old_fx = 'def _extract_character_names(project: Project) -> list[str]:'
new_fx = helper + old_fx
content = content.replace(old_fx, new_fx, 1)

old_name_list = '''    for match in re.finditer(r"([\\u4e00-\\u9fff]{2})、([\\u4e00-\\u9fff]{2})、([\\u4e00-\\u9fff]{2})", text):
        candidates.extend(match.groups())'''

new_name_list = '''    for match in re.finditer(r"[\\u4e00-\\u9fff]{2,4}(?:[\\u4e00-\\u9fff]{2,4}|[、，]\\s*[\\u4e00-\\u9fff]{2,4})+", text):
        candidates.extend(re.findall(r"[\\u4e00-\\u9fff]{2,4}", match.group(0)))'''

if old_name_list in content:
    content = content.replace(old_name_list, new_name_list)
else:
    print("WARNING: old_name_list not found")
    # Let's check what's actually there
    idx = content.find('for match in re.finditer(r"')
    snippet = content[idx:idx+200]
    print(f"Found: {repr(snippet[:100])}")

old_action = '''    name_action_pattern = (
        r"(?<![\\u4e00-\\u9fff])([\\u4e00-\\u9fff]{2,4})\\s*"
        r"(?:握着|说|低声道|道|问|答|没有|从|提醒|看着|率|与|和|同|向)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))'''

new_action = '''    name_action_pattern = (
        r"(?<![\\u4e00-\\u9fff])([\\u4e00-\\u9fff]{2,4})\\s*"
        r"(?:握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))

    for match in re.finditer(r"(?:^|[\\u3002\\uff01\\uff1f\\n])\\s*([\\u4e00-\\u9fff]{2,4})(?:[\\uff0c\\u3002\\uff01\\uff1f\\s]|$)", text):
        candidate = match.group(1)
        if not _looks_like_narrative(candidate):
            candidates.append(candidate)'''

if old_action in content:
    content = content.replace(old_action, new_action)
else:
    print("WARNING: old_action not found")

old_stopwords = '''    stopwords = {
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

if old_stopwords in content:
    content = content.replace(old_stopwords, new_stopwords)
else:
    print("WARNING: old_stopwords not found")

with open(target, 'w', encoding='utf-8', newline='') as f:
    f.write(content)
print("Done. File written.")
