# -*- coding: utf-8 -*-
"""Apply character recognition fixes to llm.py using line index replacement."""
import sys

target = 'app/services/llm.py'

with open(target, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Build new content blocks
# Block 1: Add _looks_like_narrative helper before _extract_character_names (before line 597)

helper = '''def _looks_like_narrative(word: str) -> bool:
    """Heuristic to filter out narrative phrases that look like character names."""
    narrative_starters = {"突然", "忽然", "已经", "现在", "当时", "然后", "于是",
                          "接着", "继续", "因为", "但是", "只见", "只是", "原来"}
    narrative_enders = {"起来", "下来", "上去", "进去", "出来", "过去", "过来",
                        "之后", "之前", "以后", "过后", "的时候"}
    if word in narrative_starters or word in narrative_enders:
        return True
    return False


'''

# Insert helper after def _extract_character_names line (around line 596)
# Actually insert before line 596
insert_pos = 594  # 0-based, after the return of _demo_characters
lines = lines[:insert_pos] + [helper] + lines[insert_pos:]

# Now fix the three patterns (lines shifted by 4)
# New start_idx = 602+4 = 606, end_idx = 632+4 = 636

# Build the replacement for the name list pattern (line 603+4 = 607) through stopwords (line 632+4 = 636)
pattern_block = '''    for match in re.finditer(r"[一-鿿]{2,4}(?:[一-鿿]{2,4}|[、，]\s*[一-鿿]{2,4})+", text):
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
        "上去", "起来", "进去", "出来", "过去", "过来", "只是", "只见",
        "年代", "岁月", "心中", "眼里", "手中", "之中", "瞬息",
        "分久必合", "合久必分", "三顾茅庐",
    }
'''

new_start = 602 + 4  # 会计进helper后
new_end = 632 + 4     # inclusive

# Verify the range
print(f"Replacing lines {new_start+1} through {new_end+1}")

# Show current content
print("Current content to replace:")
for i in range(new_start, new_end):
    line = lines[i].rstrip('\n\r')
    # Show without problematic chars
    print(f"  [{i+1}] contains Chinese: {any(0x4e00 <= ord(c) <= 0x9fff for c in line)}")

# Replace
result = lines[:new_start] + [pattern_block] + lines[new_end:]
with open(target, 'w', encoding='utf-8', newline='') as f:
    f.writelines(result)
print("Done writing file")
