<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AddSceneDialog from './components/AddSceneDialog.vue'
import AiAnalysisPage from './components/AiAnalysisPage.vue'
import AppSidebar from './components/AppSidebar.vue'
import GenerationSettingsDialog from './components/GenerationSettingsDialog.vue'
import NovelImportPage from './components/NovelImportPage.vue'
import ProductRoutePage from './components/ProductRoutePage.vue'
import SchemaHelpPage from './components/SchemaHelpPage.vue'
import ScriptPreviewPage from './components/ScriptPreviewPage.vue'
import ScriptWorkspace from './components/ScriptWorkspace.vue'
import SupportColumn from './components/SupportColumn.vue'
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
  projectStages,
  quickActions,
  schemaHelpContent,
  schemaValidationMock,
  scriptChapters,
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
const isGenerationSettingsOpen = ref(false)
const isAddSceneOpen = ref(false)
const generatedSettings = ref(null)
const schemaValidation = ref(schemaValidationMock)
const editorNotice = ref('')
const previewNotice = ref('')

const activeRoute = computed(() => getRouteById(route.name))
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
  const matches = [...novelText.value.matchAll(/(?:^|\n)\s*((?:第[\d一二三四五六七八九十百]+章|Chapter\s*\d+)[^\n]*)/gi)]

  return matches.map((match, index) => {
    const start = match.index || 0
    const end = matches[index + 1]?.index ?? novelText.value.length
    const body = novelText.value.slice(start, end).replace(match[1], '').trim()
    const excerpt = body.replace(/\s+/g, ' ').slice(0, 46)

    return {
      title: match[1].trim(),
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

const goToPage = (pageId) => {
  const targetRoute = getRouteById(pageId)

  router.push(targetRoute.path)

  if (pageId === 'workbench') {
    activePage.value = 'import'
  }
}

const goToAnalysis = () => {
  analysisProgress.value = 100
  analysisNotice.value = ''
  activePage.value = 'analysis'
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
  <div class="app-layout">
    <AppSidebar :icon-paths="iconPaths" :nav-items="activeNavItems" :quick-actions="quickActions" @select="goToPage" />

    <main class="main-wrapper" aria-label="工作区">
      <div class="page-content">
        <WorkspaceHeader :description="pageDescription" :icon-paths="iconPaths" :title="pageTitle" />
        <ProductRoutePage v-if="!isWorkbenchRoute" :icon-paths="iconPaths" :route="activeRoute" />

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
            :is-valid="isNovelValid"
            @file-upload="handleFileUpload"
            @next="goToAnalysis"
          />

          <AiAnalysisPage
            v-else-if="activePage === 'analysis'"
            :analysis-characters="analysisCharacters"
            :analysis-metrics="analysisMetrics"
            :analysis-scenes="analysisScenes"
            :character-relations="characterRelations"
            :dialogue-extracts="dialogueExtracts"
            :icon-paths="iconPaths"
            :notice="analysisNotice"
            :plot-events="plotEvents"
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
  </div>
</template>
