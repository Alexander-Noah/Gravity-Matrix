<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import yaml from 'js-yaml'
import { clearAuthSession, getAuthSession } from './api/auth'
import { getApiErrorMessage } from './api/http'
import {
  createProject,
  diagnoseProjectScriptDraft,
  getJob,
  getProjectReadiness,
  getProjectAnalysis,
  getProjectScript,
  getProjectWorkbench,
  listProjects,
  saveProjectScript,
  startAnalysisJob,
  startScriptJob,
  validateProjectScript,
  updateGenerationSettings,
  rerunAnalysisJob,
  addProjectScene,
  exportProjectMarkdown,
  exportProjectTxt,
  deleteProject,
} from './api/workbench'
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
const generatedScriptYaml = ref('')
const schemaValidation = ref(schemaValidationMock)
const editorNotice = ref('')
const previewNotice = ref('')
const selectedTemplateId = ref(localStorage.getItem('gravityMatrixSelectedTemplate') || 'tv-drama')
const currentUser = ref(getAuthSession().user)
const isProfileCenterOpen = ref(false)
const displayedAnalysisCharacters = ref(analysisCharacters)
const displayedAnalysisMetrics = ref(analysisMetrics)
const displayedAnalysisScenes = ref(analysisScenes)
const displayedPlotEvents = ref(plotEvents)
const displayedCharacterRelations = ref(characterRelations)
const displayedDialogueExtracts = ref(dialogueExtracts)
const displayedScriptChapters = ref(scriptChapters)
const displayedProjectCards = ref(projectCards)
const displayedProjectStats = ref(projectStats)
const displayedProjectActivities = ref(projectActivities)
const displayedLibraryItems = ref(scriptLibraryItems)
const displayedLibraryStats = ref(scriptLibraryStats)

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

const yamlTextToLines = (yamlText) =>
  yamlText.split('\n').map((line) => {
    if (!line.trim()) {
      return []
    }

    const keyMatch = line.match(/^(\s*-?\s*[\w.-]+:)(.*)$/)

    if (!keyMatch) {
      return [{ text: line, tone: 'value' }]
    }

    const value = keyMatch[2]
    const trimmedValue = value.trim()
    const valueTone = /^["'].*["']$/.test(trimmedValue) ? 'string' : /^\d+$/.test(trimmedValue) ? 'number' : 'value'

    return [
      { text: keyMatch[1], tone: 'key' },
      { text: value, tone: valueTone },
    ]
  })

const mapDiagnosisToSchemaValidation = (diagnosis, fallbackValid = true) => {
  const summary = diagnosis?.summary || {}

  return {
    yamlValid: diagnosis?.valid_schema ?? fallbackValid,
    requiredFieldsValid: diagnosis?.valid_schema ?? fallbackValid,
    chapterCount: summary.chapter_count ?? schemaValidationMock.chapterCount,
    sceneCount: summary.scene_count ?? schemaValidationMock.sceneCount,
    checkedAt: `刚刚校验 · ${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`,
    message: diagnosis?.valid_schema === false
      ? '校验未通过：请根据后端返回的诊断建议修正 YAML。'
      : `校验通过：发现 ${summary.issue_count ?? 0} 个结构问题，质量等级 ${diagnosis?.grade || 'A'}。`,
  }
}

const formatProjectTime = (value) => {
  if (!value) {
    return '刚刚更新'
  }

  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const mapProjectStatus = (project) => {
  if (project.status === 'script_edited') {
    return '编辑中'
  }

  if (project.has_script) {
    return '待导出'
  }

  if (project.has_analysis) {
    return '待生成剧本'
  }

  return '待解析'
}

const mapProjectProgress = (project) => {
  if (project.status === 'script_edited') {
    return 100
  }

  if (project.has_script) {
    return 90
  }

  if (project.has_analysis) {
    return 60
  }

  return 30
}

const mapProjectNextAction = (project) => {
  if (project.has_script) {
    return '继续编辑 YAML'
  }

  if (project.has_analysis) {
    return '生成剧本'
  }

  return '进入 AI 解析'
}

const mapProjectCard = (project) => ({
  id: project.id,
  title: `《${project.title}》改编项目`,
  type: project.has_script ? '结构化剧本 / YAML' : '小说改编 / 工作台',
  status: mapProjectStatus(project),
  progress: mapProjectProgress(project),
  updatedAt: formatProjectTime(project.updated_at),
  chapters: project.chapter_count,
  scenes: project.has_script ? '已生成' : 0,
  owner: project.author || '创作者',
  nextAction: mapProjectNextAction(project),
  raw: project,
})

const applyProjectsResult = (result) => {
  const projects = result.items || []
  const scriptCount = projects.filter((project) => project.has_script).length
  const editingCount = projects.filter((project) => project.status === 'script_edited').length
  const analysisPendingCount = projects.filter((project) => !project.has_analysis).length

  displayedProjectCards.value = projects.length ? projects.map(mapProjectCard) : projectCards
  displayedProjectStats.value = [
    { label: '全部项目', value: String(result.total ?? projects.length), note: '来自后端项目列表', tone: 'violet' },
    { label: '编辑中', value: String(editingCount), note: '已保存剧本草稿', tone: 'blue' },
    { label: '已生成剧本', value: String(scriptCount), note: '可继续编辑或导出', tone: 'mint' },
    { label: '待解析', value: String(analysisPendingCount), note: '需要进入 AI 解析', tone: 'orange' },
  ]
  displayedProjectActivities.value = projects.slice(0, 4).map((project) => ({
    title: `${mapProjectNextAction(project)}：${project.title}`,
    time: formatProjectTime(project.updated_at),
    status: mapProjectStatus(project),
  }))
}

const mapLibraryStatus = (project, diagnosis) => {
  if (diagnosis?.valid_schema === false) {
    return '校验异常'
  }

  if (project.status === 'script_edited') {
    return '编辑中'
  }

  return project.has_script ? '已完成' : '草稿'
}

const mapLibraryItem = (project, workbench) => {
  const diagnosis = workbench?.script?.diagnosis
  const summary = diagnosis?.summary || {}

  return {
    id: `project-${project.id}`,
    projectId: project.id,
    title: `《${project.title}》剧本`,
    sourceNovel: `《${project.title}》`,
    type: '影视剧',
    chapters: summary.chapter_count ?? project.chapter_count,
    scenes: summary.scene_count ?? 0,
    dialogues: summary.dialogue_count ?? 0,
    schemaStatus: diagnosis?.valid_schema === false ? '校验异常' : '校验通过',
    status: mapLibraryStatus(project, diagnosis),
    updatedAt: formatProjectTime(project.updated_at),
    tags: [project.status, project.has_analysis ? '已解析' : '待解析', 'YAML'],
    raw: project,
  }
}

const applyLibraryResult = (items) => {
  const editingCount = items.filter((item) => item.status === '编辑中').length
  const completedCount = items.filter((item) => item.status === '已完成').length
  const exportedCount = items.filter((item) => item.status === '已导出').length

  displayedLibraryItems.value = items.length ? items : scriptLibraryItems
  displayedLibraryStats.value = [
    { label: '全部剧本', value: String(items.length), note: '来自后端已生成项目', tone: 'violet' },
    { label: '编辑中', value: String(editingCount), note: '已保存 YAML 草稿', tone: 'blue' },
    { label: '已完成', value: String(completedCount), note: '可进入完整预览', tone: 'mint' },
    { label: '已导出', value: String(exportedCount), note: '后端暂未返回导出历史', tone: 'orange' },
  ]
}

const applyWorkbenchScript = (workbench) => {
  if (workbench?.script?.yaml) {
    generatedScriptYaml.value = workbench.script.yaml
  }

  if (workbench?.script?.structure?.length) {
    displayedScriptChapters.value = workbench.script.structure.map((chapter) => ({
      title: chapter.title || chapter.label,
      open: chapter.open,
      scenes: chapter.scenes.map((scene) => ({
        label: scene.label || scene.title,
        active: scene.active,
      })),
    }))
  }

  if (workbench?.script?.diagnosis) {
    schemaValidation.value = mapDiagnosisToSchemaValidation(workbench.script.diagnosis)
  }
}

const fetchProjects = async () => {
  try {
    const result = await listProjects()
    applyProjectsResult(result)
  } catch (error) {
    displayedProjectActivities.value = [
      {
        title: getApiErrorMessage(error),
        time: '刚刚',
        status: '加载失败',
      },
      ...projectActivities,
    ]
  }
}

const fetchScriptLibrary = async () => {
  try {
    const result = await listProjects()
    const scriptProjects = (result.items || []).filter((project) => project.has_script)
    const items = await Promise.all(
      scriptProjects.map(async (project) => {
        try {
          const workbench = await getProjectWorkbench(project.id)
          return mapLibraryItem(project, workbench)
        } catch {
          return mapLibraryItem(project, null)
        }
      }),
    )

    applyLibraryResult(items)
  } catch {
    displayedLibraryItems.value = scriptLibraryItems
    displayedLibraryStats.value = scriptLibraryStats
  }
}

watch(
  () => activeRoute.value.id,
  (routeId) => {
    if (routeId === 'projects') {
      fetchProjects()
    }

    if (routeId === 'library') {
      fetchScriptLibrary()
    }
  },
  { immediate: true },
)

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
  if (generatedScriptYaml.value) {
    return yamlTextToLines(generatedScriptYaml.value)
  }

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
  generatedScriptYaml.value || generatedYamlLines.value.map((line) => line.map((token) => token.text).join('')).join('\n'),
)
const displayedPreviewScenes = computed(() => {
  if (!generatedScriptYaml.value) return scriptPreviewScenes

  try {
    const parsed = yaml.load(generatedScriptYaml.value)
    if (!parsed || !parsed.script || !parsed.script.chapters) return scriptPreviewScenes
    
    const scenes = []
    parsed.script.chapters.forEach((chapter, cIdx) => {
      if (!chapter.scenes) return
      chapter.scenes.forEach((scene, sIdx) => {
        const characters = new Set()
        const dialogues = []
        if (scene.dialogues) {
          scene.dialogues.forEach(d => {
            characters.add(d.speaker)
            dialogues.push({ speaker: d.speaker, note: d.note || '', line: d.line })
          })
        }
        
        scenes.push({
          title: `场景 ${cIdx + 1}-${sIdx + 1} ${scene.label || scene.location || '未知场景'}`,
          meta: `${scene.interior || '内/外景'} / ${scene.location || '未知地点'} / ${scene.time || '未知时间'}`,
          characters: Array.from(characters),
          action: scene.action || '无动作描写',
          dialogues: dialogues
        })
      })
    })
    return scenes.length ? scenes : scriptPreviewScenes
  } catch (e) {
    console.error('YAML parsing error', e)
    return scriptPreviewScenes
  }
})

const scriptTextPreview = computed(() =>
  displayedPreviewScenes.value
    .map((scene) => {
      const cast = `出场人物：${scene.characters.join('、')}`
      const dialogues = scene.dialogues.map((dialogue) => `${dialogue.speaker}\n${dialogue.line}`).join('\n\n')

      return `${scene.title}\n${scene.meta}\n${cast}\n\n${scene.action}\n\n${dialogues}`
    })
    .join('\n\n---\n\n'),
)
const markdownPreview = computed(() =>
  displayedPreviewScenes.value
    .map((scene) => {
      const dialogues = scene.dialogues.map((dialogue) => `**${dialogue.speaker}**\n\n${dialogue.line}`).join('\n\n')

      return `## ${scene.title}\n\n${scene.meta}\n\n出场人物：${scene.characters.join('、')}\n\n${scene.action}\n\n${dialogues}`
    })
    .join('\n\n'),
)

const waitForJob = async (jobId, onProgress) => {
  for (let attempt = 0; attempt < 12; attempt += 1) {
    const job = await getJob(jobId)

    if (onProgress) {
      onProgress(job)
    } else {
      analysisProgress.value = job.progress ?? analysisProgress.value
      analysisNotice.value = job.current_step || analysisNotice.value
    }

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

  displayedAnalysisMetrics.value = [
    { label: '出场人物', value: String(characters.length), note: '主要角色', icon: 'user', tone: 'blue' },
    { label: '核心场景', value: String(locations.length), note: '主要发生地', icon: 'location', tone: 'mint' },
    { label: '核心主题', value: String(themes.length), note: '故事基调', icon: 'message', tone: 'violet' },
    { label: '冲突事件', value: String(conflicts.length), note: '高潮与转折', icon: 'conflict', tone: 'orange' },
  ]

  if (themes.length) {
    displayedInsightItems.value = themes.map((theme, idx) => ({
      title: `主题 ${idx + 1}`,
      description: `剧本围绕 "${theme}" 展开，建议在对白中强化这一主旨。`,
      tone: ['blue', 'mint', 'orange', 'violet'][idx % 4]
    }))
  } else {
    displayedInsightItems.value = insightItems
  }

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

const handleDeleteProject = async (project) => {
  if (!confirm(`确定要删除项目《${project.raw?.title || project.title}》吗？此操作无法恢复。`)) return

  try {
    await deleteProject(project.id)
    await fetchProjects()
  } catch (error) {
    alert('删除失败: ' + getApiErrorMessage(error))
  }
}

const openProject = async (project) => {
  router.push('/workbench')
  currentProjectId.value = project?.id || project?.raw?.id || null

  if (!currentProjectId.value) {
    if (project?.scenes === 0 || project?.progress < 50) {
      activePage.value = 'analysis'
      return
    }

    if (project?.progress >= 90) {
      activePage.value = 'preview'
      return
    }

    activePage.value = 'script'
    return
  }

  try {
    const workbench = await getProjectWorkbench(currentProjectId.value)

    if (workbench.analysis?.raw) {
      applyAnalysisResult(workbench.analysis.raw)
    }

    applyWorkbenchScript(workbench)

    if (workbench.project.has_script) {
      activePage.value = 'script'
      return
    }

    if (workbench.project.has_analysis) {
      activePage.value = 'analysis'
      return
    }

    activePage.value = 'import'
  } catch (error) {
    analysisNotice.value = getApiErrorMessage(error)
    activePage.value = 'analysis'
  }
}

const selectGenerationTemplate = (templateId) => {
  selectedTemplateId.value = templateId
  localStorage.setItem('gravityMatrixSelectedTemplate', templateId)
  // Navigate back to workbench if selected from template center
  if (activeRoute.value.id === 'templates') {
    router.push('/workbench')
  }
}

const defaultGenerationSettings = computed(() => {
  const templateId = selectedTemplateId.value
  let scriptType = '影视剧'
  if (templateId === 'short-drama') scriptType = '短剧'
  if (templateId === 'stage-play') scriptType = '话剧'
  if (templateId === 'storyboard') scriptType = '分镜剧本'

  return {
    scriptType,
    adaptationStyle: generationSettingOptions.adaptationStyles[0],
    contentOptions: generationSettingOptions.contentOptions.slice(0, 2),
  }
})

const editLibraryScript = async (script) => {
  router.push('/workbench')
  currentProjectId.value = script?.projectId || script?.raw?.id || null

  if (currentProjectId.value) {
    try {
      const workbench = await getProjectWorkbench(currentProjectId.value)
      applyWorkbenchScript(workbench)
    } catch (error) {
      editorNotice.value = getApiErrorMessage(error)
    }
  }

  activePage.value = 'script'
}

const previewLibraryScript = async (script) => {
  router.push('/workbench')
  currentProjectId.value = script?.projectId || script?.raw?.id || null
  previewNotice.value = ''

  if (currentProjectId.value) {
    try {
      const workbench = await getProjectWorkbench(currentProjectId.value)
      applyWorkbenchScript(workbench)
    } catch (error) {
      previewNotice.value = getApiErrorMessage(error)
    }
  }

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

const rerunAnalysis = async () => {
  if (!currentProjectId.value) return
  analysisProgress.value = 10
  analysisNotice.value = '正在请求后端重新解析小说内容...'

  try {
    const job = await rerunAnalysisJob(currentProjectId.value)
    analysisNotice.value = job.current_step || '重新解析任务已启动...'
    analysisProgress.value = job.progress || 30
    await waitForJob(job.id)
    const analysis = await getProjectAnalysis(currentProjectId.value)
    applyAnalysisResult(analysis)
    analysisProgress.value = 100
    analysisNotice.value = '重新解析完成，结果已从后端同步。'
  } catch (error) {
    analysisNotice.value = getApiErrorMessage(error)
  }
}

const openGenerationSettings = () => {
  isGenerationSettingsOpen.value = true
}

const confirmGenerationSettings = async (settings) => {
  generatedSettings.value = settings
  isGenerationSettingsOpen.value = false
  editorNotice.value = '正在启动剧本生成任务...'
  schemaValidation.value = schemaValidationMock
  activePage.value = 'script'

  if (!currentProjectId.value) {
    editorNotice.value = '当前为静态演示剧本，请先从小说导入流程创建项目后再调用后端生成。'
    return
  }

  try {
    await updateGenerationSettings(currentProjectId.value, settings)
    const job = await startScriptJob(currentProjectId.value)
    editorNotice.value = job.current_step || '剧本生成任务已启动。'

    await waitForJob(job.id, (currentJob) => {
      editorNotice.value = `${currentJob.current_step}（${currentJob.progress}%）`
    })

    const script = await getProjectScript(currentProjectId.value)
    generatedScriptYaml.value = script.yaml

    const workbench = await getProjectWorkbench(currentProjectId.value)
    applyWorkbenchScript(workbench)
    editorNotice.value = '剧本 YAML 已从后端生成并同步到编辑区。'
  } catch (error) {
    editorNotice.value = getApiErrorMessage(error)
  }
}

const openAddScene = () => {
  isAddSceneOpen.value = true
}

const confirmAddScene = async (sceneDraft) => {
  isAddSceneOpen.value = false
  if (!currentProjectId.value) {
    editorNotice.value = `${sceneDraft.sceneTitle} 已加入场景草稿，后续可写入 YAML。`
    return
  }

  try {
    editorNotice.value = `正在将场景 ${sceneDraft.sceneTitle} 提交至后端...`
    await addProjectScene(currentProjectId.value, sceneDraft)
    const workbench = await getProjectWorkbench(currentProjectId.value)
    applyWorkbenchScript(workbench)
    editorNotice.value = `场景 ${sceneDraft.sceneTitle} 已成功保存。`
  } catch (error) {
    editorNotice.value = `场景保存失败：${getApiErrorMessage(error)}`
  }
}

const validateYaml = async () => {
  if (!currentProjectId.value) {
    schemaValidation.value = {
      ...schemaValidationMock,
      checkedAt: `刚刚校验 · ${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`,
      message: '校验通过：YAML 格式正确，必填字段完整。',
    }
    editorNotice.value = 'Schema 校验已完成。'
    return
  }

  try {
    editorNotice.value = '正在调用后端校验 YAML...'
    const validation = await validateProjectScript(currentProjectId.value, generatedYamlText.value)
    const diagnosis = await diagnoseProjectScriptDraft(currentProjectId.value, generatedYamlText.value)

    schemaValidation.value = {
      ...mapDiagnosisToSchemaValidation(diagnosis, validation.valid),
      yamlValid: validation.valid,
      requiredFieldsValid: validation.valid,
      message: validation.valid
        ? mapDiagnosisToSchemaValidation(diagnosis, validation.valid).message
        : `校验未通过：${validation.errors.join('；')}`,
    }
    editorNotice.value = validation.valid ? '后端 Schema 校验已通过。' : '后端 Schema 校验未通过，请查看提示。'
  } catch (error) {
    editorNotice.value = getApiErrorMessage(error)
  }
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

const exportPreviewMarkdown = async () => {
  if (currentProjectId.value) {
    try {
      previewNotice.value = '正在向服务端请求导出 Markdown...'
      const blob = await exportProjectMarkdown(currentProjectId.value)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `project-${currentProjectId.value}-script.md`
      link.click()
      URL.revokeObjectURL(url)
      previewNotice.value = '服务端 Markdown 文件下载完成。'
    } catch (error) {
      previewNotice.value = '下载失败：' + getApiErrorMessage(error)
    }
    return
  }

  downloadTextFile(markdownPreview.value, 'generated-script.md', 'text/markdown;charset=utf-8')
  previewNotice.value = 'Markdown 文件已开始下载。'
}

const exportPreviewPdf = () => {
  previewNotice.value = '正在打开浏览器打印窗口，可选择另存为 PDF。'
  window.print()
}

const exportPreviewTxt = async () => {
  if (currentProjectId.value) {
    try {
      previewNotice.value = '正在向服务端请求导出 TXT...'
      const blob = await exportProjectTxt(currentProjectId.value)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `project-${currentProjectId.value}-script.txt`
      link.click()
      URL.revokeObjectURL(url)
      previewNotice.value = '服务端 TXT 文件下载完成。'
    } catch (error) {
      previewNotice.value = '下载失败：' + getApiErrorMessage(error)
    }
    return
  }

  downloadTextFile(scriptTextPreview.value, 'generated-script.txt', 'text/plain;charset=utf-8')
  previewNotice.value = 'TXT 文件已开始下载。'
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
    <AppSidebar :icon-paths="iconPaths" :nav-items="activeNavItems" @select="goToPage" />

    <main class="main-wrapper" aria-label="工作区">
      <div class="page-content">
        <WorkspaceHeader :description="pageDescription" :icon-paths="iconPaths" :title="pageTitle" @logout="logout"
          @open-profile="openProfileCenter" />
        <ProjectsPage v-if="activeRoute.id === 'projects'" :activities="displayedProjectActivities"
          :icon-paths="iconPaths" :projects="displayedProjectCards" :stats="displayedProjectStats"
          @open-project="openProject" @delete-project="handleDeleteProject" />

        <TemplateCenterPage v-else-if="activeRoute.id === 'templates'" :icon-paths="iconPaths"
          :selected-template-id="selectedTemplateId" :templates="scriptGenerationTemplates"
          @select-template="selectGenerationTemplate" />

        <ScriptLibraryPage v-else-if="activeRoute.id === 'library'" :icon-paths="iconPaths"
          :scripts="displayedLibraryItems" :stats="displayedLibraryStats" @edit-script="editLibraryScript"
          @preview-script="previewLibraryScript" />

        <HelpDocsPage v-else-if="activeRoute.id === 'help'" :content="productHelpDocs" :icon-paths="iconPaths" />

        <ProductRoutePage v-else-if="!isWorkbenchRoute" :icon-paths="iconPaths" :route="activeRoute" />

        <template v-else>
          <div class="workflow-sticky">
            <WorkflowStepper :icon-paths="iconPaths" :steps="currentWorkflowSteps" />
          </div>

          <NovelImportPage v-if="activePage === 'import'" v-model:novel-text="novelText" :chapter-count="chapterCount"
            :chapters="detectedChapters" :file-name="selectedFileName" :icon-paths="iconPaths"
            :import-notice="importNotice" :is-submitting="isImportSubmitting" :is-valid="isNovelValid"
            @file-upload="handleFileUpload" @next="goToAnalysis" />

          <AiAnalysisPage v-else-if="activePage === 'analysis'" :analysis-characters="displayedAnalysisCharacters"
            :analysis-metrics="displayedAnalysisMetrics" :analysis-scenes="displayedAnalysisScenes"
            :character-relations="displayedCharacterRelations" :dialogue-extracts="displayedDialogueExtracts"
            :icon-paths="iconPaths" :notice="analysisNotice" :plot-events="displayedPlotEvents"
            :progress="analysisProgress" @next="openGenerationSettings" @previous="goBackToImport"
            @rerun="rerunAnalysis" />

          <ScriptPreviewPage v-else-if="activePage === 'preview'" :export-notice="previewNotice" :icon-paths="iconPaths"
            :scenes="displayedPreviewScenes" @back="goBackToEditor" @export-markdown="exportPreviewMarkdown"
            @export-pdf="exportPreviewPdf" @export-txt="exportPreviewTxt" @export-yaml="exportPreviewYaml" />

          <SchemaHelpPage v-else-if="activePage === 'schema-doc'" :content="schemaHelpContent" :icon-paths="iconPaths"
            @back="goBackToEditor" />

          <div v-else class="content-grid">
            <SupportColumn
              :analysis-metrics="displayedAnalysisMetrics" :icon-paths="iconPaths" :insight-items="displayedInsightItems"
              :project-stages="projectStages" />
            <ScriptWorkspace :icon-paths="iconPaths" :preview-dialogues="previewDialogues"
              :schema-validation="schemaValidation" :script-chapters="displayedScriptChapters"
              :status-notice="editorNotice" :yaml-lines="generatedYamlLines" @add-scene="openAddScene"
              @copy-yaml="copyYaml" @download-yaml="downloadYaml" @open-preview="goToPreview"
              @open-schema="goToSchemaHelp" @previous="goBackToAnalysis" @validate-yaml="validateYaml" />
          </div>

          <GenerationSettingsDialog v-model="isGenerationSettingsOpen" :initial-settings="generatedSettings || defaultGenerationSettings"
            :options="generationSettingOptions" @confirm="confirmGenerationSettings" />
          <AddSceneDialog v-model="isAddSceneOpen" :chapters="displayedScriptChapters" @confirm="confirmAddScene" />
        </template>
      </div>
    </main>

    <ProfileCenterDialog v-model="isProfileCenterOpen" :icon-paths="iconPaths" :user="currentUser" @logout="logout" />
  </div>
</template>
