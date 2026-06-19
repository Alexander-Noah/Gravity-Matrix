# Gravity-Matrix Backend

FastAPI 后端服务，负责认证、项目管理、小说解析、AI 调用、剧本生成、YAML 校验、质量诊断和多格式导出。

## 环境要求

- Python 3.10 - 3.11
- 默认 SQLite，无需额外数据库服务
- 可选 MySQL 8.0+

不推荐 Python 3.14，因为当前依赖组合在本地环境中可能遇到类型兼容问题。

## 快速启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

健康检查：

```powershell
curl http://127.0.0.1:8000/api/v1/health
```

Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

## 目录结构

```text
backend/
  app/
    api/routes/
      auth.py             登录注册和个人中心
      health.py           健康检查
      parse.py            新版结构化解析任务
      projects.py         工作台、项目、模板、剧本库、导出
      novel_scripts.py    旧版 novel-to-yaml 兼容接口
    core/
      config.py           环境变量和默认配置
      security.py         密码哈希和 JWT
    db/
      session.py          数据库连接
      init_db.py          自动建表和轻量迁移
    models/               SQLAlchemy 模型
    schemas/              Pydantic 模型
    services/
      parse_tasks.py      chunk 解析、缓存、并发控制
      llm.py              LLM 调用和剧本生成
      screenplay_yaml.py  YAML 结构校验
      script_diagnosis.py 剧本质量诊断
      script_export.py    TXT / Markdown / PDF 导出
      workbench.py        工作台聚合数据
  docs/                   专题文档
  data/                   SQLite 数据库和本地素材，默认不提交
  requirements.txt
  runtime.txt
```

## 配置

后端会读取根目录 `.env` 和 `backend/.env`。推荐复制根目录 `.env.example` 后修改。

常用配置：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `API_PREFIX` | `/api/v1` | API 前缀 |
| `DATABASE_URL` | `sqlite:///./data/gravity_matrix.db` | 数据库连接 |
| `FRONTEND_ORIGINS` | `localhost:5173` 等 | CORS 白名单 |
| `LLM_PROVIDER` | `openai_compatible` | LLM 提供方 |
| `LLM_BASE_URL` | 空 | DeepSeek 示例：`https://api.deepseek.com/v1` |
| `LLM_MODEL` | 空 | DeepSeek 示例：`deepseek-chat` |
| `LLM_API_KEY` | 空 | API Key |
| `LLM_TIMEOUT_SECONDS` | `120` | LLM 超时 |
| `LLM_MAX_CONCURRENCY` | `2` | chunk 并发数 |
| `LLM_MAX_RETRIES` | `0` | 常规重试次数 |
| `LLM_CHUNK_SIZE` | `3500` | chunk 字符数 |
| `LLM_CHUNK_OVERLAP` | `0` | chunk 重叠字符数 |
| `LLM_ENABLE_CACHE` | `true` | 是否启用 chunk 缓存 |
| `JWT_SECRET_KEY` | 开发默认值 | 生产必须修改 |
| `JWT_EXPIRE_MINUTES` | `1440` | token 有效期 |

## DeepSeek 配置示例

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
LLM_API_KEY=your-deepseek-api-key
LLM_TIMEOUT_SECONDS=180
LLM_MAX_CONCURRENCY=2
LLM_MAX_RETRIES=0
LLM_CHUNK_SIZE=3500
LLM_CHUNK_OVERLAP=0
LLM_ENABLE_CACHE=true
```

如果账户余额不足，后端会直接返回“DeepSeek 账户余额不足，请充值或更换 API Key”，不会把 API 错误文本送进 JSON 解析。

## 数据库

默认 SQLite：

```env
DATABASE_URL=sqlite:///./data/gravity_matrix.db
```

切换 MySQL：

```sql
CREATE DATABASE gravity_matrix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```env
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/gravity_matrix
```

重启后端后会自动建表。

## AI 解析策略

新版解析任务在 `/parse/tasks`：

- 同一个 `project_id` 已有 pending/running 任务时直接返回已有 task。
- 文本按 chunk 处理。
- 每个 chunk 只调用一次 LLM。
- 结果字段包含人物、地点、组织、事件、对白和冲突。
- 后端合并去重。
- chunk 缓存目录为 `backend/.cache/llm_chunks/`。
- 单个 chunk 失败记录到 `failed_chunks`，不让整个任务崩溃。

## 剧本生成策略

剧本生成避免一次性大 JSON：

1. 生成 metadata。
2. 按章节生成 scenes。
3. 后端合并为最终结构。
4. 转为 YAML 保存。

所有模型返回内容都会经过 safe JSON parse 和必要的 JSON 修复提示。

## 常用接口

| 类型 | 路径 |
| --- | --- |
| 健康检查 | `GET /api/v1/health` |
| 注册 | `POST /api/v1/auth/register` |
| 登录 | `POST /api/v1/auth/login` |
| 导入预检 | `POST /api/v1/import/preview` |
| 创建项目 | `POST /api/v1/projects` |
| 新版解析任务 | `POST /api/v1/parse/tasks` |
| 查询任务 | `GET /api/v1/parse/tasks/{task_id}` |
| 获取任务结果 | `GET /api/v1/parse/tasks/{task_id}/result` |
| 剧本生成 | `POST /api/v1/projects/{project_id}/script-jobs` |
| 获取 YAML | `GET /api/v1/projects/{project_id}/script` |
| 保存 YAML | `PUT /api/v1/projects/{project_id}/script` |
| 校验 YAML | `POST /api/v1/projects/{project_id}/script/validate` |
| 剧本库 | `GET /api/v1/scripts/library` |

完整接口见根目录 [API.md](../API.md)。

## 验证

当前仓库不保留完整测试目录。推荐使用：

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app
```

短启动检查：

```powershell
python -m uvicorn app.main:app --reload
```

然后访问：

```text
http://127.0.0.1:8000/api/v1/health
```
