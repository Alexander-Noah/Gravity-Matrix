# -*- coding: utf-8 -*-
"""Apply character recognition fixes to llm.py."""
import re

target = 'app/services/llm.py'

with open(target, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Strategy: find line indices and replace by index range.
# The original file has stable structure, so we'll replace lines 603-632 (1-based).

new_block = '''    for match in re.finditer(r\"[\\u4e00-\\u9fff]{2,4}(?:[\\u4e00-\\u9fff]{2,4}|[、，]\\s*[\\u4e00-\\u9fff]{2,4})+\", text):
        candidates.extend(re.findall(r\"[\\u4e00-\\u9fff]{2,4}\", match.group(0)))

    name_action_pattern = (
        r\"(?<![\\u4e00-\\u9fff])([\\u4e00-\\u9fff]{2,4})\\s*\"
        r\"(?:握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)\"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))

    for match in re.finditer(r\"(?:^|[\\u3002\\uff01\\uff1f\\n])\\s*([\\u4e00-\\u9fff]{2,4})(?:[\\uff0c\\u3002\\uff01\\uff1f\\s]|$)\", text):
        candidate = match.group(1)
        if not _looks_like_narrative(candidate):
            candidates.append(candidate)

    stopwords = {
        \"\\u5929\\u4e0b\", \"\\u5927\\u52bf\", \"\\u4e1c\\u6c49\", \"\\u671d\\u653f\", \"\\u7fa4\\u96c4\", \"\\u4e71\\u4e16\", \"\\u9ec4\\u5dfe\", \"\\u671d\\u5ef7\", \"\\u8c6a\\u6770\",
        \"\\u56fd\\u5bb6\", \"\\u9ece\\u5eb6\", \"\\u5c0f\\u8bf4\", \"\\u7ae0\\u8282\", \"\\u4e8b\\u60c5\", \"\\u8868\\u9762\", \"\\u7acb\\u523b\", \"\\u4f17\\u4eba\", \"\\u4ed6\\u4eec\",
        \"\\u8fd9\\u91cc\", \"\\u90a3\\u91cc\", \"\\u5ffd\\u7136\", \"\\u7a81\\u7136\", \"\\u5df2\\u7ecf\", \"\\u73b0\\u5728\", \"\\u5f53\\u65f6\", \"\\u4ee5\\u540e\",
        \"\\u4ec0\\u4e48\", \"\\u600e\\u4e48\", \"\\u5982\\u4f55\", \"\\u4e3a\\u4f55\", \"\\u7136\\u540e\", \"\\u4e8e\\u662f\", \"\\u63a5\\u7740\", \"\\u7ee7\\u7eed\",
        \"\\u4e00\\u8d77\", \"\\u4e00\\u4e2a\", \"\\u4e5f\\u662f\", \"\\u56e0\\u4e3a\", \"\\u4f46\\u662f\", \"\\u4e0d\\u8fc7\", \"\\u9762\\u524d\", \"\\u65c1\\u8fb9\", \"\\u5468\\u56f4\",
        \"\\u770b\\u89c1\", \"\\u542c\\u89c1\", \"\\u77e5\\u9053\", \"\\u89c9\\u5f97\", \"\\u60f3\\u5230\", \"\\u611f\\u5230\", \"\\u53d1\\u73b0\", \"\\u660e\\u767d\",
        \"\\u4e00\\u5207\", \"\\u4e00\\u6837\", \"\\u4e00\\u9635\", \"\\u4e00\\u58f0\", \"\\u4e00\\u4e0b\", \"\\u4e00\\u773c\", \"\\u521a\\u624d\", \"\\u8fc7\\u540e\", \"\\u4e0b\\u6765\",
        \"\\u4e0a\\u53bb\", \"\\u8d77\\u6765\", \"\\u8fdb\\u53bb\", \"\\u51fa\\u6765\", \"\\u8fc7\\u53bb\", \"\\u8fc7\\u6765\", \"\\u53ea\\u662f\", \"\\u53ea\\u89c1\",
        \"\\u5e74\\u4ee3\", \"\\u5c81\\u6708\", \"\\u5fc3\\u4e2d\", \"\\u773c\\u91cc\", \"\\u624b\\u4e2d\", \"\\u4e4b\\u4e2d\", \"\\u77ac\\u606f\",
        \"\\u5206\\u4e45\\u5fc5\\u5408\", \"\\u5408\\u4e45\\u5fc5\\u5206\", \"\\u4e09\\u987e\\u8305\\u5e90\",
    }
'''

# Verify the block has correct content before replacing
print("Lines 600-615 currently:")
for i in range(599, 615):
    print(f"  {i+1}: {lines[i].rstrip()}")

# Replace lines 602 through 631 (0-based: 602-631)
# First, let's find the exact range
for i, line in enumerate(lines):
    if 'for match in re.finditer(r"([' + r'一' + '-鿿]{2})、【一' + '-鿿]{2})、【一' + '-鿿]{2})", text):' in line.replace('一-鿿', '').replace('一-鿿', '').replace('一-鿿', ''):
        print(f"Found pattern2 at line {i+1}")

# Since encoding is unreliable, find by index of known patterns
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'for match in re.finditer(r' in line and '、' in line and 'text' in line:
        start_idx = i
    if start_idx is not None and i > start_idx and i <= start_idx + 35:
        if line.strip() == '}' or line.rstrip() == '    }':
            end_idx = i + 1  # inclusive
            break

print(f"start_idx={start_idx}, end_idx={end_idx}")
if start_idx is not None and end_idx is not None:
    for i in range(start_idx, end_idx):
        print(f"  REPLACE {i+1}: {lines[i].rstrip()}")
