<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const yamlEditorRef = ref(null)

const props = defineProps({
  activeYamlLine: { type: Number, default: null },
  yamlText: { type: String, default: '' },
  iconPaths: { type: Object, required: true },
  isGenerating: { type: Boolean, default: false },
  previewScene: { type: Object, default: null },
  scriptChapters: { type: Array, required: true },
  schemaValidation: { type: Object, required: true },
  statusNotice: { type: String, default: '' },
  yamlLines: { type: Array, required: true },
  saveStatus: { type: String, default: '' },
})

defineEmits(['add-scene', 'copy-yaml', 'download-yaml', 'open-preview', 'open-schema', 'previous', 'select-chapter', 'select-scene', 'update:yaml-text', 'validate-yaml'])

const yamlLineNumbers = computed(() => Array.from({ length: yamlTextLines.value.length }, (_, index) => index + 1))
const yamlTextLines = computed(() => {
  const lines = props.yamlText.split('\n')
  return lines.length ? lines : ['']
})
const yamlEditorRows = computed(() => yamlLineNumbers.value.length)

watch(
  () => props.yamlText,
  async () => {
    await nextTick()
    yamlEditorRef.value?.scrollTo({ top: 0, left: 0 })
  },
)

const scrollToYamlLine = (lineNumber) => {
  const editor = yamlEditorRef.value

  if (!editor || !lineNumber) {
    return
  }

  const lineHeight = Number.parseFloat(getComputedStyle(editor).getPropertyValue('--yaml-line-height')) || 21
  editor.scrollTo({
    top: Math.max(0, (lineNumber - 4) * lineHeight),
    left: 0,
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
  })
}

const handleEditorKeydown = (event) => {
  if (event.key !== 'Tab') {
    return
  }

  event.preventDefault()
  const textarea = event.target
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const nextValue = `${textarea.value.slice(0, start)}  ${textarea.value.slice(end)}`

  textarea.value = nextValue
  textarea.setSelectionRange(start + 2, start + 2)
  textarea.dispatchEvent(new Event('input', { bubbles: true }))
}

defineExpose({ scrollToYamlLine })
</script>

<template>
  <section class="script-console" aria-labelledby="script-title">
    <header class="console-toolbar toolbar-v1">
      <div class="console-title">
        <span>YAML 草稿</span>
        <h2 id="script-title">生成的剧本</h2>
        <p v-if="saveStatus" :class="{ 'is-error': saveStatus === '保存失败' }">{{ saveStatus }}</p>
      </div>

      <div class="console-actions" aria-label="剧本操作">
        <button class="toolbar-button" type="button" :disabled="isGenerating" @click="$emit('previous')">
          <span>上一步</span>
        </button>
        <button class="toolbar-button" type="button" @click="$emit('open-schema')">
          <span>Schema</span>
        </button>
        <button class="toolbar-button is-success" type="button" :disabled="isGenerating" @click="$emit('validate-yaml')">
          <span>校验格式</span>
        </button>
        <button class="toolbar-button" type="button" :disabled="isGenerating" @click="$emit('copy-yaml')">
          <span>复制 YAML</span>
        </button>
        <button class="toolbar-button" type="button" :disabled="isGenerating" @click="$emit('download-yaml')">
          <span>下载 YAML</span>
        </button>
        <button class="toolbar-button is-primary" type="button" :disabled="isGenerating" @click="$emit('open-preview')">
          <span>完整预览</span>
        </button>
      </div>
    </header>

    <div class="console-grid">
      <aside class="outline-pane" aria-label="剧本结构">
        <div class="pane-heading">
          <span>结构导航</span>
          <strong>{{ scriptChapters.length }} 章</strong>
        </div>

        <ol class="chapter-tree">
          <li v-for="chapter in scriptChapters" :key="chapter.title" :class="{ 'is-open': chapter.open }">
            <button class="chapter-row" type="button" @click="$emit('select-chapter', chapter)">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
              </svg>
              <span>{{ chapter.title }}</span>
            </button>

            <ol v-if="chapter.open && chapter.scenes.length" class="scene-list">
              <li v-for="scene in chapter.scenes" :key="scene.id || scene.label">
                <button class="scene-row" :class="{ 'is-active': scene.active }" type="button" @click="$emit('select-scene', scene)">
                  {{ scene.label }}
                </button>
              </li>
            </ol>
          </li>
        </ol>

        <button class="add-scene-button" type="button" :disabled="isGenerating" @click="$emit('add-scene')">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.plus" :key="path" :d="path" />
          </svg>
          <span>添加场景</span>
        </button>
      </aside>

      <div ref="yamlEditorRef" class="yaml-editor yaml-editor-editable" aria-label="YAML 剧本文档">
        <div class="yaml-code-layer" aria-hidden="true">
          <div
            v-for="(line, index) in yamlTextLines"
            :key="`${index}-${line}`"
            class="yaml-render-line"
            :class="{ 'is-jump-target': activeYamlLine === index + 1 }"
          >
            <span class="yaml-render-line-number">{{ index + 1 }}</span>
            <span class="yaml-render-line-content">{{ line || ' ' }}</span>
          </div>
        </div>
        <textarea
          class="yaml-textarea"
          :disabled="isGenerating"
          spellcheck="false"
          :value="yamlText"
          :rows="yamlEditorRows"
          aria-label="可编辑 YAML 剧本文档"
          @input="$emit('update:yaml-text', $event.target.value)"
          @keydown="handleEditorKeydown"
        ></textarea>
      </div>

      <aside class="validation-pane" aria-labelledby="schema-title">
        <div class="pane-heading">
          <span>校验结果</span>
          <strong id="schema-title">{{ schemaValidation.yamlValid && schemaValidation.requiredFieldsValid ? '通过' : '待修正' }}</strong>
        </div>

        <dl class="validation-list">
          <div>
            <dt>YAML 格式</dt>
            <dd :class="{ 'is-valid': schemaValidation.yamlValid }">{{ schemaValidation.yamlValid ? '正确' : '需要修正' }}</dd>
          </div>
          <div>
            <dt>必填字段</dt>
            <dd :class="{ 'is-valid': schemaValidation.requiredFieldsValid }">{{ schemaValidation.requiredFieldsValid ? '完整' : '缺失' }}</dd>
          </div>
          <div>
            <dt>章节数量</dt>
            <dd>{{ schemaValidation.chapterCount }}</dd>
          </div>
          <div>
            <dt>场景数量</dt>
            <dd>{{ schemaValidation.sceneCount }}</dd>
          </div>
        </dl>

        <p class="validation-message">{{ schemaValidation.message }}</p>
        <time class="validation-time">{{ schemaValidation.checkedAt }}</time>
        <p v-if="statusNotice" class="validation-notice">{{ statusNotice }}</p>
      </aside>
    </div>

    <section class="script-preview-strip" aria-labelledby="preview-title">
      <header class="preview-strip-header">
        <h2 id="preview-title">剧本预览</h2>
        <button class="preview-toggle" type="button" :disabled="isGenerating" @click="$emit('open-preview')">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.format" :key="path" :d="path" />
          </svg>
          <span>切换视图</span>
        </button>
      </header>

      <div class="preview-strip-body">
        <article class="scene-preview">
          <div class="scene-meta">
            <h3>{{ previewScene?.title || '等待生成真实剧本' }}</h3>
            <p>{{ previewScene?.meta || '后端任务完成后会显示场景预览' }}</p>
          </div>
          <p class="scene-action">{{ previewScene?.action || '当前项目还没有可预览的 YAML 场景，请先完成剧本生成。' }}</p>
        </article>

        <div class="dialogue-preview">
          <article v-for="dialogue in previewScene?.dialogues || []" :key="`${dialogue.speaker}-${dialogue.line}`" class="dialogue-line">
            <h3>{{ dialogue.speaker }}</h3>
            <span>{{ dialogue.note || 'determined' }}</span>
            <p>{{ dialogue.line }}</p>
          </article>
          <article v-if="!previewScene?.dialogues?.length" class="dialogue-line">
            <h3>对白</h3>
            <span>等待 YAML</span>
            <p>生成完成后，这里会显示人物对白与情绪提示。</p>
          </article>
        </div>

        <div class="subway-visual" aria-label="场景画面预览">
          <div class="station-wall" aria-hidden="true"></div>
          <div class="train" aria-hidden="true"><span></span><span></span></div>
          <div class="platform" aria-hidden="true"></div>
          <div class="visual-people" aria-hidden="true"><span></span><span></span><span></span></div>
        </div>
      </div>
    </section>
  </section>
</template>
