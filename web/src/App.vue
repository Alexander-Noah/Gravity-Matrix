<script setup>
import { computed, ref } from 'vue'
import AiAnalysisPage from './components/AiAnalysisPage.vue'
import AppSidebar from './components/AppSidebar.vue'
import NovelImportPage from './components/NovelImportPage.vue'
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
  iconPaths,
  importWorkflowSteps,
  insightItems,
  navItems,
  plotEvents,
  previewDialogues,
  projectStages,
  quickActions,
  scriptChapters,
  workflowSteps,
  yamlLines,
} from './data/workbench'

const activePage = ref('import')
const novelText = ref(defaultNovelText)
const selectedFileName = ref('')
const importNotice = ref('')
const analysisProgress = ref(100)
const analysisNotice = ref('')

const activeNavItems = computed(() =>
  navItems.map((item) => ({
    ...item,
    active: item.id === 'workbench',
  })),
)

const pageTitle = computed(() => {
  return '小说转剧本工作台'
})
const pageDescription = computed(() => {
  if (activePage.value === 'import') {
    return '上传文件或粘贴原文，检查章节完整度后进入 AI 解析'
  }

  if (activePage.value === 'analysis') {
    return '检查人物、场景、剧情事件、人物关系和对白提取结果'
  }

  return '从小说到剧本，只需几步'
})
const currentWorkflowSteps = computed(() => {
  if (activePage.value === 'import') {
    return importWorkflowSteps
  }

  if (activePage.value === 'analysis') {
    return analysisWorkflowSteps
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

const goToPage = (pageId) => {
  if (pageId !== 'workbench') {
    return
  }

  activePage.value = 'import'
}

const goToAnalysis = () => {
  analysisProgress.value = 100
  analysisNotice.value = ''
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

const showGenerationPlaceholder = () => {
  analysisNotice.value = '生成设置弹窗将在下一次小粒度提交中实现。'
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
          @next="showGenerationPlaceholder"
          @rerun="rerunAnalysis"
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
            :script-chapters="scriptChapters"
            :yaml-lines="yamlLines"
          />
        </div>
      </div>
    </main>
  </div>
</template>
