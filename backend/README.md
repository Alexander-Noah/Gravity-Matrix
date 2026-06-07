# Gravity-Matrix Backend

FastAPI 后端服务，负责小说导入、AI 解析、剧本 YAML 生成、在线编辑、Schema 校验、质量诊断、多格式导出和用户认证。

## 环境要求

- Python 3.10-3.11
- 数据库默认 **SQLite**（零配置启动），可选 MySQL
- 依赖见 `requirements.txt`

## 技术栈

- FastAPI + Uvicorn
- SQLAlchemy（SQLite / MySQL）
- Pydantic / Pydantic Settings
- PyYAML
- python-jose + bcrypt（JWT 认证）
- OpenAI-compatible SDK
- Pytest

## 目录结构

```
backend/
  app/
    api/
      deps.py                  # 认证依赖注入
      routes/
        auth.py                # 注册/登录/个人中心
        health.py              # 健康检查
        projects.py            # 全部业务接口
    core/
      config.py                # 配置（环境变量 + 默认值）
      security.py              # bcrypt 密码哈希 + JWT 签发/解析
    db/
      session.py               # 数据库连接（SQLite/MySQL 自适应）
      init_db.py               # 自动建表 + 列补全
    models/
      __init__.py
      project.py               # Project / Chapter / Job / AppSetting
      user.py                  # User（id, name, email, password_hash）
    schemas/
      auth.py                  # 注册/登录/用户/个人中心响应模型
      project.py               # 请求与响应模型
      screenplay.py            # 剧本 YAML Schema（Pydantic 校验）
    services/
      frontend_data.py         # 导入预检、看板、剧本库、个人中心数据
      jobs.py                  # 分析与生成任务调度
      llm.py                   # 大模型调用 + 确定性 fallback
      screenplay_yaml.py       # YAML 结构校验
      script_diagnosis.py      # 剧本质量诊断
      script_export.py         # TXT / Markdown 格式导出
      workbench.py             # 工作台聚合数据
    main.py                    # 应用入口
  data/
    test_novels_by_book/       # 本地小说素材（剧本库可导入）
  docs/
    auth-api.md                # 认证接口文档
    screenplay-yaml-schema.md  # YAML Schema 文档
  tests/
    test_health.py
    test_llm.py
    test_projects.py
  requirements.txt
  runtime.txt
```

## 快速启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

首次启动自动在 `data/` 下创建 SQLite 数据库和所有表。

健康检查：`GET http://127.0.0.1:8000/api/v1/health`

API 文档：`http://127.0.0.1:8000/docs`

## 配置

无需 `.env` 也能启动（默认 SQLite + 确定性演示逻辑）。如需自定义，在 `backend/` 下创建 `.env`：

| 字段 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/gravity_matrix.db` | 数据库连接串 |
| `JWT_SECRET_KEY` | 内置开发密钥 | 生产务必修改 |
| `JWT_ALGORITHM` | `HS256` | JWT 签名算法 |
| `JWT_EXPIRE_MINUTES` | `1440` | Token 24h 过期 |
| `LLM_PROVIDER` | `openai_compatible` | 大模型提供商 |
| `LLM_API_KEY` | 无 | API 密钥 |
| `LLM_BASE_URL` | 无 | API 地址 |
| `LLM_MODEL` | 无 | 模型名 |
| `LLM_TIMEOUT_SECONDS` | `120` | API 超时 |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama 地址 |
| `OLLAMA_MODEL` | `qwen3:4b` | Ollama 模型 |
| `MIN_CHAPTERS` | `3` | 最少章节数 |
| `MAX_CHAPTERS` | `30` | 最多章节数 |
| `MAX_CHAPTER_CHARS` | `20000` | 单章最大字符 |
| `MAX_SCRIPT_YAML_CHARS` | `1000000` | YAML 最大字符 |

## 切换 MySQL

1. 创建数据库：`CREATE DATABASE gravity_matrix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
2. 在 `backend/.env` 中设置：`DATABASE_URL=mysql+pymysql://用户:密码@127.0.0.1:3306/gravity_matrix`
3. 重启后端即可自动建表。

## 接口列表

### 认证
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/auth/register` | 注册（name, email, password ≥6位） |
| POST | `/auth/login` | 登录（email, password） |
| GET | `/auth/me` | 获取当前用户（需 Bearer token） |
| GET | `/profile/summary` | 个人中心概览（项目数、模板、剧本状态等） |

### 主流程
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/import/preview` | 小说导入预检，识别章节 |
| POST | `/projects` | 创建项目 |
| GET | `/projects` | 分页列表（limit, offset） |
| GET | `/projects/dashboard` | 看板：统计 + 项目卡片 + 活动 |
| GET | `/projects/{id}` | 项目详情（含章节） |
| GET | `/projects/{id}/readiness` | 下一步操作指引 |
| GET | `/projects/{id}/workbench` | 工作台聚合数据 |
| POST | `/projects/{id}/analysis-jobs` | 启动 AI 解析 |
| POST | `/projects/{id}/analysis-jobs/rerun` | 重新解析 |
| GET | `/projects/{id}/analysis` | 获取解析结果 |
| POST | `/projects/{id}/script-jobs` | 启动剧本生成 |
| POST | `/projects/{id}/script-jobs/rerun` | 重新生成剧本 |
| GET | `/jobs/{job_id}` | 轮询任务状态 |

### 编辑与导出
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/projects/{id}/script` | 获取剧本 YAML |
| PUT | `/projects/{id}/script` | 保存编辑后的剧本 |
| POST | `/projects/{id}/script/validate` | YAML 结构校验 |
| GET | `/projects/{id}/script/diagnosis` | 诊断已存剧本 |
| POST | `/projects/{id}/script/diagnosis` | 诊断请求体 YAML 草稿 |
| POST | `/projects/{id}/scenes` | 添加单个场景 |
| GET | `/projects/{id}/script/export` | 导出 YAML |
| GET | `/projects/{id}/script/export/txt` | 导出 TXT |
| GET | `/projects/{id}/script/export/markdown` | 导出 Markdown |
| GET | `/projects/{id}/script/export/pdf` | 导出 PDF |

### 项目管理
| 方法 | 路径 | 说明 |
|---|---|---|
| PATCH | `/projects/{id}` | 重命名 |
| POST | `/projects/{id}/clone` | 克隆项目 |
| POST | `/projects/{id}/generation-settings` | 保存生成配置 |
| DELETE | `/projects/{id}` | 软删除到回收站 |
| POST | `/projects/{id}/restore` | 从回收站恢复 |
| GET | `/projects/recycle-bin` | 回收站列表 |
| DELETE | `/projects/recycle-bin` | 清空回收站 |

### 模板与素材
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/templates` | 模板列表（支持 q 和 target_format 筛选） |
| GET | `/templates/{id}` | 模板详情 |
| GET | `/templates/default` | 当前默认模板 |
| PUT | `/templates/default` | 设置默认模板 |
| GET | `/scripts/library` | 剧本库（已生成剧本 + 本地素材） |
| POST | `/scripts/library/sources/{id}/import` | 导入本地素材为项目 |

## AI 调用与兜底

配置 LLM API Key 后优先调用真实大模型，要求返回 JSON 再由后端校验转为 YAML。未配置时使用确定性演示逻辑：正则抽取人物名，为每章生成场景、舞台说明和多句对白。模型返回异常时自动回退。

## 质量诊断

基于现有 YAML Schema 输出 `score`（0-100）、`grade`（A/B/C/D）、`summary`（章节数/场景数/对白数/问题数）、`strengths`、`findings`，帮助定位需打磨之处。不额外调用大模型。

## 认证

- 注册/登录返回 `access_token`（JWT，24h）+ `user`（id, name, email）。
- 密码 bcrypt 哈希存储。
- 当前业务接口暂未强制鉴权，后续可通过 `get_current_user` 依赖保护。

## 测试

```powershell
pytest
```

46 个测试通过。
