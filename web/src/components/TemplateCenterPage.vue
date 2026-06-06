<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  iconPaths: { type: Object, required: true },
  selectedTemplateId: { type: String, default: '' },
  templates: { type: Array, required: true },
})

const emit = defineEmits(['select-template'])

const previewTemplate = ref(null)

const selectedTemplate = computed(() =>
  props.templates.find((template) => template.id === props.selectedTemplateId),
)

const openPreview = (template) => {
  previewTemplate.value = template
}

const closePreview = () => {
  previewTemplate.value = null
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
        <strong>{{ selectedTemplate?.name || '尚未选择' }}</strong>
        <small>{{ selectedTemplate?.scenario || '选择一个模板后，后端生成设置会保存模板并应用对应结构规则。' }}</small>
        <code v-if="selectedTemplate?.target_format">target_format: {{ selectedTemplate.target_format }}</code>
      </div>
    </section>

    <section class="template-grid" aria-label="剧本生成模板列表">
      <article
        v-for="template in templates"
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
          <button class="editor-tool is-primary" type="button" @click="emit('select-template', template.id)">
            设为生成模板
          </button>
        </div>
      </article>
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
            <button class="editor-tool is-primary" type="button" @click="emit('select-template', previewTemplate.id); closePreview()">
              设为生成模板
            </button>
          </footer>
        </section>
      </div>
    </Teleport>
  </div>
</template>
