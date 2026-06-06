<script setup>
defineProps({
  iconPaths: { type: Object, required: true },
  previewDialogues: { type: Array, required: true },
  previewScene: { type: Object, required: true },
  scriptChapters: { type: Array, required: true },
  schemaValidation: { type: Object, required: true },
  statusNotice: { type: String, default: '' },
  yamlLines: { type: Array, required: true },
  yamlText: { type: String, required: true },
  saveStatus: { type: String, default: '' },
})

defineEmits([
  'add-scene',
  'copy-yaml',
  'download-yaml',
  'open-preview',
  'open-schema',
  'previous',
  'save-yaml',
  'update:yaml-text',
  'validate-yaml',
])
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
          <button class="editor-tool" type="button" @click="$emit('previous')">
            <svg class="reverse-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
            </svg>
            <span>上一步：AI解析</span>
          </button>
          <button class="editor-tool" type="button" @click="$emit('open-schema')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.help" :key="path" :d="path" />
            </svg>
            <span>查看 Schema 文档</span>
          </button>
          <button class="editor-tool is-safe" type="button" @click="$emit('validate-yaml')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.shield" :key="path" :d="path" />
            </svg>
            <span>校验格式</span>
          </button>
          <button class="editor-tool" type="button" @click="$emit('save-yaml')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.file" :key="path" :d="path" />
            </svg>
            <span>保存 YAML</span>
          </button>
          <button class="editor-tool" type="button" @click="$emit('copy-yaml')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.copy" :key="path" :d="path" />
            </svg>
            <span>复制 YAML</span>
          </button>
          <button class="editor-tool" type="button" @click="$emit('download-yaml')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.download" :key="path" :d="path" />
            </svg>
            <span>下载 YAML</span>
          </button>
          <button class="editor-tool is-primary" type="button" @click="$emit('open-preview')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.eye" :key="path" :d="path" />
            </svg>
            <span>打开完整预览</span>
            <svg class="button-chevron" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
            </svg>
          </button>
        </div>
      </div>

      <div class="script-editor-layout">
        <aside class="structure-pane" aria-label="剧本结构">
          <div class="structure-heading">
            <h3>剧本结构</h3>
            <button class="icon-button" type="button" aria-label="更多结构操作">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.more" :key="path" :d="path" />
              </svg>
            </button>
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
                <li v-for="scene in chapter.scenes" :key="scene.label">
                  <button class="scene-row" :class="{ 'is-active': scene.active }" type="button">
                    {{ scene.label }}
                  </button>
                </li>
              </ul>
            </li>
          </ul>

          <button class="add-scene-button" type="button" @click="$emit('add-scene')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.plus" :key="path" :d="path" />
            </svg>
            <span>添加场景</span>
          </button>
        </aside>

        <div class="code-pane" aria-label="YAML 剧本文档">
          <button class="code-more" type="button" aria-label="更多编辑器操作">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.more" :key="path" :d="path" />
            </svg>
          </button>
          <textarea
            class="yaml-editor"
            :value="yamlText"
            aria-label="可编辑 YAML 剧本内容"
            spellcheck="false"
            @input="$emit('update:yaml-text', $event.target.value)"
          ></textarea>
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
        <button class="preview-toggle" type="button">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.format" :key="path" :d="path" />
          </svg>
          <span>切换视图</span>
        </button>
      </div>

      <div class="preview-body">
        <article class="scene-preview">
          <div class="scene-meta">
            <h3>{{ previewScene.title }}</h3>
            <p>{{ previewScene.meta }}</p>
          </div>
          <div v-if="previewScene.characters?.length" class="scene-cast">
            <span v-for="character in previewScene.characters" :key="character">{{ character }}</span>
          </div>
          <p class="scene-action">{{ previewScene.action }}</p>
        </article>

        <div class="dialogue-preview">
          <article v-for="dialogue in previewDialogues" :key="dialogue.speaker" class="dialogue-line">
            <h3>{{ dialogue.speaker }}</h3>
            <span>{{ dialogue.note }}</span>
            <p>{{ dialogue.line }}</p>
          </article>
        </div>

        <div class="subway-visual" aria-label="地铁站场景示意图" role="img">
          <span class="station-light"></span>
          <span class="train-body"></span>
          <span class="train-window window-one"></span>
          <span class="train-window window-two"></span>
          <span class="platform-line"></span>
          <span class="commuter commuter-one"></span>
          <span class="commuter commuter-two"></span>
          <span class="commuter commuter-three"></span>
        </div>
      </div>
    </section>
  </div>
</template>
