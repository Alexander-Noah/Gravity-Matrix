# Gravity-Matrix Backend

后端服务负责小说导入、AI 解析、剧本 YAML 生成、在线编辑保存、Schema 校验、质量诊断、多格式导出和用户认证。

## 环境要求

- Python 3.10-3.11
- 数据库默认使用 SQLite（无需安装，启动即用）。可选切换 MySQL，见项目根目录 README。
- 依赖见 `requirements.txt`

## 技术栈

- FastAPI + Uvicorn
- SQLAlchemy（MySQL + PyMySQL / SQLite）
- Pydantic / Pydantic Settings
- PyYAML（剧本解析与生成）
- python-jose + bcrypt（JWT 认证）
- OpenAI-compatible SDK（AI 调用，可选）
- Pytest

## 目录结构

```
backend/
  app/
    api/
      deps.py           # 认证依赖（get_current_user）
      routes/
        auth.py          # 注册、登录、获取当前用户
        health.py        # 健康检查
        projects.py      # 所有业务接口
    core/
      config.py          # 应用配置（环境变量 + 默认值）
      security.py        # 密码哈希 + JWT 签发/解析
    db/
      session.py         # 数据库连接与会话管理
      init_db.py         # 自动建表
    models/
      __init__.py
      project.py         # Project / Chapter / Job / AppSetting
      user.py            # User
    schemas/
      auth.py            # 注册/登录/用户响应
      project.py         # 请求与响应模型
      screenplay.py      # 剧本 YAML Schema（Pydantic 校验）
    services/
      frontend_data.py   # 导入预检、看板、剧本库数据构建
      jobs.py            # 分析与生成任务调度
      llm.py             # 大模型调用 + 确定性 fallback
      screenplay_yaml.py # YAML 结构校验
      script_diagnosis.py # 剧本质量诊断
      script_export.py   # TXT / Markdown 格式导出
      workbench.py       # 工作台聚合数据
    main.py              # 应用入口
  data/
    test_novels_by_book/ # 本地小说素材（剧本库可导入）
  docs/
    auth-api.md          # 认证接口文档
    screenplay-yaml-schema.md # YAML Schema 文档
  tests/                 # Pytest 测试
  requirements.txt
  runtime.txt
```

## 本地开发

### 1. 数据库准备

```sql
CREATE DATABASE gravity_matrix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 安装与启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

创建 `.env` 文件（可从项目根目录的 `.env.example` 复制），按需修改数据库连接：

```env
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/gravity_matrix
```

启动：

```powershell
uvicorn app.main:app --reload
```

### 3. 使用 SQLite

修改 `.env`：

```env
DATABASE_URL=sqlite:///./data/gravity_matrix.db
```

无需额外安装数据库服务。

### 4. 健康检查

```
GET http://127.0.0.1:8000/api/v1/health
```

API 文档：`http://127.0.0.1:8000/docs`

## 配置说明

`.env` 支持的完整字段（带默认值）：

| 字段 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://root:root@127.0.0.1:3306/gravity_matrix` | 数据库连接串 |
| `JWT_SECRET_KEY` | 内置开发密钥 | 生产环境务必修改 |
| `JWT_ALGORITHM` | `HS256` | JWT 签名算法 |
| `JWT_EXPIRE_MINUTES` | `1440`（24h） | Token 过期时间 |
| `LLM_PROVIDER` | `openai_compatible` | 大模型提供商 |
| `LLM_API_KEY` | 无 | API 密钥，不配则走确定性演示逻辑 |
| `LLM_BASE_URL` | 无 | API 地址 |
| `LLM_MODEL` | 无 | 模型名称 |
| `LLM_TIMEOUT_SECONDS` | `120` | API 超时 |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama 本地地址 |
| `OLLAMA_MODEL` | `qwen3:4b` | Ollama 本地模型 |
| `MIN_CHAPTERS` | `3` | 最少章节数 |
| `MAX_CHAPTERS` | `30` | 最多章节数 |
| `MAX_CHAPTER_CHARS` | `20000` | 单章最大字符数 |
| `MAX_SCRIPT_YAML_CHARS` | `1000000` | YAML 最大字符数 |

## 认证体系

后端实现了完整的 JWT 认证：

- 密码使用 bcrypt 哈希存储，不存明文。
- 注册/登录成功后返回 `access_token`（JWT，24h 过期）和 `user` 对象。
- 需要鉴权的接口通过 `Authorization: Bearer <token>` 访问。
- `GET /auth/me` 返回当前登录用户信息。

当前业务接口（项目 CRUD、生成任务等）暂未强制鉴权，后续可通过 `get_current_user` 依赖注入保护。

## AI 调用与兜底

配置 LLM 后，后端优先调用 DeepSeek / OpenAI-compatible Chat Completions，要求模型返回 JSON 对象，再由后端校验后转为剧本 YAML。

未配置 LLM 时，自动使用确定性演示逻辑：从章节文本正则抽取人物名，为每章生成场景、舞台说明和多句对白，保证无 API Key 也能看到完整剧本结构。

模型返回为空、非法 JSON 或不符合 Schema 时，自动回退。

## 质量诊断

诊断接口不额外调用大模型，基于现有 YAML Schema 和剧本结构输出 `score`（0-100）、`grade`（A/B/C/D）、`summary`（章节数/场景数/对白数/问题数）、`strengths` 和 `findings`，方便作者定位需打磨之处。

## 测试

```powershell
pytest
```

## 测试数据种子

可通过后端 API 正常走完导入→创建→分析→生成流程来产生数据，也可以直接操作数据库插入测试项目——scripts/library 接口会扫描 `data/test_novels_by_book/` 目录下的小说素材作为可导入条目。
