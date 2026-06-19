# 剧本 YAML Schema 说明

Gravity-Matrix 的核心产物是 YAML 剧本。YAML 既方便用户编辑，也方便后端校验、诊断和导出。

## 顶层结构

```yaml
script:
  schema_version: "1.0"
  metadata:
    title: "剧本标题"
    original_novel: "原小说标题"
    author: "作者"
    language: "zh-CN"
    target_format: "screenplay"
    total_chapters: 3

  characters:
    - id: "char_001"
      name: "许七安"
      role: "主角"
      gender: "unknown"
      age: null
      description: "人物简介"

  locations:
    - id: "loc_001"
      name: "京兆府监牢"
      description: "场景地点说明"

  organizations:
    - id: "org_001"
      name: "打更人"
      description: "组织说明"

  chapters:
    - id: "ch_001"
      title: "第一章 牢中苏醒"
      source_chapter_numbers: [1]
      summary: "章节摘要"
      scenes:
        - id: "sc_001_001"
          title: "牢中苏醒"
          location_id: "loc_001"
          time: "day"
          characters: ["char_001"]
          synopsis: "场景概述"
          stage_directions:
            - "动作、镜头或舞台说明"
          dialogue:
            - speaker_id: "char_001"
              speaker_name: "许七安"
              line: "系统？"
              emotion: "试探"

  adaptation_notes:
    themes: ["悬疑", "成长"]
    conflicts: ["主角需要证明清白"]
    omissions: ["省略的支线内容"]
```

## 字段说明

### `script.metadata`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `title` | string | 剧本标题 |
| `original_novel` | string | 原小说标题 |
| `author` | string | 作者或上传者 |
| `language` | string | 默认 `zh-CN` |
| `target_format` | string | 目标格式，如 `screenplay` |
| `total_chapters` | number | 章节数 |

### `characters`

人物列表。场景和对白应通过 `speaker_id` 或 `characters` 引用这里的 ID。

推荐字段：

- `id`
- `name`
- `role`
- `gender`
- `age`
- `description`

### `locations`

地点列表。场景通过 `location_id` 引用。

推荐字段：

- `id`
- `name`
- `description`

### `chapters`

章节列表。每个章节至少包含一个 scene。

推荐字段：

- `id`
- `title`
- `source_chapter_numbers`
- `summary`
- `scenes`

### `scenes`

剧本的核心结构单位。

推荐字段：

- `id`
- `title`
- `location_id`
- `time`
- `characters`
- `synopsis`
- `stage_directions`
- `dialogue`

### `dialogue`

对白列表。

推荐字段：

- `speaker_id`
- `speaker_name`
- `line`
- `emotion`

## 校验规则

后端校验重点：

- 顶层必须包含 `script`。
- `metadata` 必须存在。
- `chapters` 必须是数组。
- 每个章节应至少包含一个场景。
- 场景引用的 `location_id` 应存在于 `locations`。
- 场景引用的人物 ID 应存在于 `characters`。
- 对白的 `speaker_id` 应存在于 `characters`。
- YAML 内容不能超过 `MAX_SCRIPT_YAML_CHARS`。

## 质量诊断

质量诊断不只是检查格式，还会评估：

- 章节和场景是否足够。
- 对白是否过少。
- 场景是否缺少地点、人物或动作说明。
- 人物引用是否混乱。
- 是否存在明显空内容。

前端会把结果展示成：

- 格式正常 / 格式需修正。
- 质量良好 / 建议优化 / 需要修正。

## 设计原因

- YAML 比纯文本更容易校验和导出。
- 独立的 `characters` 和 `locations` 可以避免重复描述。
- `chapters -> scenes -> dialogue` 贴近真实剧本编辑流程。
- `source_chapter_numbers` 保留原小说来源，方便回查。
- `adaptation_notes` 记录改编取舍，方便后续人工调整。
