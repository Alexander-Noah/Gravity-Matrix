# 剧本 YAML Schema 说明

本文档定义 AI 小说转剧本工具导出的 YAML 结构。Schema 的目标是让作者快速获得可编辑、可校验、可继续打磨的剧本初稿。

## 顶层结构

```yaml
script:
  schema_version: "1.0"
  metadata:
    title: "小说名"
    original_novel: "小说名"
    author: "作者"
    language: "zh-CN"
    target_format: "screenplay"
    total_chapters: 3

  characters:
    - id: "char_001"
      name: "人物名"
      role: "主角"
      gender: "unknown"
      age: null
      description: "人物简介"

  locations:
    - id: "loc_001"
      name: "地点名"
      description: "地点说明"

  chapters:
    - id: "ch_001"
      title: "章节标题"
      source_chapter_numbers: [1]
      summary: "章节摘要"
      scenes:
        - id: "sc_001_001"
          title: "场景标题"
          location_id: "loc_001"
          time: "day"
          characters: ["char_001"]
          synopsis: "场景概述"
          stage_directions:
            - "动作或画面说明"
          dialogue:
            - speaker_id: "char_001"
              speaker_name: "人物名"
              line: "台词"
              emotion: "calm"

  adaptation_notes:
    themes: ["成长", "友情"]
    conflicts: ["主角目标与现实阻碍"]
    omissions: ["被压缩或省略的小说内容"]
```

## 设计原因

- `characters` 独立存放人物，便于前端集中编辑人物设定，也方便多个场景复用同一人物。
- `locations` 独立存放地点，避免每个场景重复写完整地点描述。
- `chapters -> scenes -> dialogue` 贴合剧本创作流程，作者可以按章节和场景逐层修改。
- `source_chapter_numbers` 保留剧本内容来源，方便作者回到原小说检查改编是否偏离原意。
- `adaptation_notes` 记录主题、冲突和删减说明，体现 AI 改编时的创作取舍。
- 使用稳定 `id` 引用人物和地点，前端可以安全地做编辑、校验和导出。

## 校验规则

- 顶层必须包含 `script`。
- `metadata.total_chapters` 必须大于或等于 3。
- 每个章节必须至少包含一个场景。
- 场景引用的 `location_id` 必须存在于 `locations`。
- 场景引用的角色 ID 必须存在于 `characters`。
- 对白的 `speaker_id` 必须存在于 `characters`。
