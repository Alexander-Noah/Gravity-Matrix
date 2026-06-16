#!/usr/bin/env python3
"""Apply character recognition fixes to llm.py."""
import sys

target = 'app/services/llm.py'

with open(target, 'rb') as f:
    raw = f.read()

# Encode the Chinese strings we need to match using raw byte patterns
text = raw.decode('utf-8')
lines = text.splitlines(keepends=True)

# Find the exact line indices
name_list_line = -1
action_pattern_start = -1
action_pattern_end = -1
stopwords_start = -1
stopwords_end = -1

for i, line in enumerate(lines):
    # Line has 'for match in re.finditer' AND a Chinese comma sign
    if 'for match in re.finditer(r' in line and 'text):' in line and ('u4e00' in line or '鿿' in line):
        if '[' in line and ']' in line and '(' in line and ')' in line:
            name_list_line = i
            break

for i, line in enumerate(lines):
    if 'name_action_pattern = (' in line:
        action_pattern_start = i
    elif action_pattern_start >= 0 and action_pattern_end < 0 and '    )' in line and i > action_pattern_start:
        action_pattern_end = i
        break

for i, line in enumerate(lines):
    if i > action_pattern_end > 0 and line.strip().startswith('for match in re.finditer(name_action_pattern'):
        # The next line with '    stopwords = {'
        for j in range(i+1, min(i+5, len(lines))):
            if 'stopwords = {' in lines[j]:
                stopwords_start = j
                break
    if stopwords_start >= 0:
        # Find closing } of stopwords dict
        depth = 0
        found_open = False
        for j in range(stopwords_start, min(stopwords_start+25, len(lines))):
            if '{' in lines[j]:
                depth += lines[j].count('{')
                found_open = True
            if '}' in lines[j]:
                depth -= lines[j].count('}')
                if found_open and depth == 0:
                    stopwords_end = j
                    break
        if stopwords_end >= 0:
            break

print(f"name_list_line={name_list_line}, action_start={action_pattern_start}, "
      f"action_end={action_pattern_end}, stopwords_start={stopwords_start}, "
      f"stopwords_end={stopwords_end}")

# Construct replacement
new_name_list = '''    for match in re.finditer(r"[\\u4e00-\\u9fff]{2,4}(?:[\\u4e00-\\u9fff]{2,4}|[\\u3001\\uff0c]\\s*[\\u4e00-\\u9fff]{2,4})+", text):
        candidates.extend(re.findall(r"[\\u4e00-\\u9fff]{2,4}", match.group(0)))

'''

new_action = '''    name_action_pattern = (
        r"(?<![\\u4e00-\\u9fff])([\\u4e00-\\u9fff]{2,4})\\s*"
        r"(?:\\u63e1\\u7740|\\u8bf4|\\u4f4e\\u58f0\\u9053|\\u558a\\u9053|\\u95ee\\u9053|\\u7b54\\u9053|\\u56de\\u7b54\\u9053|\\u8bf4\\u9053|\\u63d0\\u9192|\\u770b\\u7740|\\u9053|\\u95ee|\\u7b54|\\u70b9\\u5934|\\u6447\\u5934|\\u79bb\\u5f00|\\u8f6c\\u8eab|\\u8d70\\u8fdb|\\u8d70\\u4e86|\\u6765\\u4e86|\\u5750\\u4e0b|\\u7ad9\\u8d77|\\u6325|\\u62d4|\\u4e3e\\u8d77|\\u653e\\u4e0b|\\u63a8\\u5f00|\\u5173\\u4e0a)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))

    for match in re.finditer(r"(?:^|[\\u3002\\uff01\\uff1f\\n])\\s*([\\u4e00-\\u9fff]{2,4})(?:[\\uff0c\\u3002\\uff01\\uff1f\\s]|$)", text):
        candidate = match.group(1)
        if not _looks_like_narrative(candidate):
            candidates.append(candidate)

'''

new_stopwords = '''    stopwords = {
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

# Build new file content
if name_list_line >= 0 and stopwords_end >= 0:
    result = (
        lines[:name_list_line] +
        [new_name_list] +
        [new_action] +
        lines[action_pattern_end+2:stopwords_start] +  # the 'for match in re.finditer(name_action_pattern' line
        [new_stopwords] +
        lines[stopwords_end+1:]
    )
    with open(target, 'w', encoding='utf-8', newline='') as f:
        f.writelines(result)
    print("File updated successfully")
else:
    print("ERROR: Could not find all targets")
    sys.exit(1)
