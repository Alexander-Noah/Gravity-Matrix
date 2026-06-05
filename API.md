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

## 4. 待补齐的边缘功能与暂无接口预留 (待实现)

后端同学已明确以下功能暂不提供或接不上，属于后续迭代范畴，前端需增加 mock 或特定页面状态流转：

### 4.1 认证模块 (Auth)
- `POST /auth/register`、`POST /auth/login`、`GET /auth/me` **当前后端全部没有路由**。
- **应对方案**：前端可直接绕过或允许在无 `Authorization` 头时使用 mock session。

### 4.2 高级文档导入
- **Docx 等文件上传**：当前无后端接口，前端只应允许上传 TXT 或直接粘贴，随后转字符串喂给 `POST /import/preview`。

### 4.3 基础模板数据获取
- `GET /templates`：获取可用剧本模板（当前前端退化为本地默认变量）。

### 4.4 项目管理二次操作
- `DELETE /projects/{id}`：删除项目。
- `PATCH /projects/{id}`：重命名项目。
- `POST /projects/{id}/clone`：克隆项目。

### 4.5 高级生成与多格式导出
- `POST /projects/{id}/generation-settings`：保存用户剧本生成时的配置偏好。
- `POST /projects/{id}/analysis-jobs/rerun`：覆盖原分析并重跑大模型。
- `POST /projects/{id}/scenes`：添加右侧单场景编辑入库。
- `GET /projects/{id}/script/export/markdown`、`/txt`：导出特定格式附件。
