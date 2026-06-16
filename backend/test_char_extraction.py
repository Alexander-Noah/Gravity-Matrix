# -*- coding: utf-8 -*-
import re

def _extract_character_names(text):
    candidates = []

    # Pattern 1: explicit name labels
    for match in re.finditer(r'(?:主角|主要人物|人物|角色)[:：]\s*([^\n]+)', text):
        candidates.extend(re.findall(r'[一-鿿]{2,4}', match.group(1)))

    # Pattern 2: three names separated by 、 (Chinese enumeration comma)
    for match in re.finditer(r'([一-鿿]{2})、([一-鿿]{2})、([一-鿿]{2})', text):
        candidates.extend(match.groups())

    # Pattern 3: name before action words
    name_action_pattern = (
        r'(?<![一-鿿])([一-鿿]{2,4})\s*'
        r'(?:握着|说|低声道|道|问|答|没有|从|提醒|看着|率|与|和|同|向)'
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))

    stopwords = {
        '天下', '大势', '东汉', '朝政', '群雄', '乱世', '黄巾', '朝廷', '豪杰',
        '国家', '黎庶', '小说', '章节', '事情', '表面', '立刻', '众人', '他们',
    }
    seen = set()
    names = []
    for candidate in candidates:
        if candidate in stopwords or candidate in seen:
            continue
        seen.add(candidate)
        names.append(candidate)
    return names


print("=" * 60)
print("BUG 1: functional words as action verbs")
t1 = '从表面看没有立刻回答，事情向着坏方向走了。'
r1 = _extract_character_names(t1)
print(f"  Input: {t1}")
print(f"  Result: {r1}")
print(f"  Expected: []")

print()
print("BUG 2: compound word false matches")
t2 = '他与同僚商议，国家大势从表面看没有改变。'
r2 = _extract_character_names(t2)
print(f"  Input: {t2}")
print(f"  Result: {r2}")
print(f"  Expected: [] or minimal")

print()
print("BUG 3: Three-name 、 pattern misses 2-name or mixed lists")
t3 = '刘备、关羽和张飞一起出发。'
r3 = _extract_character_names(t3)
print(f"  Input: {t3}")
print(f"  Result: {r3}")
print(f"  Expected: ['刘备', '关羽', '张飞']")

print()
print("BUG 4: Two-name list completely missed")
t4 = '刘备、关羽二人结拜。'
r4 = _extract_character_names(t4)
print(f"  Input: {t4}")
print(f"  Result: {r4}")
print(f"  Expected: ['刘备', '关羽']")

print()
print("BUG 5: Good case - names before actions")
t5 = '刘备握着剑，关羽说道：乱世之中。张飞大声回答。'
r5 = _extract_character_names(t5)
print(f"  Input: {t5}")
print(f"  Result: {r5}")
print(f"  Expected: ['刘备', '关羽', '张飞']")

print()
print("BUG 6: Label pattern")
t6 = '主角：刘备，主要人物：关羽、张飞。'
r6 = _extract_character_names(t6)
print(f"  Input: {t6}")
print(f"  Result: {r6}")
print(f"  Expected: ['刘备', '关羽', '张飞']")

print()
print("BUG 7: '率' false match")
t7 = '刘备率大军出征。'
r7 = _extract_character_names(t7)
print(f"  Input: {t7}")
print(f"  Result: {r7}")
print(f"  Expected: ['刘备']")

print()
print("BUG 8: Realistic mixed novel text")
t8 = '''第1章：天下大乱。刘备在桃园中叹息。关羽和张飞走过来。
    刘备说：'天下大势，分久必合。' 关羽问道：'兄长有何打算？'
    张飞回答道：'我们三人结为兄弟！' 从那天起，三人同心协力。
    主要人物：刘备、关羽、张飞。还有其他角色：赵云。'''
r8 = _extract_character_names(t8)
print(f"  Input excerpt: {t8[:80]}...")
print(f"  Result: {r8}")
print(f"  Expected first 3: ['刘备', '关羽', '张飞']")
