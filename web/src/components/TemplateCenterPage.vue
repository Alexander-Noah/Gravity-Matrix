<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  iconPaths: { type: Object, required: true },
  selectedTemplateId: { type: String, default: '' },
  templates: { type: Array, required: true },
})

const emit = defineEmits(['select-template', 'use-template'])

const previewTemplate = ref(null)
const searchKeyword = ref('')
const selectedFormat = ref('全部')

const selectedTemplate = computed(() =>
  props.templates.find((template) => template.id === props.selectedTemplateId),
)

const templateFormats = computed(() => {
  const formats = props.templates.map((template) => template.target_format || template.id).filter(Boolean)
  return ['全部', ...Array.from(new Set(formats))]
})

const filteredTemplates = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return props.templates.filter((template) => {
    const format = template.target_format || template.id
    const matchesFormat = selectedFormat.value === '全部' || format === selectedFormat.value
    if (!matchesFormat) return false

    if (!keyword) return true
    const haystack = [
      template.name,
      template.scenario,
      template.target_format,
      ...(template.features || []),
      ...(template.fields || []),
      ...(template.backend_rules || []),
    ].join(' ').toLowerCase()
    return haystack.includes(keyword)
  })
})

const selectedTemplateSummary = computed(() => {
  if (!selectedTemplate.value) {
    return {
      name: '尚未选择',
      description: '选择一个模板后，后端生成设置会保存模板并应用对应结构规则。',
      format: '未设置',
      featureCount: 0,
      fieldCount: 0,
    }
  }

  return {
    name: selectedTemplate.value.name,
    description: selectedTemplate.value.scenario,
    format: selectedTemplate.value.target_format || selectedTemplate.value.id,
    featureCount: selectedTemplate.value.features?.length || 0,
    fieldCount: selectedTemplate.value.fields?.length || 0,
  }
})

const openPreview = (template) => {
  previewTemplate.value = template
}

const closePreview = () => {
  previewTemplate.value = null
}

const resetFilters = () => {
  searchKeyword.value = ''
  selectedFormat.value = '全部'
}
</script>

<template>
  <div class="template-center-page">
    <section class="template-summary" aria-label="模板中心说明">
      <div class="template-summary-copy">
        <span>剧本生成规则</span>
        <h2>选择后续生成剧本时默认使用的结构模板</h2>
        <p>
          模板只影响剧本字段、场景组织和 YAML 结构，不改变页面皮肤，也不包含会员套餐或价格内容。
        </p>
      </div>
      <div class="template-selected-panel">
        <span>当前默认模板</span>
        <strong>{{ selectedTemplateSummary.name }}</strong>
        <small>{{ selectedTemplateSummary.description }}</small>
        <div class="template-selected-meta">
          <code>target_format: {{ selectedTemplateSummary.format }}</code>
          <span>{{ selectedTemplateSummary.featureCount }} 个生成特点</span>
          <span>{{ selectedTemplateSummary.fieldCount }} 个字段</span>
        </div>
      </div>
    </section>

    <section class="template-toolbar" aria-label="模板筛选">
      <label class="template-search">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.eye" :key="path" :d="path" />
        </svg>
        <input v-model="searchKeyword" type="search" placeholder="搜索模板名称、字段、规则或适用场景" />
      </label>

      <div class="template-format-tabs" role="tablist" aria-label="模板格式">
        <button
          v-for="format in templateFormats"
          :key="format"
          type="button"
          :class="{ 'is-active': selectedFormat === format }"
          @click="selectedFormat = format"
        >
          {{ format }}
        </button>
      </div>
    </section>

    <section class="template-grid" aria-label="剧本生成模板列表">
      <article
        v-for="template in filteredTemplates"
        :key="template.id"
        class="template-card"
        :class="{ 'is-selected': selectedTemplateId === template.id }"
      >
        <div class="template-card-header">
          <div class="template-card-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.file" :key="path" :d="path" />
            </svg>
          </div>
          <div>
            <span>{{ selectedTemplateId === template.id ? '已选择' : '可用模板' }}</span>
            <h2>{{ template.name }}</h2>
          </div>
        </div>

        <div class="template-section">
          <h3>适用场景</h3>
          <p>{{ template.scenario }}</p>
        </div>

        <div class="template-format-row">
          <code>target_format: {{ template.target_format || template.id }}</code>
          <span>{{ template.fields?.length || 0 }} fields</span>
        </div>

        <div class="template-section">
          <h3>生成特点</h3>
          <ul>
            <li v-for="feature in template.features" :key="feature">{{ feature }}</li>
          </ul>
        </div>

        <div class="template-section">
          <h3>包含字段</h3>
          <div class="template-field-list">
            <span v-for="field in template.fields" :key="field">{{ field }}</span>
          </div>
        </div>

        <div class="template-section">
          <h3>后端生成规则</h3>
          <ul>
            <li v-for="rule in template.backend_rules || []" :key="rule">{{ rule }}</li>
          </ul>
        </div>

        <div class="template-card-actions">
          <button class="editor-tool" type="button" @click="openPreview(template)">预览 Schema</button>
          <button class="editor-tool" type="button" @click="emit('select-template', template.id)">
            设为默认
          </button>
          <button class="editor-tool is-primary" type="button" @click="emit('use-template', template.id)">
            使用并返回工作台
          </button>
        </div>
      </article>

      <div v-if="filteredTemplates.length === 0" class="template-empty-state">
        <strong>没有匹配的模板</strong>
        <p>换一个关键词或清空格式筛选后再试。</p>
        <button class="editor-tool is-primary" type="button" @click="resetFilters">清空筛选</button>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="previewTemplate" class="dialog-backdrop" role="presentation" @click.self="closePreview">
        <section class="generation-dialog template-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="template-preview-title">
          <header class="dialog-header">
            <div>
              <span>YAML 示例结构</span>
              <h2 id="template-preview-title">{{ previewTemplate.name }}</h2>
            </div>
            <button class="dialog-close" type="button" aria-label="关闭模板结构预览" @click="closePreview">×</button>
          </header>

          <div class="dialog-body">
            <p class="inline-note">
              选择该模板后，前端会把模板 ID 写入生成设置，后端生成 YAML 时会使用
              target_format={{ previewTemplate.target_format }} 和对应生成规则。
            </p>
            <pre class="template-yaml-preview"><code>{{ previewTemplate.yamlExample.join('\n') }}</code></pre>
          </div>

          <footer class="dialog-actions">
            <button class="editor-tool" type="button" @click="closePreview">关闭</button>
            <button class="editor-tool" type="button" @click="emit('select-template', previewTemplate.id); closePreview()">
              设为默认
            </button>
            <button class="editor-tool is-primary" type="button" @click="emit('use-template', previewTemplate.id); closePreview()">
              使用并返回工作台
            </button>
          </footer>
        </section>
      </div>
    </Teleport>
  </div>
</template>
