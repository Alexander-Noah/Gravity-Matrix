<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import yaml from 'js-yaml'
import { clearAuthSession, fetchCurrentUser, getAuthSession, hasActiveAuthSession } from './api/auth'
import { getApiErrorMessage } from './api/http'
import {
  createProject,
  diagnoseProjectScriptDraft,
  getJob,
  getProjectReadiness,
  getProjectAnalysis,
  getProjectScript,
  getProjectWorkbench,
  saveProjectScript,
  startAnalysisJob,
  startScriptJob,
  validateProjectScript,
  updateGenerationSettings,
  rerunAnalysisJob,
  addProjectScene,
  exportProjectMarkdown,
  exportProjectPdf,
  exportProjectTxt,
  deleteProject,
  getScriptTemplates,
  getDefaultTemplate,
  updateProject,
  cloneProject,
  previewImport,
  getScriptsLibrary,
  importLibrarySource,
  rerunScriptJob,
  updateDefaultTemplate,
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
  dialogueExtracts,
  generationSettingOptions,
  iconPaths,
  importWorkflowSteps,
  insightItems,
  navItems,
  plotEvents,
  previewWorkflowSteps,
  projectStages,
  productHelpDocs,
  schemaHelpContent,
  schemaValidationMock,
  scriptGenerationTemplates as mockTemplates,
  scriptChapters,
  scriptPreviewScenes,
  workflowSteps,
  yamlLines,
} from './data/workbench'
import { getRouteById } from './router/routes'

const route = useRoute()
const router = useRouter()
const activePage = ref('import')
const novelText = ref('')
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
const editableScriptYaml = ref('')
const schemaValidation = ref(schemaValidationMock)
const editorNotice = ref('')
const previewNotice = ref('')
const selectedTemplateId = ref(localStorage.getItem('gravityMatrixSelectedTemplate') || 'tv-drama')
const currentUser = ref(getAuthSession().user)
const isProfileCenterOpen = ref(false)
const isGuideOpen = ref(false)
const displayedAnalysisCharacters = ref(analysisCharacters)
const displayedAnalysisMetrics = ref(analysisMetrics)
const displayedAnalysisScenes = ref(analysisScenes)
const displayedPlotEvents = ref(plotEvents)
const displayedCharacterRelations = ref(characterRelations)
const displayedDialogueExtracts = ref(dialogueExtracts)
const displayedInsightItems = ref(insightItems)
const displayedScriptChapters = ref(scriptChapters)
const displayedLibraryItems = ref([])
const displayedLibraryStats = ref([
  { label: '全部剧本', value: '0', note: '等待读取真实剧本库', tone: 'violet' },
  { label: '编辑中', value: '0', note: '等待读取真实剧本库', tone: 'blue' },
  { label: '已完成', value: '0', note: '等待读取真实剧本库', tone: 'mint' },
  { label: '素材库', value: '0', note: '等待读取真实剧本库', tone: 'orange' },
])
const displayedTemplates = ref(mockTemplates)
const selectedSceneId = ref(null)
const libraryNotice = ref('')
const isLibraryLoading = ref(false)
const hasLibraryLoaded = ref(false)
const isScriptGenerating = ref(false)
const currentProjectTitle = ref('未创建项目')
const currentProjectProgress = ref(0)
const currentProjectStages = ref(projectStages)
const scriptWorkspaceRef = ref(null)
const activeYamlLine = ref(null)
let isExplicitProjectOpen = false
let scriptSaveTimeout = null

const CURRENT_PROJECT_STORAGE_KEY = 'gravityMatrixCurrentProjectId'

const guideSteps = [
  {
    title: '导入小说',
    description: '上传 TXT 文件或粘贴小说正文，系统会自动识别章节结构。至少识别 3 章后才能进入下一步。',
    icon: 'upload',
  },
  {
    title: 'AI 解析',
    description: '提取人物、场景、剧情事件、人物关系和对白线索，形成后续生成剧本的结构依据。',
    icon: 'spark',
  },
  {
    title: '生成剧本',
    description: '选择模板和生成偏好后，系统会生成可编辑的 YAML 剧本草稿。',
    icon: 'format',
  },
  {
    title: '编辑与导出',
    description: '在工作台校验 YAML、补充场景、预览成稿，并导出 YAML、TXT、Markdown 或 PDF。',
    icon: 'download',
  },
]

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
    const [templates, defaultTemplate] = await Promise.all([
      getScriptTemplates(),
      getDefaultTemplate(),
    ])
    displayedTemplates.value = templates?.length ? templates : mockTemplates
    if (defaultTemplate?.templateId) {
      selectedTemplateId.value = defaultTemplate.templateId
      localStorage.setItem('gravityMatrixSelectedTemplate', defaultTemplate.templateId)
    }
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

const normalizeYamlSearchValue = (value) =>
  String(value || '')
    .replace(/^['"]|['"]$/g, '')
    .trim()

const getGeneratedYamlPlainLines = () => generatedYamlLines.value.map((line) => line.map((token) => token.text).join(''))

const findYamlLineByFieldValue = (fieldName, value) => {
  const targetValue = normalizeYamlSearchValue(value)

  if (!targetValue) {
    return null
  }

  const lines = getGeneratedYamlPlainLines()
  const targetIndex = lines.findIndex((line) => {
    const match = line.match(new RegExp(`^\\s*-?\\s*${fieldName}:\\s*(.+?)\\s*$`))
    return match && normalizeYamlSearchValue(match[1]) === targetValue
  })

  return targetIndex >= 0 ? targetIndex + 1 : null
}

const findYamlLineByText = (text) => {
  const targetText = normalizeYamlSearchValue(text)

  if (!targetText) {
    return null
  }

  const lines = getGeneratedYamlPlainLines()
  const targetIndex = lines.findIndex((line) => normalizeYamlSearchValue(line).includes(targetText))

  return targetIndex >= 0 ? targetIndex + 1 : null
}

const getSceneSearchTexts = (scene) => {
  const label = scene?.label || scene?.title || ''
  const shortLabel = label.replace(/^场景\s*\d+\s*-\s*\d+\s*/, '').trim()

  return [...new Set([label, shortLabel].filter(Boolean))]
}

const scrollScriptYamlToLine = (lineNumber) => {
  if (!lineNumber) {
    return
  }

  activeYamlLine.value = lineNumber
  requestAnimationFrame(() => {
    scriptWorkspaceRef.value?.scrollToYamlLine(lineNumber)
  })
}

const mapDiagnosisToSchemaValidation = (diagnosis, fallbackValid = true) => {
  const summary = diagnosis?.summary || {}
  const yamlSummary = getScriptSummaryFromYaml(generatedYamlText.value || generatedScriptYaml.value)

  return {
    yamlValid: diagnosis?.valid_schema ?? fallbackValid,
    requiredFieldsValid: diagnosis?.valid_schema ?? fallbackValid,
    chapterCount: summary.chapter_count ?? yamlSummary?.chapterCount ?? 0,
    sceneCount: summary.scene_count ?? yamlSummary?.sceneCount ?? 0,
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
  const sourceCount = items.filter((item) => item.source_type === 'source_novel').length

  displayedLibraryItems.value = items
  displayedLibraryStats.value = [
    { label: '全部条目', value: String(items.length), note: '来自后端剧本与素材库', tone: 'violet' },
    { label: '编辑中', value: String(editingCount), note: '已保存 YAML 草稿', tone: 'blue' },
    { label: '已完成', value: String(completedCount), note: '可进入完整预览', tone: 'mint' },
    { label: '素材库', value: String(sourceCount || exportedCount), note: sourceCount ? '可导入工作台' : '后端暂未返回导出历史', tone: 'orange' },
  ]
}

const getScriptBody = (yamlText) => {
  if (!yamlText) return null

  const parsed = yaml.load(yamlText)
  return parsed?.script || parsed
}

const getScriptSummaryFromYaml = (yamlText) => {
  try {
    const script = getScriptBody(yamlText)
    const chapters = Array.isArray(script?.chapters) ? script.chapters : []
    const sceneCount = chapters.reduce((total, chapter) => total + (chapter.scenes?.length || 0), 0)
    const dialogueCount = chapters.reduce(
      (total, chapter) => total + (chapter.scenes || []).reduce(
        (sceneTotal, scene) => sceneTotal + ((scene.dialogue || scene.dialogues || []).length || 0),
        0,
      ),
      0,
    )

    return {
      chapterCount: chapters.length,
      sceneCount,
      dialogueCount,
      characterCount: Array.isArray(script?.characters) ? script.characters.length : 0,
      locationCount: Array.isArray(script?.locations) ? script.locations.length : 0,
    }
  } catch {
    return null
  }
}

const applyScriptMetricsFromYaml = (yamlText) => {
  const summary = getScriptSummaryFromYaml(yamlText)

  if (!summary) {
    return
  }

  displayedAnalysisMetrics.value = [
    { label: '人物', value: String(summary.characterCount), icon: 'users', tone: 'violet' },
    { label: '剧本场景', value: String(summary.sceneCount), icon: 'scene', tone: 'blue' },
    { label: '章节', value: String(summary.chapterCount), icon: 'chapter', tone: 'mint' },
    { label: '对白', value: String(summary.dialogueCount), icon: 'message', tone: 'orange' },
  ]
}

const formatScriptChapterTitle = (title, chapterIndex) => {
  const normalizedTitle = String(title || '').trim()
  if (/^第\s*[\d一二三四五六七八九十百千万零〇两]+\s*[章节回幕卷部集]/.test(normalizedTitle)) {
    return normalizedTitle
  }

  return `第${chapterIndex + 1}章 ${normalizedTitle || '未命名章节'}`
}

const buildScriptChaptersFromYaml = (yamlText) => {
  let script

  try {
    script = getScriptBody(yamlText)
  } catch (error) {
    console.error('YAML structure parsing error', error)
    return []
  }

  if (!script?.chapters?.length) return []

  return script.chapters.map((chapter, chapterIndex) => ({
    id: chapter.id || `ch_${String(chapterIndex + 1).padStart(3, '0')}`,
    title: formatScriptChapterTitle(chapter.title, chapterIndex),
    open: chapterIndex === 0,
    scenes: (chapter.scenes || []).map((scene, sceneIndex) => ({
      id: scene.id || `${chapter.id || chapterIndex + 1}-${sceneIndex + 1}`,
      label: `场景 ${chapterIndex + 1}-${sceneIndex + 1} ${scene.title || scene.label || '未命名场景'}`,
      active: chapterIndex === 0 && sceneIndex === 0,
    })),
  }))
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

  const yamlStructure = buildScriptChaptersFromYaml(workbench?.script?.yaml)
  const backendStructure = workbench?.script?.structure?.length
    ? workbench.script.structure.map((chapter) => ({
      id: chapter.id,
      title: chapter.title || chapter.label,
      open: chapter.open,
      scenes: chapter.scenes.map((scene) => ({
        id: scene.id,
        label: scene.label || scene.title,
        active: selectedSceneId.value ? scene.id === selectedSceneId.value : scene.active,
      })),
    }))
    : []
  const nextStructure = yamlStructure.length ? yamlStructure : backendStructure

  if (nextStructure.length) {
    const existingSceneIds = nextStructure.flatMap((chapter) => chapter.scenes.map((scene) => scene.id))
    if (!selectedSceneId.value || !existingSceneIds.includes(selectedSceneId.value)) {
      selectedSceneId.value = existingSceneIds[0] || null
    }

    displayedScriptChapters.value = nextStructure.map((chapter, chapterIndex) => ({
      ...chapter,
      open: chapter.open || chapter.scenes.some((scene) => scene.id === selectedSceneId.value) || chapterIndex === 0,
      scenes: chapter.scenes.map((scene) => ({
        ...scene,
        active: scene.id === selectedSceneId.value,
      })),
    }))

    if (!selectedSceneId.value) {
      selectedSceneId.value = nextStructure[0]?.scenes?.[0]?.id || null
    }
  } else if (currentProjectId.value) {
    displayedScriptChapters.value = []
  }

  if (workbench?.script?.diagnosis) {
    schemaValidation.value = mapDiagnosisToSchemaValidation(workbench.script.diagnosis)
  }

  if (workbench?.script?.yaml) {
    applyScriptMetricsFromYaml(workbench.script.yaml)
  }
}

const applyWorkbenchProgress = (workbench) => {
  const project = workbench?.project || {}
  currentProjectTitle.value = project.title ? `《${project.title}》改编项目` : '项目工作台'
  currentProjectProgress.value = workbench?.progress?.percent ?? currentProjectProgress.value

  if (workbench?.progress?.steps?.length) {
    currentProjectStages.value = workbench.progress.steps.map((step) => ({
      label: step.label,
      note: step.description || '',
      status: step.status === 'completed' ? 'done' : step.status === 'current' ? 'active' : 'pending',
    }))
    return
  }

  if (project.has_script) {
    currentProjectStages.value = buildProjectStages('script')
  } else if (project.has_analysis) {
    currentProjectStages.value = buildProjectStages('analysis')
  } else {
    currentProjectStages.value = buildProjectStages('import')
  }
}

const fetchScriptLibrary = async () => {
  if (isLibraryLoading.value) return
  isLibraryLoading.value = true
  libraryNotice.value = ''
  try {
    const library = await getScriptsLibrary()
    if (library) {
      displayedLibraryStats.value = library.stats || [
        { label: '全部条目', value: '0', note: '后端暂无剧本或素材', tone: 'violet' },
        { label: '编辑中', value: '0', note: '暂无编辑中剧本', tone: 'blue' },
        { label: '已完成', value: '0', note: '暂无已完成剧本', tone: 'mint' },
        { label: '素材库', value: '0', note: '暂无可导入素材', tone: 'orange' },
      ]
      displayedLibraryItems.value = library.items || []
    }
    hasLibraryLoaded.value = true
  } catch (error) {
    libraryNotice.value = `剧本库加载失败：${getApiErrorMessage(error)}`
    if (!hasLibraryLoaded.value) {
      displayedLibraryStats.value = [
        { label: '全部条目', value: '0', note: '后端暂不可用', tone: 'violet' },
        { label: '编辑中', value: '0', note: '后端暂不可用', tone: 'blue' },
        { label: '已完成', value: '0', note: '后端暂不可用', tone: 'mint' },
        { label: '素材库', value: '0', note: '后端暂不可用', tone: 'orange' },
      ]
      displayedLibraryItems.value = []
    }
  } finally {
    isLibraryLoading.value = false
  }
}

watch(
  () => activeRoute.value.id,
  (routeId) => {
    if (routeId === 'templates') {
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
      if (isExplicitProjectOpen) {
        isExplicitProjectOpen = false
        return
      }
      enterWorkbenchHome()
    }
  },
)

onMounted(async () => {
  const session = getAuthSession()
  if (!session.token || !hasActiveAuthSession()) {
    currentUser.value = null
    if (!isAuthRoute.value) {
      router.replace('/auth')
    }
    return
  }

  try {
    currentUser.value = await fetchCurrentUser()
  } catch {
    clearAuthSession()
    currentUser.value = null
    if (!isAuthRoute.value) {
      router.replace('/auth')
    }
    return
  }

  if (isWorkbenchRoute.value) {
    enterWorkbenchHome()
  }
})

const resetWorkbenchFlow = () => {
  setCurrentProjectId(null)
  generatedScriptYaml.value = ''
  generatedSettings.value = null
  selectedSceneId.value = null
  editorNotice.value = ''
  previewNotice.value = ''
  analysisNotice.value = ''
  analysisProgress.value = 0
  currentProjectTitle.value = '未创建项目'
  currentProjectProgress.value = 0
  currentProjectStages.value = buildProjectStages('import')
  displayedScriptChapters.value = []
  schemaValidation.value = schemaValidationMock
}

const enterWorkbenchHome = () => {
  resetWorkbenchFlow()
  activePage.value = 'import'
  importNotice.value = '工作台已回到导入准备区；从“剧本库”打开项目时才会进入已生成剧本。'
}

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
let previewRequestId = 0
watch(novelText, (newText) => {
  if (previewTimeout) clearTimeout(previewTimeout)
  if (!newText || !newText.trim()) {
    previewRequestId += 1
    detectedChapters.value = []
    chapterCount.value = 0
    isNovelValid.value = false
    return
  }

  const localChapters = detectChaptersLocally(newText)
  detectedChapters.value = localChapters
  chapterCount.value = localChapters.length
  isNovelValid.value = localChapters.length >= 3
  currentProjectProgress.value = isNovelValid.value ? 20 : 10
  currentProjectStages.value = buildProjectStages('import')
  const requestId = ++previewRequestId

  previewTimeout = setTimeout(async () => {
    try {
      const result = await previewImport({
        title: selectedFileName.value ? selectedFileName.value.replace(/\.[^.]+$/, '') : '未命名小说',
        author: '创作者',
        text: newText,
      })

      if (requestId !== previewRequestId) {
        return
      }

      detectedChapters.value = (result.chapters || []).map((chapter, index) => ({
        ...chapter,
        content: chapter.content || localChapters[index]?.content || '',
        excerpt: chapter.excerpt || localChapters[index]?.excerpt || '等待补充正文',
      }))
      chapterCount.value = result.chapter_count || detectedChapters.value.length
      isNovelValid.value = result.can_create_project || false
      applyPreprocessResult(result.preprocess)
      currentProjectTitle.value = result.title ? `《${result.title}》本地整理` : '未创建项目'
      currentProjectProgress.value = isNovelValid.value ? 25 : 10
      currentProjectStages.value = buildProjectStages('import')
    } catch (error) {
      if (requestId !== previewRequestId) {
        return
      }
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
  editableScriptYaml.value || generatedScriptYaml.value || (!currentProjectId.value
    ? generatedYamlLines.value.map((line) => line.map((token) => token.text).join('')).join('\n')
    : ''),
)

watch(generatedScriptYaml, (yamlText) => {
  editableScriptYaml.value = yamlText || ''
  const summary = getScriptSummaryFromYaml(yamlText)

  if (summary) {
    schemaValidation.value = {
      ...schemaValidation.value,
      chapterCount: summary.chapterCount,
      sceneCount: summary.sceneCount,
    }
  }
})

const handleYamlTextUpdate = (yamlText) => {
  editableScriptYaml.value = yamlText
  generatedScriptYaml.value = yamlText
  schemaValidation.value = {
    ...schemaValidation.value,
    checkedAt: '等待重新校验',
    message: 'YAML 已修改，请点击校验格式检查结构。',
  }

  if (scriptSaveTimeout) {
    clearTimeout(scriptSaveTimeout)
  }

  if (!currentProjectId.value || isScriptGenerating.value) {
    editorNotice.value = 'YAML 已在本地编辑。'
    return
  }

  editorNotice.value = 'YAML 已修改，正在自动保存...'
  scriptSaveTimeout = setTimeout(async () => {
    try {
      await saveProjectScript(currentProjectId.value, yamlText)
      editorNotice.value = 'YAML 已自动保存。'
    } catch (error) {
      editorNotice.value = `自动保存失败：${getApiErrorMessage(error)}`
    }
  }, 900)
}
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

const syncCurrentWorkbench = async () => {
  if (!currentProjectId.value) {
    return null
  }

  const workbench = await getProjectWorkbench(currentProjectId.value)

  if (workbench.analysis?.raw) {
    applyAnalysisResult(workbench.analysis.raw)
  }

  applyWorkbenchScript(workbench)
  applyWorkbenchProgress(workbench)
  return workbench
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

const applyPreprocessResult = (preprocess) => {
  if (!preprocess) return

  applyAnalysisResult({
    characters: preprocess.characters || [],
    locations: preprocess.locations || [],
    chapter_summaries: preprocess.chapter_summaries || [],
    conflicts: preprocess.conflicts || [],
    themes: preprocess.themes || [],
  })

  const notes = preprocess.preparation_notes || []
  if (notes.length) {
    displayedInsightItems.value = notes.slice(0, 4).map((note, index) => ({
      label: `整理 ${index + 1}`,
      value: note,
      tone: ['blue', 'mint', 'orange', 'violet'][index % 4],
    }))
  }
}

const buildProjectStages = (stage) => {
  const order = ['import', 'analysis', 'script', 'preview']
  const labels = {
    import: '本地整理',
    analysis: 'AI 解析',
    script: '剧本生成',
    preview: '校验导出',
  }
  const notes = {
    import: '章节结构',
    analysis: '人物/剧情',
    script: 'YAML 草稿',
    preview: '成品检查',
  }
  const currentIndex = order.indexOf(stage)

  return order.map((key, index) => ({
    label: labels[key],
    note: notes[key],
    status: currentIndex > index ? 'done' : currentIndex === index ? 'active' : 'pending',
  }))
}

const goToPage = (pageId) => {
  const targetRoute = getRouteById(pageId)

  router.push(targetRoute.path)

  if (pageId === 'workbench') {
    enterWorkbenchHome()
  }
}

const openCurrentProject = () => {
  if (currentProjectId.value) {
    activePage.value = generatedScriptYaml.value ? 'script' : 'analysis'
    return
  }

  enterWorkbenchHome()
}

const handleAuthenticated = async () => {
  try {
    currentUser.value = await fetchCurrentUser()
  } catch {
    currentUser.value = getAuthSession().user
  }
  router.push('/workbench')
}

const openProfileCenter = async () => {
  try {
    currentUser.value = await fetchCurrentUser()
  } catch {
    currentUser.value = getAuthSession().user
  }
  isProfileCenterOpen.value = true
}

const logout = () => {
  isProfileCenterOpen.value = false
  clearAuthSession()
  currentUser.value = null
  router.push('/auth')
}

const openGuide = () => {
  isGuideOpen.value = true
}

const closeGuide = () => {
  isGuideOpen.value = false
}

const openProject = async (project) => {
  isExplicitProjectOpen = true
  router.push('/workbench')
  setCurrentProjectId(project?.id || project?.raw?.id || null)
  currentProjectTitle.value = project?.raw?.title || project?.title || '项目工作台'
  currentProjectProgress.value = Number(project?.progress || 0)

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
    const workbench = await syncCurrentWorkbench()

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

const selectGenerationTemplate = async (templateId) => {
  selectedTemplateId.value = templateId
  localStorage.setItem('gravityMatrixSelectedTemplate', templateId)
  try {
    await updateDefaultTemplate(templateId)
  } catch (error) {
    console.warn('保存默认模板失败，已保留本地选择', error)
  }
}

const useGenerationTemplate = async (templateId) => {
  await selectGenerationTemplate(templateId)
  router.push('/workbench')
}

const defaultGenerationSettings = computed(() => {
  const templateId = selectedTemplateId.value
  let scriptType = '影视剧'
  if (templateId === 'short-drama') scriptType = '短剧'
  if (templateId === 'stage-play') scriptType = '话剧'
  if (templateId === 'storyboard') scriptType = '分镜剧本'
  if (templateId === 'audio-drama') scriptType = '广播剧'

  return {
    templateId,
    scriptType,
    adaptationStyle: generationSettingOptions.adaptationStyles[0],
    contentOptions: generationSettingOptions.contentOptions.slice(0, 2),
  }
})
const selectedTemplateName = computed(() =>
  displayedTemplates.value.find((template) => template.id === selectedTemplateId.value)?.name || '未选择模板',
)
const profileStats = computed(() => ({
  workspaceName: pageTitle.value,
  currentProject: currentProjectTitle.value,
  projectProgress: currentProjectProgress.value,
  workflowStep: currentWorkflowSteps.value.find((step) => step.status === 'active')?.label || activeRoute.value.title,
  selectedTemplate: selectedTemplateName.value,
  scriptStatus: generatedYamlText.value ? '已有 YAML 草稿' : '尚未生成剧本',
  libraryCount: displayedLibraryItems.value.length,
  schemaStatus: schemaValidation.value.yamlValid && schemaValidation.value.requiredFieldsValid ? '校验通过' : '待校验',
}))

const getScriptProjectId = (script) => script?.projectId || script?.project_id || script?.raw?.id || null

const editLibraryScript = async (script) => {
  if (script?.source_type === 'source_novel') {
    await importSourceNovel(script)
    return
  }

  isExplicitProjectOpen = true
  router.push('/workbench')
  setCurrentProjectId(getScriptProjectId(script))

  if (currentProjectId.value) {
    try {
      await syncCurrentWorkbench()
    } catch (error) {
      editorNotice.value = getApiErrorMessage(error)
    }
  }

  activePage.value = 'script'
}

const previewLibraryScript = async (script) => {
  isExplicitProjectOpen = true
  router.push('/workbench')
  setCurrentProjectId(getScriptProjectId(script))
  previewNotice.value = ''

  if (currentProjectId.value) {
    try {
      await syncCurrentWorkbench()
    } catch (error) {
      previewNotice.value = getApiErrorMessage(error)
    }
  }

  activePage.value = 'preview'
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
      blob = await exportProjectPdf(projectId)
    } else {
      blob = await exportProjectTxt(projectId)
    }

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${script.title}.${format === 'Markdown' ? 'md' : format === 'YAML' ? 'yaml' : format === 'PDF' ? 'pdf' : 'txt'}`
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
    currentProjectTitle.value = `《${project.title}》改编项目`
    currentProjectProgress.value = 35
    currentProjectStages.value = buildProjectStages('analysis')
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
    currentProjectProgress.value = 60
    currentProjectStages.value = buildProjectStages('analysis')
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

  const normalizedSettings = {
    ...settings,
    templateId: settings.templateId || selectedTemplateId.value,
  }

  generatedSettings.value = normalizedSettings
  isGenerationSettingsOpen.value = false
  editorNotice.value = '正在启动剧本生成任务...'
  schemaValidation.value = {
    yamlValid: false,
    requiredFieldsValid: false,
    chapterCount: 0,
    sceneCount: 0,
    checkedAt: '等待后端生成',
    message: '正在生成真实剧本 YAML，完成后会自动同步章节、场景和校验结果。',
  }
  activePage.value = 'script'
  currentProjectStages.value = buildProjectStages('script')
  currentProjectProgress.value = Math.max(currentProjectProgress.value, 70)
  generatedScriptYaml.value = ''
  selectedSceneId.value = null
  isScriptGenerating.value = true

  if (!currentProjectId.value) {
    editorNotice.value = '当前为静态演示剧本，请先从小说导入流程创建项目后再调用后端生成。'
    isScriptGenerating.value = false
    return
  }

  try {
    await updateGenerationSettings(currentProjectId.value, normalizedSettings)
    const job = await rerunScriptJob(currentProjectId.value)
    editorNotice.value = job.current_step || '剧本生成任务已启动。'

    await waitForJob(job.id, (currentJob) => {
      editorNotice.value = `${currentJob.current_step}（${currentJob.progress}%）`
    }, { timeoutMs: 300000, intervalMs: 1200 })

    const workbench = await syncCurrentWorkbench()
    if (workbench?.script?.yaml) {
      editorNotice.value = '剧本 YAML 已从后端生成并同步到编辑区。'
    } else {
      editorNotice.value = '后端任务已结束，但尚未返回剧本 YAML；请稍后点击剧本库重新打开项目。'
    }
  } catch (error) {
    try {
      const workbench = await syncCurrentWorkbench()
      editorNotice.value = workbench?.script?.yaml
        ? '剧本已在后端生成完成，已重新同步到编辑区。'
        : getApiErrorMessage(error)
    } catch {
      editorNotice.value = getApiErrorMessage(error)
    }
  } finally {
    isScriptGenerating.value = false
  }
}

const openAddScene = () => {
  isAddSceneOpen.value = true
}

const selectScriptScene = (scenePayload) => {
  const sceneId = typeof scenePayload === 'object' ? scenePayload?.id : scenePayload
  const selectedScene = displayedScriptChapters.value
    .flatMap((chapter) => chapter.scenes)
    .find((scene) => scene.id === sceneId || scene.label === scenePayload?.label)
    || (typeof scenePayload === 'object' ? scenePayload : null)
  const lineNumber = findYamlLineByFieldValue('id', sceneId)
    || getSceneSearchTexts(selectedScene).map(findYamlLineByText).find(Boolean)

  selectedSceneId.value = sceneId || selectedScene?.label || null
  displayedScriptChapters.value = displayedScriptChapters.value.map((chapter) => ({
    ...chapter,
    open: chapter.open || chapter.scenes.some((scene) => scene.id === sceneId || scene.label === selectedScene?.label),
    scenes: chapter.scenes.map((scene) => ({
      ...scene,
      active: scene.id === sceneId || scene.label === selectedScene?.label,
    })),
  }))
  scrollScriptYamlToLine(lineNumber)
}

const selectScriptChapter = (selectedChapter) => {
  const chapterId = selectedChapter?.id
  const chapterKey = chapterId || selectedChapter?.title
  const firstSceneId = selectedChapter?.scenes?.[0]?.id
  const lineNumber = findYamlLineByFieldValue('id', chapterId)
    || findYamlLineByText(selectedChapter?.title)
    || findYamlLineByFieldValue('id', firstSceneId)

  displayedScriptChapters.value = displayedScriptChapters.value.map((chapter) => ({
    ...chapter,
    open: (chapter.id || chapter.title) === chapterKey ? !chapter.open : chapter.open,
  }))
  scrollScriptYamlToLine(lineNumber)
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
  currentProjectStages.value = buildProjectStages('preview')
  currentProjectProgress.value = Math.max(currentProjectProgress.value, 90)
  activePage.value = 'preview'
}

const importSourceNovel = async (script) => {
  const sourceId = script?.source_id
  if (!sourceId) return

  try {
    libraryNotice.value = `正在导入素材 ${script.sourceNovel}...`
    const project = await importLibrarySource(sourceId)
    isExplicitProjectOpen = true
    router.push('/workbench')
    setCurrentProjectId(project.id)
    currentProjectTitle.value = `《${project.title}》改编项目`
    currentProjectProgress.value = 35
    currentProjectStages.value = buildProjectStages('analysis')
    activePage.value = 'analysis'
    analysisProgress.value = 10
    analysisNotice.value = '素材已导入，正在启动 AI 解析...'

    const job = await startAnalysisJob(project.id)
    analysisNotice.value = job.current_step || 'AI 解析任务已启动。'
    analysisProgress.value = job.progress ?? 30
    await waitForJob(job.id)

    const analysis = await getProjectAnalysis(project.id)
    applyAnalysisResult(analysis)
    analysisProgress.value = 100
    analysisNotice.value = '素材小说已导入并完成 AI 解析。'
  } catch (error) {
    libraryNotice.value = `素材导入失败：${getApiErrorMessage(error)}`
  }
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

const exportPreviewPdf = async () => {
  if (!currentProjectId.value) {
    previewNotice.value = '当前预览还没有后端项目，无法生成 PDF 文件。'
    return
  }

  try {
    previewNotice.value = '正在向服务端请求导出 PDF...'
    const blob = await exportProjectPdf(currentProjectId.value)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `project-${currentProjectId.value}-script.pdf`
    link.click()
    URL.revokeObjectURL(url)
    previewNotice.value = '服务端 PDF 文件下载完成。'
  } catch (error) {
    previewNotice.value = '下载失败：' + getApiErrorMessage(error)
  }
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
    <AppSidebar :icon-paths="iconPaths" :nav-items="activeNavItems" @select="goToPage"
      @open-recycle-bin="openRecycleBin" />

    <main class="main-wrapper" aria-label="工作区">
      <div class="page-content">
        <WorkspaceHeader :description="pageDescription" :icon-paths="iconPaths" :title="pageTitle" :user="currentUser" @logout="logout"
          @open-guide="openGuide" @open-profile="openProfileCenter" />
        <section class="workspace-body" aria-label="工作台内容">
        <TemplateCenterPage v-if="activeRoute.id === 'templates'" :icon-paths="iconPaths"
          :selected-template-id="selectedTemplateId" :templates="displayedTemplates"
          @select-template="selectGenerationTemplate" @use-template="useGenerationTemplate" />

        <ScriptLibraryPage v-else-if="activeRoute.id === 'library'" :icon-paths="iconPaths"
          :is-loaded="hasLibraryLoaded" :is-loading="isLibraryLoading" :notice="libraryNotice"
          :scripts="displayedLibraryItems" :stats="displayedLibraryStats" @edit-script="editLibraryScript"
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
              :project-progress="currentProjectProgress" :project-stages="currentProjectStages"
              :project-title="currentProjectTitle" @show-analysis="goBackToAnalysis" />
            <ScriptWorkspace ref="scriptWorkspaceRef" :active-yaml-line="activeYamlLine" :icon-paths="iconPaths" :preview-scene="selectedPreviewScene"
              :schema-validation="schemaValidation" :script-chapters="displayedScriptChapters"
              :is-generating="isScriptGenerating" :status-notice="editorNotice" :yaml-lines="generatedYamlLines" :yaml-text="generatedYamlText" @add-scene="openAddScene"
              @copy-yaml="copyYaml" @download-yaml="downloadYaml" @open-preview="goToPreview"
              @open-schema="goToSchemaHelp" @previous="goBackToAnalysis" @select-chapter="selectScriptChapter" @select-scene="selectScriptScene"
              @update:yaml-text="handleYamlTextUpdate" @validate-yaml="validateYaml" />
          </div>

          <GenerationSettingsDialog v-model="isGenerationSettingsOpen" :initial-settings="generatedSettings || defaultGenerationSettings"
            :options="generationSettingOptions" @confirm="confirmGenerationSettings" />
          <AddSceneDialog v-model="isAddSceneOpen" :chapters="displayedScriptChapters" @confirm="confirmAddScene" />
        </template>
        </section>
      </div>
    </main>

    <ProfileCenterDialog v-model="isProfileCenterOpen" :icon-paths="iconPaths" :stats="profileStats" :user="currentUser" @logout="logout" />

    <Teleport to="body">
      <div v-if="isGuideOpen" class="dialog-backdrop" role="presentation" @click.self="closeGuide">
        <section class="generation-dialog guide-dialog" role="dialog" aria-modal="true" aria-labelledby="guide-title">
          <header class="dialog-header guide-dialog-header">
            <div class="guide-title-row">
              <span class="guide-title-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path v-for="path in iconPaths.shield" :key="path" :d="path" />
                </svg>
              </span>
              <div>
                <span>使用指南</span>
                <h2 id="guide-title">从小说到剧本的完整流程</h2>
                <p>按步骤完成导入、解析、生成、校验和导出，适合第一次使用时快速对齐操作路径。</p>
              </div>
            </div>
            <button class="dialog-close" type="button" aria-label="关闭使用指南" @click="closeGuide">×</button>
          </header>

          <div class="dialog-body guide-dialog-body">
            <ol class="guide-step-list">
              <li v-for="(step, index) in guideSteps" :key="step.title" class="guide-step-item">
                <span class="guide-step-number">{{ index + 1 }}</span>
                <span class="guide-step-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path v-for="path in iconPaths[step.icon]" :key="path" :d="path" />
                  </svg>
                </span>
                <div>
                  <strong>{{ step.title }}</strong>
                  <p>{{ step.description }}</p>
                </div>
              </li>
            </ol>

            <div class="guide-tips">
              <strong>使用提示</strong>
              <ul>
                <li>TXT 会读取正文内容；DOCX 当前只记录文件名，建议粘贴正文后继续。</li>
                <li>生成后的 YAML 可以继续编辑，校验通过后再进入预览和导出。</li>
                <li>已生成的剧本可在剧本库继续编辑、预览、导出或移动到回收站。</li>
              </ul>
            </div>
          </div>

          <footer class="dialog-actions guide-actions">
            <button class="editor-tool" type="button" @click="goToPage('help'); closeGuide()">查看帮助文档</button>
            <button class="editor-tool is-primary" type="button" @click="closeGuide">开始使用</button>
          </footer>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showRecycleBin" class="dialog-backdrop" role="presentation" @click.self="closeRecycleBin">
        <section class="generation-dialog recycle-dialog" role="dialog" aria-modal="true" aria-labelledby="recycle-bin-title">
          <header class="dialog-header recycle-dialog-header">
            <div class="recycle-title-row">
              <span class="recycle-title-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path v-for="path in iconPaths.trash" :key="path" :d="path" />
                </svg>
              </span>
              <div>
                <span>项目管理</span>
                <h2 id="recycle-bin-title">回收站</h2>
                <p>{{ recycleBinItems.length === 0 ? '没有待处理记录' : `共 ${recycleBinItems.length} 条本地删除记录` }}</p>
              </div>
            </div>
            <button class="dialog-close" type="button" aria-label="关闭回收站" @click="closeRecycleBin">×</button>
          </header>

          <div class="dialog-body recycle-dialog-body">
            <div v-if="recycleBinItems.length === 0" class="recycle-empty-state">
              <span class="recycle-empty-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path v-for="path in iconPaths.trash" :key="path" :d="path" />
                </svg>
              </span>
              <strong>回收站是空的</strong>
              <p>删除记录会显示在这里，便于核对最近移除的剧本。</p>
            </div>
            <div v-else>
              <div class="recycle-note">
                <div>
                  <strong>本地删除历史</strong>
                  <p>当前后端删除为永久删除，回收站仅记录本地删除历史，暂不支持恢复。</p>
                </div>
                <span>{{ recycleBinItems.length }} 条</span>
              </div>
              <div class="recycle-table-wrap">
                <table class="recycle-table">
                  <thead>
                    <tr>
                      <th>剧本名称</th>
                      <th>删除时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in recycleBinItems" :key="item.id">
                      <td>
                        <strong>{{ item.title }}</strong>
                        <span>来源小说：{{ item.sourceNovel }}</span>
                      </td>
                      <td>{{ item.deletedAt }}</td>
                      <td>
                        <button class="recycle-disabled-action" type="button" disabled @click="restoreFromRecycleBin">暂不支持恢复</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <footer class="dialog-actions recycle-actions">
            <button class="editor-tool is-danger" type="button" :disabled="recycleBinItems.length === 0" @click="clearRecycleBin">清空回收站</button>
            <button class="editor-tool is-primary" type="button" @click="closeRecycleBin">关闭</button>
          </footer>
        </section>
      </div>
    </Teleport>
  </div>
</template>
