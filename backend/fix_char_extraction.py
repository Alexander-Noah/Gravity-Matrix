# -*- coding: utf-8 -*-
"""Fix the _extract_character_names function and add _looks_like_narrative helper."""
import re
import os

target = os.path.join(os.path.dirname(__file__), 'app', 'services', 'llm.py')

with open(target, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """    for match in re.finditer(r"[一-鿿]{2,4}(?:[、，]\\s*[一-鿿]{2,4})+", text):
        candidates.extend(re.findall(r"[一-鿿]{2,4}", match.group(0)))

    name_action_pattern = (
        r"(?<![一-鿿])([一-鿿]{2,4})\\s*"
        r"(?:握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))

    for match in re.finditer(r"(?:^|[。！？
])\\s*([一-鿿]{2,4})(?:[，。！？\\s]|$)", text):
        candidate = match.group(1)
        if not _looks_like_narrative(candidate):
            candidates.append(candidate)

    stopwords = {
        "天下", "大势", "东汉", "朝政", "群雄", "乱世", "黄巾", "朝廷", "豪杰",
        "国家", "黎庶", "小说", "章节", "事情", "表面", "立刻", "众人", "他们",
        "这里", "那里", "忽然", "突然", "已经", "现在", "当时", "以后",
        "什么", "怎么", "如何", "为何", "然后", "于是", "接着", "继续",
        "一起", "一个", "也是", "因为", "但是", "不过", "面前", "旁边", "周围",
        "看见", "听见", "知道", "觉得", "想到", "感到", "发现", "明白",
        "一切", "一样", "一阵", "一声", "一下", "一眼", "刚才", "过后", "下来",
        "上去", "起来", "进去", "出来", "过去", "过来", "不过", "只是", "只见",
        "年代", "岁月", "心中", "眼中", "手中", "之中", "瞬息",
        "分久必合", "合久必分", "三顾茅庐",
    }"""

new_block = """    for match in re.finditer(r"[一-鿿]{2,4}(?:[、，]\s*[一-鿿]{2,4})+", text):
        candidates.extend(re.findall(r"[一-鿿]{2,4}", match.group(0)))

    name_action_pattern = (
        r"(?<![一-鿿])([一-鿿]{2,4})\s*"
        r"(?:握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))

    for match in re.finditer(r"(?:^|[。！？\n])\s*([一-鿿]{2,4})(?:[，。！？\s]|$)", text):
        candidate = match.group(1)
        if not _looks_like_narrative(candidate):
            candidates.append(candidate)

    stopwords = {
        "天下", "大势", "东汉", "朝政", "群雄", "乱世", "黄巾", "朝廷", "豪杰",
        "国家", "黎庶", "小说", "章节", "事情", "表面", "立刻", "众人", "他们",
        "这里", "那里", "忽然", "突然", "已经", "现在", "当时", "以后",
        "什么", "怎么", "如何", "为何", "然后", "于是", "接着", "继续",
        "一起", "一个", "也是", "因为", "但是", "不过", "面前", "旁边", "周围",
        "看见", "听见", "知道", "觉得", "想到", "感到", "发现", "明白",
        "一切", "一样", "一阵", "一声", "一下", "一眼", "刚才", "过后", "下来",
        "上去", "起来", "进去", "出来", "过去", "过来", "不过", "只是", "只见",
        "年代", "岁月", "心中", "眼里", "手中", "之中", "瞬息",
        "分久必合", "合久必分", "三顾茅庐",
    }"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(target, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print("OK: replaced the block")
else:
    print("ERROR: old_block not found")
    # Try to find what's actually there
    idx = content.find("for match in re.finditer")
    if idx >= 0:
        snippet = content[idx-10:idx+300]
        print(f"Found at {idx}: {repr(snippet)}")
