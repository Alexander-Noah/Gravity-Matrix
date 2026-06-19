<script setup>
import { computed } from 'vue'

const props = defineProps({
  exportNotice: { type: String, default: '' },
  iconPaths: { type: Object, required: true },
  scenes: { type: Array, required: true },
})

const emit = defineEmits(['back', 'export-document', 'export-json', 'export-yaml'])

const closeExportMenu = (event, exportType) => {
  const menu = event.currentTarget.closest('details')
  if (menu) {
    menu.open = false
  }
  emit(exportType)
}

const previewStats = computed(() => {
  const characterNames = new Set()
  const dialogueCount = props.scenes.reduce((total, scene) => {
    ;(scene.characters || []).forEach((character) => characterNames.add(character))
    return total + (scene.dialogues?.length || 0)
  }, 0)

  return [
    { label: '场景', value: props.scenes.length },
    { label: '角色', value: characterNames.size },
    { label: '对白', value: dialogueCount },
  ]
})
</script>

<template>
  <div class="script-preview-page">
    <section class="preview-export-toolbar" aria-labelledby="full-preview-title">
      <div>
        <span>完整预览</span>
        <h2 id="full-preview-title">标准剧本文本</h2>
      </div>
      <div class="preview-export-stats" aria-label="剧本预览统计">
        <span v-for="stat in previewStats" :key="stat.label">
          <strong>{{ stat.value }}</strong>{{ stat.label }}
        </span>
      </div>
      <div class="preview-export-actions" aria-label="预览导出操作">
        <button class="editor-tool" type="button" @click="emit('back')">
          <svg class="reverse-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
          </svg>
          <span>返回编辑</span>
        </button>
        <div class="preview-export-menu">
          <button class="editor-tool is-primary" type="button" @click="emit('export-document')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.file" :key="path" :d="path" />
            </svg>
            <span>导出剧本文档</span>
          </button>
          <details class="export-format-menu">
            <summary class="editor-tool" aria-label="选择导出格式">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
              </svg>
            </summary>
            <div class="export-format-list" role="menu">
              <button type="button" role="menuitem" @click="closeExportMenu($event, 'export-document')">
                <strong>导出中文文档（推荐）</strong>
                <span>适合阅读、审稿和发给非技术用户</span>
              </button>
              <button type="button" role="menuitem" @click="closeExportMenu($event, 'export-yaml')">
                <strong>导出 YAML 技术文件</strong>
                <span>适合再次导入、校验和继续编辑</span>
              </button>
              <button type="button" role="menuitem" @click="closeExportMenu($event, 'export-json')">
                <strong>导出 JSON 数据文件</strong>
                <span>适合系统对接和二次处理</span>
              </button>
            </div>
          </details>
        </div>
      </div>
    </section>

    <p v-if="exportNotice" class="inline-note preview-export-notice">{{ exportNotice }}</p>

    <div class="screenplay-preview-shell">
      <section class="screenplay-paper" aria-label="剧本文本预览">
        <article v-for="(scene, index) in scenes" :id="`preview-scene-${index}`" :key="scene.title" class="screenplay-scene">
          <header>
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <div>
              <h3>{{ scene.title }}</h3>
              <p>{{ scene.meta }}</p>
            </div>
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

      <aside class="screenplay-outline" aria-label="场景概览">
        <div>
          <span>场景概览</span>
          <strong>{{ scenes.length }} 个场景</strong>
        </div>
        <nav>
          <a v-for="(scene, index) in scenes" :key="scene.title" :href="`#preview-scene-${index}`">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <strong>{{ scene.title }}</strong>
            <small>{{ scene.meta }}</small>
          </a>
        </nav>
      </aside>
    </div>
  </div>
</template>
