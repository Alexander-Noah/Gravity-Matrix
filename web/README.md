# Gravity-Matrix Web

AI 小说转剧本工具前端，基于 Vue 3 + Vite。本文档给后端同学用于本地启动、接口联调和确认前端当前请求约定。

## 技术栈

- Vue 3
- Vite
- Vue Router
- Axios

## 本地启动

进入前端目录：

```powershell
cd C:\Users\zhibi\Desktop\Gravity-Matrix\web
```

安装依赖：

```powershell
npm install
```

启动开发服务：

```powershell
npm run dev
```

默认访问：

```text
http://localhost:5173
```

构建检查：

```powershell
npm run build
```

## 后端接口地址配置

前端统一使用 `src/api/http.js` 中的 axios 实例。

默认接口地址：

```text
http://127.0.0.1:8000/api/v1
```

如果后端地址不同，请在 `web` 目录新增 `.env.local`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

修改后需要重启 `npm run dev`。

## 鉴权约定

登录或注册成功后，前端会保存：

| localStorage key | 说明 |
| --- | --- |
| `gm_auth_token` | 后端返回的 token |
| `gm_auth_user` | 后端返回的用户信息 JSON |

后续 axios 请求会自动携带：

```http
Authorization: Bearer <token>
```

退出登录时会清理这两个 localStorage key。

> 当前后端主流程尚未实现真实账号数据库和 `/auth/*` 路由。前端在检测到认证路由不存在时，会创建本地演示会话，避免比赛演示被登录页阻断。企业级版本应补真实用户表、密码哈希、Token 签发和鉴权中间件。

## 认证接口

### 注册

```http
POST /auth/register
```

请求体：

```json
{
  "name": "林默",
  "email": "creator@example.com",
  "password": "123456"
}
```

期望响应：

```json
{
  "access_token": "token-string",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "林默",
    "email": "creator@example.com"
  }
}
```

### 登录

```http
POST /auth/login
```

请求体：

```json
{
  "email": "creator@example.com",
  "password": "123456"
}
```

期望响应同注册接口。

### 当前用户

```http
GET /auth/me
Authorization: Bearer <token>
```

期望响应：

```json
{
  "id": 1,
  "name": "林默",
  "email": "creator@example.com"
}
```

## 工作台接口

前端工作台 API 封装在 `src/api/workbench.js`。

### 项目列表

```http
GET /projects?limit=20&offset=0
```

前端“我的项目”页面进入时会调用该接口，并把返回的 `items` 映射为项目卡片、顶部统计和最近编辑记录。

期望响应：

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

项目卡片会使用 `id`、`title`、`author`、`status`、`chapter_count`、`has_analysis`、`has_script`、`updated_at` 字段。点击“打开项目”后，前端会继续调用 `/projects/{project_id}/workbench` 同步工作台状态。

### 导入预检

```http
POST /import/preview
```

请求体：

```json
{
  "title": "chapter_demo",
  "author": "创作者",
  "text": "第1章 ...\n正文..."
}
```

响应会返回 `chapter_count`、`can_create_project`、`issues` 和 `chapters`。每个章节必须包含 `title`、`content`、`char_count`、`excerpt`，前端创建项目时会直接使用 `chapters[].content`。

### 项目看板数据

```http
GET /projects/dashboard
```

前端“我的项目”页面使用该接口读取统计卡片、项目卡片和最近活动。接口失败时页面显示空状态和错误提示，不再回退到本地 mock 项目。

### 剧本库数据

```http
GET /scripts/library
```

前端“剧本库”页面使用该接口展示已生成剧本。条目需包含 `project_id`、`title`、`sourceNovel`、`type`、`chapters`、`scenes`、`dialogues`、`schemaStatus`、`status`、`updatedAt`、`tags`。

### 创建项目

```http
POST /projects
```

请求体：

```json
{
  "title": "星辰之下",
  "author": "创作者",
  "chapters": [
    {
      "title": "第一章 初入城市",
      "content": "章节正文..."
    }
  ]
}
```

前端要求至少识别出 3 个章节后才允许继续。

### 启动 AI 解析任务

```http
POST /projects/{project_id}/analysis-jobs
```

期望响应：

```json
{
  "id": 1,
  "project_id": 1,
  "type": "analysis",
  "status": "queued",
  "progress": 0,
  "current_step": "等待开始",
  "result_id": null,
  "error_message": null
}
```

### 查询任务状态

```http
GET /jobs/{job_id}
```

前端会根据 `status` 判断任务是否完成。

常用状态：

| status | 说明 |
| --- | --- |
| `queued` | 排队中 |
| `running` | 执行中 |
| `succeeded` | 成功 |
| `failed` | 失败 |

### 获取 AI 解析结果

```http
GET /projects/{project_id}/analysis
```

期望响应：

```json
{
  "project_id": 1,
  "analysis": {
    "characters": [],
    "locations": [],
    "chapter_summaries": [],
    "themes": [],
    "conflicts": []
  }
}
```

### 获取工作台聚合数据

```http
GET /projects/{project_id}/workbench
```

用于一次性获取项目状态、流程步骤、分析概览和剧本结构。

### 启动剧本生成任务

```http
POST /projects/{project_id}/script-jobs
```

前端在“生成设置”弹窗确认后调用该接口。当前后端接口不接收生成设置请求体，前端会先在本地保存设置，再按项目当前 AI 解析结果启动剧本生成任务。

### 生成设置

```http
POST /projects/{project_id}/generation-settings
```

当前后端只做兼容接收，不落库，不影响生成逻辑。企业级版本可将模板、风格、内容选项持久化并传给 LLM prompt。

### 获取剧本 YAML

```http
GET /projects/{project_id}/script
```

期望响应：

```json
{
  "project_id": 1,
  "yaml": "script:\n  metadata:\n    title: ..."
}
```

前端会把 `yaml` 转换为编辑器行结构，并使用 `/workbench` 返回的 `script.structure` 更新章节/场景树。

### 校验 YAML

```http
POST /projects/{project_id}/script/validate
```

请求体：

```json
{
  "yaml": "script:\n  metadata:\n    title: ..."
}
```

期望响应：

```json
{
  "valid": true,
  "errors": []
}
```

### 诊断 YAML 草稿

```http
POST /projects/{project_id}/script/diagnosis
```

前端在点击“校验格式”时会同时调用校验和诊断接口，并把 `summary.chapter_count`、`summary.scene_count`、`valid_schema`、`grade` 映射到右侧 Schema 校验面板。

### 前端兼容操作接口

```http
GET /templates
PATCH /projects/{project_id}
POST /projects/{project_id}/clone
POST /projects/{project_id}/analysis-jobs/rerun
POST /projects/{project_id}/scenes
GET /projects/{project_id}/script/export/txt
GET /projects/{project_id}/script/export/markdown
DELETE /projects/{project_id}
```

这些接口用于模板中心、项目重命名、复制为新版本、重新解析、添加场景、导出和删除等页面操作。

## 前端路由

| 路径 | 说明 |
| --- | --- |
| `/auth` | 登录注册页 |
| `/workbench` | 小说转剧本工作台 |
| `/projects` | 我的项目 |
| `/templates` | 模板中心 |
| `/library` | 剧本库 |
| `/help` | 帮助文档 |
| `/profile` | 重定向到工作台，个人中心通过顶部创作者菜单弹窗打开 |

## 后端联调检查清单

1. 后端启动在 `http://127.0.0.1:8000`。
2. 后端统一前缀为 `/api/v1`。
3. CORS 允许 `http://localhost:5173` 和 `http://127.0.0.1:5173`。
4. 登录和注册响应需要返回 `access_token` 或 `token`。
5. 登录和注册响应建议返回 `user` 对象，至少包含 `id`、`name`、`email`。
6. 需要鉴权的接口请支持 `Authorization: Bearer <token>`。
7. 错误响应推荐使用 FastAPI 默认结构：

```json
{
  "detail": "错误说明"
}
```

前端会优先展示 `detail` 字段。
