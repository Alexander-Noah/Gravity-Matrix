# Gravity-Matrix 全量接口文档

本文档描述了 Gravity-Matrix 整个项目的前后端 API 接口情况。为了清晰反映目前的工程进度，文档被划分为两大部分：**第一部分**记录了后端已通过 FastAPI 真实实现的接口；**第二部分**记录了前端已在 UI 逻辑中调用，但后端暂时【待实现】的缺失接口。

## 基础约定
- **Base URL**: `http://127.0.0.1:8000/api/v1`
- **内容类型**: 默认使用 `application/json`。

---

## 第一部分：后端已实现的真实接口 (Implemented)

### 1. 系统状态
- **GET /health**
  健康检查接口。返回 `{"status": "ok"}`。

### 2. 项目管理 (Projects)
- **GET /projects**
  获取项目列表（支持 `limit` 和 `offset` 分页）。
- **POST /projects**
  创建项目。入参: `{ title, author, chapters: [{title, content}] }`。
- **GET /projects/{project_id}**
  获取项目基础信息及章节列表。
- **GET /projects/{project_id}/workbench**
  获取项目工作台详情（聚合项目信息、解析结果、YAML剧本）。
- **GET /projects/{project_id}/readiness**
  检查项目就绪状态（是否可解析、是否可生成剧本、是否可导出）。

### 3. 工作流任务 (Jobs & Analysis)
- **GET /jobs/{job_id}**
  轮询查询任务（AI 解析、剧本生成）进度和详情。
- **POST /projects/{project_id}/analysis-jobs**
  异步启动 AI 小说解析任务，返回对应的 Job 信息。
- **GET /projects/{project_id}/analysis**
  获取项目完整的 AI 解析 JSON 结果。
- **POST /projects/{project_id}/script-jobs**
  异步启动大模型剧本生成任务，返回对应的 Job 信息。

### 4. 剧本编辑与校验 (Scripting)
- **GET /projects/{project_id}/script**
  获取项目已生成的剧本 YAML 内容。
- **PUT /projects/{project_id}/script**
  全量保存修改后的剧本 YAML 草稿。
- **POST /projects/{project_id}/script/validate**
  对传入的剧本 YAML 进行结构与语法初步校验。
- **GET /projects/{project_id}/script/diagnosis**
  针对**已存库**的剧本 YAML 进行深度业务逻辑与规则诊断。
- **POST /projects/{project_id}/script/diagnosis**
  针对**前端草稿**的剧本 YAML 进行深度业务逻辑与规则诊断。
- **GET /projects/{project_id}/script/export**
  将数据库中已生成的剧本 YAML 文件以附件流（`application/x-yaml`）的形式导出下载。

---

## 第二部分：前端已调用但后端【待实现】的预留接口 (To Be Implemented)

此部分为前端已写好 Axios 请求，但后端 Python 尚未编写对应的路由逻辑。**开发后续需补齐。**

### 1. 认证与用户模块 (Auth)
- **POST /auth/register**：用户注册。
- **POST /auth/login**：用户登录。
- **GET /auth/me**：获取当前登录用户信息。

### 2. 模板中心 (Templates)
- **GET /templates**：获取系统默认的剧本格式模板列表（如影视剧、短剧等）。前端目前带有本地数据兜底机制。

### 3. 项目管理高级操作 (Project Operations)
- **PATCH /projects/{project_id}**：修改项目元数据（如重命名）。
- **DELETE /projects/{project_id}**：彻底删除该项目及其关联的所有任务、解析与剧本。
- **POST /projects/{project_id}/clone**：复制项目为全新版本，包含剧本内容。

### 4. 工作台与任务控制 (Workbench Extensions)
- **POST /projects/{project_id}/generation-settings**：持久化保存用户生成剧本时的偏好设置（如文风、选项等）。
- **POST /projects/{project_id}/analysis-jobs/rerun**：清除旧解析缓存并重新触发一次解析 Job。

### 5. 剧本高级编辑与特定导出 (Scripting Extensions)
- **POST /projects/{project_id}/scenes**：追加/保存前端侧边栏新建的单场景片段。
- **GET /projects/{project_id}/script/export/markdown**：将剧本直接导出并下载为 Markdown 格式。
- **GET /projects/{project_id}/script/export/txt**：将剧本直接导出并下载为纯文本 TXT 格式。
