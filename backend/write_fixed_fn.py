# -*- coding: utf-8 -*-
"""Write the fixed _extract_character_names function as a temp file for binary splicing."""

fixed = '''def _extract_character_names(project: Project) -> list[str]:
    text = "\\n".join(chapter.content for chapter in project.chapters)
    candidates: list[str] = []

    for match in re.finditer(r"(?:主角|主要人物|人物|角色)[:：]\s*([^\\n]+)", text):
        candidates.extend(re.findall(r"[\\u4e00-\\u9fff]{2,4}", match.group(1)))

    for match in re.finditer(r"[\\u4e00-\\u9fff]{2,4}(?:[、，]\s*[\\u4e00-\\u9fff]{2,4})+", text):
        candidates.extend(re.findall(r"[\\u4e00-\\u9fff]{2,4}", match.group(0)))

    name_action_pattern = (
        r"(?<![\\u4e00-\\u9fff])([\\u4e00-\\u9fff]{2,4})\\s*"
        r"(?:握着|说|低声道|喊道|问道|答道|回答道|说道|提醒|看着|道|问|答|没有|从|向|点头|摇头|离开|转身|走进|走了|来了|坐下|站起|挥|拔|举起|放下|推开|关上)"
    )
    for match in re.finditer(name_action_pattern, text):
        candidates.append(match.group(1))

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
    seen = set()
    names = []
    for candidate in candidates:
        if candidate in stopwords or candidate in seen:
            continue
        seen.add(candidate)
        names.append(candidate)
    return names

'''

# Write to a temp file
with open('fixed_extract.py', 'w', encoding='utf-8', newline='') as f:
    f.write(fixed)
print('Wrote fixed_extract.py')
