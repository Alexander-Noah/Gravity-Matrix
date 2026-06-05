# Gravity-Matrix Backend

Gravity-Matrix 后端服务负责把 3 个章节以上的小说文本转换为可编辑的结构化剧本 YAML。当前版本先搭建 FastAPI 基础骨架，为后续小说导入、AI 解析、剧本生成、YAML 校验和导出接口做准备。

## 技术栈

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic Settings
- SQLAlchemy
- PyYAML
- Pytest
- SQLite
- OpenAI-compatible 大模型 API 配置
- Ollama 本地兜底配置

## 目录结构

```text
backend/
  app/
    api/
      routes/
        health.py
        projects.py
    core/
      config.py
    db/
      session.py
      init_db.py
    main.py
  docs/
    screenplay-yaml-schema.md
  tests/
    test_health.py
    test_projects.py
  README.md
  requirements.txt
```

## 本地开发

进入后端目录：

```powershell
cd backend
```

创建虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
pip install -r requirements.txt
```

复制环境变量模板：

```powershell
Copy-Item ..\.env.example .\.env
```

启动开发服务：

```powershell
uvicorn app.main:app --reload
```

健康检查接口：

```text
GET http://127.0.0.1:8000/api/v1/health
```

## 测试

```powershell
pytest
```

## 当前接口

- `GET /api/v1/health`：健康检查。
- `POST /api/v1/projects`：创建小说改编项目，至少需要 3 个章节。
- `GET /api/v1/projects/{project_id}`：获取项目详情。
- `POST /api/v1/projects/{project_id}/analysis-jobs`：启动 AI 解析任务。
- `GET /api/v1/projects/{project_id}/analysis`：获取 AI 解析结果。
- `POST /api/v1/projects/{project_id}/script-jobs`：启动剧本生成任务。
- `GET /api/v1/jobs/{job_id}`：查询任务状态。
- `GET /api/v1/projects/{project_id}/script`：获取剧本 YAML。
- `PUT /api/v1/projects/{project_id}/script`：保存作者编辑后的剧本 YAML。
- `POST /api/v1/projects/{project_id}/script/validate`：校验剧本 YAML。
- `GET /api/v1/projects/{project_id}/script/export`：导出剧本 YAML。

如果没有配置大模型 API，后端会使用确定性的演示生成逻辑，保证评委本地可以跑通完整流程。配置 `LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL` 后，后端会优先调用 DeepSeek/OpenAI-compatible Chat Completions，并要求模型返回 JSON 对象，再由后端校验后转成剧本 YAML。模型返回为空、不是合法 JSON 或不符合剧本 Schema 时，会自动回退到确定性演示生成逻辑。

## 配置说明

`.env` 用于本地私密配置，不提交 GitHub。`.env.example` 提供字段模板：

- `APP_NAME`：后端应用名。
- `API_PREFIX`：接口统一前缀，默认 `/api/v1`。
- `DATABASE_URL`：SQLite 数据库地址，后续 PR 使用。
- `FRONTEND_ORIGINS`：允许访问后端的前端地址，默认包含 Vite 本地地址。
- `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`：DeepSeek/OpenAI-compatible 大模型平台配置。
- `OLLAMA_BASE_URL`、`OLLAMA_MODEL`：本地模型兜底配置，后续 PR 使用。
- `MIN_CHAPTERS`：小说最少章节数，比赛要求至少 3 章。

DeepSeek 配置示例：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

## PR 开发节奏

后端按小 PR 分步提交：

1. 搭建 FastAPI 后端骨架。
2. 增加配置、数据库和小说项目存储。
3. 增加小说导入接口。
4. 增加 YAML Schema 文档和校验服务。
5. 增加大模型调用抽象。
6. 增加 AI 解析任务。
7. 增加剧本生成任务。
8. 增加剧本导出接口。

每个 PR 只做一个功能，PR 描述需要包含功能描述、实现思路、测试方式和依赖说明。
