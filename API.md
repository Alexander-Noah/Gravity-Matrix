# Gravity-Matrix 全量接口文档 (前端对接后端)

本文档结合了后端最新的真实路由表与前端所需交互，旨在提供整个 Gravity-Matrix 项目最权威的接口规范。

## 基础约定
- **Base URL**: `http://127.0.0.1:8000/api/v1`
- **数据格式**: 默认使用 `application/json`（导出与导入除外）

---

## 1. 核心流程接口 (已实现)

### 1.1 小说导入预检
- **请求方式**: `POST /import/preview`
- **说明**: 接收用户上传或粘贴的纯文本，由后端完成章节解析与前置校验。
- **请求体 (JSON)**:
  ```json
  {
    "title": "三国演义",
    "author": "罗贯中",
    "text": "第一章 ...\n第二章 ..."
  }
  ```
- **响应重点字段**:
  ```json
  {
    "chapter_count": 3,
    "can_create_project": true,
    "chapters": [ { "number": 1, "title": "...", "excerpt": "..." } ]
  }
  ```

### 1.2 创建项目
- **请求方式**: `POST /projects`
- **说明**: 将确认后的章节列表传入，正式生成项目实体。

### 1.3 启动/查询 AI 分析任务
- **启动分析**: `POST /projects/{project_id}/analysis-jobs`
- **轮询任务**: `GET /jobs/{job_id}`
- **获取解析结果**: `GET /projects/{project_id}/analysis`

### 1.4 启动/查询剧本生成
- **启动生成**: `POST /projects/{project_id}/script-jobs`
- **轮询任务**: `GET /jobs/{job_id}`
- **获取生成好的剧本**: `GET /projects/{project_id}/script`

### 1.5 工作台全量状态聚合
- **请求方式**: `GET /projects/{project_id}/workbench`
- **说明**: 一次性拿到当前项目所有基础信息、结构、YAML和诊断结果，用于恢复编辑器界面。

---

## 2. 剧本校验与诊断接口 (已实现)

- **初步校验**: `POST /projects/{project_id}/script/validate`
- **质量诊断 (前端草稿)**: `POST /projects/{project_id}/script/diagnosis`
- **质量诊断 (已存库剧本)**: `GET /projects/{project_id}/script/diagnosis`
- **全量保存草稿**: `PUT /projects/{project_id}/script`
- **直接导出YAML附件**: `GET /projects/{project_id}/script/export`

---

## 3. 大盘聚合页面数据 (已实现)

### 3.1 我的项目页仪表盘
- **请求方式**: `GET /projects/dashboard`
- **说明**: 后端直出当前用户的项目总览统计卡片、项目列表及近期动态活动。

### 3.2 剧本库列表数据
- **请求方式**: `GET /scripts/library`
- **说明**: 获取有剧本的项目专用的统计状态与所有剧本条目，供剧本库页面展示。

### 3.3 常规分页项目列表
- **请求方式**: `GET /projects`
- **说明**: 支持带 `limit` 和 `offset` 的标准分页。

---

## 4. 认证模块 (Auth) — 已实现

### 4.1 注册
- `POST /auth/register`：注册新账号，密码 bcrypt 哈希存储。
  - 请求体：`{ "name": "林默", "email": "creator@example.com", "password": "123456" }`
  - 响应：`{ "access_token": "...", "token_type": "bearer", "user": { "id": 1, "name": "林默", "email": "creator@example.com" } }`
  - 邮箱重复时返回 409。

### 4.2 登录
- `POST /auth/login`：验证邮箱和密码，返回 JWT token。
  - 请求体：`{ "email": "creator@example.com", "password": "123456" }`
  - 验证失败返回 401。

### 4.3 获取当前用户
- `GET /auth/me`：需要 `Authorization: Bearer <token>`，返回 `{ "id": 1, "name": "林默", "email": "creator@example.com" }`。

### 4.4 个人中心概览
- `GET /profile/summary`：需要 `Authorization: Bearer <token>`，返回当前用户的创作概览。
  - 响应包含 `user`（个人信息）和 `stats`（工作区名、当前项目、进度、流程步骤、所选模板、剧本状态、剧本库数量、Schema 状态）。

---

## 5. 项目管理二次操作 — 已实现

### 5.1 回收站
- `DELETE /projects/{id}`：软删除，项目移入回收站（deleted_at 标记）。
- `GET /projects/recycle-bin`：获取回收站列表，返回 `items` 和 `total`。
- `POST /projects/{id}/restore`：恢复项目，deleted_at 置空。
- `DELETE /projects/recycle-bin`：清空回收站，永久删除。

### 5.2 项目操作
- `PATCH /projects/{id}`：重命名项目或修改作者。请求体：`{ "title": "新名称" }`。
- `POST /projects/{id}/clone`：克隆项目（含章节和分析结果）。

### 5.3 模板管理
- `GET /templates`：获取所有剧本模板，支持 `q` 关键词和 `target_format` 筛选。
- `GET /templates/{template_id}`：获取单个模板详情和 YAML 示例。
- `GET /templates/default`：获取当前默认模板。
- `PUT /templates/default`：设置默认模板，请求体 `{ "templateId": "short-drama" }`。

### 5.4 高级操作
- `POST /projects/{id}/generation-settings`：保存生成配置（templateId、scriptType、adaptationStyle、contentOptions）。
- `POST /projects/{id}/analysis-jobs/rerun`：重新解析。
- `POST /projects/{id}/script-jobs/rerun`：重新生成剧本。
- `POST /projects/{id}/scenes`：添加单个场景。
  - 请求体：`{ "chapterTitle": "...", "sceneTitle": "...", "location": "...", "time": "...", "characters": "...", "action": "..." }`
  - 响应返回更新后的 YAML 和场景 ID。

### 5.5 多格式导出
- `GET /projects/{id}/script/export`：导出 YAML（`application/x-yaml`）。
- `GET /projects/{id}/script/export/txt`：导出纯文本剧本。
- `GET /projects/{id}/script/export/markdown`：导出 Markdown。
- `GET /projects/{id}/script/export/pdf`：导出 PDF（`application/pdf`）。

---

## 6. 待补齐 (后续迭代)

- **Docx 等文件上传**：当前仅支持 TXT 或直接粘贴文本。
- **业务接口鉴权**：当前项目 CRUD 接口未强制校验 JWT，后续可通过 get_current_user 依赖保护。
