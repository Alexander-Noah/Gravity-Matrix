<script setup>
defineProps({
  exportNotice: { type: String, default: '' },
  iconPaths: { type: Object, required: true },
  scenes: { type: Array, required: true },
})

defineEmits(['back', 'export-markdown', 'export-pdf', 'export-txt', 'export-yaml'])
</script>

<template>
  <div class="script-preview-page">
    <section class="preview-export-toolbar" aria-labelledby="full-preview-title">
      <div>
        <span>完整预览</span>
        <h2 id="full-preview-title">标准剧本文本</h2>
      </div>
      <div class="preview-export-actions" aria-label="预览导出操作">
        <button class="editor-tool" type="button" @click="$emit('back')">
          <svg class="reverse-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
          </svg>
          <span>返回编辑</span>
        </button>
        <button class="editor-tool" type="button" @click="$emit('export-yaml')">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.download" :key="path" :d="path" />
          </svg>
          <span>导出 YAML</span>
        </button>
        <button class="editor-tool" type="button" @click="$emit('export-txt')">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.text" :key="path" :d="path" />
          </svg>
          <span>导出 TXT</span>
        </button>
        <button class="editor-tool" type="button" @click="$emit('export-markdown')">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.format" :key="path" :d="path" />
          </svg>
          <span>导出 Markdown</span>
        </button>
        <button class="editor-tool is-primary" type="button" @click="$emit('export-pdf')">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.file" :key="path" :d="path" />
          </svg>
          <span>导出 PDF</span>
        </button>
      </div>
    </section>

    <p v-if="exportNotice" class="inline-note preview-export-notice">{{ exportNotice }}</p>

    <section class="screenplay-paper" aria-label="剧本文本预览">
      <article v-for="scene in scenes" :key="scene.title" class="screenplay-scene">
        <header>
          <h3>{{ scene.title }}</h3>
          <p>{{ scene.meta }}</p>
        </header>

        <div class="screenplay-cast" aria-label="出场人物">
          <span v-for="character in scene.characters" :key="character">{{ character }}</span>
        </div>

        <p class="screenplay-action">{{ scene.action }}</p>

        <div class="screenplay-dialogues">
          <article v-for="dialogue in scene.dialogues" :key="`${scene.title}-${dialogue.speaker}-${dialogue.line}`">
            <h4>{{ dialogue.speaker }}</h4>
            <p>{{ dialogue.line }}</p>
          </article>
        </div>
      </article>
    </section>
  </div>
</template>
