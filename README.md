# Gravity-Matrix

Gravity-Matrix 是一个 AI 小说转剧本工作台，用于把长篇小说整理成可编辑、可校验、可导出的结构化剧本草稿。

项目面向小说作者、编剧、短剧团队和内容运营人员，核心流程是：

```text
导入小说 -> 结构化解析 -> 选择生成方式 -> 生成剧本 YAML -> 在线编辑校验 -> 预览与导出
```

## 当前能力

- 支持粘贴小说正文或上传 TXT 文件。
- 至少 3 章内容才能创建项目，后端会做章节识别和导入预检。
- AI 解析按 chunk 调用模型，一次返回人物、地点、组织、事件、对白和冲突，后端负责合并去重。
- 支持 DeepSeek / OpenAI-compatible API，也保留本地确定性 fallback，方便无 Key 演示。
- 生成剧本采用分阶段方式，避免一次性输出超大 JSON。
- YAML 剧本可在线编辑、保存、校验、复制、下载和导出。
- 支持 YAML / TXT / Markdown / PDF 导出。
- 模板中心提供影视剧、短剧、分镜、广播剧、舞台话剧等生成方式。
- 剧本库支持继续编辑、查看预览、导出、重命名、复制和回收站管理。
- 登录注册使用 JWT，本地开发默认 SQLite。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 后端 | FastAPI, Uvicorn, SQLAlchemy, Pydantic Settings |
| 数据库 | SQLite 默认，可切换 MySQL |
| AI 调用 | OpenAI-compatible SDK，推荐 DeepSeek |
| 剧本处理 | PyYAML, 自定义 YAML 校验与导出 |
| 前端 | Vue 3, Vite, Vue Router, Element Plus, Axios |
| 包管理 | npm |

## 目录结构

```text
Gravity-Matrix/
  backend/                 FastAPI 后端
    app/
      api/routes/          接口路由
      core/                配置与安全
      db/                  数据库初始化与连接
      models/              SQLAlchemy 模型
      schemas/             Pydantic 模型
      services/            AI、解析、导出、诊断等业务服务
    docs/                  后端专题说明
    data/                  本地数据库和素材，默认不提交
    requirements.txt
  web/                     Vue 前端
    src/
      api/                 前端请求封装
      components/          页面与弹窗组件
      router/              路由配置
      styles/              页面样式
    package.json
  API.md                   接口总览
  DESIGN.md                UI 与交互规范
  FEATURE_DESCRIPTION.md   功能说明
  PRODUCT.md               产品定义
  VIDEO_DEMO_SCRIPT.md     演示讲解脚本
```

## 本地启动

### 1. 后端

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

接口文档：

```text
http://127.0.0.1:8000/docs
```

### 2. 前端

```powershell
cd web
npm install
npm run dev
```

浏览器打开：

```text
http://localhost:5173
```

## 推荐环境变量

根目录或 `backend/.env` 均可配置，示例见 [.env.example](./.env.example)。

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

如果不配置 `LLM_API_KEY`，后端仍可使用确定性 fallback 跑通演示流程，但输出质量不会等同真实模型。

## 常用命令

| 场景 | 命令 |
| --- | --- |
| 前端开发 | `cd web && npm run dev` |
| 前端构建 | `cd web && npm run build` |
| 后端开发 | `cd backend && python -m uvicorn app.main:app --reload` |
| 后端编译检查 | `cd backend && .\.venv\Scripts\python.exe -m compileall app` |
| 查看 API | 打开 `http://127.0.0.1:8000/docs` |

## 主要页面

| 路由 | 页面 | 用途 |
| --- | --- | --- |
| `/auth` | 登录注册 | 创建账号或登录 |
| `/workbench` | 小说转剧本工作台 | 导入、解析、生成、编辑和导出 |
| `/templates` | 选择剧本生成方式 | 选择影视剧、短剧、分镜等生成方式 |
| `/library` | 剧本库 | 管理草稿、版本、预览和导出 |
| `/help` | 帮助文档 | 查看流程说明和 YAML Schema |

`/novel-to-yaml` 已不再作为主页面使用，会重定向到 `/workbench`。

## 数据与缓存

- `backend/data/` 保存 SQLite 数据库和本地素材，默认不提交。
- `backend/.cache/llm_chunks/` 保存 LLM chunk 缓存，默认不提交。
- `web/dist/` 是前端构建产物，默认不提交。
- `.env` 包含本地密钥，默认不提交。

## 文档索引

- [API.md](./API.md)：接口总览。
- [FEATURE_DESCRIPTION.md](./FEATURE_DESCRIPTION.md)：产品功能说明。
- [PRODUCT.md](./PRODUCT.md)：产品定位和用户场景。
- [DESIGN.md](./DESIGN.md)：界面设计规范。
- [backend/README.md](./backend/README.md)：后端开发说明。
- [web/README.md](./web/README.md)：前端开发说明。
- [backend/docs/screenplay-yaml-schema.md](./backend/docs/screenplay-yaml-schema.md)：剧本 YAML 结构。
- [backend/docs/auth-api.md](./backend/docs/auth-api.md)：认证接口。
