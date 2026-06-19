<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  iconPaths: { type: Object, required: true },
  selectedTemplateId: { type: String, default: '' },
  templates: { type: Array, required: true },
})

const emit = defineEmits(['select-template', 'use-template'])

const previewTemplate = ref(null)
const schemaTemplate = ref(null)
const searchKeyword = ref('')
const selectedFilter = ref('全部')

const templateProfiles = {
  'tv-drama': {
    actionTitle: '生成影视剧剧本',
    shortName: '影视剧剧本',
    audience: '适合大多数小说改编，尤其是长篇、连载文和需要后续精修的项目。',
    result: '会生成章节、场景、人物、地点、动作描写和对白，结构稳定，方便继续编辑。',
    tags: ['适合长篇', '结构稳定', '对白适中', '方便编辑', '成本适中'],
    cost: '中',
    speed: '中',
    quality: '高质量',
    usage: '推荐用于网剧、电视剧、电影分场稿和标准剧本初稿。',
    filters: ['适合长篇', '对白丰富', '适合拍摄'],
    reason: '适合大多数小说改编场景，结构稳定，方便后续编辑。',
    structureExample: '剧本 > 人物表 > 地点表 > 章节 > 场景 > 动作与对白',
    sceneExample: '场景 1-1：监牢清晨。主角醒来，发现自己被卷入案件核心。',
    dialogueExample: '许七安：先别急着定罪，证据会自己说话。',
  },
  'short-drama': {
    actionTitle: '生成短剧脚本',
    shortName: '短剧脚本',
    audience: '适合短视频、竖屏短剧、强冲突爽点和需要快速试稿的内容。',
    result: '会突出开场冲突、反转节点和结尾钩子，对白更短，节奏更快。',
    tags: ['省成本', '生成快', '适合短视频', '强冲突', '结尾钩子'],
    cost: '低',
    speed: '快',
    quality: '标准',
    usage: '推荐用于短剧分集、投流脚本、短视频剧情号和快速测试版本。',
    filters: ['省成本', '生成快', '适合短视频'],
    reason: '适合短视频和竖屏短剧，输出更快，重点保留冲突和反转。',
    structureExample: '集数 > 开场钩子 > 冲突 > 反转 > 结尾悬念',
    sceneExample: '开场冲突：主角被当众质疑身份，三秒内抛出核心矛盾。',
    dialogueExample: '主角：你们要证据，我现在就给。',
  },
  'stage-play': {
    actionTitle: '生成舞台话剧',
    shortName: '舞台话剧',
    audience: '适合排练、舞台演出、朗读会和以对白推动情节的小说改编。',
    result: '会强化人物入退场、舞台调度、灯光提示和长对白冲突。',
    tags: ['对白丰富', '舞台调度', '人物入退场', '高质量', '适合排练'],
    cost: '中',
    speed: '中',
    quality: '高质量',
    usage: '推荐用于话剧稿、舞台排练稿、朗读剧和表演练习文本。',
    filters: ['对白丰富'],
    reason: '适合需要人物对白和舞台调度的改编，不适合大量镜头化动作。',
    structureExample: '幕 > 场 > 舞台说明 > 人物入退场 > 对白',
    sceneExample: '第一幕：灯光渐亮，人物从舞台左侧入场，冲突在桌边爆发。',
    dialogueExample: '角色乙：这里不是逃避的地方，是选择的地方。',
  },
  storyboard: {
    actionTitle: '生成分镜脚本',
    shortName: '分镜脚本',
    audience: '适合导演、视频创作者、动画、广告片和需要镜头表达的项目。',
    result: '会按镜头拆分画面、景别、机位、声音和转场，方便进入拍摄或绘制。',
    tags: ['镜头感强', '适合拍摄', '画面拆分', '高质量', '信息更细'],
    cost: '高',
    speed: '慢',
    quality: '高质量',
    usage: '推荐用于短片、广告、动画分镜、导演阐述和拍摄沟通稿。',
    filters: ['适合拍摄', '镜头感强'],
    reason: '适合需要镜头设计的项目，细节更多，生成会更慢一些。',
    structureExample: '镜号 > 景别机位 > 画面内容 > 声音 > 转场',
    sceneExample: '镜头 1：中景跟拍，主角穿过人群，镜头停在他紧握的手上。',
    dialogueExample: '角色甲：这一次，我不能再退。',
  },
  'audio-drama': {
    actionTitle: '生成广播剧脚本',
    shortName: '广播剧脚本',
    audience: '适合有声剧、有声书改编、多人配音和以声音氛围为主的故事。',
    result: '会把画面信息改写成环境音、音效、旁白和更清晰的人物对白。',
    tags: ['生成快', '对白丰富', '声音氛围', '适合配音', '省画面'],
    cost: '中',
    speed: '快',
    quality: '标准',
    usage: '推荐用于广播剧、有声书试播稿、配音脚本和音频内容制作。',
    filters: ['生成快', '对白丰富'],
    reason: '适合快速生成声音导向的脚本，画面依赖更少。',
    structureExample: '场景 > 环境音 > 音效 > 旁白 > 对白',
    sceneExample: '夜雨来信：雨声渐强，纸张展开，角色压低声音读出关键线索。',
    dialogueExample: '角色甲：这封信，终于到了。',
  },
}

const filterOptions = [
  '全部',
  '省成本',
  '生成快',
  '适合长篇',
  '适合短视频',
  '适合拍摄',
  '对白丰富',
  '镜头感强',
]

const selectedTemplate = computed(() =>
  props.templates.find((template) => template.id === props.selectedTemplateId),
)

const recommendedTemplate = computed(() =>
  props.templates.find((template) => template.id === 'tv-drama') ||
  props.templates.find((template) => getTemplateFormat(template) === 'screenplay') ||
  props.templates[0],
)

const selectedTemplateSummary = computed(() => {
  const template = selectedTemplate.value || recommendedTemplate.value
  if (!template) {
    return {
      name: '影视剧剧本',
      description: '下次生成剧本时将默认使用该方式，你也可以临时选择其他生成方式。',
      format: 'screenplay',
    }
  }

  const profile = getTemplateProfile(template)
  return {
    name: profile.shortName,
    description: '下次生成剧本时将默认使用该方式，你也可以临时选择其他生成方式。',
    format: getTemplateFormat(template),
  }
})

const filteredTemplates = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()

  return props.templates.filter((template) => {
    if (!matchesFilter(template, selectedFilter.value)) return false

    if (!keyword) return true
    const profile = getTemplateProfile(template)
    const haystack = [
      profile.actionTitle,
      profile.shortName,
      profile.audience,
      profile.result,
      profile.usage,
      getTemplateFormat(template),
      ...(profile.tags || []),
      ...(template.features || []),
      ...(template.fields || []),
      ...(template.backend_rules || []),
    ].join(' ').toLowerCase()
    return haystack.includes(keyword)
  })
})

function getTemplateProfile(template) {
  return templateProfiles[template.id] || {
    actionTitle: `生成${template.name || '剧本'}`,
    shortName: template.name || '剧本',
    audience: template.scenario || '适合自定义剧本生成。',
    result: '会根据当前模板生成结构化剧本草稿。',
    tags: ['结构清晰', '可继续编辑', '标准输出'],
    cost: '中',
    speed: '中',
    quality: '标准',
    usage: '推荐用于常规剧本初稿。',
    filters: [],
    reason: '结构清晰，适合常规剧本生成流程。',
    structureExample: '剧本 > 章节 > 场景 > 对白',
    sceneExample: '场景示例：人物进入关键地点，冲突被逐步揭开。',
    dialogueExample: '角色：这件事，需要重新判断。',
  }
}

function getTemplateFormat(template) {
  if (template.target_format) return template.target_format
  if (template.id === 'tv-drama') return 'screenplay'
  if (template.id === 'short-drama') return 'short_drama'
  if (template.id === 'stage-play') return 'stage_play'
  if (template.id === 'audio-drama') return 'audio_drama'
  return template.id
}

function matchesFilter(template, filter) {
  if (filter === '全部') return true
  const profile = getTemplateProfile(template)
  return profile.filters.includes(filter) || profile.tags.includes(filter)
}

function metricClass(value) {
  if (['低', '快', '高质量'].includes(value)) return 'is-strong'
  if (['高', '慢'].includes(value)) return 'is-warning'
  return ''
}

function openPreview(template) {
  previewTemplate.value = template
}

function closePreview() {
  previewTemplate.value = null
}

function openSchema(template) {
  schemaTemplate.value = template
}

function closeSchema() {
  schemaTemplate.value = null
}

function resetFilters() {
  searchKeyword.value = ''
  selectedFilter.value = '全部'
}

function selectAndClose(template) {
  emit('select-template', template.id)
  closePreview()
  closeSchema()
}

function useAndClose(template) {
  emit('use-template', template.id)
  closePreview()
  closeSchema()
}
</script>

<template>
  <div class="template-center-page">
    <section class="template-summary" aria-label="选择剧本生成方式说明">
      <div class="template-summary-copy">
        <span>生成方式</span>
        <h2>选择剧本生成方式</h2>
        <p>
          不同生成方式会影响剧本结构、场景拆分、对白数量和生成成本。不知道选哪个，优先选择影视剧剧本。
        </p>
      </div>
      <div class="template-selected-panel">
        <span>当前默认生成方式</span>
        <strong>{{ selectedTemplateSummary.name }}</strong>
        <small>{{ selectedTemplateSummary.description }}</small>
        <div class="template-selected-meta">
          <code>{{ selectedTemplateSummary.format }}</code>
        </div>
      </div>
    </section>

    <section v-if="recommendedTemplate" class="template-recommendation" aria-label="系统推荐">
      <div class="template-recommendation-copy">
        <span>系统推荐：影视剧剧本</span>
        <h2>{{ getTemplateProfile(recommendedTemplate).actionTitle }}</h2>
        <p>原因：适合大多数小说改编场景，结构稳定，方便后续编辑。</p>
      </div>
      <div class="template-recommendation-meta">
        <span>成本 {{ getTemplateProfile(recommendedTemplate).cost }}</span>
        <span>速度 {{ getTemplateProfile(recommendedTemplate).speed }}</span>
        <span>{{ getTemplateProfile(recommendedTemplate).quality }}</span>
      </div>
      <div class="template-recommendation-actions">
        <button class="editor-tool" type="button" @click="openPreview(recommendedTemplate)">查看示例</button>
        <button
          class="editor-tool is-primary"
          type="button"
          :disabled="selectedTemplateId === recommendedTemplate.id"
          @click="emit('use-template', recommendedTemplate.id)"
        >
          {{ selectedTemplateId === recommendedTemplate.id ? '当前使用中' : '使用推荐方式' }}
        </button>
      </div>
    </section>

    <section class="template-toolbar" aria-label="生成方式筛选">
      <label class="template-search">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.eye" :key="path" :d="path" />
        </svg>
        <input v-model="searchKeyword" type="search" placeholder="搜索生成方式、用途或特点" />
      </label>

      <div class="template-format-tabs" role="tablist" aria-label="生成方式筛选项">
        <button
          v-for="filter in filterOptions"
          :key="filter"
          type="button"
          :class="{ 'is-active': selectedFilter === filter }"
          @click="selectedFilter = filter"
        >
          {{ filter }}
        </button>
      </div>
    </section>

    <section class="template-grid" aria-label="剧本生成方式列表">
      <article
        v-for="template in filteredTemplates"
        :key="template.id"
        class="template-card"
        :class="{ 'is-selected': selectedTemplateId === template.id }"
      >
        <div v-if="selectedTemplateId === template.id" class="template-current-badge">当前使用中</div>

        <div class="template-card-header">
          <div class="template-card-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.file" :key="path" :d="path" />
            </svg>
          </div>
          <div>
            <h2>{{ getTemplateProfile(template).actionTitle }}</h2>
            <span>{{ getTemplateFormat(template) }}</span>
          </div>
        </div>

        <div class="template-scenario">
          <strong>适合什么用户/场景</strong>
          <p>{{ getTemplateProfile(template).audience }}</p>
        </div>

        <div class="template-scenario">
          <strong>生成出来是什么效果</strong>
          <p>{{ getTemplateProfile(template).result }}</p>
        </div>

        <div class="template-metric-row" aria-label="成本速度质量">
          <span :class="metricClass(getTemplateProfile(template).cost)">成本 {{ getTemplateProfile(template).cost }}</span>
          <span :class="metricClass(getTemplateProfile(template).speed)">速度 {{ getTemplateProfile(template).speed }}</span>
          <span :class="metricClass(getTemplateProfile(template).quality)">{{ getTemplateProfile(template).quality }}</span>
        </div>

        <div class="template-feature-list">
          <span v-for="tag in getTemplateProfile(template).tags" :key="tag">{{ tag }}</span>
        </div>

        <div class="template-usage">
          <strong>推荐用途</strong>
          <p>{{ getTemplateProfile(template).usage }}</p>
        </div>

        <div class="template-card-actions">
          <button class="editor-tool" type="button" @click="openPreview(template)">查看生成示例</button>

          <details class="template-more">
            <summary>更多</summary>
            <div class="template-more-menu">
              <button type="button" @click="emit('select-template', template.id)">设为默认</button>
              <button type="button" @click="openSchema(template)">查看 Schema</button>
            </div>
          </details>

          <button
            class="editor-tool is-primary"
            type="button"
            :disabled="selectedTemplateId === template.id"
            @click="emit('use-template', template.id)"
          >
            {{ selectedTemplateId === template.id ? '当前使用中' : '用它生成剧本' }}
          </button>
        </div>
      </article>

      <div v-if="filteredTemplates.length === 0" class="template-empty-state">
        <strong>没有匹配的生成方式</strong>
        <p>换一个关键词，或清空筛选后再试。</p>
        <button class="editor-tool is-primary" type="button" @click="resetFilters">清空筛选</button>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="previewTemplate" class="dialog-backdrop" role="presentation" @click.self="closePreview">
        <section class="generation-dialog template-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="template-preview-title">
          <header class="dialog-header">
            <div>
              <span>生成示例</span>
              <h2 id="template-preview-title">{{ getTemplateProfile(previewTemplate).actionTitle }}</h2>
            </div>
            <button class="dialog-close" type="button" aria-label="关闭生成示例" @click="closePreview">×</button>
          </header>

          <div class="dialog-body template-preview-body">
            <div class="template-preview-grid">
              <section>
                <span>生成结构示例</span>
                <p>{{ getTemplateProfile(previewTemplate).structureExample }}</p>
              </section>
              <section>
                <span>场景示例</span>
                <p>{{ getTemplateProfile(previewTemplate).sceneExample }}</p>
              </section>
              <section>
                <span>对白示例</span>
                <p>{{ getTemplateProfile(previewTemplate).dialogueExample }}</p>
              </section>
            </div>

            <section class="template-yaml-section">
              <span>YAML 片段示例</span>
              <pre class="template-yaml-preview"><code>{{ previewTemplate.yamlExample?.join('\n') }}</code></pre>
            </section>
          </div>

          <footer class="dialog-actions">
            <button class="editor-tool" type="button" @click="openSchema(previewTemplate)">查看 Schema</button>
            <button class="editor-tool" type="button" @click="selectAndClose(previewTemplate)">设为默认</button>
            <button class="editor-tool is-primary" type="button" @click="useAndClose(previewTemplate)">用它生成剧本</button>
          </footer>
        </section>
      </div>

      <div v-if="schemaTemplate" class="dialog-backdrop" role="presentation" @click.self="closeSchema">
        <section class="generation-dialog template-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="template-schema-title">
          <header class="dialog-header">
            <div>
              <span>Schema 字段</span>
              <h2 id="template-schema-title">{{ getTemplateProfile(schemaTemplate).actionTitle }}</h2>
            </div>
            <button class="dialog-close" type="button" aria-label="关闭 Schema 预览" @click="closeSchema">×</button>
          </header>

          <div class="dialog-body template-schema-body">
            <dl class="template-schema-list">
              <div>
                <dt>target_format</dt>
                <dd>{{ getTemplateFormat(schemaTemplate) }}</dd>
              </div>
              <div>
                <dt>fields</dt>
                <dd>{{ schemaTemplate.fields?.join('、') }}</dd>
              </div>
              <div>
                <dt>backend_rules</dt>
                <dd>{{ schemaTemplate.backend_rules?.join('；') || '使用默认生成规则' }}</dd>
              </div>
              <div>
                <dt>features</dt>
                <dd>{{ schemaTemplate.features?.join('、') }}</dd>
              </div>
            </dl>
            <pre class="template-yaml-preview"><code>{{ schemaTemplate.yamlExample?.join('\n') }}</code></pre>
          </div>

          <footer class="dialog-actions">
            <button class="editor-tool" type="button" @click="closeSchema">关闭</button>
            <button class="editor-tool is-primary" type="button" @click="useAndClose(schemaTemplate)">用它生成剧本</button>
          </footer>
        </section>
      </div>
    </Teleport>
  </div>
</template>
