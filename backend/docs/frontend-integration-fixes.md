# 前端接口接入与交互修复说明

本文档用于说明当前前端页面为什么上传小说后仍显示《星辰之下》、林晓、地铁站等静态内容，以及前端需要如何接入后端接口。

## 结论

当前问题主要在前端没有接入后端业务接口，不是后端生成接口失效。

已用 `backend/data/test_novels_by_book/novel_001/chapters/chapter_demo.txt` 直接测试后端，结果如下：

- `POST /api/v1/import/preview` 能识别 5 章。
- `POST /api/v1/projects` 能创建 5 章项目。
- 分析、剧本生成、YAML 校验、质量诊断、工作台聚合接口都能跑通。
- 后端生成的 YAML 包含 `chapter_demo` 和 `魏北辰`，不包含 `林晓`。
- 后端工作台结构返回的章节标题为：
  - `第1章 长明城 的旧照片`
  - `第2章 镜湖 的旧照片`
  - `第3章 白塔 的旧戏票`
  - `第4章 流萤车站 的匿名录音`
  - `第5章 南山矿场 的半枚铜钱`

浏览器页面仍显示《星辰之下》、林晓、5 章、28 场、场景 1-1 地铁站相遇，是因为这些内容来自 `web/src/data/workbench.js` 的静态 mock。

## 当前前端具体问题

### 1. 上传只能覆盖，不能累加

`web/src/components/NovelImportPage.vue` 的文件输入框是单文件上传：

```html
<input id="novel-file" type="file" accept=".txt,.docx" @change="$emit('file-upload', $event)" />
```

`web/src/App.vue` 中的 `handleFileUpload()` 每次都会执行：

```js
novelText.value = await file.text()
```

所以第二次上传会覆盖第一次上传内容。

建议：

- 如果产品目标是“一个 txt 文件包含三章以上”，保持单文件上传即可，但文案要改清楚。
- 如果产品目标是“多个 txt 文件分别代表章节”，前端需要改成 `multiple`，并把多个文件内容合并成一个项目 payload。

### 2. 当前页面没有调用导入预检接口

前端现在只用本地正则识别章节：

```js
const detectedChapters = computed(() => {
  const matches = [...novelText.value.matchAll(/(?:^|\n)\s*((?:第[\d一二三四五六七八九十百]+章|Chapter\s*\d+)[^\n]*)/gi)]
  ...
})
```

它没有调用：

```http
POST /api/v1/import/preview
```

建议：

- 上传或粘贴文本后调用 `/import/preview`。
- 使用后端返回的 `chapter_count`、`chapters`、`issues`、`can_create_project` 渲染导入页。
- “下一步：AI解析”按钮应根据 `can_create_project` 启用/禁用。

### 3. 点击“下一步：AI解析”没有创建项目

当前 `goToAnalysis()` 只是切换页面：

```js
const goToAnalysis = () => {
  analysisProgress.value = 100
  analysisNotice.value = ''
  activePage.value = 'analysis'
}
```

它没有调用：

```http
POST /api/v1/projects
POST /api/v1/projects/{project_id}/analysis-jobs
GET /api/v1/jobs/{job_id}
GET /api/v1/projects/{project_id}/analysis
```

建议流程：

1. 调 `/import/preview` 获得章节。
2. 用章节标题和正文组装 `POST /projects` payload。
3. 保存返回的 `project_id`。
4. 调 `POST /projects/{project_id}/analysis-jobs`。
5. 轮询 `GET /jobs/{job_id}`。
6. 分析完成后调 `GET /projects/{project_id}/analysis`。
7. 用真实分析结果替换 `analysisMetrics`、`analysisCharacters`、`analysisScenes`、`plotEvents` 等 mock 数据。

### 4. AI 解析页面仍显示 mock

`web/src/App.vue` 仍从 `web/src/data/workbench.js` 导入：

```js
analysisCharacters,
analysisMetrics,
analysisScenes,
characterRelations,
dialogueExtracts,
plotEvents,
```

因此“AI 解析结果概览”显示的人物 12、场景 28、章节 5、冲突事件 16 都是静态数据。

建议：

- 新增 `analysisState`。
- 后端分析结果完成后，把返回数据转换为组件所需结构。
- 如果某些字段后端暂时没有，前端可以显示空态，而不要继续显示《星辰之下》的 mock。

### 5. “查看详细”没有反应

截图里的“查看详细”按钮目前没有绑定业务逻辑。

建议：

- 绑定到工作台内的分析详情区域。
- 或打开一个分析详情弹窗/抽屉。
- 若暂不实现，应隐藏按钮，避免用户误以为功能失效。

### 6. 生成剧本 YAML 不是上传内容

当前生成 YAML 使用的是静态 `yamlLines`：

```js
const generatedYamlLines = computed(() => {
  if (!generatedSettings.value) {
    return yamlLines
  }
  ...
})
```

`yamlLines` 来自 `web/src/data/workbench.js`，内容固定为《星辰之下》。

建议流程：

1. 点击“下一步：生成剧本”后调用 `POST /projects/{project_id}/script-jobs`。
2. 轮询 `GET /jobs/{job_id}`。
3. 完成后调用 `GET /projects/{project_id}/script`。
4. 用返回的 `yaml` 字符串渲染 YAML 编辑器。
5. 不要再使用 `yamlLines` mock 作为真实结果。

### 7. 剧本结构只能显示 1-1，其他点击没反应

`ScriptWorkspace.vue` 中章节和场景按钮没有点击事件：

```html
<button class="chapter-row" type="button">
...
<button class="scene-row" :class="{ 'is-active': scene.active }" type="button">
```

并且右侧预览区域固定写死：

```html
<h3>场景 1-1 地铁站相遇</h3>
<p>内景 / 地铁站 / 傍晚</p>
<p>...林晓...</p>
```

建议：

- 为 `chapter-row` 增加展开/收起事件。
- 为 `scene-row` 增加选中事件。
- 新增 `selectedSceneId` 状态。
- 从后端 `GET /projects/{project_id}/workbench` 的 `script.structure` 或解析后的 YAML 中生成章节/场景树。
- 右侧预览根据 `selectedSceneId` 显示当前场景，而不是写死“地铁站相遇”。

### 8. 校验、复制、下载只操作 mock YAML

当前：

- “校验格式”只改本地 `schemaValidationMock`。
- “复制 YAML”复制 `generatedYamlText`。
- “下载 YAML”下载 `generatedYamlText`。

这些都没有调用真实后端保存或校验接口。

建议接入：

```http
POST /api/v1/projects/{project_id}/script/validate
PUT /api/v1/projects/{project_id}/script
GET /api/v1/projects/{project_id}/script/export
GET /api/v1/projects/{project_id}/script/diagnosis
POST /api/v1/projects/{project_id}/script/diagnosis
```

### 9. 我的项目和剧本库仍是静态数据

当前 `ProjectsPage` 使用：

```js
projectStats,
projectCards,
projectActivities,
```

当前 `ScriptLibraryPage` 使用：

```js
scriptLibraryStats,
scriptLibraryItems,
```

建议接入：

```http
GET /api/v1/projects/dashboard
GET /api/v1/scripts/library
```

## 推荐新增前端 API 封装

建议新增 `web/src/api/projects.js`：

```js
import { http } from './http'

export const previewImport = (payload) => http.post('/import/preview', payload)
export const createProject = (payload) => http.post('/projects', payload)
export const getProjectsDashboard = () => http.get('/projects/dashboard')
export const getScriptsLibrary = () => http.get('/scripts/library')
export const getProjectWorkbench = (projectId) => http.get(`/projects/${projectId}/workbench`)
export const startAnalysisJob = (projectId) => http.post(`/projects/${projectId}/analysis-jobs`)
export const startScriptJob = (projectId) => http.post(`/projects/${projectId}/script-jobs`)
export const getJob = (jobId) => http.get(`/jobs/${jobId}`)
export const getAnalysis = (projectId) => http.get(`/projects/${projectId}/analysis`)
export const getScript = (projectId) => http.get(`/projects/${projectId}/script`)
export const validateScript = (projectId, yaml) => http.post(`/projects/${projectId}/script/validate`, { yaml })
export const saveScript = (projectId, yaml) => http.put(`/projects/${projectId}/script`, { yaml })
export const getScriptDiagnosis = (projectId) => http.get(`/projects/${projectId}/script/diagnosis`)
```

## 推荐状态设计

`App.vue` 至少需要新增这些状态：

```js
const currentProjectId = ref(null)
const importPreview = ref(null)
const analysisData = ref(null)
const scriptYaml = ref('')
const scriptStructure = ref([])
const selectedSceneId = ref(null)
const isLoading = ref(false)
const errorNotice = ref('')
```

## 文本上传建议

对于 `chapter_demo.txt` 这种“一个文件包含 5 章”的文本，推荐流程是：

1. 用户上传一个 `.txt` 文件。
2. 前端读取 `file.text()`。
3. 调用 `POST /import/preview`。
4. 后端返回 5 章。
5. 用户点击下一步后，前端按后端章节标题拆分正文并创建项目。

如果要支持“上传多个章节文件”，前端需要：

- `<input type="file" multiple accept=".txt">`
- 读取所有文件。
- 按文件名或内容标题排序。
- 合并成 `chapters` 数组。
- 不要覆盖前一次上传，除非用户点击“重新选择”。

## 后端接口可用性验收

后端已经验证通过：

- `chapter_demo.txt` 预检：5 章，`can_create_project=true`
- 创建项目：201
- 分析读取：200
- 剧本读取：200
- YAML 校验：valid
- 质量诊断：`score=77`，`grade=good`
- 工作台结构：返回 5 个真实章节

## 前端验收标准

前端改完后，使用 `chapter_demo.txt` 测试应满足：

- 导入页显示 5 章，不要求上传 3 个文件。
- 点击“下一步：AI解析”后真实创建后端项目。
- AI 解析页不再显示《星辰之下》、林晓等 mock。
- 生成剧本 YAML 中包含 `chapter_demo`、`魏北辰` 等上传内容。
- 剧本结构显示后端返回的 5 章。
- 点击每个章节/场景，右侧预览和选中状态会变化。
- “校验格式”调用后端校验接口。
- “下载 YAML”导出后端生成的真实 YAML。
- “我的项目”和“剧本库”显示真实后端数据。

