<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  iconPaths: { type: Object, required: true },
  scripts: { type: Array, required: true },
  stats: { type: Array, required: true },
})

const emit = defineEmits(['edit-script', 'preview-script', 'export-script', 'delete-script', 'rename-script', 'clone-script'])

const searchKeyword = ref('')
const selectedType = ref('全部')
const selectedStatus = ref('全部')
const exportTarget = ref(null)
const activeMoreId = ref('')
const actionNotice = ref('')

const typeFilters = ['全部', '影视剧', '短剧', '话剧', '分镜剧本', '广播剧']
const statusFilters = ['全部', '草稿', '编辑中', '已完成', '已导出', '校验异常']
const exportFormats = ['YAML', 'TXT', 'Markdown', 'PDF']

const filteredScripts = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()

  return props.scripts.filter((script) => {
    const matchesType = selectedType.value === '全部' || script.type === selectedType.value
    const matchesStatus = selectedStatus.value === '全部' || script.status === selectedStatus.value
    const searchableText = [script.title, script.sourceNovel, script.type, script.status, ...script.tags]
      .join(' ')
      .toLowerCase()

    return matchesType && matchesStatus && (!keyword || searchableText.includes(keyword))
  })
})

const resetFilters = () => {
  searchKeyword.value = ''
  selectedType.value = '全部'
  selectedStatus.value = '全部'
}

const openExport = (script) => {
  exportTarget.value = script
  activeMoreId.value = ''
}

const closeExport = () => {
  exportTarget.value = null
}

const confirmExport = (format) => {
  emit('export-script', exportTarget.value, format)
  closeExport()
}

const toggleMore = (scriptId) => {
  activeMoreId.value = activeMoreId.value === scriptId ? '' : scriptId
}

const handleMoreAction = (script, action) => {
  if (action === '移动到回收站') emit('delete-script', script)
  else if (action === '重命名') emit('rename-script', script)
  else if (action === '复制为新版本') emit('clone-script', script)
  activeMoreId.value = ''
}
</script>

<template>
  <div class="script-library-page">
    <section class="library-stats" aria-label="剧本库统计">
      <article v-for="stat in stats" :key="stat.label" class="library-stat-card" :class="`tone-${stat.tone}`">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.note }}</small>
      </article>
    </section>

    <section class="library-toolbar" aria-label="剧本筛选">
      <label class="library-search">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.eye" :key="path" :d="path" />
        </svg>
        <input v-model="searchKeyword" type="search" placeholder="搜索剧本名称、来源小说或标签" />
      </label>

      <label class="library-select">
        <span>类型</span>
        <select v-model="selectedType">
          <option v-for="type in typeFilters" :key="type" :value="type">{{ type }}</option>
        </select>
      </label>

      <label class="library-select">
        <span>状态</span>
        <select v-model="selectedStatus">
          <option v-for="status in statusFilters" :key="status" :value="status">{{ status }}</option>
        </select>
      </label>
    </section>

    <div class="library-result-row">
      <span>当前显示 {{ filteredScripts.length }} 个剧本</span>
      <p v-if="actionNotice">{{ actionNotice }}</p>
      <button
        v-if="searchKeyword || selectedType !== '全部' || selectedStatus !== '全部'"
        class="link-button"
        type="button"
        @click="resetFilters"
      >
        清空筛选
      </button>
    </div>

    <section class="library-card-list" aria-label="剧本列表">
      <article v-for="script in filteredScripts" :key="script.id" class="library-script-card">
        <div class="library-card-head">
          <div class="library-file-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.book" :key="path" :d="path" />
            </svg>
          </div>
          <div>
            <span>{{ script.type }}</span>
            <h2>{{ script.title }}</h2>
            <p>来源小说：{{ script.sourceNovel }}</p>
          </div>
        </div>

        <dl class="library-meta-grid">
          <div>
            <dt>章节</dt>
            <dd>{{ script.chapters }}</dd>
          </div>
          <div>
            <dt>场景</dt>
            <dd>{{ script.scenes }}</dd>
          </div>
          <div>
            <dt>对白</dt>
            <dd>{{ script.dialogues }}</dd>
          </div>
          <div>
            <dt>Schema</dt>
            <dd :class="{ 'is-warning': script.schemaStatus !== '校验通过' }">{{ script.schemaStatus }}</dd>
          </div>
        </dl>

        <div class="library-card-foot">
          <div class="library-status">
            <span>{{ script.status }}</span>
            <time>{{ script.updatedAt }}</time>
          </div>
          <div class="library-tags">
            <span v-for="tag in script.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>

        <div class="library-actions">
          <button class="editor-tool is-primary" type="button" @click="emit('edit-script', script)">继续编辑</button>
          <button class="editor-tool" type="button" @click="emit('preview-script', script)">预览</button>
          <button class="editor-tool" type="button" @click="openExport(script)">导出</button>
          <div class="library-more">
            <button class="editor-tool" type="button" @click="toggleMore(script.id)">更多</button>
            <div v-if="activeMoreId === script.id" class="library-more-menu">
              <button type="button" @click="handleMoreAction(script, '重命名')">重命名</button>
              <button type="button" @click="handleMoreAction(script, '复制为新版本')">复制为新版本</button>
              <button type="button" @click="handleMoreAction(script, '移动到回收站')">移动到回收站</button>
            </div>
          </div>
        </div>
      </article>

      <div v-if="filteredScripts.length === 0" class="library-empty-state">
        <strong>没有找到匹配剧本</strong>
        <p>可以换一个关键词，或清空筛选后查看全部剧本。</p>
        <button class="editor-tool is-primary" type="button" @click="resetFilters">清空筛选</button>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="exportTarget" class="dialog-backdrop" role="presentation" @click.self="closeExport">
        <section class="generation-dialog library-export-dialog" role="dialog" aria-modal="true" aria-labelledby="library-export-title">
          <header class="dialog-header">
            <div>
              <span>选择导出格式</span>
              <h2 id="library-export-title">{{ exportTarget.title }}</h2>
            </div>
            <button class="dialog-close" type="button" aria-label="关闭导出格式选择" @click="closeExport">×</button>
          </header>

          <div class="dialog-body">
            <div class="library-export-grid">
              <button v-for="format in exportFormats" :key="format" type="button" @click="confirmExport(format)">
                {{ format }}
              </button>
            </div>
          </div>

          <footer class="dialog-actions">
            <button class="editor-tool" type="button" @click="closeExport">取消</button>
          </footer>
        </section>
      </div>
    </Teleport>
  </div>
</template>
