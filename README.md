# Gravity-Matrix

AI 小说转剧本工具 —— 将 3 章以上小说文本自动转换为结构化 YAML 剧本初稿。

面向小说作者、编剧和内容创作者，提供从小说导入、AI 解析、模板选择、剧本生成、在线编辑、校验诊断到多格式导出的完整创作链路。

视频Demo链接：https://www.bilibili.com/video/BV1r5Eb6cEW6/?share_source=copy_web&vd_source=fc4d1d67662ee0db1436153e9cafbda5

## 项目亮点

- 支持 3 章以上小说输入，自动识别章节结构。
- 完整创作链路：导入 → AI 解析 → 模板选择 → 剧本生成 → 编辑校验 → 导出。
- 剧本使用结构化 YAML Schema，支持校验、质量诊断和多格式导出（YAML / TXT / Markdown / PDF）。
- 5 种剧本模板：影视剧、短剧、话剧、分镜剧本、广播剧。
- 支持 DeepSeek / OpenAI-compatible 大模型；未配置 API Key 时自动使用确定性演示逻辑，零配置也能跑通完整流程。
- JWT 认证体系：注册、登录、会话管理、个人中心。
- 回收站机制：软删除、恢复、清空。

## 作品流程

```
导入小说 → AI 解析人物/场景/事件 → 选择剧本模板 → 生成 YAML 剧本 → 在线编辑校验 → 质量诊断 → 导出
```

## 仓库结构

```
Gravity-Matrix/
  backend/     FastAPI 后端 — 小说导入、AI 解析、剧本生成、校验、诊断、导出、认证
  web/         Vue 3 + Vite 前端 — 工作台、模板中心、剧本库、帮助文档
  data/        本地小说素材库
  README.md    本文件
  API.md       全量接口文档
  DESIGN.md    设计规范
  PRODUCT.md   产品定义
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | SQLite（默认），可选 MySQL |
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
> 数据库默认使用 **SQLite**，启动即用，无需额外安装。如需 MySQL，见文末「可选：切换 MySQL」。

---

### 第一步：克隆项目

```powershell
git clone <repo-url> Gravity-Matrix
cd Gravity-Matrix
```

---

### 第二步：启动后端

打开 **PowerShell** 终端，进入 `backend` 目录：

```powershell
cd backend
```

**2.1 创建虚拟环境（仅首次）：**

```powershell
python -m venv .venv
```

**2.2 激活虚拟环境：**

```powershell
.\.venv\Scripts\Activate.ps1
```

> 如报错「无法加载文件」，先执行：`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**2.3 安装依赖（仅首次）：**

```powershell
pip install -r requirements.txt
```

**2.4 启动：**

```powershell
uvicorn app.main:app --reload
```

首次启动自动在 `backend/data/` 下创建 SQLite 数据库。

**2.5 验证：**

```powershell
curl http://127.0.0.1:8000/api/v1/health
# → {"status":"ok"}
```

浏览器打开 `http://127.0.0.1:8000/docs` 可查看自动生成的 API 文档。

---

### 第三步：启动前端

新开一个终端，进入 `web` 目录：

```powershell
cd web
```

**3.1 安装依赖（仅首次）：**

```powershell
npm install
```

**3.2 启动：**

```powershell
npm run dev
```

浏览器打开 `http://localhost:5173`。

---

### 第四步：注册并体验

1. 打开 `http://localhost:5173`，自动跳转登录注册页。
2. 注册：填写用户名、邮箱、密码（≥6 位）。
3. 进入工作台，粘贴小说正文（至少 3 章，用「第X章」标记章节标题）。
4. 按流程提示完成导入 → 解析 → 生成 → 编辑 → 导出。

> `backend/data/test_novels_by_book/` 预置了小说素材，可在剧本库中一键导入工作台。

---

### 关闭与重启

| 操作 | 命令 |
|---|---|
| 停止后端 | 在 uvicorn 终端按 `Ctrl+C` |
| 停止前端 | 在 vite 终端按 `Ctrl+C` |
| 重启后端 | 激活虚拟环境后执行 `uvicorn app.main:app --reload` |
| 重启前端 | `npm run dev` |
| 清除数据库 | 删除 `backend/data/gravity_matrix.db`，重启后端自动重建 |

---

### 可选：切换 MySQL

**1. 安装 MySQL 8.0+ 并创建数据库：**

```sql
CREATE DATABASE gravity_matrix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**2. 在 `backend/` 目录创建 `.env` 文件：**

```env
DATABASE_URL=mysql+pymysql://用户名:密码@127.0.0.1:3306/gravity_matrix
```

**3. 重启后端即自动在 MySQL 中建表。**

---

### 常见问题

**Q: 激活虚拟环境报错「无法加载文件」？**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Q: 启动后端报「No module named 'app'」？**
确认在 `backend/` 目录下，且虚拟环境已激活（终端前有 `(.venv)`）。

**Q: 前端页面打开但接口请求失败？**
确认后端在另一个终端中运行，`curl http://127.0.0.1:8000/api/v1/health` 正常返回。

**Q: 注册时报「该邮箱已注册」？**
用同一邮箱和密码登录，或换一个邮箱注册。

**Q: 数据库连接失败？**
默认 SQLite 无需配置。如切换了 MySQL，检查 MySQL 是否运行、`.env` 中用户名密码是否正确。

## 配置说明

无需 `.env` 也能启动。如需自定义，在 `backend/` 下创建 `.env` 文件：

| 字段 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/gravity_matrix.db` | 数据库连接串 |
| `JWT_SECRET_KEY` | 内置开发密钥 | 生产环境务必修改 |
| `JWT_EXPIRE_MINUTES` | `1440`（24h） | Token 过期时间 |
| `LLM_API_KEY` | 无 | 不配则用确定性演示逻辑 |
| `LLM_BASE_URL` | 无 | DeepSeek 示例：`https://api.deepseek.com` |
| `LLM_MODEL` | 无 | 示例：`deepseek-v4-flash` |


## 页面与路由

| 路由 | 页面 | 说明 |
|---|---|---|
| `/auth` | 登录注册 | 注册账号或登录，JWT 认证 |
| `/workbench` | 工作台 | 导入 → AI 解析 → 生成 → 编辑 → 预览 → 导出 |
| `/templates` | 模板中心 | 5 种剧本模板，选择后可设为默认 |
| `/library` | 剧本库 | 管理已生成剧本，支持编辑/预览/导出/重命名/复制 |
| `/help` | 帮助文档 | YAML Schema 说明、字段定义、设计原因、FAQ |

## 接口总览

### 认证
`POST /auth/register` · `POST /auth/login` · `GET /auth/me` · `GET /profile/summary`

### 主流程
`POST /import/preview` · `POST /projects` · `POST /projects/{id}/analysis-jobs` · `GET /jobs/{id}` · `POST /projects/{id}/script-jobs` · `GET /projects/{id}/script` · `GET /projects/{id}/workbench`

### 编辑与导出
`PUT /projects/{id}/script` · `POST /projects/{id}/script/validate` · `GET/POST /projects/{id}/script/diagnosis` · `GET /projects/{id}/script/export` · `GET /projects/{id}/script/export/txt` · `GET /projects/{id}/script/export/markdown` · `GET /projects/{id}/script/export/pdf`

### 项目管理
`GET /projects` · `GET /projects/dashboard` · `PATCH /projects/{id}` · `POST /projects/{id}/clone` · `DELETE /projects/{id}` · `POST /projects/{id}/restore` · `GET /projects/recycle-bin` · `DELETE /projects/recycle-bin`

### 模板与素材
`GET /templates` · `GET /templates/{id}` · `GET/PUT /templates/default` · `GET /scripts/library` · `POST /scripts/library/sources/{id}/import`

## 测试

```powershell
cd backend
pytest
```
