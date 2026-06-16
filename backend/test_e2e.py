#!/usr/bin/env python3
"""Test the actual _extract_character_names from llm.py."""
import re
import sys

# Directly define the function we just wrote to test it
def _looks_like_narrative(word):
    narrative = {'突然', '忽然', '已经', '现在', '当时', '然后', '于是',
                 '接着', '继续', '因为', '但是', '只见', '只是', '原来',
                 '起来', '下来', '上去', '进去', '出来', '过去', '过来',
                 '之后', '之前', '以后', '过后', '的时候'}
    return word in narrative

def _extract_character_names(text):
    candidates = []
    for match in re.finditer(r'(?:主角|主要人物|人物|角色)[:：]\s*([^\n]+)', text):
        candidates.extend(re.findall(r'[一-鿿]{2,4}', match.group(1)))
    for match in re.finditer(r'[一-鿿]{2,4}(?:[一-鿿]{2,4}|[、，]\s*[一-鿿]{2,4})+', text):
        candidates.extend(re.findall(r'[一-鿿]{2,4}', match.group(0)))
    name_action_pattern = (
        r'(?<![一-鿿])([一-鿿]{2,4})\s*'
        r'(?:握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)'
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))
    for match in re.finditer(r'(?:^|[。！？\n])\s*([一-鿿]{2,4})(?:[，。！？\s]|$)', text):
        candidate = match.group(1)
        if not _looks_like_narrative(candidate):
            candidates.append(candidate)
    stopwords = {
        '天下', '大势', '东汉', '朝政', '群雄', '乱世', '黄巾', '朝廷', '豪杰',
        '国家', '黎庶', '小说', '章节', '事情', '表面', '立刻', '众人', '他们',
        '这里', '那里', '忽然', '突然', '已经', '现在', '当时', '以后',
        '什么', '怎么', '如何', '为何', '然后', '于是', '接着', '继续',
        '一起', '一个', '也是', '因为', '但是', '不过', '面前', '旁边', '周围',
        '看见', '听见', '知道', '觉得', '想到', '感到', '发现', '明白',
        '一切', '一样', '一阵', '一声', '一下', '一眼', '刚才', '过后', '下来',
        '上去', '起来', '进去', '出来', '过去', '过来', '只是', '只见',
        '年代', '岁月', '心中', '眼里', '手中', '之中', '瞬息',
        '分久必合', '合久必分', '三顾茅庐',
    }
    seen = set()
    names = []
    for c in candidates:
        if c in stopwords or c in seen:
            continue
        seen.add(c)
        names.append(c)
    return names

# Key test: the test_demo_analysis_extracts_spaced_character_names test case
chapter_text = (
    "流萤车站 的风在夜色里慢慢压低，魏北辰 握着断裂玉牌，听见远处传来断续的z钟声。"
    "秦知 说，事情不会只停在表面。温微 没有立刻回答，只把断裂玉牌 推到桌边。"
    "沈珩 从阴影里看着他们。"
)

result = _extract_character_names(chapter_text)
print(f"Full result: {result}")
print(f"First 4: {result[:4]}")

expected = ['魏北辰', '秦知', '温微', '沈珩']
for name in expected:
    if name in result:
        print(f"  OK: '{name}' found at index {result.index(name)}")
    else:
        print(f"  MISSiNG: '{name}' not found!")
