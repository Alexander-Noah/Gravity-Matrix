# 前后端联调说明

本文档记录当前前端与后端的对接约定，方便排查页面数据不刷新、任务重复调用、YAML 保存失败等问题。

## 基础地址

后端默认：

```text
http://127.0.0.1:8000/api/v1
```

前端可在 `web/.env.local` 配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## 当前推荐流程

```text
POST /import/preview
  -> POST /projects
  -> POST /parse/tasks
  -> GET /parse/tasks/{task_id}
  -> GET /parse/tasks/{task_id}/result
  -> POST /projects/{project_id}/script-jobs
  -> GET /jobs/{job_id}
  -> GET /projects/{project_id}/script
  -> PUT /projects/{project_id}/script
  -> POST /projects/{project_id}/script/validate
  -> export
```

## 导入阶段

前端提交：

```json
{
  "title": "小说标题",
  "author": "作者",
  "text": "小说正文"
}
```

后端返回的 `chapters` 应成为创建项目的来源。不要继续使用固定 mock 章节作为真实结果。

## 防止重复解析任务

`POST /parse/tasks` 会检查同一 `project_id` 是否已有 `pending` 或 `running` 任务。

- 有任务：直接返回已有 `task_id`。
- 无任务：创建新任务。

前端点击开始解析后应禁用按钮，直到任务结束或失败。

## AI 解析结果映射

解析结果包含：

- `characters`
- `locations`
- `organizations`
- `events`
- `dialogues`
- `conflicts`
- `failed_chunks`

前端应允许这些数组为空。某个 chunk 失败时，页面应提示有部分内容未解析，而不是直接清空全部结果。

## 剧本生成

剧本生成仍使用项目任务：

```http
POST /projects/{project_id}/script-jobs
GET /jobs/{job_id}
GET /projects/{project_id}/script
```

生成成功后，前端应以 `GET /projects/{project_id}/script` 返回的 `yaml` 作为编辑器内容。

## YAML 编辑

编辑器中的 `yamlContent` 是当前唯一可信文本源：

- 校验格式使用当前 `yamlContent`。
- 保存修改使用当前 `yamlContent`。
- 复制 YAML 使用当前 `yamlContent`。
- 下载 YAML 使用当前 `yamlContent`。

不要再从只读展示区、旧 mock 或生成初始值读取导出内容。

## 剧本库

剧本库数据来自：

```http
GET /scripts/library
```

卡片操作对应：

| 操作 | 接口 |
| --- | --- |
| 继续编辑 | `GET /projects/{id}/workbench` |
| 查看预览 | `GET /projects/{id}/script` |
| 导出 | `/projects/{id}/script/export*` |
| 重命名 | `PATCH /projects/{id}` |
| 复制一份 | `POST /projects/{id}/clone` |
| 移动到回收站 | `DELETE /projects/{id}` |
| 清空回收站 | `DELETE /projects/recycle-bin` |

## 模板中心

模板列表来自：

```http
GET /templates
GET /templates/default
PUT /templates/default
```

前端主界面应展示用户语言，技术字段只放到 Schema 弹窗。

## 常见问题

### 页面仍显示旧内容

检查是否仍从 `web/src/data/workbench.js` 读取 mock 作为真实结果。兜底数据可以保留，但真实接口成功后必须覆盖。

### 解析重复扣费

检查：

- 前端是否重复点击开始解析。
- 后端 `/parse/tasks` 是否收到同一 `project_id`。
- `LLM_ENABLE_CACHE` 是否为 `true`。

### JSON 解析失败

后端会：

- 去掉 Markdown 代码块。
- 提取 `{...}`。
- 记录完整错误。
- 必要时要求模型只修复 JSON 格式。

前端只展示错误摘要和可读提示，不应自行解析模型原始错误。

### API 404

确认前缀是 `/api/v1`。健康检查路径是：

```text
/api/v1/health
```

旧 parse 兼容路径 `/api/parse/tasks` 仍存在，但新代码优先使用 `/api/v1/parse/tasks`。
