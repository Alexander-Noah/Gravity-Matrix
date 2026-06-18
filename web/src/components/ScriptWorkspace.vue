<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Collection, Document, Plus } from '@element-plus/icons-vue'

const yamlInputRef = ref(null)

const props = defineProps({
  activeYamlLine: { type: Number, default: null },
  correctionScene: { type: Object, default: null },
  yamlContent: { type: String, default: '' },
  iconPaths: { type: Object, required: true },
  isGenerating: { type: Boolean, default: false },
  previewScene: { type: Object, default: null },
  scriptChapters: { type: Array, required: true },
  schemaValidation: { type: Object, required: true },
  statusNotice: { type: String, default: '' },
  yamlLines: { type: Array, required: true },
  saveStatus: { type: String, default: '' },
})

const emit = defineEmits(['add-scene', 'copy-yaml', 'download-yaml', 'open-preview', 'open-schema', 'previous', 'save-yaml', 'select-chapter', 'select-scene', 'update:character', 'update:dialogue', 'update:scene-field', 'update:yamlContent', 'validate-yaml'])

const yamlContent = ref(props.yamlContent)
const isSyncingYamlContent = ref(false)
const yamlLineNumbers = computed(() => Array.from({ length: yamlTextLines.value.length }, (_, index) => index + 1))
const yamlTextLines = computed(() => {
  const lines = yamlContent.value.split('\n')
  return lines.length ? lines : ['']
})
const yamlEditorRows = computed(() => Math.max(18, yamlLineNumbers.value.length))
const outlineTree = computed(() =>
  props.scriptChapters.map((chapter, chapterIndex) => ({
    id: `chapter-${chapter.id || chapter.title || chapterIndex}`,
    label: chapter.title,
    type: 'chapter',
    open: chapter.open,
    source: chapter,
    children: (chapter.scenes || []).map((scene, sceneIndex) => ({
      id: `scene-${scene.id || scene.label || `${chapterIndex}-${sceneIndex}`}`,
      label: scene.label,
      type: 'scene',
      active: scene.active,
      source: scene,
    })),
  })),
)
const outlineExpandedKeys = computed(() => outlineTree.value.filter((chapter) => chapter.open).map((chapter) => chapter.id))

const handleOutlineNodeClick = (node) => {
  if (node.type === 'chapter') {
    emit('select-chapter', node.source)
    return
  }

  emit('select-scene', node.source)
}

watch(
  () => props.yamlContent,
  (nextYaml) => {
    if (nextYaml !== yamlContent.value) {
      isSyncingYamlContent.value = true
      yamlContent.value = nextYaml || ''
      nextTick(() => {
        isSyncingYamlContent.value = false
      })
    }
  },
)

watch(
  yamlContent,
  (nextYaml) => {
    if (isSyncingYamlContent.value) {
      return
    }
    emit('update:yamlContent', nextYaml)
  },
)

watch(
  () => props.yamlContent,
  async (nextYaml, previousYaml) => {
    const isInitialLoad = !previousYaml
    const isDocumentReplace = Math.abs((nextYaml || '').length - (previousYaml || '').length) > 500
    if (!isInitialLoad && !isDocumentReplace) {
      return
    }

    await nextTick()
    getYamlTextarea()?.scrollTo({ top: 0, left: 0 })
  },
)

const getYamlTextarea = () => yamlInputRef.value?.textarea || null

const scrollToYamlLine = (lineNumber) => {
  const editor = getYamlTextarea()

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

  yamlContent.value = nextValue
  nextTick(() => {
    textarea.setSelectionRange(start + 2, start + 2)
  })
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
        <button class="toolbar-button" type="button" :disabled="isGenerating" @click="$emit('save-yaml')">
          <span>保存修改</span>
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

        <el-scrollbar class="chapter-scroll">
          <el-tree
            class="chapter-tree"
            :data="outlineTree"
            node-key="id"
            :default-expanded-keys="outlineExpandedKeys"
            :expand-on-click-node="false"
            :highlight-current="false"
            @node-click="handleOutlineNodeClick"
          >
            <template #default="{ data }">
              <span class="outline-node" :class="[`is-${data.type}`, { 'is-active': data.active }]">
                <el-icon aria-hidden="true">
                  <Collection v-if="data.type === 'chapter'" />
                  <Document v-else />
                </el-icon>
                <span class="outline-node-label">{{ data.label }}</span>
              </span>
            </template>
          </el-tree>
        </el-scrollbar>

        <el-button
          class="add-scene-button"
          type="primary"
          plain
          :icon="Plus"
          :disabled="isGenerating"
          @click="$emit('add-scene')"
        >
          <span>添加场景</span>
        </el-button>
      </aside>

      <div class="yaml-editor yaml-editor-editable" aria-label="YAML 剧本文档">
        <el-input
          ref="yamlInputRef"
          v-model="yamlContent"
          class="yaml-content-input"
          type="textarea"
          :disabled="isGenerating"
          :rows="yamlEditorRows"
          resize="none"
          wrap="off"
          spellcheck="false"
          aria-label="可编辑 YAML 剧本文档"
          @keydown="handleEditorKeydown"
        />
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

    <section class="correction-panel" aria-labelledby="correction-title">
      <header class="correction-header">
        <div>
          <span>人工校正</span>
          <h2 id="correction-title">{{ correctionScene?.title || '选择场景后编辑' }}</h2>
        </div>
        <p>{{ statusNotice || '修改会同步写回 YAML，可保存后导出最终稿。' }}</p>
      </header>

      <div v-if="correctionScene" class="correction-grid">
        <fieldset class="correction-section">
          <legend>场景描述</legend>
          <label>
            <span>场景标题</span>
            <input
              type="text"
              :disabled="isGenerating"
              :value="correctionScene.title"
              @input="$emit('update:scene-field', { field: 'title', value: $event.target.value })"
            />
          </label>
          <div class="correction-pair">
            <label>
              <span>地点</span>
              <input
                type="text"
                :disabled="isGenerating"
                :value="correctionScene.locationName"
                @input="$emit('update:scene-field', { field: 'locationName', value: $event.target.value })"
              />
            </label>
            <label>
              <span>时间</span>
              <input
                type="text"
                :disabled="isGenerating"
                :value="correctionScene.time"
                @input="$emit('update:scene-field', { field: 'time', value: $event.target.value })"
              />
            </label>
          </div>
          <label>
            <span>场景概述</span>
            <textarea
              :disabled="isGenerating"
              :value="correctionScene.synopsis"
              rows="4"
              @input="$emit('update:scene-field', { field: 'synopsis', value: $event.target.value })"
            ></textarea>
          </label>
          <label>
            <span>动作描写</span>
            <textarea
              :disabled="isGenerating"
              :value="correctionScene.stageDirections"
              rows="4"
              @input="$emit('update:scene-field', { field: 'stageDirections', value: $event.target.value })"
            ></textarea>
          </label>
        </fieldset>

        <fieldset class="correction-section">
          <legend>角色信息</legend>
          <div v-for="character in correctionScene.characters" :key="character.id" class="character-editor">
            <div class="correction-pair">
              <label>
                <span>姓名</span>
                <input
                  type="text"
                  :disabled="isGenerating"
                  :value="character.name"
                  @input="$emit('update:character', { characterId: character.id, field: 'name', value: $event.target.value })"
                />
              </label>
              <label>
                <span>身份</span>
                <input
                  type="text"
                  :disabled="isGenerating"
                  :value="character.role"
                  @input="$emit('update:character', { characterId: character.id, field: 'role', value: $event.target.value })"
                />
              </label>
            </div>
            <label>
              <span>角色备注</span>
              <textarea
                :disabled="isGenerating"
                :value="character.description"
                rows="3"
                @input="$emit('update:character', { characterId: character.id, field: 'description', value: $event.target.value })"
              ></textarea>
            </label>
          </div>
          <p v-if="!correctionScene.characters.length" class="correction-empty">当前场景还没有关联角色。</p>
        </fieldset>

        <fieldset class="correction-section dialogue-correction-section">
          <legend>对白内容</legend>
          <article v-for="dialogue in correctionScene.dialogues" :key="dialogue.index" class="dialogue-editor">
            <div class="correction-pair">
              <label>
                <span>说话人</span>
                <select
                  :disabled="isGenerating"
                  :value="dialogue.speakerId"
                  @change="$emit('update:dialogue', { index: dialogue.index, field: 'speaker_id', value: $event.target.value })"
                >
                  <option v-for="character in correctionScene.characterOptions" :key="character.id" :value="character.id">
                    {{ character.name }}
                  </option>
                </select>
              </label>
              <label>
                <span>情绪</span>
                <input
                  type="text"
                  :disabled="isGenerating"
                  :value="dialogue.emotion"
                  @input="$emit('update:dialogue', { index: dialogue.index, field: 'emotion', value: $event.target.value })"
                />
              </label>
            </div>
            <label>
              <span>台词</span>
              <textarea
                :disabled="isGenerating"
                :value="dialogue.line"
                rows="3"
                @input="$emit('update:dialogue', { index: dialogue.index, field: 'line', value: $event.target.value })"
              ></textarea>
            </label>
          </article>
          <p v-if="!correctionScene.dialogues.length" class="correction-empty">当前场景还没有对白。</p>
        </fieldset>
      </div>

      <p v-else class="correction-empty">生成剧本后，在左侧结构里选择一个场景即可校正角色、场景、动作和对白。</p>
    </section>

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
