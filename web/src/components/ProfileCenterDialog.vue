<script setup>
import { computed } from 'vue'

const props = defineProps({
  iconPaths: { type: Object, required: true },
  modelValue: { type: Boolean, default: false },
  stats: { type: Object, default: () => ({}) },
  user: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue', 'logout'])

const closeDialog = () => {
  emit('update:modelValue', false)
}

const logout = () => {
  emit('logout')
}

const displayName = computed(() => props.user?.name || props.user?.username || '创作者')
const displayEmail = computed(() => props.user?.email || '未绑定邮箱')
const avatarChar = computed(() => displayName.value.slice(0, 1).toLowerCase())
const roleLabel = computed(() => {
  if (props.user?.is_admin || props.user?.role === 'admin') {
    return '管理员'
  }

  if (props.user?.role) {
    return props.user.role
  }

  return '创作者'
})
const profileCards = computed(() => [
  { label: '账号状态', value: props.user ? '已登录' : '未登录' },
  { label: '当前项目', value: props.stats.currentProject || '未创建项目' },
  { label: '工作阶段', value: props.stats.workflowStep || '等待开始' },
  { label: '项目进度', value: `${props.stats.projectProgress ?? 0}%` },
  { label: '默认模板', value: props.stats.selectedTemplate || '未选择模板' },
  { label: '剧本状态', value: props.stats.scriptStatus || '尚未生成剧本' },
  { label: '剧本库条目', value: `${props.stats.libraryCount ?? 0} 个` },
  { label: 'Schema 状态', value: props.stats.schemaStatus || '待校验' },
])
</script>

<template>
  <div v-if="modelValue" class="dialog-backdrop" role="presentation" @click.self="closeDialog">
    <section class="profile-dialog" role="dialog" aria-modal="true" aria-labelledby="profile-dialog-title">
      <header class="dialog-header">
        <div>
          <span>账号信息</span>
          <h2 id="profile-dialog-title">个人中心</h2>
        </div>
        <button class="dialog-close" type="button" aria-label="关闭个人中心" @click="closeDialog">×</button>
      </header>

      <div class="profile-dialog-body">
        <div class="profile-identity">
          <div class="profile-avatar" aria-hidden="true">{{ avatarChar }}</div>
          <div>
            <strong>{{ displayName }}</strong>
            <span>{{ displayEmail }}</span>
          </div>
        </div>

        <dl class="profile-info-grid">
          <div v-for="card in profileCards" :key="card.label">
            <dt>{{ card.label }}</dt>
            <dd>{{ card.value }}</dd>
          </div>
        </dl>

        <div class="profile-preference-panel">
          <div>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.spark" :key="path" :d="path" />
            </svg>
          </div>
          <p>{{ roleLabel }}正在使用「{{ stats.workspaceName || 'AI 小说转剧本' }}」。后续生成剧本时，会优先保留当前模板、YAML 编辑状态和最近项目上下文。</p>
        </div>
      </div>

      <footer class="dialog-actions">
        <button class="editor-tool" type="button" @click="closeDialog">关闭</button>
        <button class="editor-tool is-primary" type="button" @click="logout">退出登录</button>
      </footer>
    </section>
  </div>
</template>
