#!/usr/bin/env python3
"""Compare extraction quality with different action verb sets."""
import re

def _looks_like_narrative(word):
    narrative = {'突然', '忽然', '已经', '现在', '当时', '然后', '于是',
                 '接着', '继续', '因为', '但是', '只见', '只是', '原来',
                 '起来', '下来', '上去', '进去', '出来', '过去', '过来',
                 '之后', '之前', '以后', '过后', '的时候'}
    return word in narrative

STOPWORDS = {
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

def extract(text, action_verbs):
    candidates = []
    # Pattern 1: labels
    for match in re.finditer(r'(?:主角|主要人物|人物|角色)[:：]\s*([^\n]+)', text):
        candidates.extend(re.findall(r'[一-鿿]{2,4}', match.group(1)))
    # Pattern 2: name lists with 、or ，
    for match in re.finditer(r'[一-鿿]{2,4}(?:[一-鿿]{2,4}|[、，]\s*[一-鿿]{2,4})+', text):
        candidates.extend(re.findall(r'[一-鿿]{2,4}', match.group(0)))
    # Pattern 3: name before action
    name_action_pattern = (
        r'(?<![一-鿿])([一-鿿]{2,4})\s*'
        r'(?:' + '|'.join(action_verbs) + r')'
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))
    # Pattern 4: sentence-initial name (tight: only 2-char, filtered)
    for match in re.finditer(r'(?:^|[。！？\n])\s*([一-鿿]{2})(?:[，。！？\s]|$)', text):
        candidate = match.group(1)
        if not _looks_like_narrative(candidate):
            candidates.append(candidate)

    seen = set()
    names = []
    for c in candidates:
        if c in STOPWORDS or c in seen:
            continue
        seen.add(c)
        names.append(c)
    return names

chapter_text = (
    "流萤车站 的风在夜色里慢慢压低，魏北辰 握着断裂玉牌，听见远处传来断续的钟声。"
    "秦知 说，事情不会只停在表面。温微 没有立刻回答，只把断裂玉牌 推到桌边。"
    "沈珩 从阴影里看着他们。"
)

# Test A: OLD verbs (original code)
old_verbs = ['握着','说','低声道','道','问','答','没有','从','提醒','看着','率','与','和','同','向']
r_old = extract(chapter_text, old_verbs)
print(f"OLD verbs: {r_old}")
print(f"  First 4: {r_old[:4]}")

# Test B: NEW verbs only (no 没有/从/率/与/和/同/向)
new_verbs = ['握着','说','低声道','喊道','问道','答道','回答道','说道','提醒','看着','道','问','答','点头','摇头','离开','转身','走进','走了','来了','坐下','站起','挥','拔','举起','放下','推开','关上']
r_new = extract(chapter_text, new_verbs)
print(f"NEW verbs: {r_new}")
print(f"  First 4: {r_new[:4]}")

# Test C: Keep 没有 and 从 but with full filtering
compromise_verbs = ['握着','说','低声道','喊道','问道','答道','回答道','说道','提醒','看着','道','问','答','没有','从','点头','摇头','离开','转身','走进','走了','来了','坐下','站起','挥','拔','举起','放下','推开','关上']
r_comp = extract(chapter_text, compromise_verbs)
print(f"COMPROMISE verbs: {r_comp}")
print(f"  First 4: {r_comp[:4]}")

# Test D: Old verbs + expanded stopwords (just filter better)
r_old_stop = extract(chapter_text, old_verbs)
print(f"OLD verbs + new stopwords: {r_old_stop}")
print(f"  First 4: {r_old_stop[:4]}")

# Now test with NO spaces (realistic novel text)
real_text = (
    "流萤车站的风在夜色里慢慢压低，魏北辰握着断裂玉牌，听见远处传来断续的钟声。"
    "秦知说，事情不会只停在表面。温微没有立刻回答，只把断裂玉牌推到桌边。"
    "沈珩从阴影里看着他们。"
)
print()
print("=== Realistic text (no spaces) ===")
r_real_old = extract(real_text, old_verbs)
print(f"OLD verbs: {r_real_old}")
r_real_new = extract(real_text, new_verbs)
print(f"NEW verbs: {r_real_new}")
r_real_comp = extract(real_text, compromise_verbs)
print(f"COMPROMISE verbs: {r_real_comp}")
