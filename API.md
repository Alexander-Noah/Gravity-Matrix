# Gravity-Matrix API 文档

默认后端地址：

```text
http://127.0.0.1:8000/api/v1
```

大多数接口使用 `application/json`。导出接口返回文件流。登录后前端会自动携带：

```http
Authorization: Bearer <access_token>
```

## 1. 健康检查

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 返回 `{ "status": "ok" }` |

## 2. 认证与个人中心

### 注册

```http
POST /auth/register
Content-Type: application/json
```

```json
{
  "name": "创作者",
  "email": "creator@example.com",
  "password": "123456"
}
```

成功返回：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "创作者",
    "email": "creator@example.com"
  }
}
```

### 登录

```http
POST /auth/login
Content-Type: application/json
```

```json
{
  "email": "creator@example.com",
  "password": "123456"
}
```

### 当前用户

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/auth/me` | 获取当前登录用户 |
| GET | `/profile/summary` | 获取个人中心聚合数据 |

## 3. 推荐工作台流程

### 3.1 导入预检

```http
POST /import/preview
Content-Type: application/json
```

```json
{
  "title": "小说标题",
  "author": "作者",
  "text": "第一章 ...\n第二章 ...\n第三章 ..."
}
```

返回重点字段：

```json
{
  "title": "小说标题",
  "chapter_count": 3,
  "can_create_project": true,
  "chapters": [
    {
      "number": 1,
      "title": "第一章",
      "content": "...",
      "excerpt": "..."
    }
  ],
  "preprocess": {
    "characters": [],
    "locations": [],
    "themes": [],
    "conflicts": []
  }
}
```

### 3.2 创建项目

```http
POST /projects
Content-Type: application/json
```

请求体由导入预检结果组装，包含标题、作者、原文和章节列表。成功后返回项目 ID。

### 3.3 结构化解析任务

推荐使用新的 parse task 接口，避免重复任务：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/parse/tasks` | 创建或复用当前项目的解析任务 |
| GET | `/parse/tasks/{task_id}` | 查询任务状态 |
| GET | `/parse/tasks/{task_id}/result` | 获取解析结果 |

兼容路径 `/api/parse/tasks` 仍存在，用于旧前端或旧脚本。

任务状态通常为：

```text
pending -> running -> succeeded
pending -> running -> failed
```

单个 chunk 解析失败不会让整个任务崩溃，后端会记录 `failed_chunks`。

### 3.4 旧版项目解析任务

仍保留以下接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/projects/{project_id}/analysis-jobs` | 启动 AI 解析 |
| POST | `/projects/{project_id}/analysis-jobs/rerun` | 重新解析 |
| GET | `/projects/{project_id}/analysis` | 获取解析结果 |
| GET | `/jobs/{job_id}` | 查询后台任务 |

### 3.5 剧本生成

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/projects/{project_id}/script-jobs` | 启动剧本生成 |
| POST | `/projects/{project_id}/script-jobs/rerun` | 重新生成剧本 |
| GET | `/projects/{project_id}/script` | 获取当前 YAML 剧本 |
| POST | `/projects/{project_id}/generation-settings` | 保存生成偏好 |

后端生成剧本时采用分阶段策略：

1. 生成 metadata、人物、地点、组织等基础信息。
2. 按章节逐章生成 scenes。
3. 后端用 Python 合并为最终 script JSON，再转换为 YAML。

## 4. 工作台聚合接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/projects/{project_id}` | 项目详情 |
| GET | `/projects/{project_id}/readiness` | 下一步可执行状态 |
| GET | `/projects/{project_id}/workbench` | 工作台完整恢复数据 |
| GET | `/projects/dashboard` | 项目看板统计 |

## 5. YAML 编辑、校验和导出

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| PUT | `/projects/{project_id}/script` | 保存当前 YAML |
| POST | `/projects/{project_id}/script/validate` | 校验 YAML 结构 |
| GET | `/projects/{project_id}/script/diagnosis` | 诊断已保存剧本 |
| POST | `/projects/{project_id}/script/diagnosis` | 诊断请求体中的 YAML 草稿 |
| POST | `/projects/{project_id}/scenes` | 追加场景 |
| GET | `/projects/{project_id}/script/export` | 导出 YAML |
| GET | `/projects/{project_id}/script/export/txt` | 导出 TXT |
| GET | `/projects/{project_id}/script/export/markdown` | 导出 Markdown |
| GET | `/projects/{project_id}/script/export/pdf` | 导出 PDF |

保存 YAML 请求示例：

```json
{
  "yaml": "script:\n  schema_version: \"1.0\"\n  ..."
}
```

追加场景请求示例：

```json
{
  "chapterTitle": "第一章",
  "sceneTitle": "密室对峙",
  "location": "书房",
  "time": "夜晚",
  "characters": "主角, 反派",
  "action": "两人在书房中发现关键证据。"
}
```

## 6. 模板中心

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/templates` | 模板列表，支持 `q` 和 `target_format` |
| GET | `/templates/{template_id}` | 模板详情 |
| GET | `/templates/default` | 当前默认模板 |
| PUT | `/templates/default` | 设置默认模板 |

设置默认模板：

```json
{
  "templateId": "tv-drama"
}
```

常见模板：

| templateId | 用户看到的生成方式 |
| --- | --- |
| `tv-drama` | 生成影视剧剧本 |
| `short-drama` | 生成短剧脚本 |
| `storyboard` | 生成分镜脚本 |
| `audio-drama` | 生成广播剧脚本 |
| `stage-play` | 生成舞台话剧 |

## 7. 剧本库与项目管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/scripts/library` | 剧本库列表和统计 |
| POST | `/scripts/library/sources/{source_id}/import` | 导入本地素材为项目 |
| GET | `/projects` | 项目分页列表 |
| PATCH | `/projects/{project_id}` | 重命名或更新项目 |
| POST | `/projects/{project_id}/clone` | 复制项目 |
| DELETE | `/projects/{project_id}` | 移入回收站 |
| GET | `/projects/recycle-bin` | 回收站列表 |
| POST | `/projects/{project_id}/restore` | 恢复项目 |
| DELETE | `/projects/recycle-bin` | 清空回收站 |

## 8. 旧版 novel-to-yaml 兼容接口

以下接口来自早期“小说转 YAML”流程，仍保留兼容：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/novels` | 创建小说 |
| POST | `/novels/{novel_id}/extract-characters` | 抽取人物 |
| PUT | `/novels/{novel_id}/characters` | 保存人物 |
| POST | `/novels/{novel_id}/extract-scenes` | 抽取场景 |
| PUT | `/novels/{novel_id}/scenes` | 保存场景 |
| POST | `/scenes/{scene_id}/generate-content` | 生成场景内容 |
| PUT | `/scenes/{scene_id}/content` | 保存场景内容 |
| POST | `/novels/{novel_id}/generate-yaml` | 生成 YAML |
| PUT | `/scripts/{script_id}` | 保存 YAML |
| GET | `/scripts/{script_id}/download` | 下载 YAML |

当前推荐新功能统一走 `/workbench` 和 `/projects` 工作台流程。

## 9. 错误处理约定

FastAPI 默认错误结构：

```json
{
  "detail": "错误说明"
}
```

AI 调用错误处理：

- `401`、`402`、`403` 不重试。
- `402` 返回余额不足提示：DeepSeek 账户余额不足，请充值或更换 API Key。
- `429` 最多重试 1 次。
- `5xx` 最多重试 1 次。
- API 错误文本不会送入 JSON 解析。

## 10. 开发调试

- Swagger: `http://127.0.0.1:8000/docs`
- 健康检查: `http://127.0.0.1:8000/api/v1/health`
- 前端默认请求前缀: `http://127.0.0.1:8000/api/v1`
