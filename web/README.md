# Gravity-Matrix Web

AI 小说转剧本工具前端，基于 Vue 3 + Vite。

## 技术栈

- Vue 3（Composition API）
- Vite
- Vue Router
- Axios
- js-yaml（YAML 解析与高亮）

## 本地启动

```powershell
cd web
npm install
npm run dev
```

默认访问 `http://localhost:5173`。构建检查：

```powershell
npm run build
```

## 目录结构

```
web/
  src/
    api/
      auth.js            # 注册、登录、获取当前用户
      http.js             # Axios 实例（baseURL、超时、token 注入）
      workbench.js        # 所有业务接口调用
    components/
      AddSceneDialog.vue         # 添加场景弹窗
      AiAnalysisPage.vue         # AI 解析结果页
      AppSidebar.vue             # 左侧导航栏
      AuthPage.vue               # 登录注册页
      GenerationSettingsDialog.vue  # 剧本生成设置弹窗
      HelpDocsPage.vue           # 帮助文档页
      NovelImportPage.vue        # 小说导入页
      ProductRoutePage.vue       # 路由占位页（已废弃路由用）
      ProfileCenterDialog.vue    # 个人中心弹窗
      SchemaHelpPage.vue         # YAML Schema 说明页
      ScriptLibraryPage.vue      # 剧本库页
      ScriptPreviewPage.vue      # 剧本预览导出页
      ScriptWorkspace.vue        # YAML 编辑器 + 场景树
      SupportColumn.vue          # 左侧进度面板
      TemplateCenterPage.vue     # 模板中心页
      WorkflowStepper.vue        # 流程步骤条
      WorkspaceHeader.vue        # 顶栏（标题、用户头像、使用指南）
    data/
      workbench.js       # 静态演示数据 + 帮助文档内容
    router/
      index.js           # Vue Router 配置
      routes.js          # 路由定义
    styles/              # 各页面 / 组件样式
    App.vue              # 根组件（路由分发 + 全局状态）
    main.js              # 入口
    style.css            # 样式入口
  index.html
  package.json
  vite.config.js
```

## 页面与路由

| 路由 | 页面 | 说明 |
|---|---|---|
| `/auth` | 登录注册 | 注册账号或登录，支持表单校验 |
| `/workbench` | 工作台 | 导入 → 解析 → 生成 → 编辑 → 预览 → 导出 |
| `/templates` | 模板中心 | 选择默认模板，查看 YAML 示例结构 |
| `/library` | 剧本库 | 已生成剧本管理：编辑、预览、导出、重命名、复制、回收站 |
| `/help` | 帮助文档 | 使用流程、YAML Schema、字段说明、设计原因、FAQ |

`/projects` 和 `/profile` 已移除，分别由剧本库和个人中心弹窗替代。

## 工作台流程

工作台按 4 步流程组织，由工作区左侧 Stepper 指示当前进度：

1. **小说导入** — 上传 TXT 或粘贴正文，后端 /import/preview 识别章节结构，本地正则兜底。
2. **AI 解析** — 启动 analysis-jobs，轮询完成后展示人物、场景、事件、对白识别结果。
3. **剧本生成** — 选择模板和生成偏好，启动 script-jobs，生成可编辑 YAML。
4. **编辑与导出** — 校验 YAML 结构，在线编辑内容，预览场景文本，导出 YAML / TXT / Markdown。

## 后端接口配置

默认接口地址 `http://127.0.0.1:8000/api/v1`，由 `src/api/http.js` 中 `VITE_API_BASE_URL` 环境变量控制。

如需修改，在 `web/` 目录创建 `.env.local`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### 请求约定

- 所有请求使用 `application/json`。
- 导出类接口使用 `responseType: 'blob'`。
- 超时 15 秒。
- 前端自动注入 `Authorization: Bearer <token>`（从 localStorage 读取 `gm_auth_token`）。

### 错误处理

前端优先展示 `error.response.data.detail` 字符串；网络不通时提示「暂时无法连接服务」。

## 认证

登录/注册成功后保存：

| localStorage Key | 说明 |
|---|---|
| `gm_auth_token` | 后端返回的 `access_token` |
| `gm_auth_user` | 后端返回的 `user` JSON `{id, name, email}` |

退出登录清除两个 Key，重定向到 `/auth`。

注册接口要求 `name`、`email`、`password`（≥6 位），登录接口要求 `email`、`password`。

## 关键交互

### 打开已有项目

剧本库中点击「继续编辑」→ 前端切换到工作台 → 调用 `/workbench` 一次性恢复项目状态、剧本 YAML、场景树和诊断结果。

### 校验 YAML

编辑器中点击「校验格式」→ 同时调用 `POST /script/validate` 和 `POST /script/diagnosis` → 右侧面板显示校验结果、统计信息和质量等级。

### 添加场景

「新增场景」弹窗选择目标章节、填写场景标题/地点/时间/人物/动作描述 → 后端拼接 scene 到 YAML → 校验通过后落库。

### 导出

- YAML：前端本地 Blob 下载
- Markdown / TXT：调用后端 `/script/export/markdown` 或 `/script/export/txt` 获得 Blob 后下载
- PDF：打开浏览器打印窗口另存

## 后端联调清单

1. 后端运行在 `http://127.0.0.1:8000`，CORS 允许 `localhost:5173`。
2. 所有接口统一前缀 `/api/v1`。
3. 登录注册返回 `{access_token, token_type, user{id, name, email}}`。
4. 错误响应使用 `{detail: "错误说明"}` 结构。
5. 当前业务接口不需要鉴权，后续可通过 `Authorization: Bearer <token>` 保护。
