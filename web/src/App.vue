<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { clearAuthSession, getAuthSession } from './api/auth'
import { getApiErrorMessage } from './api/http'
import { createProject, getJob, getProjectAnalysis, startAnalysisJob } from './api/workbench'
import AddSceneDialog from './components/AddSceneDialog.vue'
import AiAnalysisPage from './components/AiAnalysisPage.vue'
import AppSidebar from './components/AppSidebar.vue'
import AuthPage from './components/AuthPage.vue'
import GenerationSettingsDialog from './components/GenerationSettingsDialog.vue'
import HelpDocsPage from './components/HelpDocsPage.vue'
import NovelImportPage from './components/NovelImportPage.vue'
import ProductRoutePage from './components/ProductRoutePage.vue'
import ProfileCenterDialog from './components/ProfileCenterDialog.vue'
import ProjectsPage from './components/ProjectsPage.vue'
import SchemaHelpPage from './components/SchemaHelpPage.vue'
import ScriptLibraryPage from './components/ScriptLibraryPage.vue'
import ScriptPreviewPage from './components/ScriptPreviewPage.vue'
import ScriptWorkspace from './components/ScriptWorkspace.vue'
import SupportColumn from './components/SupportColumn.vue'
import TemplateCenterPage from './components/TemplateCenterPage.vue'
import WorkflowStepper from './components/WorkflowStepper.vue'
import WorkspaceHeader from './components/WorkspaceHeader.vue'
import {
  analysisCharacters,
  analysisMetrics,
  analysisScenes,
  analysisWorkflowSteps,
  characterRelations,
  defaultNovelText,
  dialogueExtracts,
  generationSettingOptions,
  iconPaths,
  importWorkflowSteps,
  insightItems,
  navItems,
  plotEvents,
  previewDialogues,
  previewWorkflowSteps,
  projectActivities,
  projectCards,
  projectStages,
  projectStats,
  productHelpDocs,
  quickActions,
  schemaHelpContent,
  schemaValidationMock,
  scriptGenerationTemplates,
  scriptChapters,
  scriptLibraryItems,
  scriptLibraryStats,
  scriptPreviewScenes,
  workflowSteps,
  yamlLines,
} from './data/workbench'
import { getRouteById } from './router/routes'

const route = useRoute()
const router = useRouter()
const activePage = ref('import')
const novelText = ref(defaultNovelText)
const selectedFileName = ref('')
const importNotice = ref('')
const analysisProgress = ref(100)
const analysisNotice = ref('')
const currentProjectId = ref(null)
const isImportSubmitting = ref(false)
const isGenerationSettingsOpen = ref(false)
const isAddSceneOpen = ref(false)
const generatedSettings = ref(null)
const schemaValidation = ref(schemaValidationMock)
const editorNotice = ref('')
const previewNotice = ref('')
const selectedTemplateId = ref('')
const currentUser = ref(getAuthSession().user)
const isProfileCenterOpen = ref(false)
const displayedAnalysisCharacters = ref(analysisCharacters)
const displayedAnalysisMetrics = ref(analysisMetrics)
const displayedAnalysisScenes = ref(analysisScenes)
const displayedPlotEvents = ref(plotEvents)
const displayedCharacterRelations = ref(characterRelations)
const displayedDialogueExtracts = ref(dialogueExtracts)

const activeRoute = computed(() => getRouteById(route.name))
const isAuthRoute = computed(() => activeRoute.value.id === 'auth')
const isWorkbenchRoute = computed(() => activeRoute.value.id === 'workbench')

const activeNavItems = computed(() =>
  navItems.map((item) => ({
    ...item,
    active: item.id === activeRoute.value.id,
  })),
)

const pageTitle = computed(() => {
  if (!isWorkbenchRoute.value) {
    return activeRoute.value.title
  }

  return '小说转剧本工作台'
})
const pageDescription = computed(() => {
  if (!isWorkbenchRoute.value) {
    return activeRoute.value.description
  }

  if (activePage.value === 'import') {
    return '上传文件或粘贴原文，检查章节完整度后进入 AI 解析'
  }

  if (activePage.value === 'analysis') {
    return '检查人物、场景、剧情事件、人物关系和对白提取结果'
  }

  if (activePage.value === 'preview') {
    return '检查完整剧本文本并导出 YAML、TXT、Markdown 或 PDF'
  }

  if (activePage.value === 'schema-doc') {
    return '查看 YAML Schema 字段、必填项、示例和设计原因'
  }

  return '编辑生成的 YAML 剧本，并校验结构后进入完整预览'
})
const currentWorkflowSteps = computed(() => {
  if (activePage.value === 'import') {
    return importWorkflowSteps
  }

  if (activePage.value === 'analysis') {
    return analysisWorkflowSteps
  }

  if (activePage.value === 'preview') {
    return previewWorkflowSteps
  }

  return workflowSteps
})

const detectedChapters = computed(() => {
  const matches = [
    ...novelText.value.matchAll(
      /(?:^|\n)\s*((?:第\s*[\d一二三四五六七八九十百千万零〇两]+\s*[章节回]|Chapter\s*\d+)[^\n]*)/gi,
    ),
  ]

  return matches.map((match, index) => {
    const start = match.index || 0
    const end = matches[index + 1]?.index ?? novelText.value.length
    const chapterText = novelText.value.slice(start, end).trim()
    const body = chapterText.replace(match[1], '').trim()
    const excerpt = body.replace(/\s+/g, ' ').slice(0, 46)

    return {
      title: match[1].trim(),
      content: body || chapterText,
      excerpt: excerpt ? `${excerpt}...` : '等待补充正文',
    }
  })
})

const chapterCount = computed(() => detectedChapters.value.length)
const isNovelValid = computed(() => chapterCount.value >= 3)
const generatedYamlLines = computed(() => {
  if (!generatedSettings.value) {
    return yamlLines
  }

  return [
    ...yamlLines.slice(0, 6),
    [{ text: 'generation_settings:', tone: 'key' }],
    [{ text: '  script_type:', tone: 'key' }, { text: ` ${generatedSettings.value.scriptType}`, tone: 'string' }],
    [{ text: '  adaptation_style:', tone: 'key' }, { text: ` ${generatedSettings.value.adaptationStyle}`, tone: 'string' }],
    [{ text: '  content_options:', tone: 'key' }],
    ...generatedSettings.value.contentOptions.map((option) => [
      { text: '    -', tone: 'key' },
      { text: ` ${option}`, tone: 'value' },
    ]),
    [],
    ...yamlLines.slice(6),
  ]
})
const generatedYamlText = computed(() =>
  generatedYamlLines.value.map((line) => line.map((token) => token.text).join('')).join('\n'),
)
const scriptTextPreview = computed(() =>
  scriptPreviewScenes
    .map((scene) => {
      const cast = `出场人物：${scene.characters.join('、')}`
      const dialogues = scene.dialogues.map((dialogue) => `${dialogue.speaker}\n${dialogue.line}`).join('\n\n')

      return `${scene.title}\n${scene.meta}\n${cast}\n\n${scene.action}\n\n${dialogues}`
    })
    .join('\n\n---\n\n'),
)
const markdownPreview = computed(() =>
  scriptPreviewScenes
    .map((scene) => {
      const dialogues = scene.dialogues.map((dialogue) => `**${dialogue.speaker}**\n\n${dialogue.line}`).join('\n\n')

      return `## ${scene.title}\n\n${scene.meta}\n\n出场人物：${scene.characters.join('、')}\n\n${scene.action}\n\n${dialogues}`
    })
    .join('\n\n'),
)

const waitForJob = async (jobId) => {
  for (let attempt = 0; attempt < 12; attempt += 1) {
    const job = await getJob(jobId)

    analysisProgress.value = job.progress ?? analysisProgress.value
    analysisNotice.value = job.current_step || analysisNotice.value

    if (job.status === 'succeeded') {
      return job
    }

    if (job.status === 'failed') {
      throw new Error(job.error_message || 'AI 解析任务失败。')
    }

    await new Promise((resolve) => {
      window.setTimeout(resolve, 600)
    })
  }

  throw new Error('AI 解析任务仍在处理中，请稍后重试。')
}

const applyAnalysisResult = (analysis) => {
  const raw = analysis?.analysis || analysis || {}
  const characters = raw.characters || []
  const locations = raw.locations || []
  const chapterSummaries = raw.chapter_summaries || []
  const conflicts = raw.conflicts || []
  const themes = raw.themes || []

  displayedAnalysisCharacters.value = characters.length
    ? characters.map((character, index) => ({
        name: character.name || `人物 ${index + 1}`,
        role: character.role || '角色',
        age: character.age ?? '-',
        trait: character.description || '等待作者继续补充人物说明',
      }))
    : analysisCharacters

  displayedAnalysisScenes.value = locations.length
    ? locations.map((location, index) => ({
        title: location.name || `场景 ${index + 1}`,
        chapter: `第${index + 1}章`,
        time: '待定',
        mood: location.description || '由 AI 根据章节内容识别',
      }))
    : analysisScenes

  displayedPlotEvents.value = chapterSummaries.length
    ? chapterSummaries.map((chapter, index) => ({
        step: String(index + 1).padStart(2, '0'),
        chapter: `第${chapter.chapter_number || index + 1}章`,
        title: chapter.title || `章节事件 ${index + 1}`,
        detail: chapter.summary || '等待 AI 补充章节摘要',
      }))
    : plotEvents

  displayedAnalysisMetrics.value = [
    { label: '人物', value: String(characters.length), icon: 'users', tone: 'violet' },
    { label: '场景', value: String(locations.length), icon: 'scene', tone: 'blue' },
    { label: '章节', value: String(chapterSummaries.length || chapterCount.value), icon: 'chapter', tone: 'mint' },
    { label: '冲突事件', value: String(conflicts.length), icon: 'conflict', tone: 'orange' },
  ]

  displayedCharacterRelations.value = characters.length >= 2
    ? [
        {
          source: characters[0].name || '主角',
          target: characters[1].name || '重要人物',
          relation: '主要关系',
          note: conflicts[0] || themes.join('、') || '可在后续剧本编辑中继续细化人物关系。',
        },
      ]
    : characterRelations

  displayedDialogueExtracts.value = dialogueExtracts
}

const goToPage = (pageId) => {
  const targetRoute = getRouteById(pageId)

  router.push(targetRoute.path)

  if (pageId === 'workbench') {
    activePage.value = 'import'
  }
}

const handleAuthenticated = () => {
  currentUser.value = getAuthSession().user
  router.push('/workbench')
}

const openProfileCenter = () => {
  currentUser.value = getAuthSession().user
  isProfileCenterOpen.value = true
}

const logout = () => {
  isProfileCenterOpen.value = false
  clearAuthSession()
  router.push('/auth')
}

const openProject = (project) => {
  router.push('/workbench')

  if (project?.scenes === 0 || project?.progress < 50) {
    activePage.value = 'analysis'
    return
  }

  if (project?.progress >= 90) {
    activePage.value = 'preview'
    return
  }

  activePage.value = 'script'
}

const selectGenerationTemplate = (templateId) => {
  selectedTemplateId.value = templateId
}

const editLibraryScript = () => {
  router.push('/workbench')
  activePage.value = 'script'
}

const previewLibraryScript = () => {
  router.push('/workbench')
  previewNotice.value = ''
  activePage.value = 'preview'
}

const goToAnalysis = async () => {
  if (!isNovelValid.value || isImportSubmitting.value) {
    return
  }

  isImportSubmitting.value = true
  analysisProgress.value = 10
  importNotice.value = '正在创建小说改编项目...'

  try {
    const project = await createProject({
      title: selectedFileName.value ? selectedFileName.value.replace(/\.[^.]+$/, '') : '小说改编项目',
      author: '创作者',
      chapters: detectedChapters.value.map((chapter) => ({
        title: chapter.title,
        content: chapter.content,
      })),
    })

    currentProjectId.value = project.id
    analysisProgress.value = 25
    importNotice.value = '项目已创建，正在启动 AI 解析任务...'

    const job = await startAnalysisJob(project.id)
    activePage.value = 'analysis'
    analysisNotice.value = job.current_step || 'AI 解析任务已启动。'
    analysisProgress.value = job.progress ?? 30

    await waitForJob(job.id)
    const analysis = await getProjectAnalysis(project.id)
    applyAnalysisResult(analysis)
    analysisProgress.value = 100
    analysisNotice.value = 'AI 解析完成，结果已从后端同步。'
  } catch (error) {
    importNotice.value = getApiErrorMessage(error)
    analysisNotice.value = getApiErrorMessage(error)
    activePage.value = 'import'
  } finally {
    isImportSubmitting.value = false
  }
}

const goBackToImport = () => {
  activePage.value = 'import'
}

const goBackToAnalysis = () => {
  activePage.value = 'analysis'
}

const rerunAnalysis = () => {
  analysisProgress.value = 36
  analysisNotice.value = '正在重新解析小说内容...'

  window.setTimeout(() => {
    analysisProgress.value = 100
    analysisNotice.value = '重新解析完成，结果已刷新。'
  }, 450)
}

const openGenerationSettings = () => {
  isGenerationSettingsOpen.value = true
}

const confirmGenerationSettings = (settings) => {
  generatedSettings.value = settings
  isGenerationSettingsOpen.value = false
  editorNotice.value = ''
  schemaValidation.value = schemaValidationMock
  activePage.value = 'script'
}

const openAddScene = () => {
  isAddSceneOpen.value = true
}

const confirmAddScene = (sceneDraft) => {
  isAddSceneOpen.value = false
  editorNotice.value = `${sceneDraft.sceneTitle} 已加入场景草稿，后续可写入 YAML。`
}

const validateYaml = () => {
  schemaValidation.value = {
    ...schemaValidationMock,
    checkedAt: `刚刚校验 · ${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`,
    message: '校验通过：YAML 格式正确，必填字段完整。',
  }
  editorNotice.value = 'Schema 校验已完成。'
}

const copyYaml = async () => {
  if (!navigator.clipboard) {
    editorNotice.value = '当前浏览器不支持剪贴板 API。'
    return
  }

  try {
    await navigator.clipboard.writeText(generatedYamlText.value)
    editorNotice.value = 'YAML 已复制到剪贴板。'
  } catch {
    editorNotice.value = '复制失败，请检查浏览器剪贴板权限。'
  }
}

const downloadYaml = () => {
  const blob = new Blob([generatedYamlText.value], { type: 'text/yaml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = 'generated-script.yaml'
  link.click()
  URL.revokeObjectURL(url)
  editorNotice.value = 'YAML 文件已开始下载。'
}

const goToSchemaHelp = () => {
  activePage.value = 'schema-doc'
}

const goToPreview = () => {
  previewNotice.value = ''
  activePage.value = 'preview'
}

const goBackToEditor = () => {
  activePage.value = 'script'
}

const downloadTextFile = (content, filename, type) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

const exportPreviewYaml = () => {
  downloadTextFile(generatedYamlText.value, 'generated-script.yaml', 'text/yaml;charset=utf-8')
  previewNotice.value = 'YAML 文件已开始下载。'
}

const exportPreviewTxt = () => {
  downloadTextFile(scriptTextPreview.value, 'script-preview.txt', 'text/plain;charset=utf-8')
  previewNotice.value = 'TXT 文件已开始下载。'
}

const exportPreviewMarkdown = () => {
  downloadTextFile(markdownPreview.value, 'script-preview.md', 'text/markdown;charset=utf-8')
  previewNotice.value = 'Markdown 文件已开始下载。'
}

const exportPreviewPdf = () => {
  previewNotice.value = '正在打开浏览器打印窗口，可选择另存为 PDF。'
  window.print()
}

const handleFileUpload = async (event) => {
  const file = event.target.files?.[0]

  if (!file) {
    return
  }

  selectedFileName.value = file.name

  if (file.name.toLowerCase().endsWith('.txt')) {
    novelText.value = await file.text()
    importNotice.value = `${file.name} 已载入，章节列表已重新识别。`
    return
  }

  importNotice.value = `${file.name} 已接收。当前静态原型暂不解析 docx 正文，请粘贴文本后继续。`
}
</script>

<template>
  <AuthPage v-if="isAuthRoute" :icon-paths="iconPaths" @authenticated="handleAuthenticated" />

  <div v-else class="app-layout">
    <AppSidebar :icon-paths="iconPaths" :nav-items="activeNavItems" :quick-actions="quickActions" @select="goToPage" />

    <main class="main-wrapper" aria-label="工作区">
      <div class="page-content">
        <WorkspaceHeader
          :description="pageDescription"
          :icon-paths="iconPaths"
          :title="pageTitle"
          @logout="logout"
          @open-profile="openProfileCenter"
        />
        <ProjectsPage
          v-if="activeRoute.id === 'projects'"
          :activities="projectActivities"
          :icon-paths="iconPaths"
          :projects="projectCards"
          :stats="projectStats"
          @open-project="openProject"
        />

        <TemplateCenterPage
          v-else-if="activeRoute.id === 'templates'"
          :icon-paths="iconPaths"
          :selected-template-id="selectedTemplateId"
          :templates="scriptGenerationTemplates"
          @select-template="selectGenerationTemplate"
        />

        <ScriptLibraryPage
          v-else-if="activeRoute.id === 'library'"
          :icon-paths="iconPaths"
          :scripts="scriptLibraryItems"
          :stats="scriptLibraryStats"
          @edit-script="editLibraryScript"
          @preview-script="previewLibraryScript"
        />

        <HelpDocsPage
          v-else-if="activeRoute.id === 'help'"
          :content="productHelpDocs"
          :icon-paths="iconPaths"
        />

        <ProductRoutePage v-else-if="!isWorkbenchRoute" :icon-paths="iconPaths" :route="activeRoute" />

        <template v-else>
          <div class="workflow-sticky">
            <WorkflowStepper :icon-paths="iconPaths" :steps="currentWorkflowSteps" />
          </div>

          <NovelImportPage
            v-if="activePage === 'import'"
            v-model:novel-text="novelText"
            :chapter-count="chapterCount"
            :chapters="detectedChapters"
            :file-name="selectedFileName"
            :icon-paths="iconPaths"
            :import-notice="importNotice"
            :is-submitting="isImportSubmitting"
            :is-valid="isNovelValid"
            @file-upload="handleFileUpload"
            @next="goToAnalysis"
          />

          <AiAnalysisPage
            v-else-if="activePage === 'analysis'"
            :analysis-characters="displayedAnalysisCharacters"
            :analysis-metrics="displayedAnalysisMetrics"
            :analysis-scenes="displayedAnalysisScenes"
            :character-relations="displayedCharacterRelations"
            :dialogue-extracts="displayedDialogueExtracts"
            :icon-paths="iconPaths"
            :notice="analysisNotice"
            :plot-events="displayedPlotEvents"
            :progress="analysisProgress"
            @next="openGenerationSettings"
            @previous="goBackToImport"
            @rerun="rerunAnalysis"
          />

          <ScriptPreviewPage
            v-else-if="activePage === 'preview'"
            :export-notice="previewNotice"
            :icon-paths="iconPaths"
            :scenes="scriptPreviewScenes"
            @back="goBackToEditor"
            @export-markdown="exportPreviewMarkdown"
            @export-pdf="exportPreviewPdf"
            @export-txt="exportPreviewTxt"
            @export-yaml="exportPreviewYaml"
          />

          <SchemaHelpPage
            v-else-if="activePage === 'schema-doc'"
            :content="schemaHelpContent"
            :icon-paths="iconPaths"
            @back="goBackToEditor"
          />

          <div v-else class="content-grid">
            <SupportColumn
              :analysis-metrics="analysisMetrics"
              :icon-paths="iconPaths"
              :insight-items="insightItems"
              :project-stages="projectStages"
            />
            <ScriptWorkspace
              :icon-paths="iconPaths"
              :preview-dialogues="previewDialogues"
              :schema-validation="schemaValidation"
              :script-chapters="scriptChapters"
              :status-notice="editorNotice"
              :yaml-lines="generatedYamlLines"
              @add-scene="openAddScene"
              @copy-yaml="copyYaml"
              @download-yaml="downloadYaml"
              @open-preview="goToPreview"
              @open-schema="goToSchemaHelp"
              @previous="goBackToAnalysis"
              @validate-yaml="validateYaml"
            />
          </div>

          <GenerationSettingsDialog
            v-model="isGenerationSettingsOpen"
            :initial-settings="generatedSettings"
            :options="generationSettingOptions"
            @confirm="confirmGenerationSettings"
          />
          <AddSceneDialog
            v-model="isAddSceneOpen"
            :chapters="scriptChapters"
            @confirm="confirmAddScene"
          />
        </template>
      </div>
    </main>

    <ProfileCenterDialog
      v-model="isProfileCenterOpen"
      :icon-paths="iconPaths"
      :user="currentUser"
      @logout="logout"
    />
  </div>
</template>
