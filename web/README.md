# Gravity-Matrix Web

AI 小说转剧本工具前端，基于 Vue 3 + Vite。

## 技术栈

- Vue 3（Composition API）
- Vite
- Vue Router
- Axios
- js-yaml

## 快速启动

```powershell
cd web
npm install
npm run dev
```

默认 `http://localhost:5173`。构建：`npm run build`。

## 目录结构

```
web/
  src/
    api/
      auth.js                    # 注册/登录/获取用户/会话管理
      http.js                    # Axios 实例（baseURL、超时、token 注入）
      workbench.js               # 全部业务接口
    components/
      AddSceneDialog.vue         # 添加场景弹窗
      AiAnalysisPage.vue         # AI 解析结果页
      AppSidebar.vue             # 左侧导航 + 回收站入口
      AuthPage.vue               # 登录注册页
      GenerationSettingsDialog.vue  # 生成设置弹窗
      HelpDocsPage.vue           # 帮助文档页
      NovelImportPage.vue        # 小说导入页
      ProductRoutePage.vue       # 路由占位
      ProfileCenterDialog.vue    # 个人中心弹窗
      SchemaHelpPage.vue         # Schema 说明页
      ScriptLibraryPage.vue      # 剧本库页
      ScriptPreviewPage.vue      # 预览导出页
      ScriptWorkspace.vue        # YAML 编辑器 + 场景树
      SupportColumn.vue          # 左侧进度面板
      TemplateCenterPage.vue     # 模板中心页
      WorkflowStepper.vue        # 流程步骤条
      WorkspaceHeader.vue        # 顶栏（标题、用户名、使用指南）
    data/
      workbench.js               # 静态演示数据 + 帮助文档内容
    router/
      index.js                   # Vue Router
      routes.js                  # 路由表
    styles/                      # 各页面 CSS
    App.vue                      # 根组件
    main.js                      # 入口
    style.css                    # 样式入口
  index.html
  package.json
  vite.config.js
```

## 路由

| 路由 | 页面 | 说明 |
|---|---|---|
| `/auth` | 登录注册 | 支持表单校验 |
| `/workbench` | 工作台 | 4 步流程：导入→解析→生成→编辑导出 |
| `/templates` | 模板中心 | 5 种模板，设为默认，查看 YAML 示例 |
| `/library` | 剧本库 | 管理/编辑/预览/导出/重命名/复制/回收站 |
| `/help` | 帮助文档 | 流程说明、Schema、字段表、设计原因、FAQ |

## 工作台流程

1. **小说导入** — 上传 TXT 或粘贴正文，`/import/preview` 识别章节，本地正则兜底。
2. **AI 解析** — 启动 analysis-jobs，轮询展示人物/场景/事件/对白。
3. **剧本生成** — 选择模板和偏好，启动 script-jobs，生成 YAML。
4. **编辑与导出** — 在线编辑 YAML、校验、诊断、预览、导出 YAML/TXT/Markdown/PDF。

## 后端接口

默认地址 `http://127.0.0.1:8000/api/v1`。可在 `web/` 下创建 `.env.local` 覆盖：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### 请求约定

- Content-Type: `application/json`
- 导出接口 `responseType: 'blob'`
- 超时 15 秒
- 自动注入 `Authorization: Bearer <token>`

### 错误处理

优先展示 `error.response.data.detail`，网络不通时提示「暂时无法连接服务」。

## 认证

| localStorage Key | 说明 |
|---|---|
| `gm_auth_token` | 后端返回的 `access_token` |
| `gm_auth_user` | 后端返回的 `user` JSON `{id, name, email}` |

注册要求 name + email + password（≥6 位）。登录成功后右上角头像和用户名从数据库同步。退出清空 token 和 user，重定向到 `/auth`。

## 关键交互

**打开已有项目**：剧本库点「继续编辑」→ 切换工作台 → `/workbench` 恢复状态、YAML、场景树。

**校验 YAML**：点「校验格式」→ 同时调 validate + diagnosis → 右侧面板显示结果、统计和质量等级。

**添加场景**：弹窗选目标章节 → 填标题/地点/时间/人物/动作 → 后端拼接 YAML → 校验落库。

**导出**：YAML 本地 Blob 下载；Markdown/TXT 调后端返回 Blob；PDF 通过浏览器打印另存。

## 后端联调清单

1. 后端 `http://127.0.0.1:8000`，CORS 允许 `localhost:5173`。
2. 统一前缀 `/api/v1`。
3. 登录注册返回 `{access_token, token_type, user{id, name, email}}`。
4. 错误用 `{detail: "..."}` 结构。
