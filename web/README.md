# Gravity-Matrix Web

Vue 3 + Vite 前端应用，提供小说转剧本工作台、模板中心、剧本库、完整预览、帮助文档和个人中心。

## 技术栈

- Vue 3 Composition API
- Vite
- Vue Router
- Element Plus
- Axios
- js-yaml
- npm

## 快速启动

```powershell
cd web
npm install
npm run dev
```

默认地址：

```text
http://localhost:5173
```

生产构建：

```powershell
npm run build
```

本地预览构建结果：

```powershell
npm run preview
```

## 环境变量

如需覆盖后端地址，可在 `web/.env.local` 中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

默认后端前缀是：

```text
http://127.0.0.1:8000/api/v1
```

## 目录结构

```text
web/
  src/
    api/
      auth.js             登录注册、当前用户、会话处理
      http.js             Axios 实例、baseURL、token 注入、错误提取
      workbench.js        工作台、项目、模板、剧本库接口
    components/
      AuthPage.vue        登录注册
      NovelImportPage.vue 小说导入
      AiAnalysisPage.vue  AI 解析结果
      ScriptWorkspace.vue YAML 编辑和校验
      TemplateCenterPage.vue 选择剧本生成方式
      ScriptLibraryPage.vue 剧本库
      ScriptPreviewPage.vue 完整预览和导出
      HelpDocsPage.vue    帮助文档
      AppSidebar.vue      左侧导航
      WorkspaceHeader.vue 顶部栏
    data/
      workbench.js        图标、流程、帮助文案和兜底数据
    router/
      index.js            Vue Router 实例
      routes.js           路由元信息
    styles/               页面样式
    App.vue               应用壳和主业务状态
    main.js               入口
```

## 页面路由

| 路由 | 页面 | 说明 |
| --- | --- | --- |
| `/auth` | 登录注册 | 注册、登录、获取当前用户 |
| `/workbench` | 工作台 | 导入、解析、生成、编辑、导出 |
| `/templates` | 选择剧本生成方式 | 选择模板、查看示例、查看 Schema |
| `/library` | 剧本库 | 草稿管理、预览、导出、复制、回收站 |
| `/help` | 帮助文档 | 流程和 YAML Schema 说明 |

`/novel-to-yaml` 会重定向到 `/workbench`。

## 工作台交互

### 导入小说

- 粘贴正文或上传 TXT。
- 前端会调用 `/import/preview` 获取章节预检结果。
- 至少 3 章时允许继续。

### AI 解析

- 创建项目后启动解析任务。
- 通过任务接口轮询进度。
- 解析结果映射成人物、地点、事件、对白和冲突展示。

### 生成剧本

- 用户选择生成方式和偏好。
- 前端启动剧本生成任务。
- 完成后拉取项目 YAML。

### 编辑和导出

- YAML 编辑区是可编辑 textarea。
- 校验、保存、复制和下载均使用当前 `yamlContent`。
- 完整预览页支持 YAML / TXT / Markdown / PDF 导出。

## 剧本库交互

剧本库用于管理已有草稿和版本：

- 继续编辑：加载项目并跳回工作台。
- 查看预览：打开完整预览。
- 导出：下载当前剧本。
- 更多：重命名、复制一份、重新生成、移动到回收站、查看日志。

所有确认、输入和错误提示统一使用 Element Plus，不使用浏览器原生 `alert / confirm / prompt`。

## 登录状态

前端使用 localStorage 保存：

| Key | 说明 |
| --- | --- |
| `gm_auth_token` | JWT token |
| `gm_auth_user` | 当前用户 JSON |
| `gravityMatrixSelectedTemplate` | 当前默认模板 |
| `gravityMatrixCurrentProjectId` | 当前项目 ID |

Axios 请求会自动携带：

```http
Authorization: Bearer <token>
```

## 开发约定

- 使用 npm，不使用 pnpm。
- 非首屏页面可使用异步组件加载，降低首屏体积。
- Element Plus 的按钮原生类型使用 `native-type="button"`。
- 控制台调试日志应限制在 `import.meta.env.DEV`。
- 页面文案面向普通用户，避免在主界面突出技术字段。

## 验证

```powershell
npm run build
```

构建通过后，可启动：

```powershell
npm run dev
```

重点回归页面：

- `/auth`
- `/workbench`
- `/templates`
- `/library`
- `/help`
