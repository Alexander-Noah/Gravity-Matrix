#!/usr/bin/env python3
"""Fix llm.py character extraction by writing the replacement code to a .py file
that llm.py imports, then byte-patch llm.py."""

import codecs

# Read the original file
# with open('app/services/llm.py', 'r', encoding='utf-8') as f:
#    lines = f.readlines()
with codecs.open('app/services/llm.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find the range: from line containing 'for match in re.finditer(r' with chinese comma
# to the closing } of stopwords
start = None
stopwords_end = None
for i, line in enumerate(lines):
    stripped = line.strip()
    if start is None and 'for match in re.finditer' in line and 'text):' in line:
        start = i
    ts = stripped
    if start is not None and i > start and (ts == '}' or (ts.startswith('"') and ts.endswith(',') and i > start + 20)):
        # check if this looks like the end of stopwords set
        if '}' in ts:
            stopwords_end = i
            break

# More robust: find the end by looking for the closing brace of stopwords
if start is not None:
    brace_depth = 0
    in_set = False
    for i in range(start, len(lines)):
        line = lines[i]
        if '{' in line:
            brace_depth += line.count('{')
            in_set = True
        if '}' in line:
            brace_depth -= line.count('}')
            if in_set and brace_depth == 0:
                stopwords_end = i
                break

print(f"Start at line {start+1}, stopwords end at line {stopwords_end+1}")

# Write the replacement block to a temp file
replacement = '''    for match in re.finditer(r"[\\u4e00-\\u9fff]{2,4}(?:[\\u4e00-\\u9fff]{2,4}|[\\u3001\\uff0c]\\s*[\\u4e00-\\u9fff]{2,4})+", text):
        candidates.extend(re.findall(r"[\\u4e00-\\u9fff]{2,4}", match.group(0)))

    name_action_pattern = (
        r"(?<![\\u4e00-\\u9fff])([\\u4e00-\\u9fff]{2,4})\\s*"
        r"(?:\\u63e1\\u7740|\\u8bf4|\\u4f4e\\u58f0\\u9053|\\u558a\\u9053|\\u95ee\\u9053|\\u7b54\\u9053|\\u56de\\u7b54\\u9053|\\u8bf4\\u9053|\\u63d0\\u9192|\\u770b\\u7740|\\u9053|\\u95ee|\\u7b54|\\u70b9\\u5934|\\u6447\\u5934|\\u79bb\\u5f00|\\u8f6c\\u8eab|\\u8d70\\u8fdb|\\u8d70\\u4e86|\\u6765\\u4e86|\\u5750\\u4e0b|\\u7ad9\\u8d77|\\u6325|\\u62d4|\\u4e3e\\u8d77|\\u653e\\u4e0b|\\u63a8\\u5f00|\\u5173\\u4e0a)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))

    for match in re.finditer(r"(?:^|[\\u3002\\uff01\\uff1f\\n])\\s*([\\u4e00-\\u9fff]{2,4})(?:[\\uff0c\\u3002\\uff01\\uff1f\\s]|$)", text):
        candidate = match.group(1)
        if not _looks_like_narrative(candidate):
            candidates.append(candidate)

    stopwords = {
        "\\u5929\\u4e0b", "\\u5927\\u52bf", "\\u4e1c\\u6c49", "\\u671d\\u653f", "\\u7fa4\\u96c4", "\\u4e71\\u4e16", "\\u9ec4\\u5dfe", "\\u671d\\u5ef7", "\\u8c6a\\u6770",
        "\\u56fd\\u5bb6", "\\u9ece\\u5eb6", "\\u5c0f\\u8bf4", "\\u7ae0\\u8282", "\\u4e8b\\u60c5", "\\u8868\\u9762", "\\u7acb\\u523b", "\\u4f17\\u4eba", "\\u4ed6\\u4eec",
        "\\u8fd9\\u91cc", "\\u90a3\\u91cc", "\\u5ffd\\u7136", "\\u7a81\\u7136", "\\u5df2\\u7ecf", "\\u73b0\\u5728", "\\u5f53\\u65f6", "\\u4ee5\\u540e",
        "\\u4ec0\\u4e48", "\\u600e\\u4e48", "\\u5982\\u4f55", "\\u4e3a\\u4f55", "\\u7136\\u540e", "\\u4e8e\\u662f", "\\u63a5\\u7740", "\\u7ee7\\u7eed",
        "\\u4e00\\u8d77", "\\u4e00\\u4e2a", "\\u4e5f\\u662f", "\\u56e0\\u4e3a", "\\u4f46\\u662f", "\\u4e0d\\u8fc7", "\\u9762\\u524d", "\\u65c1\\u8fb9", "\\u5468\\u56f4",
        "\\u770b\\u89c1", "\\u542c\\u89c1", "\\u77e5\\u9053", "\\u89c9\\u5f97", "\\u60f3\\u5230", "\\u611f\\u5230", "\\u53d1\\u73b0", "\\u660e\\u767d",
        "\\u4e00\\u5207", "\\u4e00\\u6837", "\\u4e00\\u9635", "\\u4e00\\u58f0", "\\u4e00\\u4e0b", "\\u4e00\\u773c", "\\u521a\\u624d", "\\u8fc7\\u540e", "\\u4e0b\\u6765",
        "\\u4e0a\\u53bb", "\\u8d77\\u6765", "\\u8fdb\\u53bb", "\\u51fa\\u6765", "\\u8fc7\\u53bb", "\\u8fc7\\u6765", "\\u53ea\\u662f", "\\u53ea\\u89c1",
        "\\u5e74\\u4ee3", "\\u5c81\\u6708", "\\u5fc3\\u4e2d", "\\u773c\\u91cc", "\\u624b\\u4e2d", "\\u4e4b\\u4e2d", "\\u77ac\\u606f",
        "\\u5206\\u4e45\\u5fc5\\u5408", "\\u5408\\u4e45\\u5fc5\\u5206", "\\u4e09\\u987e\\u8305\\u5e90",
    }
'''

with codecs.open('replacement_block.txt', 'w', 'utf-8') as f:
    f.write(replacement)
print("Wrote replacement block to replacement_block.txt")
