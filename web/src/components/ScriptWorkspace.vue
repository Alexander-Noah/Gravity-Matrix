<script setup>
defineProps({
  iconPaths: { type: Object, required: true },
  previewDialogues: { type: Array, required: true },
  scriptChapters: { type: Array, required: true },
  yamlLines: { type: Array, required: true },
})
</script>

<template>
  <div class="main-column">
    <section class="script-panel" aria-labelledby="script-title">
      <div class="script-panel-header">
        <div>
          <h2 id="script-title">生成的剧本（YAML）</h2>
          <span>自动保存中...</span>
        </div>
        <div class="editor-actions" aria-label="剧本操作">
          <button class="editor-tool" type="button">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.format" :key="path" :d="path" />
            </svg>
            <span>格式说明</span>
          </button>
          <button class="editor-tool is-safe" type="button">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.shield" :key="path" :d="path" />
            </svg>
            <span>校验</span>
          </button>
          <button class="editor-tool" type="button">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.copy" :key="path" :d="path" />
            </svg>
            <span>复制</span>
          </button>
          <button class="editor-tool is-primary" type="button">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.download" :key="path" :d="path" />
            </svg>
            <span>导出</span>
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

          <button class="add-scene-button" type="button">
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
          <pre><code><span v-for="(line, index) in yamlLines" :key="index" class="code-line"><span class="line-number">{{ index + 1 }}</span><span class="line-content"><template v-for="(token, tokenIndex) in line" :key="`${index}-${tokenIndex}`"><span :class="`yaml-${token.tone}`">{{ token.text }}</span></template></span></span></code></pre>
        </div>
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
            <h3>场景 1-1 地铁站相遇</h3>
            <p>内景 / 地铁站 / 傍晚</p>
          </div>
          <p class="scene-action">人头攒动的地铁站，广播声回荡。林晓背着吉他包，低头看着手机，神情略显迷茫。</p>
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
