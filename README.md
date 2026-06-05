# Gravity-Matrix

七牛云 XEngineer 暑期实训营项目：AI 小说转剧本工具。

本仓库计划包含：

- `backend/`：FastAPI 后端服务，负责小说导入、AI 解析、YAML 剧本生成、校验和导出。
- `web/`：Vue 3 + Vite 前端项目，由前端同学维护。

## 后端本地运行

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

健康检查：

```text
GET http://127.0.0.1:8000/api/v1/health
```
