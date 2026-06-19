<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  iconPaths: { type: Object, required: true },
  isLoaded: { type: Boolean, default: false },
  isLoading: { type: Boolean, default: false },
  notice: { type: String, default: '' },
  scripts: { type: Array, required: true },
  stats: { type: Array, required: true },
})

const emit = defineEmits(['edit-script', 'preview-script', 'export-script', 'delete-script', 'rename-script', 'clone-script'])

const searchKeyword = ref('')
const selectedType = ref('全部')
const selectedStatus = ref('全部')
const selectedSort = ref('最近编辑')
const exportTarget = ref(null)
const activeMoreId = ref('')
const actionNotice = ref('')

const typeFilters = ['全部', '影视剧', '短剧', '分镜', '广播剧']
const statusFilters = ['全部', '草稿中', '已完成', '需修正']
const sortOptions = ['最近编辑', '创建时间', '场景数量', '对白数量']
const exportFormats = ['导出中文文档（推荐）', '导出 YAML 技术文件', '导出 JSON 数据文件']

const libraryScripts = computed(() =>
  props.scripts
    .filter((script) => script.source_type !== 'source_novel')
    .map((script, index) => normalizeScript(script, index)),
)

const displayStats = computed(() => {
  const items = libraryScripts.value
  const draftCount = items.filter((item) => item.displayStatus === '草稿中').length
  const completedCount = items.filter((item) => item.displayStatus === '已完成').length
  const fixCount = items.filter((item) => item.displayStatus === '需修正').length
  const exportedCount = props.scripts.filter((item) => normalizeStatus(item.status) === '最近导出' || item.status === '已导出').length

  return [
    { label: '全部剧本', value: String(items.length), note: '已生成的剧本草稿', tone: 'violet' },
    { label: '草稿中', value: String(draftCount), note: '可继续编辑', tone: 'blue' },
    { label: '已完成', value: String(completedCount), note: '可预览和导出', tone: 'mint' },
    { label: '需要修正', value: String(fixCount), note: '格式或质量需处理', tone: 'orange' },
    { label: '最近导出', value: String(exportedCount), note: '已生成交付文件', tone: 'neutral' },
  ]
})

const filteredScripts = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  const items = libraryScripts.value.filter((script) => {
    const matchesType = selectedType.value === '全部' || script.displayType === selectedType.value
    const matchesStatus = selectedStatus.value === '全部' || script.displayStatus === selectedStatus.value
    const searchableText = [
      script.displayTitle,
      script.sourceNovel,
      script.displayType,
      script.displayStatus,
      script.versionLabel,
      ...(script.tags || []),
    ].join(' ').toLowerCase()

    return matchesType && matchesStatus && (!keyword || searchableText.includes(keyword))
  })

  return [...items].sort((a, b) => {
    if (selectedSort.value === '场景数量') return Number(b.scenes || 0) - Number(a.scenes || 0)
    if (selectedSort.value === '对白数量') return Number(b.dialogues || 0) - Number(a.dialogues || 0)
    if (selectedSort.value === '创建时间') return sortTime(b.createdAt || b.updatedAt) - sortTime(a.createdAt || a.updatedAt)
    return sortTime(b.updatedAt) - sortTime(a.updatedAt)
  })
})

const hasActiveFilters = computed(() =>
  searchKeyword.value.trim() ||
  selectedType.value !== '全部' ||
  selectedStatus.value !== '全部' ||
  selectedSort.value !== '最近编辑',
)

const emptyTitle = computed(() => {
  if (props.isLoading && !props.isLoaded) return '正在读取剧本库'
  if (hasActiveFilters.value) return '没有找到匹配剧本'
  return '暂无剧本草稿'
})

const emptyDescription = computed(() => {
  if (props.isLoading && !props.isLoaded) return '正在从后端同步剧本草稿、版本和生成结果，请稍候。'
  if (hasActiveFilters.value) return '可以换一个关键词，或清空筛选后查看全部剧本。'
  return '生成剧本后会出现在这里。你可以先新建剧本，或导入已有 YAML 继续编辑。'
})

function normalizeScript(script, index) {
  const displayType = normalizeType(script.type)
  const formatStatus = normalizeFormatStatus(script.schemaStatus)
  const qualityStatus = normalizeQualityStatus(script)
  const displayStatus = normalizeStatus(script.status, formatStatus, qualityStatus)
  const versionLabel = script.version || script.versionLabel || (script.generated_count ? `生成稿 ${script.generated_count}` : `生成稿 ${index + 1}`)
  const title = normalizeTitle(script.title, script.sourceNovel, displayType, versionLabel)

  return {
    ...script,
    displayTitle: title,
    displayType,
    displayStatus,
    formatStatus,
    qualityStatus,
    versionLabel,
    updatedAt: script.updatedAt || script.updated_at || '刚刚编辑',
    createdAt: script.createdAt || script.created_at || script.updatedAt,
  }
}

function normalizeTitle(title, sourceNovel, type, versionLabel) {
  const baseTitle = (title || '').trim()
  if (baseTitle && /\bv\d+|生成稿|版本草稿/i.test(baseTitle)) return baseTitle

  const source = (sourceNovel || baseTitle || '小说').replace(/剧本$/, '').trim()
  const cleanType = type === '分镜' ? '分镜脚本' : `${type}改编稿`
  return `${source}${cleanType} ${versionLabel}`
}

function normalizeType(type) {
  if (type === '短剧') return '短剧'
  if (type === '分镜' || type === '分镜剧本' || type === 'storyboard') return '分镜'
  if (type === '广播剧' || type === 'audio_drama') return '广播剧'
  return '影视剧'
}

function normalizeStatus(status, formatStatus = '格式正常', qualityStatus = '质量良好') {
  if (status === '校验异常' || status === '需修正' || status === '需要修正' || formatStatus === '格式需修正' || qualityStatus === '需要修正') {
    return '需修正'
  }
  if (status === '已完成' || status === '已导出') return '已完成'
  return '草稿中'
}

function normalizeFormatStatus(schemaStatus) {
  if (schemaStatus === '校验通过' || schemaStatus === '格式正常') return '格式正常'
  return '格式需修正'
}

function normalizeQualityStatus(script) {
  const raw = String(script.qualityStatus || script.quality || script.grade || '').toLowerCase()
  if (raw === 'poor' || raw.includes('低') || raw.includes('修正')) return '需要修正'
  if (raw.includes('建议') || raw === 'b' || raw === 'c') return '建议优化'
  if (script.schemaStatus && normalizeFormatStatus(script.schemaStatus) !== '格式正常') return '需要修正'
  return '质量良好'
}

function statusTone(status) {
  if (status === '已完成') return 'is-success'
  if (status === '需修正') return 'is-warning'
  return 'is-draft'
}

function qualityTone(status) {
  if (status === '质量良好') return 'is-success'
  if (status === '建议优化') return 'is-attention'
  return 'is-warning'
}

function sortTime(value) {
  if (!value) return 0
  if (String(value).includes('刚刚') || String(value).includes('分钟')) return Date.now()
  if (String(value).includes('昨天')) return Date.now() - 24 * 60 * 60 * 1000
  if (String(value).includes('天前')) {
    const days = Number(String(value).match(/\d+/)?.[0] || 1)
    return Date.now() - days * 24 * 60 * 60 * 1000
  }
  if (String(value).includes('上周')) return Date.now() - 7 * 24 * 60 * 60 * 1000
  const parsed = Date.parse(value)
  return Number.isNaN(parsed) ? 0 : parsed
}

function resetFilters() {
  searchKeyword.value = ''
  selectedType.value = '全部'
  selectedStatus.value = '全部'
  selectedSort.value = '最近编辑'
}

function openExport(script) {
  exportTarget.value = script
  activeMoreId.value = ''
}

function closeExport() {
  exportTarget.value = null
}

function confirmExport(format) {
  emit('export-script', exportTarget.value, format)
  closeExport()
}

function toggleMore(scriptId) {
  activeMoreId.value = activeMoreId.value === scriptId ? '' : scriptId
}

function handleMoreAction(script, action) {
  if (action === '移动到回收站') {
    const items = JSON.parse(localStorage.getItem('gravityMatrixRecycleBin') || '[]')
    if (!items.find((i) => i.id === script.id)) {
      items.push({ ...script, deletedAt: new Date().toLocaleString() })
      localStorage.setItem('gravityMatrixRecycleBin', JSON.stringify(items))
    }
    emit('delete-script', script)
  } else if (action === '重命名') {
    emit('rename-script', script)
  } else if (action === '复制一份') {
    emit('clone-script', script)
  } else {
    actionNotice.value = `${action} 功能已保留入口，后续可接入后端。`
  }
  activeMoreId.value = ''
}

function showEntryNotice(action) {
  actionNotice.value = `${action} 入口已准备好，后续可接入对应流程。`
}
</script>

<template>
  <div class="script-library-page">
    <section class="library-command-bar" aria-label="剧本库操作">
      <div>
        <span>剧本草稿与版本</span>
        <strong>管理所有已生成的剧本、版本和导出文件</strong>
      </div>
      <div class="library-command-actions">
        <button class="editor-tool is-primary" type="button" @click="showEntryNotice('新建剧本')">新建剧本</button>
        <button class="editor-tool" type="button" @click="showEntryNotice('导入 YAML')">导入 YAML</button>
        <button class="editor-tool" type="button" @click="showEntryNotice('批量导出')">批量导出</button>
      </div>
    </section>

    <section class="library-stats" aria-label="剧本库统计">
      <article v-for="stat in displayStats" :key="stat.label" class="library-stat-card" :class="`tone-${stat.tone}`">
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

      <label class="library-select">
        <span>排序</span>
        <select v-model="selectedSort">
          <option v-for="sort in sortOptions" :key="sort" :value="sort">{{ sort }}</option>
        </select>
      </label>
    </section>

    <div class="library-result-row">
      <span>{{ isLoading ? '正在同步剧本库...' : `当前显示 ${filteredScripts.length} 个剧本` }}</span>
      <p v-if="notice" class="inline-note">{{ notice }}</p>
      <p v-if="actionNotice">{{ actionNotice }}</p>
      <button v-if="hasActiveFilters" class="link-button" type="button" @click="resetFilters">清空筛选</button>
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
            <div class="library-title-row">
              <span class="library-type-pill">{{ script.displayType }}</span>
              <span class="library-status-pill" :class="statusTone(script.displayStatus)">{{ script.displayStatus }}</span>
            </div>
            <h2>{{ script.displayTitle }}</h2>
            <p>来源小说：{{ script.sourceNovel }}</p>
            <p class="library-version">{{ script.versionLabel }} · 最后编辑 {{ script.updatedAt }}</p>
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
            <dt>格式</dt>
            <dd :class="{ 'is-warning': script.formatStatus !== '格式正常' }">{{ script.formatStatus }}</dd>
          </div>
          <div>
            <dt>质量</dt>
            <dd :class="qualityTone(script.qualityStatus)">{{ script.qualityStatus }}</dd>
          </div>
        </dl>

        <div class="library-card-foot">
          <div class="library-tags">
            <span v-for="tag in script.tags" :key="tag">{{ tag === 'poor' ? '需要优化' : tag }}</span>
          </div>
        </div>

        <div class="library-actions">
          <button class="editor-tool is-primary" type="button" @click="emit('edit-script', script)">继续编辑</button>
          <button class="editor-tool" type="button" @click="emit('preview-script', script)">查看预览</button>
          <button class="editor-tool" type="button" @click="openExport(script)">导出</button>
          <div class="library-more">
            <button class="editor-tool" type="button" @click="toggleMore(script.id)">更多</button>
            <div v-if="activeMoreId === script.id" class="library-more-menu">
              <button type="button" @click="handleMoreAction(script, '重命名')">重命名</button>
              <button type="button" @click="handleMoreAction(script, '复制一份')">复制一份</button>
              <button type="button" @click="handleMoreAction(script, '设为最终版')">设为最终版</button>
              <button type="button" @click="handleMoreAction(script, '重新生成')">重新生成</button>
              <button type="button" @click="handleMoreAction(script, '移动到回收站')">移动到回收站</button>
              <button type="button" @click="handleMoreAction(script, '查看生成日志')">查看生成日志</button>
            </div>
          </div>
        </div>
      </article>

      <div v-if="filteredScripts.length === 0" class="library-empty-state" :class="{ 'is-loading': isLoading }">
        <strong>{{ emptyTitle }}</strong>
        <p>{{ emptyDescription }}</p>
        <button v-if="hasActiveFilters" class="editor-tool is-primary" type="button" @click="resetFilters">清空筛选</button>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="exportTarget" class="dialog-backdrop" role="presentation" @click.self="closeExport">
        <section class="generation-dialog library-export-dialog" role="dialog" aria-modal="true" aria-labelledby="library-export-title">
          <header class="dialog-header">
            <div>
              <span>选择导出格式</span>
              <h2 id="library-export-title">{{ exportTarget.displayTitle || exportTarget.title }}</h2>
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
