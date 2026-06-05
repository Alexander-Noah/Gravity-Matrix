<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  activities: { type: Array, required: true },
  iconPaths: { type: Object, required: true },
  projects: { type: Array, required: true },
  stats: { type: Array, required: true },
})

defineEmits(['open-project', 'delete-project'])

const searchKeyword = ref('')
const activeStatus = ref('all')

const statusFilters = computed(() => [
  { label: '全部', value: 'all' },
  ...Array.from(new Set(props.projects.map((project) => project.status))).map((status) => ({
    label: status,
    value: status,
  })),
])

const filteredProjects = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()

  return props.projects.filter((project) => {
    const matchesStatus = activeStatus.value === 'all' || project.status === activeStatus.value
    const searchableText = [
      project.title,
      project.type,
      project.status,
      project.updatedAt,
      project.owner,
      project.nextAction,
    ]
      .join(' ')
      .toLowerCase()

    return matchesStatus && (!keyword || searchableText.includes(keyword))
  })
})

const resetFilters = () => {
  searchKeyword.value = ''
  activeStatus.value = 'all'
}
</script>

<template>
  <div class="projects-page">
    <section class="projects-overview" aria-label="项目概览">
      <article v-for="stat in stats" :key="stat.label" class="project-stat-card" :class="`tone-${stat.tone}`">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small>{{ stat.note }}</small>
      </article>
    </section>

    <section class="projects-toolbar" aria-label="项目筛选">
      <label class="project-search">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.eye" :key="path" :d="path" />
        </svg>
        <input v-model="searchKeyword" type="search" placeholder="搜索项目、剧本类型或最近动作" />
      </label>
      <div class="project-filter-tabs" role="tablist" aria-label="项目状态">
        <button
          v-for="filter in statusFilters"
          :key="filter.value"
          :aria-selected="activeStatus === filter.value"
          :class="{ 'is-active': activeStatus === filter.value }"
          role="tab"
          type="button"
          @click="activeStatus = filter.value"
        >
          {{ filter.label }}
        </button>
      </div>
    </section>

    <div class="project-result-row">
      <span>当前显示 {{ filteredProjects.length }} 个项目</span>
      <button v-if="searchKeyword || activeStatus !== 'all'" class="link-button" type="button" @click="resetFilters">
        清空筛选
      </button>
    </div>

    <div class="projects-content-grid">
      <section class="project-card-list" aria-label="项目列表">
        <article v-for="project in filteredProjects" :key="project.title" class="project-card">
          <div class="project-card-main">
            <div class="project-icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.folder" :key="path" :d="path" />
              </svg>
            </div>
            <div>
              <span>{{ project.type }}</span>
              <h2>{{ project.title }}</h2>
              <p>{{ project.owner }} · {{ project.updatedAt }}</p>
            </div>
          </div>

          <div class="project-progress" aria-label="项目进度">
            <div>
              <span>{{ project.status }}</span>
              <strong>{{ project.progress }}%</strong>
            </div>
            <meter min="0" max="100" :value="project.progress">{{ project.progress }}%</meter>
          </div>

          <dl class="project-meta">
            <div>
              <dt>章节</dt>
              <dd>{{ project.chapters }}</dd>
            </div>
            <div>
              <dt>场景</dt>
              <dd>{{ project.scenes }}</dd>
            </div>
            <div>
              <dt>下一步</dt>
              <dd>{{ project.nextAction }}</dd>
            </div>
          </dl>

          <div class="project-card-actions">
            <button class="editor-tool" type="button" @click="$emit('delete-project', project)">删除项目</button>
            <button class="editor-tool is-primary" type="button" @click="$emit('open-project', project)">
              <span>打开项目</span>
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
              </svg>
            </button>
          </div>
        </article>

        <div v-if="filteredProjects.length === 0" class="project-empty-state">
          <strong>没有找到匹配项目</strong>
          <p>可以换一个关键词，或清空筛选后查看全部项目。</p>
          <button class="editor-tool is-primary" type="button" @click="resetFilters">清空筛选</button>
        </div>
      </section>

      <aside class="project-activity-panel" aria-labelledby="activity-title">
        <div class="project-section-header">
          <h2 id="activity-title">最近编辑记录</h2>
          <button class="link-button" type="button">
            <span>查看全部</span>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
            </svg>
          </button>
        </div>
        <ol class="activity-list">
          <li v-for="activity in activities" :key="activity.title">
            <span>{{ activity.status }}</span>
            <strong>{{ activity.title }}</strong>
            <time>{{ activity.time }}</time>
          </li>
        </ol>
      </aside>
    </div>
  </div>
</template>
