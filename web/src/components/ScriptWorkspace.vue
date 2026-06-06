<script setup>
import { ref } from 'vue'

defineProps({
  iconPaths: { type: Object, required: true },
  isGenerating: { type: Boolean, default: false },
  previewScene: { type: Object, default: null },
  scriptChapters: { type: Array, required: true },
  schemaValidation: { type: Object, required: true },
  statusNotice: { type: String, default: '' },
  yamlLines: { type: Array, required: true },
  yamlText: { type: String, required: true },
  saveStatus: { type: String, default: '' },
})

defineEmits(['add-scene', 'copy-yaml', 'download-yaml', 'open-preview', 'open-schema', 'previous', 'select-scene', 'validate-yaml', 'update:yamlText'])

const preRef = ref(null)
const syncScroll = (e) => {
  if (preRef.value) {
    preRef.value.scrollTop = e.target.scrollTop
    preRef.value.scrollLeft = e.target.scrollLeft
  }
}
</script>

<template>
  <div class="main-column">
    <section class="script-panel" aria-labelledby="script-title">
      <div class="script-panel-header">
        <div>
          <h2 id="script-title">生成的剧本（YAML）</h2>
          <span v-if="saveStatus" :class="{ 'is-error': saveStatus === '保存失败' }">{{ saveStatus }}</span>
        </div>
        <div class="editor-actions" aria-label="剧本操作">
          <div class="editor-action-group">
            <span>流程</span>
            <button class="editor-tool" type="button" :disabled="isGenerating" @click="$emit('previous')">
              <svg class="reverse-icon" viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
              </svg>
              <span>AI解析</span>
            </button>
            <button class="editor-tool is-primary" type="button" :disabled="isGenerating" @click="$emit('open-preview')">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.eye" :key="path" :d="path" />
              </svg>
              <span>完整预览</span>
            </button>
          </div>
          <div class="editor-action-group">
            <span>结构</span>
            <button class="editor-tool" type="button" @click="$emit('open-schema')">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.help" :key="path" :d="path" />
              </svg>
              <span>Schema</span>
            </button>
            <button class="editor-tool is-safe" type="button" :disabled="isGenerating" @click="$emit('validate-yaml')">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.shield" :key="path" :d="path" />
              </svg>
              <span>校验</span>
            </button>
          </div>
          <div class="editor-action-group">
            <span>导出</span>
            <button class="editor-tool" type="button" :disabled="isGenerating" @click="$emit('copy-yaml')">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.copy" :key="path" :d="path" />
              </svg>
              <span>复制</span>
            </button>
            <button class="editor-tool" type="button" :disabled="isGenerating" @click="$emit('download-yaml')">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.download" :key="path" :d="path" />
              </svg>
              <span>下载</span>
            </button>
          </div>
        </div>
      </div>

      <div class="script-editor-layout">
        <aside class="structure-pane" aria-label="剧本结构">
          <div class="structure-heading">
            <h3>剧本结构</h3>
          </div>

          <ul class="chapter-tree">
            <li v-for="chapter in scriptChapters" :key="chapter.title" :class="{ 'is-open': chapter.open }">
              <button class="chapter-row" type="button">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
                </svg>
                <span>{{ chapter.title }}</span>
              </button>
              <ul v-if="chapter.scenes.length" class="scene-list">
                <li v-for="scene in chapter.scenes" :key="scene.id || scene.label">
                  <button class="scene-row" :class="{ 'is-active': scene.active }" type="button" @click="$emit('select-scene', scene.id)">
                    {{ scene.label }}
                  </button>
                </li>
              </ul>
            </li>
          </ul>

          <button class="add-scene-button" type="button" :disabled="isGenerating" @click="$emit('add-scene')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.plus" :key="path" :d="path" />
            </svg>
            <span>添加场景</span>
          </button>
        </aside>

        <div class="code-pane" aria-label="YAML 剧本文档">
          <textarea
            class="yaml-editor-textarea"
            :value="yamlText"
            @input="$emit('update:yamlText', $event.target.value)"
            @scroll="syncScroll"
            spellcheck="false"
          ></textarea>
          <pre ref="preRef" aria-hidden="true"><code><span v-for="(line, index) in yamlLines" :key="index" class="code-line"><span class="line-number">{{ index + 1 }}</span><span class="line-content"><template v-for="(token, tokenIndex) in line" :key="`${index}-${tokenIndex}`"><span :class="`yaml-${token.tone}`">{{ token.text }}</span></template></span></span></code></pre>
        </div>

        <aside class="schema-panel" aria-labelledby="schema-title">
          <div class="schema-panel-header">
            <div>
              <span>Schema 校验</span>
              <h3 id="schema-title">结构检查结果</h3>
            </div>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.shield" :key="path" :d="path" />
            </svg>
          </div>

          <dl class="schema-check-list">
            <div>
              <dt>YAML 格式</dt>
              <dd :class="{ 'is-valid': schemaValidation.yamlValid }">
                {{ schemaValidation.yamlValid ? '正确' : '需要修正' }}
              </dd>
            </div>
            <div>
              <dt>必填字段</dt>
              <dd :class="{ 'is-valid': schemaValidation.requiredFieldsValid }">
                {{ schemaValidation.requiredFieldsValid ? '完整' : '缺失' }}
              </dd>
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

          <p class="schema-message">{{ schemaValidation.message }}</p>
          <p class="schema-time">{{ schemaValidation.checkedAt }}</p>
          <p v-if="statusNotice" class="inline-note schema-status">{{ statusNotice }}</p>
        </aside>
      </div>
    </section>

    <section class="preview-panel" aria-labelledby="preview-title">
      <div class="preview-header">
        <h2 id="preview-title">剧本预览</h2>
        <button class="preview-toggle" type="button" :disabled="isGenerating" @click="$emit('open-preview')">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.format" :key="path" :d="path" />
          </svg>
          <span>切换视图</span>
        </button>
      </div>

      <div class="preview-body">
        <article v-if="previewScene" class="scene-preview">
          <div class="scene-meta">
            <h3>{{ previewScene.title }}</h3>
            <p>{{ previewScene.meta }}</p>
          </div>
          <p class="scene-action">{{ previewScene.action }}</p>
        </article>
        <article v-else class="scene-preview">
          <div class="scene-meta">
            <h3>等待生成真实剧本</h3>
            <p>后端任务完成后会显示场景预览</p>
          </div>
          <p class="scene-action">当前项目还没有可预览的 YAML 场景，请先完成剧本生成。</p>
        </article>

        <div v-if="previewScene?.dialogues?.length" class="dialogue-preview">
          <article v-for="dialogue in previewScene.dialogues" :key="`${dialogue.speaker}-${dialogue.line}`" class="dialogue-line">
            <h3>{{ dialogue.speaker }}</h3>
            <span>{{ dialogue.note }}</span>
            <p>{{ dialogue.line }}</p>
          </article>
        </div>

        <div v-if="previewScene" class="scene-facts" aria-label="场景要素">
          <span v-for="character in previewScene.characters" :key="character">{{ character }}</span>
        </div>
        <div v-else class="scene-facts" aria-label="场景要素">
          <span>等待 YAML</span>
        </div>
      </div>
    </section>
  </div>
</template>
