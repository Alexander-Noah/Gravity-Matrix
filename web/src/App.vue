<script setup>
import { computed, onMounted, ref, watch } from 'vue'
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
  getScriptTemplates,
  updateProject,
  cloneProject,
  previewImport,
  getProjectsDashboard,
  getScriptsLibrary,
  rerunScriptJob,
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
  previewWorkflowSteps,
  projectActivities,
  projectCards,
  projectStages,
  projectStats,
  productHelpDocs,
  schemaHelpContent,
  schemaValidationMock,
  scriptGenerationTemplates as mockTemplates,
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
const displayedInsightItems = ref(insightItems)
const displayedScriptChapters = ref(scriptChapters)
const displayedProjectCards = ref(projectCards)
const displayedProjectStats = ref(projectStats)
const displayedProjectActivities = ref(projectActivities)
const displayedLibraryItems = ref(scriptLibraryItems)
const displayedLibraryStats = ref(scriptLibraryStats)
const displayedTemplates = ref(mockTemplates)
const selectedSceneId = ref(null)
const projectListNotice = ref('')
const libraryNotice = ref('')
const isScriptGenerating = ref(false)

const CURRENT_PROJECT_STORAGE_KEY = 'gravityMatrixCurrentProjectId'

const setCurrentProjectId = (projectId) => {
  currentProjectId.value = projectId || null

  if (projectId) {
    localStorage.setItem(CURRENT_PROJECT_STORAGE_KEY, String(projectId))
    return
  }

  localStorage.removeItem(CURRENT_PROJECT_STORAGE_KEY)
}

const fetchTemplates = async () => {
  try {
    const templates = await getScriptTemplates()
    displayedTemplates.value = templates?.length ? templates : mockTemplates
  } catch (error) {
    console.warn('获取模板失败，使用本地默认模板', error)
  }
}

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
    return '导入小说原文，确认章节结构后进入 AI 解析与剧本生成流程'
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

const getScriptBody = (yamlText) => {
  if (!yamlText) return null

  const parsed = yaml.load(yamlText)
  return parsed?.script || parsed
}

const buildScriptScenes = (yamlText) => {
  let script

  try {
    script = getScriptBody(yamlText)
  } catch (error) {
    console.error('YAML parsing error', error)
    return []
  }

  if (!script?.chapters?.length) return []

  const locationById = new Map((script.locations || []).map((location) => [location.id, location]))
  const characterById = new Map((script.characters || []).map((character) => [character.id, character]))
  const scenes = []

  script.chapters.forEach((chapter, chapterIndex) => {
    ;(chapter.scenes || []).forEach((scene, sceneIndex) => {
      const location = locationById.get(scene.location_id)
      const characters = (scene.characters || [])
        .map((characterId) => characterById.get(characterId)?.name || characterId)
        .filter(Boolean)
      const dialogues = (scene.dialogue || scene.dialogues || []).map((dialogue) => ({
        speaker: dialogue.speaker_name || dialogue.speaker || characterById.get(dialogue.speaker_id)?.name || '人物',
        note: dialogue.emotion || dialogue.note || '',
        line: dialogue.line || '',
      }))
      const stageDirections = scene.stage_directions || []
      const action = [
        scene.synopsis || scene.action,
        ...stageDirections,
      ].filter(Boolean).join('\n')

      scenes.push({
        id: scene.id || `${chapter.id || chapterIndex + 1}-${sceneIndex + 1}`,
        title: `场景 ${chapterIndex + 1}-${sceneIndex + 1} ${scene.title || scene.label || location?.name || '未命名场景'}`,
        meta: `${scene.interior || '场景'} / ${location?.name || scene.location || scene.location_id || '未知地点'} / ${scene.time || '未知时间'}`,
        characters: characters.length ? characters : dialogues.map((dialogue) => dialogue.speaker),
        action: action || '后端未返回场景动作说明。',
        dialogues,
      })
    })
  })

  return scenes
}

const applyWorkbenchScript = (workbench) => {
  if (workbench?.script?.yaml) {
    generatedScriptYaml.value = workbench.script.yaml
  } else if (currentProjectId.value) {
    generatedScriptYaml.value = ''
  }

  if (workbench?.script?.structure?.length) {
    displayedScriptChapters.value = workbench.script.structure.map((chapter) => ({
      id: chapter.id,
      title: chapter.title || chapter.label,
      open: chapter.open,
      scenes: chapter.scenes.map((scene) => ({
        id: scene.id,
        label: scene.label || scene.title,
        active: selectedSceneId.value ? scene.id === selectedSceneId.value : scene.active,
      })),
    }))

    if (!selectedSceneId.value) {
      selectedSceneId.value = workbench.script.structure[0]?.scenes?.[0]?.id || null
    }
  } else if (currentProjectId.value) {
    displayedScriptChapters.value = []
  }

  if (workbench?.script?.diagnosis) {
    schemaValidation.value = mapDiagnosisToSchemaValidation(workbench.script.diagnosis)
  }
}

const fetchProjects = async () => {
  projectListNotice.value = ''
  try {
    const dashboard = await getProjectsDashboard()
    if (dashboard) {
      displayedProjectStats.value = dashboard.stats || projectStats
      displayedProjectCards.value = dashboard.project_cards || dashboard.cards || []
      displayedProjectActivities.value = dashboard.activities || projectActivities
    }
  } catch (error) {
    projectListNotice.value = `项目列表加载失败：${getApiErrorMessage(error)}`
    displayedProjectStats.value = [
      { label: '进行中项目', value: '0', note: '后端暂不可用', tone: 'violet' },
      { label: '已生成剧本', value: '0', note: '后端暂不可用', tone: 'blue' },
      { label: '待校验 YAML', value: '0', note: '后端暂不可用', tone: 'orange' },
      { label: '已导出文件', value: '0', note: '后端暂不可用', tone: 'mint' },
    ]
    displayedProjectCards.value = []
    displayedProjectActivities.value = []
  }
}

const fetchScriptLibrary = async () => {
  libraryNotice.value = ''
  try {
    const library = await getScriptsLibrary()
    if (library) {
      displayedLibraryStats.value = library.stats || scriptLibraryStats
      displayedLibraryItems.value = library.items || []
    }
  } catch (error) {
    libraryNotice.value = `剧本库加载失败：${getApiErrorMessage(error)}`
    displayedLibraryStats.value = [
      { label: '全部剧本', value: '0', note: '后端暂不可用', tone: 'violet' },
      { label: '编辑中', value: '0', note: '后端暂不可用', tone: 'blue' },
      { label: '已完成', value: '0', note: '后端暂不可用', tone: 'mint' },
      { label: '校验异常', value: '0', note: '后端暂不可用', tone: 'orange' },
    ]
    displayedLibraryItems.value = []
  }
}

watch(
  () => activeRoute.value.id,
  (routeId) => {
    if (routeId === 'projects') {
      fetchProjects()
    } else if (routeId === 'templates') {
      fetchTemplates()
    } else if (routeId === 'library') {
      fetchScriptLibrary()
    }
  },
  { immediate: true },
)

watch(
  () => activeRoute.value.id,
  (routeId) => {
    if (routeId === 'workbench') {
      restoreWorkbenchProject()
    }
  },
)

onMounted(() => {
  restoreWorkbenchProject()
})

const detectedChapters = ref([])
const isNovelValid = ref(false)
const chapterCount = ref(0)

const detectChaptersLocally = (text) => {
  const matches = [
    ...text.matchAll(
      /(^|\n)\s*((?:第\s*[\d一二三四五六七八九十百千万零〇两]+\s*[章节回幕]|Chapter\s*\d+)[^\n]*)/gi,
    ),
  ]

  return matches.map((match, index) => {
    const titleStart = (match.index || 0) + match[1].length
    const nextStart = matches[index + 1]
      ? (matches[index + 1].index || 0) + matches[index + 1][1].length
      : text.length
    const chapterText = text.slice(titleStart, nextStart).trim()
    const body = chapterText.replace(match[2], '').trim()
    const excerpt = body.replace(/\s+/g, ' ').slice(0, 46)

    return {
      number: index + 1,
      title: match[2].trim(),
      content: body || chapterText,
      excerpt: excerpt ? `${excerpt}...` : '等待补充正文',
    }
  })
}

let previewTimeout = null
watch(novelText, (newText) => {
  if (previewTimeout) clearTimeout(previewTimeout)
  if (!newText || !newText.trim()) {
    detectedChapters.value = []
    chapterCount.value = 0
    isNovelValid.value = false
    return
  }

  previewTimeout = setTimeout(async () => {
    const localChapters = detectChaptersLocally(newText)

    try {
      const result = await previewImport({
        title: selectedFileName.value ? selectedFileName.value.replace(/\.[^.]+$/, '') : '未命名小说',
        author: '创作者',
        text: newText,
      })
      detectedChapters.value = (result.chapters || []).map((chapter, index) => ({
        ...chapter,
        content: chapter.content || localChapters[index]?.content || '',
        excerpt: chapter.excerpt || localChapters[index]?.excerpt || '等待补充正文',
      }))
      chapterCount.value = result.chapter_count || detectedChapters.value.length
      isNovelValid.value = result.can_create_project || false
    } catch (error) {
      console.warn('后端解析章节失败，请检查网络或后端服务', error)
      detectedChapters.value = localChapters
      chapterCount.value = localChapters.length
      isNovelValid.value = localChapters.length >= 3
      importNotice.value = '后端章节预览接口暂不可用，已使用本地章节识别。'
    }
  }, 800)
}, { immediate: true })
const generatedYamlLines = computed(() => {
  if (generatedScriptYaml.value) {
    return yamlTextToLines(generatedScriptYaml.value)
  }

  if (currentProjectId.value) {
    return yamlTextToLines('# 剧本 YAML 尚未生成。\n# 请等待后端任务完成，完成后这里会显示真实 YAML。')
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
  generatedScriptYaml.value || (!currentProjectId.value
    ? generatedYamlLines.value.map((line) => line.map((token) => token.text).join('')).join('\n')
    : ''),
)
const displayedPreviewScenes = computed(() => {
  if (!generatedScriptYaml.value) {
    return currentProjectId.value ? [] : scriptPreviewScenes
  }

  const scenes = buildScriptScenes(generatedScriptYaml.value)
  return scenes.length ? scenes : (currentProjectId.value ? [] : scriptPreviewScenes)
})

const selectedPreviewScene = computed(() => {
  if (!displayedPreviewScenes.value.length) {
    return null
  }

  return displayedPreviewScenes.value.find((scene) => scene.id === selectedSceneId.value) || displayedPreviewScenes.value[0]
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

const waitForJob = async (jobId, onProgress, { timeoutMs = 180000, intervalMs = 1000 } = {}) => {
  const startedAt = Date.now()
  let lastJob = null

  while (Date.now() - startedAt < timeoutMs) {
    const job = await getJob(jobId)
    lastJob = job

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
      window.setTimeout(resolve, intervalMs)
    })
  }

  throw new Error(lastJob?.current_step
    ? `任务仍在处理中：${lastJob.current_step}（${lastJob.progress ?? 0}%）。请稍后重试或刷新工作台查看结果。`
    : '任务仍在处理中，请稍后重试或刷新工作台查看结果。')
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

  if (pageId === 'workbench' && !currentProjectId.value) {
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
  setCurrentProjectId(project?.id || project?.raw?.id || null)

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

const getScriptProjectId = (script) => script?.projectId || script?.project_id || script?.raw?.id || null

const editLibraryScript = async (script) => {
  router.push('/workbench')
  setCurrentProjectId(getScriptProjectId(script))

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
  setCurrentProjectId(getScriptProjectId(script))
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

const restoreWorkbenchProject = async () => {
  if (!isWorkbenchRoute.value || currentProjectId.value) return

  const storedProjectId = Number(localStorage.getItem(CURRENT_PROJECT_STORAGE_KEY))
  let projectId = Number.isFinite(storedProjectId) && storedProjectId > 0 ? storedProjectId : null

  try {
    if (!projectId) {
      const projects = await listProjects({ limit: 1, offset: 0 })
      projectId = projects.items?.[0]?.id || null
    }

    if (!projectId) {
      activePage.value = 'import'
      return
    }

    setCurrentProjectId(projectId)
    const workbench = await getProjectWorkbench(projectId)

    if (workbench.analysis?.raw) {
      applyAnalysisResult(workbench.analysis.raw)
    }

    applyWorkbenchScript(workbench)

    if (workbench.project.has_script) {
      activePage.value = 'script'
      editorNotice.value = '已恢复最近生成的真实剧本。'
    } else if (workbench.project.has_analysis) {
      activePage.value = 'analysis'
      analysisNotice.value = '已恢复最近项目的 AI 解析结果。'
      analysisProgress.value = 100
    } else {
      activePage.value = 'import'
    }
  } catch (error) {
    console.warn('恢复工作台项目失败', error)
    setCurrentProjectId(null)
    activePage.value = 'import'
  }
}

const exportLibraryScript = async (script, format) => {
  const projectId = getScriptProjectId(script)
  if (!projectId) return

  try {
    let blob
    if (format === 'YAML') {
      const scriptData = await getProjectScript(projectId)
      blob = new Blob([scriptData.yaml], { type: 'text/yaml;charset=utf-8' })
    } else if (format === 'Markdown') {
      blob = await exportProjectMarkdown(projectId)
    } else if (format === 'PDF') {
      await previewLibraryScript(script)
      window.print()
      return
    } else {
      blob = await exportProjectTxt(projectId)
    }

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${script.title}.${format === 'Markdown' ? 'md' : format === 'YAML' ? 'yaml' : 'txt'}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    alert('导出失败: ' + getApiErrorMessage(error))
  }
}

const deleteLibraryScript = async (script) => {
  const projectId = getScriptProjectId(script)
  if (!projectId) return

  if (!confirm(`确定要删除剧本《${script.title}》吗？此操作无法恢复。`)) return

  try {
    await deleteProject(projectId)
    await fetchScriptLibrary()
  } catch (error) {
    alert('删除失败: ' + getApiErrorMessage(error))
  }
}

const renameLibraryScript = async (script) => {
  const projectId = getScriptProjectId(script)
  if (!projectId) return

  const newName = prompt('请输入新的剧本名称：', script.title)
  if (!newName || newName === script.title) return

  try {
    await updateProject(projectId, { title: newName })
    await fetchScriptLibrary()
  } catch (error) {
    alert('重命名失败: ' + getApiErrorMessage(error))
  }
}

const cloneLibraryScript = async (script) => {
  const projectId = getScriptProjectId(script)
  if (!projectId) return

  try {
    await cloneProject(projectId)
    await fetchScriptLibrary()
  } catch (error) {
    alert('复制失败: ' + getApiErrorMessage(error))
  }
}

const goToAnalysis = async () => {
  if (!isNovelValid.value || isImportSubmitting.value) {
    return
  }

  isImportSubmitting.value = true
  analysisProgress.value = 10
  importNotice.value = '正在创建小说改编项目...'
  let hasEnteredAnalysis = false
  generatedScriptYaml.value = ''
  selectedSceneId.value = null

  try {
    const project = await createProject({
      title: selectedFileName.value ? selectedFileName.value.replace(/\.[^.]+$/, '') : '小说改编项目',
      author: '创作者',
      chapters: detectedChapters.value.map((chapter) => ({
        title: chapter.title,
        content: chapter.content,
      })),
    })

    setCurrentProjectId(project.id)
    analysisProgress.value = 25
    importNotice.value = '项目已创建，正在启动 AI 解析任务...'

    const job = await startAnalysisJob(project.id)
    activePage.value = 'analysis'
    hasEnteredAnalysis = true
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
    if (hasEnteredAnalysis || currentProjectId.value) {
      activePage.value = 'analysis'
    } else {
      activePage.value = 'import'
    }
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
  if (isScriptGenerating.value) return

  generatedSettings.value = settings
  isGenerationSettingsOpen.value = false
  editorNotice.value = '正在启动剧本生成任务...'
  schemaValidation.value = schemaValidationMock
  activePage.value = 'script'
  generatedScriptYaml.value = ''
  selectedSceneId.value = null
  isScriptGenerating.value = true

  if (!currentProjectId.value) {
    editorNotice.value = '当前为静态演示剧本，请先从小说导入流程创建项目后再调用后端生成。'
    isScriptGenerating.value = false
    return
  }

  try {
    await updateGenerationSettings(currentProjectId.value, settings)
    const job = await rerunScriptJob(currentProjectId.value)
    editorNotice.value = job.current_step || '剧本生成任务已启动。'

    await waitForJob(job.id, (currentJob) => {
      editorNotice.value = `${currentJob.current_step}（${currentJob.progress}%）`
    }, { timeoutMs: 300000, intervalMs: 1200 })

    const script = await getProjectScript(currentProjectId.value)
    generatedScriptYaml.value = script.yaml

    const workbench = await getProjectWorkbench(currentProjectId.value)
    applyWorkbenchScript(workbench)
    editorNotice.value = '剧本 YAML 已从后端生成并同步到编辑区。'
  } catch (error) {
    editorNotice.value = getApiErrorMessage(error)
  } finally {
    isScriptGenerating.value = false
  }
}

const openAddScene = () => {
  isAddSceneOpen.value = true
}

const selectScriptScene = (sceneId) => {
  selectedSceneId.value = sceneId
  displayedScriptChapters.value = displayedScriptChapters.value.map((chapter) => ({
    ...chapter,
    scenes: chapter.scenes.map((scene) => ({
      ...scene,
      active: scene.id === sceneId,
    })),
  }))
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

const showRecycleBin = ref(false)
const recycleBinItems = ref([])

const openRecycleBin = () => {
  recycleBinItems.value = JSON.parse(localStorage.getItem('gravityMatrixRecycleBin') || '[]')
  showRecycleBin.value = true
}

const closeRecycleBin = () => {
  showRecycleBin.value = false
}

const clearRecycleBin = () => {
  if (!confirm('确定要清空回收站吗？此操作无法恢复。')) return
  localStorage.removeItem('gravityMatrixRecycleBin')
  recycleBinItems.value = []
}

const restoreFromRecycleBin = () => {
  previewNotice.value = '当前后端删除是永久删除，回收站只保留本地删除记录，暂不支持恢复。'
}


const handleFileUpload = async (event) => {
  const files = Array.from(event.target.files || [])

  if (!files.length) {
    return
  }

  selectedFileName.value = files.length === 1 ? files[0].name : `${files.length} 个文件`
  const sortedFiles = files.sort((first, second) => first.name.localeCompare(second.name, 'zh-CN', { numeric: true }))
  const txtFiles = sortedFiles.filter((file) => file.name.toLowerCase().endsWith('.txt'))
  const unsupportedFiles = sortedFiles.filter((file) => !file.name.toLowerCase().endsWith('.txt'))

  if (txtFiles.length) {
    const texts = await Promise.all(txtFiles.map((file) => file.text()))
    const chapterTitlePattern = /^\s*(?:第[\d一二三四五六七八九十百千万零〇两]+[章节回卷幕部集]|Chapter\s+\d+|CHAPTER\s+[IVXLCDM\d]+)/im
    novelText.value = texts.map((text, index) => {
      if (chapterTitlePattern.test(text)) {
        return text.trim()
      }

      const filename = txtFiles[index].name.replace(/\.[^.]+$/, '')
      return `第${index + 1}章 ${filename}\n\n${text.trim()}`
    }).join('\n\n')
    importNotice.value = txtFiles.length === 1
      ? `${txtFiles[0].name} 已载入，章节列表已重新识别。`
      : `${txtFiles.length} 个 txt 文件已按文件名顺序合并载入；无章节标题的文件已自动补全章节标题。`
    if (unsupportedFiles.length) {
      importNotice.value += ` ${unsupportedFiles.length} 个非 txt 文件未解析正文。`
    }
    return
  }

  importNotice.value = `${sortedFiles.map((file) => file.name).join('、')} 已接收。当前暂不解析 docx 正文，请粘贴文本后继续。`
}
</script>

<template>
  <AuthPage v-if="isAuthRoute" :icon-paths="iconPaths" @authenticated="handleAuthenticated" />

  <div v-else class="app-layout">
    <AppSidebar :icon-paths="iconPaths" :nav-items="activeNavItems" @select="goToPage" @open-recycle-bin="openRecycleBin" />

    <main class="main-wrapper" aria-label="工作区">
      <div class="page-content">
        <WorkspaceHeader :description="pageDescription" :icon-paths="iconPaths" :title="pageTitle" @logout="logout"
          @open-profile="openProfileCenter" />
        <section class="workspace-body" aria-label="工作台内容">
        <ProjectsPage v-if="activeRoute.id === 'projects'" :activities="displayedProjectActivities"
          :icon-paths="iconPaths" :projects="displayedProjectCards" :stats="displayedProjectStats"
          :notice="projectListNotice" @open-project="openProject" @delete-project="handleDeleteProject" />

        <TemplateCenterPage v-else-if="activeRoute.id === 'templates'" :icon-paths="iconPaths"
          :selected-template-id="selectedTemplateId" :templates="displayedTemplates"
          @select-template="selectGenerationTemplate" />

        <ScriptLibraryPage v-else-if="activeRoute.id === 'library'" :icon-paths="iconPaths"
          :notice="libraryNotice" :scripts="displayedLibraryItems" :stats="displayedLibraryStats" @edit-script="editLibraryScript"
          @preview-script="previewLibraryScript" @export-script="exportLibraryScript" @delete-script="deleteLibraryScript"
          @rename-script="renameLibraryScript" @clone-script="cloneLibraryScript" />

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
            <ScriptWorkspace :icon-paths="iconPaths" :preview-scene="selectedPreviewScene"
              :schema-validation="schemaValidation" :script-chapters="displayedScriptChapters"
              :is-generating="isScriptGenerating" :status-notice="editorNotice" :yaml-lines="generatedYamlLines" @add-scene="openAddScene"
              @copy-yaml="copyYaml" @download-yaml="downloadYaml" @open-preview="goToPreview"
              @open-schema="goToSchemaHelp" @previous="goBackToAnalysis" @select-scene="selectScriptScene"
              @validate-yaml="validateYaml" />
          </div>

          <GenerationSettingsDialog v-model="isGenerationSettingsOpen" :initial-settings="generatedSettings || defaultGenerationSettings"
            :options="generationSettingOptions" @confirm="confirmGenerationSettings" />
          <AddSceneDialog v-model="isAddSceneOpen" :chapters="displayedScriptChapters" @confirm="confirmAddScene" />
        </template>
        </section>
      </div>
    </main>

    <ProfileCenterDialog v-model="isProfileCenterOpen" :icon-paths="iconPaths" :user="currentUser" @logout="logout" />

    <Teleport to="body">
      <div v-if="showRecycleBin" class="dialog-backdrop" role="presentation" @click.self="closeRecycleBin">
        <section class="generation-dialog" style="max-width: 800px; width: 90%;" role="dialog" aria-modal="true" aria-labelledby="recycle-bin-title">
          <header class="dialog-header">
            <div>
              <span>项目管理</span>
              <h2 id="recycle-bin-title">回收站</h2>
            </div>
            <button class="dialog-close" type="button" aria-label="关闭回收站" @click="closeRecycleBin">×</button>
          </header>

          <div class="dialog-body" style="max-height: 60vh; overflow-y: auto;">
            <div v-if="recycleBinItems.length === 0" class="library-empty-state" style="padding: 40px 0;">
              <strong>回收站是空的</strong>
            </div>
            <div v-else>
              <p class="inline-note">当前后端删除为永久删除，回收站仅记录本地删除历史，暂不支持恢复。</p>
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
              <thead>
                <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary);">
                  <th style="padding: 12px 8px; font-weight: 500;">剧本名称</th>
                  <th style="padding: 12px 8px; font-weight: 500;">删除时间</th>
                  <th style="padding: 12px 8px; font-weight: 500; text-align: right;">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recycleBinItems" :key="item.id" style="border-bottom: 1px solid var(--border-color-light);">
                  <td style="padding: 16px 8px;">
                    <strong>{{ item.title }}</strong>
                    <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">来源小说：{{ item.sourceNovel }}</div>
                  </td>
                  <td style="padding: 16px 8px; color: var(--text-secondary);">{{ item.deletedAt }}</td>
                  <td style="padding: 16px 8px; text-align: right;">
                    <button class="link-button" type="button" disabled @click="restoreFromRecycleBin">暂不支持恢复</button>
                  </td>
                </tr>
              </tbody>
            </table>
            </div>
          </div>

          <footer class="dialog-actions" style="justify-content: space-between;">
            <button class="editor-tool is-danger" type="button" :disabled="recycleBinItems.length === 0" @click="clearRecycleBin">清空回收站</button>
            <button class="editor-tool is-primary" type="button" @click="closeRecycleBin">关闭</button>
          </footer>
        </section>
      </div>
    </Teleport>
  </div>
</template>
