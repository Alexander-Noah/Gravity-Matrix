# Gravity-Matrix 功能描述文档

## 1. 项目概述

Gravity-Matrix 是一个 AI 小说转剧本工具，面向小说作者、编剧、内容创作者和课程/实训场景中的文本改编需求。系统支持将 3 章以上的小说文本导入平台，通过章节识别、AI 内容解析、模板化生成、YAML 剧本编辑、Schema 校验、质量诊断和多格式导出，帮助用户快速得到一份结构化、可继续修改的剧本初稿。

项目采用前后端分离架构：

- 前端使用 Vue 3 + Vite，提供登录注册、工作台、模板中心、剧本库、帮助文档和个人中心等页面。
- 后端使用 FastAPI + SQLAlchemy + SQLite/MySQL 兼容存储，负责认证、项目管理、小说解析、剧本生成、YAML 校验、质量诊断、导出和剧本库数据聚合。
- AI 能力支持 DeepSeek / OpenAI-compatible Chat Completions；未配置大模型密钥时，系统会使用确定性演示逻辑，保证本地环境也能完整跑通流程。

## 2. 核心业务流程

系统围绕“小说导入到剧本产出”的创作链路设计，完整流程如下：

```text
注册/登录
  → 导入小说文本
  → 章节识别与导入预检
  → 创建项目
  → AI 解析人物、地点、剧情事件、主题与冲突
  → 选择剧本模板与生成偏好
  → 生成结构化 YAML 剧本
  → 在线编辑 YAML
  → Schema 校验与质量诊断
  → 预览剧本文本
  → 导出 YAML / TXT / Markdown / PDF
```

该流程既支持用户从空白工作台导入小说，也支持从剧本库中的本地素材一键导入并进入后续解析和生成步骤。

## 3. 用户与认证功能

### 3.1 登录注册

系统提供基础账号体系：

- 用户注册：填写用户名、邮箱和密码创建账号。
- 用户登录：使用邮箱和密码登录系统。
- 当前用户读取：通过 token 获取当前用户信息。
- 退出登录：清除本地登录态并返回登录页。

前端默认入口为登录页。未完成本次登录时，用户即使直接输入 `/workbench`、`/library`、`/templates`、`/help` 等功能页面地址，也会被拦截回 `/auth`，避免绕过登录直接进入工作台。

### 3.2 个人中心

个人中心用于展示当前账号和工作区状态，包括：

- 用户名、邮箱、角色。
- 当前工作区名称。
- 当前项目名称。
- 项目进度。
- 当前流程阶段。
- 当前选择的剧本模板。
- 剧本状态。
- 剧本库数量。
- Schema 校验状态。

后端提供 `/profile/summary` 聚合接口，个人中心数据可从真实项目、模板和剧本状态中派生，减少前端静态展示数据带来的偏差。

## 4. 小说导入与预处理

### 4.1 文本导入

用户可以在工作台导入小说正文，支持：

- 粘贴小说文本。
- 上传一个或多个 TXT 文件。
- 多 TXT 文件按文件名顺序合并。
- 对没有章节标题的 TXT 文件自动补全章节标题。

系统要求小说至少包含 3 个章节，章节标题可识别类似“第1章”“第一章”“Chapter 1”等格式。

### 4.2 导入预检

后端提供 `POST /api/v1/import/preview` 接口，在正式创建项目前进行预检：

- 自动识别章节。
- 返回章节数量、总字数、每章字数和正文摘录。
- 判断是否满足创建项目条件。
- 返回错误、警告或提示信息。
- 本地预处理人物候选、地点候选、章节摘要、主题和冲突线索。

该能力可以让用户在进入 AI 解析前确认文本结构是否正确，减少后续生成失败或内容错位。

## 5. 项目管理功能

项目是小说改编流程的核心数据单位。每个项目包含小说标题、作者、章节、AI 解析结果、生成设置、剧本 YAML、任务状态和软删除状态。

系统支持：

- 创建项目。
- 查询项目列表。
- 查询项目详情。
- 项目重命名。
- 克隆项目。
- 删除项目。
- 回收站查看。
- 从回收站恢复项目。
- 清空回收站。
- 获取项目 readiness，判断下一步可执行操作。
- 获取工作台聚合数据。
- 获取项目看板统计。

项目列表和看板数据均由后端真实数据派生，避免刷新后出现假数据闪现或空状态误判。

## 6. AI 解析功能

AI 解析用于将小说章节转化为后续生成剧本所需的结构化素材。解析结果包括：

- 主要人物。
- 人物身份、年龄、角色定位和描述。
- 地点和场景。
- 章节摘要。
- 剧情事件。
- 主题。
- 冲突线索。
- 人物关系和对白线索。

后端通过任务接口启动解析流程：

- `POST /api/v1/projects/{project_id}/analysis-jobs`
- `POST /api/v1/projects/{project_id}/analysis-jobs/rerun`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/projects/{project_id}/analysis`

解析任务使用任务状态记录进度，前端可以轮询任务状态并展示“正在读取章节”“正在分析人物、场景和冲突”“正在整理 AI 解析结果”等阶段信息。

当未配置真实大模型时，系统会使用本地确定性逻辑从章节文本中抽取候选人物和摘要，保证演示环境可用。

## 7. 模板中心与生成设置

模板中心用于控制剧本生成目标格式和改编策略。目前支持 5 类模板：

- 影视剧剧本模板。
- 短剧剧本模板。
- 话剧剧本模板。
- 分镜剧本模板。
- 广播剧剧本模板。

模板包含：

- 模板 ID。
- 模板名称。
- 适用场景。
- 目标格式。
- 后端生成规则。
- 模板特性。
- YAML 示例字段。

用户可以设置默认模板，也可以在生成剧本前选择具体模板和生成偏好。生成设置会保存到项目中，并参与后端 prompt 和兜底生成逻辑。

## 8. 剧本生成与 YAML 结构

剧本生成会根据项目章节、AI 解析结果和生成设置，输出结构化 YAML。YAML 内容包含：

- 剧本元信息。
- 原著信息。
- 模板和目标格式信息。
- 人物列表。
- 地点列表。
- 章节列表。
- 场景列表。
- 场景时间、地点、出场人物。
- 场景梗概。
- 舞台/镜头/动作说明。
- 对白。
- 改编说明。

后端生成接口包括：

- `POST /api/v1/projects/{project_id}/script-jobs`
- `POST /api/v1/projects/{project_id}/script-jobs/rerun`
- `GET /api/v1/projects/{project_id}/script`

生成成功后，剧本会持久化到项目中，前端工作台进入 YAML 编辑和预览阶段。

## 9. YAML 在线编辑功能

剧本编辑页提供黑色 YAML 编辑区和结构导航能力，支持用户直接手动修改生成后的 YAML 内容。

主要能力包括：

- 展示后端生成的 YAML 剧本。
- 手动编辑 YAML。
- 自动保存已修改内容。
- 点击章节或场景后定位到对应 YAML 行。
- 新增场景。
- 复制 YAML。
- 下载 YAML。
- 打开 Schema 帮助文档。
- 进入剧本完整预览。

编辑后的 YAML 会通过后端保存接口写回项目：

- `PUT /api/v1/projects/{project_id}/script`

## 10. Schema 校验与质量诊断

系统提供两类质量保障能力。

### 10.1 YAML Schema 校验

校验用于判断 YAML 是否符合系统定义的剧本结构，覆盖字段类型、必填字段、章节、场景、人物引用、地点引用等基础结构问题。

接口：

- `POST /api/v1/projects/{project_id}/script/validate`

返回内容包括：

- 是否有效。
- 错误列表。

### 10.2 剧本质量诊断

质量诊断在 Schema 校验基础上，进一步评估剧本内容质量，返回：

- 分数。
- 等级。
- 摘要统计。
- 优点。
- 问题列表。
- 问题严重级别。
- 问题路径和修复建议。

诊断覆盖：

- 章节数量。
- 场景数量。
- 对白数量。
- 人物覆盖。
- 场景人物引用。
- 章节摘要长度。
- 改编说明完整度。

接口：

- `GET /api/v1/projects/{project_id}/script/diagnosis`
- `POST /api/v1/projects/{project_id}/script/diagnosis`

## 11. 剧本预览与导出

生成后的剧本可以进入完整预览页，用户可以按标准剧本文本方式查看场景、人物、动作说明和对白。

系统支持多格式导出：

- YAML：保留结构化数据，适合继续编辑和程序读取。
- TXT：纯文本剧本稿，适合快速阅读。
- Markdown：带标题层级和基础格式的阅读稿。
- PDF：后端生成 PDF 文件并下载，不再依赖浏览器打印窗口。

相关接口：

- `GET /api/v1/projects/{project_id}/script/export`
- `GET /api/v1/projects/{project_id}/script/export/txt`
- `GET /api/v1/projects/{project_id}/script/export/markdown`
- `GET /api/v1/projects/{project_id}/script/export/pdf`

前端预览页和剧本库均可触发导出。

## 12. 剧本库功能

剧本库用于集中管理已生成剧本和本地素材。页面展示：

- 剧本统计。
- 已生成剧本列表。
- 本地素材列表。
- 剧本标题。
- 来源小说。
- 剧本类型。
- 章节数、场景数、对白数。
- Schema 状态。
- 更新时间。
- 标签。

支持操作：

- 编辑剧本。
- 预览剧本。
- 导出剧本。
- 删除剧本。
- 重命名剧本。
- 克隆剧本。
- 从本地素材导入项目。

后端剧本库接口会同时整合已生成剧本和 `backend/data/test_novels_by_book` 中的本地小说素材：

- `GET /api/v1/scripts/library`
- `POST /api/v1/scripts/library/sources/{source_id}/import`

## 13. 模板中心功能

模板中心提供剧本模板浏览、筛选和默认模板设置能力。用户可以查看每个模板的：

- 适用场景。
- 后端生成规则。
- 结构字段。
- YAML 示例。
- 目标格式。

接口：

- `GET /api/v1/templates`
- `GET /api/v1/templates/{template_id}`
- `GET /api/v1/templates/default`
- `PUT /api/v1/templates/default`

## 14. 帮助文档与 Schema 文档

帮助文档页面用于解释系统使用流程、常见问题和 YAML Schema 设计原因。页面支持结构导航，当前阅读位置会在导航栏中高亮，便于用户在长文档中定位。

Schema 帮助内容覆盖：

- YAML 顶层结构。
- metadata 字段。
- characters 字段。
- locations 字段。
- chapters 字段。
- scenes 字段。
- dialogue 字段。
- 必填项说明。
- 示例片段。
- 设计原因。

## 15. 工作台聚合能力

工作台需要同时展示项目状态、流程步骤、AI 解析、剧本结构、YAML、质量诊断和进度信息。后端提供聚合接口：

- `GET /api/v1/projects/{project_id}/workbench`

该接口一次性返回：

- 项目基础信息。
- 工作流步骤。
- 当前进度。
- AI 解析概览。
- 剧本 YAML。
- 剧本结构导航。
- 质量诊断。

前端通过该接口减少多次请求和状态错位，保证刷新后能恢复真实项目状态。

## 16. 数据存储与任务机制

后端使用 SQLAlchemy 定义数据模型，主要包括：

- User：用户账号。
- Project：小说改编项目。
- Chapter：小说章节。
- Job：分析和剧本生成任务。
- ProjectGenerationSettings：项目生成设置。
- AppSetting：应用级设置，例如默认模板。

任务机制覆盖：

- AI 解析任务。
- 剧本生成任务。
- 任务排队状态。
- 任务运行状态。
- 任务成功状态。
- 任务失败状态。
- 超时任务自动标记失败。
- 重新运行任务时取消旧任务。

## 17. 前端页面结构

前端主要路由包括：

| 路由 | 页面 | 功能 |
|---|---|---|
| `/auth` | 登录注册 | 用户注册、登录、本次会话入口 |
| `/workbench` | 工作台 | 小说导入、AI 解析、剧本生成、编辑、预览、导出 |
| `/templates` | 模板中心 | 查看、筛选、设置剧本模板 |
| `/library` | 剧本库 | 管理已生成剧本和本地素材 |
| `/help` | 帮助文档 | 查看产品流程和 Schema 文档 |

整体界面定位为克制、清晰、工具型的创作工作台，强调真实数据、流程状态、长文本编辑和可导出结果。

## 18. 后端接口概览

### 认证与用户

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/profile/summary`

### 小说导入

- `POST /api/v1/import/preview`

### 项目管理

- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/clone`
- `DELETE /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/restore`
- `GET /api/v1/projects/recycle-bin`
- `DELETE /api/v1/projects/recycle-bin`
- `GET /api/v1/projects/dashboard`
- `GET /api/v1/projects/{project_id}/readiness`
- `GET /api/v1/projects/{project_id}/workbench`

### AI 解析与剧本生成

- `POST /api/v1/projects/{project_id}/analysis-jobs`
- `POST /api/v1/projects/{project_id}/analysis-jobs/rerun`
- `GET /api/v1/projects/{project_id}/analysis`
- `POST /api/v1/projects/{project_id}/script-jobs`
- `POST /api/v1/projects/{project_id}/script-jobs/rerun`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/projects/{project_id}/generation-settings`

### 剧本编辑、校验、诊断与导出

- `GET /api/v1/projects/{project_id}/script`
- `PUT /api/v1/projects/{project_id}/script`
- `POST /api/v1/projects/{project_id}/script/validate`
- `GET /api/v1/projects/{project_id}/script/diagnosis`
- `POST /api/v1/projects/{project_id}/script/diagnosis`
- `GET /api/v1/projects/{project_id}/script/export`
- `GET /api/v1/projects/{project_id}/script/export/txt`
- `GET /api/v1/projects/{project_id}/script/export/markdown`
- `GET /api/v1/projects/{project_id}/script/export/pdf`
- `POST /api/v1/projects/{project_id}/scenes`

### 模板与剧本库

- `GET /api/v1/templates`
- `GET /api/v1/templates/{template_id}`
- `GET /api/v1/templates/default`
- `PUT /api/v1/templates/default`
- `GET /api/v1/scripts/library`
- `POST /api/v1/scripts/library/sources/{source_id}/import`

## 19. 当前功能边界

当前版本已经具备完整本地演示和真实接口链路，但仍有进一步优化空间：

- PDF 导出已改为后端文件下载，但排版能力仍是基础版本，后续可接入专业 PDF 渲染方案。
- 认证已具备注册、登录和会话拦截，但还没有完整的角色权限体系。
- 项目数据目前按全局项目聚合，后续可增加用户与项目的归属关系。
- 生成质量依赖大模型配置；无 API Key 时使用确定性演示逻辑，适合本地演示但不是最终创作质量上限。
- 回收站后端支持软删除和恢复，但前端部分历史删除记录仍需继续与后端完全统一。
- 前端状态管理仍集中在主应用组件中，后续可拆分为 composables 或 store。

## 20. 总结

Gravity-Matrix 已实现从小说文本到结构化剧本初稿的完整闭环。它不仅能生成 YAML 剧本，还覆盖了导入预检、AI 解析、模板化生成、在线编辑、结构校验、质量诊断、多格式导出、剧本库管理和帮助文档等配套能力。

项目适合用于 AI 小说改编剧本场景的课程展示、实训作品、原型验证和后续产品化扩展。其核心价值在于把非结构化小说文本转化为可编辑、可校验、可导出的结构化剧本资产，让创作者能够更快进入“修改和打磨”阶段。
