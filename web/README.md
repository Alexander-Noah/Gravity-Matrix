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

## 前端路由

| 路径 | 说明 |
| --- | --- |
| `/auth` | 登录注册页 |
| `/workbench` | 小说转剧本工作台 |
| `/projects` | 我的项目 |
| `/templates` | 模板中心 |
| `/library` | 剧本库 |
| `/help` | 帮助文档 |
| `/profile` | 个人中心占位页 |

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
