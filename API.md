# Gravity-Matrix API 文档

本文档描述了 Gravity-Matrix 现有的以及需要后端跟进实现的各类接口规范。

## 基础说明
- **基础路径 (Base URL)**: `http://127.0.0.1:8000/api/v1`
- **数据格式**: 请求与响应默认使用 `application/json`。
- **错误响应**: 当接口抛出错误时，统一返回如下结构：
  ```json
  {
    "detail": "具体的错误信息或原因说明"
  }
  ```

---

## 1. 项目管理相关 (Projects)

### 1.1 创建项目
- **请求方式**: `POST /projects`
- **说明**: 接收用户导入的小说章节，创建一个新的剧本转换项目。
- **请求体 (JSON)**:
  ```json
  {
    "title": "项目名称",
    "author": "创作者",
    "chapters": [
      {
        "title": "章节名称",
        "content": "小说正文"
      }
    ]
  }
  ```
- **响应 (201 Created)**: 返回创建的 `Project` 基础信息（包含 `id`）。

### 1.2 获取项目列表
- **请求方式**: `GET /projects`
- **说明**: 分页获取用户所有的项目。
- **查询参数**: `limit`, `offset`
- **响应 (200 OK)**:
  ```json
  {
    "items": [...],
    "total": 10,
    "limit": 20,
    "offset": 0
  }
  ```

### 1.3 获取项目基础信息 / 就绪状态
- **请求方式**: `GET /projects/{project_id}` / `GET /projects/{project_id}/readiness`
- **说明**: 获取项目的详情或是否准备好导出（包含 `can_export`, `progress` 等）。

### 1.4 【新增预留】删除项目
- **请求方式**: `DELETE /projects/{project_id}`
- **说明**: 根据项目 ID 删除项目及其相关的解析、任务和剧本记录。
- **响应 (200 OK 或 204 No Content)**:
  ```json
  {
    "detail": "项目删除成功"
  }
  ```

---

## 2. 工作台与工作流 (Workbench & Workflow)

### 2.1 获取项目工作台数据
- **请求方式**: `GET /projects/{project_id}/workbench`
- **说明**: 返回前端恢复工作台所需的各类结构数据（解析记录、YAML、项目元数据等）。
- **响应 (200 OK)**:
  ```json
  {
    "project": {...},
    "analysis": {...},
    "script": {...}
  }
  ```

### 2.2 【新增预留】保存生成配置
- **请求方式**: `POST /projects/{project_id}/generation-settings`
- **说明**: 用户在 AI 解析后，弹窗选择的生成偏好配置，需要通过该接口持久化到后端。
- **请求体 (JSON)**:
  ```json
  {
    "scriptType": "影视剧",
    "adaptationStyle": "原汁原味",
    "contentOptions": ["保留内心独白", "增加动作细节"]
  }
  ```
- **响应 (200 OK)**: 返回保存成功的状态。

### 2.3 启动剧本生成任务 / 解析任务
- **请求方式**:
  - `POST /projects/{project_id}/script-jobs` (启动 YAML 剧本生成)
  - `POST /projects/{project_id}/analysis-jobs` (启动小说结构解析)
- **说明**: 触发服务端的长耗时任务。
- **响应 (200 OK)**: 返回 `Job` 对象，包含任务的 `id`，前端通过此 `id` 轮询进度。

### 2.4 【新增预留】重新解析项目
- **请求方式**: `POST /projects/{project_id}/analysis-jobs/rerun`
- **说明**: 清除该项目之前产生的 `analysis_json` 和 `script_yaml` 等衍生数据，并重新触发一个 `analysis` 类型的 Job。
- **响应 (200 OK)**: 返回新的 `Job` 对象以供前端轮询。

---

## 3. 剧本编辑与导出 (Script & Export)

### 3.1 获取 / 保存 剧本草稿
- **请求方式**:
  - `GET /projects/{project_id}/script` (获取最新的剧本内容)
  - `PUT /projects/{project_id}/script` (前端手动修改 YAML 后同步到后端)
- **请求体 (PUT)**:
  ```json
  {
    "yaml": "script:\n  chapters:\n    ..."
  }
  ```

### 3.2 诊断与校验 YAML
- **请求方式**:
  - `POST /projects/{project_id}/script/validate` (结构和语法校验)
  - `POST /projects/{project_id}/script/diagnosis` (业务级诊断)
- **说明**: 对前端修改后的 YAML 进行规则检查，返回详细的错误日志或等级打分。

### 3.3 【新增预留】保存单场景草稿
- **请求方式**: `POST /projects/{project_id}/scenes`
- **说明**: 将前端侧面板新增的场景片段 (`sceneDraft`) 附加或合并到服务端的 `script_yaml` 中。
- **请求体 (JSON)**:
  ```json
  {
    "sceneTitle": "新场景",
    "sceneLocation": "室内",
    "sceneTime": "白天",
    "sceneAction": "动作描写..."
  }
  ```

### 3.4 【新增预留】导出为纯文本和 Markdown
- **请求方式**:
  - `GET /projects/{project_id}/script/export/markdown`
  - `GET /projects/{project_id}/script/export/txt`
- **说明**: 将服务端存储的剧本结构转换为 Markdown 或纯 TXT 格式，返回二进制文件流 (`Blob`) 供浏览器下载。
- **响应头**: 必须设置 `Content-Disposition: attachment; filename="..."` 及合适的 `Content-Type`。
