# Gravity-Matrix

AI 小说转剧本工具 —— 将 3 章以上小说文本自动转换为结构化 YAML 剧本初稿。

面向小说作者、编剧和内容创作者，提供从小说导入、AI 解析、模板选择、剧本生成、在线编辑、校验诊断到多格式导出的完整创作链路。

## 项目亮点

- 支持 3 章以上小说输入，自动识别章节结构。
- 完整创作链路：导入 → AI 解析 → 模板选择 → 剧本生成 → 编辑校验 → 导出。
- 剧本使用结构化 YAML Schema，支持校验、质量诊断和多格式导出（YAML / TXT / Markdown）。
- 5 种剧本模板：影视剧、短剧、话剧、分镜剧本、广播剧。
- 支持 DeepSeek / OpenAI-compatible 大模型；未配置 API Key 时使用确定性演示逻辑，本地也能跑通完整流程。
- JWT 认证体系：注册、登录、会话管理。
- 回收站机制：软删除、恢复、清空。

## 作品流程

```
导入小说 → AI 解析人物/场景/事件 → 选择剧本模板 → 生成 YAML 剧本 → 在线编辑校验 → 质量诊断 → 导出
```

## 仓库结构

```
Gravity-Matrix/
  backend/   FastAPI 后端 — 小说导入、AI 解析、剧本生成、校验、诊断、导出、认证
  web/       Vue 3 + Vite 前端 — 工作台、模板中心、剧本库、帮助文档
  data/      本地小说素材库
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | MySQL（PyMySQL），兼容 SQLite |
| ORM | SQLAlchemy |
| 数据校验 | Pydantic / Pydantic Settings |
| 剧本处理 | PyYAML |
| 认证 | JWT（python-jose）+ bcrypt |
| AI 调用 | OpenAI-compatible SDK |
| 前端 | Vue 3 + Vite + Vue Router + Axios |
| 测试 | Pytest |

## 本地运行

### 前置环境

| 工具 | 版本要求 | 检查命令 |
|---|---|---|
| Python | 3.10 - 3.11 | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

> Python 3.14 不推荐：SQLAlchemy 当前锁定版本可能遇到类型兼容问题。
>
> 数据库默认使用 **SQLite**，无需额外安装。如果想用 MySQL，见文末「可选：切换 MySQL」。

---

### 第一步：克隆项目并进入目录

```powershell
git clone <repo-url> Gravity-Matrix
cd Gravity-Matrix
```

---

### 第二步：启动后端

打开 **PowerShell** 终端（不是 CMD），进入 `backend` 目录：

```powershell
cd backend
```

**2.1 创建 Python 虚拟环境（仅首次需要）：**

```powershell
python -m venv .venv
```

**2.2 激活虚拟环境：**

```powershell
.\.venv\Scripts\Activate.ps1
```

激活成功后终端前会显示 `(.venv)`。如果遇到执行策略错误，先执行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**2.3 安装依赖：**

```powershell
pip install -r requirements.txt
```

**2.4 启动服务：**

```powershell
uvicorn app.main:app --reload
```

首次启动时后端会自动在 `backend/data/` 目录下创建 SQLite 数据库文件 `gravity_matrix.db`，无需手动建库。

**2.5 验证后端是否启动成功：**

新开一个终端，执行：

```powershell
curl http://127.0.0.1:8000/api/v1/health
```

返回 `{"status":"ok"}` 即表示成功。

也可以浏览器打开自动生成的 API 文档：

```
http://127.0.0.1:8000/docs
```

---

### 第三步：启动前端

新开一个终端，进入 `web` 目录：

```powershell
cd web
```

**4.1 安装依赖（仅首次需要）：**

```powershell
npm install
```

**4.2 启动开发服务器：**

```powershell
npm run dev
```

启动后终端会显示本地地址，通常是：

```
http://localhost:5173
```

浏览器打开这个地址即可进入产品。

---

### 第四步：注册账号并体验

1. 浏览器打开 `http://localhost:5173`，会自动跳转到登录注册页 `/auth`。
2. 点击「注册」，填写用户名、邮箱和密码（≥6 位），点击「创建账号」。
3. 注册成功后自动进入工作台 `/workbench`。
4. 在导入页粘贴小说正文（至少 3 章，用「第X章」标记章节标题），点击「下一步」即可走完完整流程。

> 数据库在 `backend/data/test_novels_by_book/` 目录下预置了小说素材，这些素材会出现在剧本库中，可以一键导入工作台。

---

### 关闭与重启

- 后端：在运行 uvicorn 的终端按 `Ctrl+C` 停止。
- 前端：在运行 vite 的终端按 `Ctrl+C` 停止。
- 重新启动：分别执行「第二步 2.2 → 2.4」和「第三步 3.2」即可（不需要重新安装依赖和创建虚拟环境）。
- 数据库数据在 `backend/data/gravity_matrix.db` 中持久保存，重启不会丢失。

---

### 可选：切换 MySQL

如果团队协作或生产环境需要 MySQL，按以下步骤切换：

**1. 安装 MySQL 8.0+ 并创建数据库：**

```sql
CREATE DATABASE gravity_matrix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**2. 安装 Python MySQL 驱动：**

```powershell
pip install pymysql
```

**3. 修改 `backend/.env` 中的数据库连接串：**

```env
DATABASE_URL=mysql+pymysql://用户名:密码@127.0.0.1:3306/gravity_matrix
```

**4. 重启后端：**

```powershell
uvicorn app.main:app --reload
```

后端会自动在 MySQL 中创建所有需要的表。已有的 SQLite 数据不会自动迁移，需要手动转移或用 API 重新导入。详细配置见 `.env.example`。

---

### 常见问题

**Q: 激活虚拟环境报错「无法加载文件」？**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新执行 `.\\.venv\\Scripts\\Activate.ps1`。

**Q: 启动后端报「ModuleNotFoundError: No module named 'app'」？**

确认当前在 `backend/` 目录下，且虚拟环境已激活（终端前有 `(.venv)` 标识）。

**Q: 前端页面打开但接口请求失败？**

确认后端已在另一个终端中运行，且 `http://127.0.0.1:8000/api/v1/health` 能正常返回。

**Q: 注册时报「该邮箱已注册」？**

该邮箱已注册过，切换到「登录」标签页用同一邮箱和密码登录即可。

**Q: 数据库连接失败？**

默认使用 SQLite，不需要额外配置。如果切换了 MySQL，请检查 MySQL 是否运行中、`.env` 中 `DATABASE_URL` 的用户名和密码是否正确。

## 配置说明

以下配置均可选——不创建 `.env` 文件也能直接启动，后端使用 SQLite 数据库和确定性演示逻辑。如需自定义，参考下表：

| 字段 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/gravity_matrix.db` | 数据库连接串，MySQL 格式见上方「可选：切换 MySQL」 |
| `JWT_SECRET_KEY` | 内置开发密钥 | 生产部署时务必修改 |
| `JWT_EXPIRE_MINUTES` | `1440`（24h） | Token 过期时间 |
| `LLM_API_KEY` | 无 | 配置后调用真实大模型，不配则用确定性演示逻辑 |
| `LLM_BASE_URL` | 无 | API 地址，DeepSeek 示例：`https://api.deepseek.com` |
| `LLM_MODEL` | 无 | 模型名，示例：`deepseek-v4-flash` |

DeepSeek 配置示例（写入 `backend/.env`）：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

不配置 LLM 时，后端自动从章节文本抽取人物名，生成场景、舞台说明和多句对白，保证无 API Key 也能完整演示。

## 页面与路由

| 路由 | 页面 | 说明 |
|---|---|---|
| `/auth` | 登录注册 | 注册账号或登录，JWT 认证 |
| `/workbench` | 工作台 | 导入小说 → AI 解析 → 生成剧本 → 编辑导出 |
| `/templates` | 模板中心 | 选择影视剧/短剧/话剧/分镜/广播剧模板 |
| `/library` | 剧本库 | 管理已生成剧本，编辑/预览/导出/重命名/复制 |
| `/help` | 帮助文档 | Schema 说明、字段定义、设计原因、FAQ |

## 核心接口

### 认证
- `POST /api/v1/auth/register` — 注册
- `POST /api/v1/auth/login` — 登录
- `GET /api/v1/auth/me` — 获取当前用户

### 主流程
- `POST /api/v1/import/preview` — 小说导入预检
- `POST /api/v1/projects` — 创建项目
- `POST /api/v1/projects/{id}/analysis-jobs` — 启动 AI 解析
- `GET /api/v1/jobs/{id}` — 轮询任务状态
- `POST /api/v1/projects/{id}/script-jobs` — 启动剧本生成
- `GET /api/v1/projects/{id}/script` — 获取剧本 YAML
- `GET /api/v1/projects/{id}/workbench` — 工作台聚合数据

### 编辑与导出
- `PUT /api/v1/projects/{id}/script` — 保存编辑后剧本
- `POST /api/v1/projects/{id}/script/validate` — YAML 校验
- `POST /api/v1/projects/{id}/script/diagnosis` — 质量诊断
- `GET /api/v1/projects/{id}/script/export` — 导出 YAML
- `GET /api/v1/projects/{id}/script/export/txt` — 导出 TXT
- `GET /api/v1/projects/{id}/script/export/markdown` — 导出 Markdown

### 项目管理
- `GET /api/v1/projects` — 分页列表
- `GET /api/v1/projects/dashboard` — 看板数据
- `PATCH /api/v1/projects/{id}` — 重命名
- `POST /api/v1/projects/{id}/clone` — 克隆
- `DELETE /api/v1/projects/{id}` — 移入回收站
- `POST /api/v1/projects/{id}/restore` — 恢复
- `GET /api/v1/projects/recycle-bin` — 回收站列表
- `DELETE /api/v1/projects/recycle-bin` — 清空回收站

完整接口文档见 [API.md](API.md)，后端细节见 [backend/README.md](backend/README.md)，前端细节见 [web/README.md](web/README.md)。

## 测试

```powershell
cd backend
pytest
```

当前 46 个测试通过，覆盖项目创建、导入预检、分析任务、剧本生成、校验、诊断、导出、回收站、模板中心全链路。
