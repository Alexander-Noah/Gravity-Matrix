<script setup>
import { computed, ref } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import NovelImportPage from './components/NovelImportPage.vue'
import ScriptWorkspace from './components/ScriptWorkspace.vue'
import SupportColumn from './components/SupportColumn.vue'
import WorkflowStepper from './components/WorkflowStepper.vue'
import WorkspaceHeader from './components/WorkspaceHeader.vue'
import {
  analysisMetrics,
  defaultNovelText,
  iconPaths,
  importWorkflowSteps,
  insightItems,
  navItems,
  previewDialogues,
  projectStages,
  quickActions,
  scriptChapters,
  workflowSteps,
  yamlLines,
} from './data/workbench'

const activePage = ref('workbench')
const novelText = ref(defaultNovelText)
const selectedFileName = ref('')
const importNotice = ref('')

const activeNavItems = computed(() =>
  navItems.map((item) => ({
    ...item,
    active: item.id === activePage.value,
  })),
)

const pageTitle = computed(() => (activePage.value === 'import' ? '小说导入' : '小说转剧本工作台'))
const pageDescription = computed(() =>
  activePage.value === 'import' ? '上传文件或粘贴原文，检查章节完整度后进入 AI 解析' : '从小说到剧本，只需几步',
)
const currentWorkflowSteps = computed(() => (activePage.value === 'import' ? importWorkflowSteps : workflowSteps))

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
  if (!['workbench', 'import'].includes(pageId)) {
    return
  }

  activePage.value = pageId
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
          @next="importNotice = 'AI解析页面将在下一次小粒度提交中实现。'"
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
