# Gravity-Matrix

七牛云 XEngineer 暑期实训营项目：AI 小说转剧本工具。

Gravity-Matrix 面向小说作者和剧本创作者，目标是把 3 个章节以上的小说文本转换为结构化剧本 YAML，让作者快速获得可编辑、可校验、可继续打磨的剧本初稿。

## 项目亮点

- 支持 3 章以上小说输入，符合题目对多章节改编的要求。
- 提供 AI 解析、剧本生成、YAML 校验、编辑保存、质量诊断和导出完整链路。
- 剧本结果使用稳定 YAML Schema，便于前端展示、作者修改和后续扩展。
- 支持 DeepSeek/OpenAI-compatible 大模型接口；未配置 API Key 时自动使用确定性演示逻辑，评委本地也能跑通流程。
- 新增剧本质量诊断能力，可基于 YAML 检查章节、场景、对白、人物使用和改编说明，体现“AI 辅助打磨”而不是只生成文本。

## 作品流程

```text
导入小说文本
  -> AI 解析人物、地点、章节摘要、主题和冲突
  -> 生成结构化剧本 YAML
  -> YAML Schema 校验和质量诊断
  -> 作者编辑保存
  -> 导出 YAML 剧本
```

## 仓库结构

```text
Gravity-Matrix/
  backend/   FastAPI 后端服务，负责小说导入、AI 解析、剧本 YAML 生成、校验、诊断和导出
  web/       Vue 3 + Vite 前端项目，由前端同学维护
```

## 后端说明

后端负责比赛核心能力的落地：把小说章节转成可编辑的结构化剧本 YAML，并保证没有真实大模型配置时也可以完整演示。

### 后端优势

- **完整主链路**：创建项目、AI 分析、剧本生成、读取剧本、保存编辑、校验、质量诊断、导出均已打通。
- **可运行兜底**：未配置 `LLM_API_KEY` 时走 deterministic demo，避免评审环境缺少 Key 导致项目不可运行。
- **真实模型接入**：配置 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 后优先调用 DeepSeek/OpenAI-compatible Chat Completions。
- **Schema 约束**：通过 Pydantic 和 PyYAML 校验剧本结构，保证 YAML 可解析、可引用、可维护。
- **质量诊断**：基于现有剧本 YAML 输出 `score`、`grade`、`summary`、`strengths`、`findings`，帮助作者定位可打磨位置。

### 后端技术栈

- Python
- FastAPI
- SQLAlchemy + SQLite
- Pydantic / Pydantic Settings
- PyYAML
- OpenAI-compatible SDK
- Pytest

### 后端核心接口

- `GET /api/v1/health`：健康检查。
- `GET /api/v1/projects`：分页获取项目列表。
- `POST /api/v1/projects`：创建小说改编项目。
- `GET /api/v1/projects/{project_id}`：获取项目详情。
- `POST /api/v1/projects/{project_id}/analysis-jobs`：启动 AI 解析任务。
- `GET /api/v1/projects/{project_id}/analysis`：读取 AI 分析结果。
- `POST /api/v1/projects/{project_id}/script-jobs`：启动剧本生成任务。
- `GET /api/v1/jobs/{job_id}`：查询任务状态。
- `GET /api/v1/projects/{project_id}/script`：读取剧本 YAML。
- `PUT /api/v1/projects/{project_id}/script`：保存作者编辑后的剧本 YAML。
- `POST /api/v1/projects/{project_id}/script/validate`：校验剧本 YAML。
- `GET /api/v1/projects/{project_id}/script/diagnosis`：诊断已生成剧本质量。
- `POST /api/v1/projects/{project_id}/script/diagnosis`：诊断请求体中的 YAML 草稿。
- `GET /api/v1/projects/{project_id}/script/export`：导出剧本 YAML。

更多后端细节见 [backend/README.md](backend/README.md) 和 [剧本 YAML Schema 文档](backend/docs/screenplay-yaml-schema.md)。

## 前端说明

前端位于 `web/`，技术栈为 Vue 3 + Vite。当前由前端同学维护，后端同学不直接修改前端设计和交互。

### 前端同学补充区

> 这里预留给前端开发同学补充：页面结构、核心交互、运行截图、工作台流程、组件说明、前后端联调方式等内容。

可补充方向：

- 工作台页面与流程步骤说明。
- 小说导入、AI 解析、剧本编辑与导出页面说明。
- 前端本地运行和构建方式。
- 页面截图或演示 GIF。

## 本地运行

### 后端

```powershell
cd backend
D:\Programming\anaconda3\python.exe -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

推荐使用 Python 3.10-3.11；本项目本地验证使用 Python 3.10.20。后端依赖见 `backend/requirements.txt`，推荐运行版本见 `backend/runtime.txt`。

后端默认地址：

```text
http://127.0.0.1:8000
```

健康检查：

```text
GET http://127.0.0.1:8000/api/v1/health
```

### 前端

```powershell
cd web
npm install
npm run dev
```

Vite 默认本地地址通常为：

```text
http://localhost:5173
```

## 配置说明

仓库提供 `.env.example` 作为后端环境变量模板，真实 `.env` 不提交 GitHub。

DeepSeek/OpenAI-compatible 配置示例：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
LLM_TIMEOUT_SECONDS=120
```

如果不配置大模型 API，后端会自动使用 deterministic demo 生成逻辑，仍可完成小说导入、AI 分析、剧本生成、YAML 校验、质量诊断和导出。
该兜底逻辑会尽量从章节文本抽取人物名，并生成场景、舞台说明和多句对白，保证评委没有 API Key 时也能看到完整剧本初稿。

## 测试记录

已在从 GitHub 最新 `main` 重新克隆的干净目录中验证后端：

```text
15 passed
```

无 `.env`、无 API Key 的情况下，比赛主流程冒烟测试通过：

```text
3 章小说 -> AI 分析 -> 剧本 YAML -> YAML 校验 -> 质量诊断 -> YAML 导出
```

测试结果摘要：

```text
analysis_status: succeeded
script_status: succeeded
script_has_yaml: True
valid_yaml: True
diagnosis_valid_schema: True
diagnosis_grade: good
export_status: 200
```

## 协作说明

- 后端开发集中在 `backend/`，前端开发集中在 `web/`。
- 每个功能建议单独开分支、单独提交、单独合并，避免前后端改动混在一个分支里。
- `.env`、数据库文件、缓存文件和本地协作说明不要提交到 GitHub。
