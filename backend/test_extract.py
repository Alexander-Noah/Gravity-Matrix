#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

def _looks_like_narrative(word):
    narrative = {'突然', '忽然', '已经', '现在', '当时', '然后', '于是',
                 '接着', '继续', '因为', '但是', '只见', '只是', '原来',
                 '起来', '下来', '上去', '进去', '出来', '过去', '过来',
                 '之后', '之前', '以后', '过后', '的时候'}
    return word in narrative

def extract(text):
    candidates = []
    for match in re.finditer(r'(?:主角|主要人物|人物|角色)[:：]\s*([^
]+)', text):
        candidates.extend(re.findall(r'[一-鿿]{2,4}', match.group(1)))
    for match in re.finditer(r'[一-鿿]{2,4}(?:[一-鿿]{2,4}|[、，]\s*[一-鿿]{2,4})+', text):
        candidates.extend(re.findall(r'[一-鿿]{2,4}', match.group(0)))
    name_action_pattern = (
        r'(?<![一-鿿])([一-鿿]{2,4})\s*'
        r'(?:握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)'
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))
    for match in re.finditer(r'(?:^|[。！？
])\s*([一-鿿]{2,4})(?:[，。！？\s]|$)', text):
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

# Run tests
tests = []
t1 = '刘备握着剑，关羽说道：乱世之中。张飞大声回答。'
tests.append(('Action pattern', t1, ['刘备', '关羽', '张飞']))
t2 = '从表面看没有立刻回答，事情向着坏方向走了。'
tests.append(('No false from func', t2, []))
t3 = '刘备、关羽二人结拜。'
tests.append(('2-name list', t3, ['刘备', '关羽']))
t4 = '刘备、关羽和张飞一起出发。'
tests.append(('Mixed list', t4, ['刘备', '关羽', '张飞']))
t5 = '主角：刘备，主要人物：关羽、张飞。'
tests.append(('Labels', t5, ['刘备', '关羽', '张飞']))
t6 = '第1章：天下大乱。刘备在桃园中叹息。关羽和张飞走过来。'
tests.append(('Novel text', t6, ['刘备', '关羽', '张飞', '桃园']))

passed = 0
failed = 0
for name, text, expected in tests:
    got = extract(text)
    ok = all(e in got for e in expected)
    if expected:
        ok = all(e in got for e in expected)
    else:
        # expect no real names (can have spurious very short items)
        ok = len([g for g in got if g not in stopwords]) == 0 or all(len(g) > 4 for g in got)
    status = 'PASS' if ok else 'FAIL'
    if ok: passed += 1
    else: failed += 1
    print(f'[{status}] {name}')
    print(f'  Got: {got}')
    print(f'  Expected: {expected}')
    print()

print(f'{passed} passed, {failed} failed')
