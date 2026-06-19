<script setup>
import { computed, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  iconPaths: { type: Object, required: true },
  modelValue: { type: Boolean, default: false },
  stats: { type: Object, default: () => ({}) },
  user: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits([
  'update:modelValue',
  'continue-edit',
  'open-library',
  'switch-template',
  'revalidate',
  'logout',
])

let previousBodyOverflow = ''
let isBodyScrollLocked = false

const unlockBackgroundScroll = () => {
  if (!isBodyScrollLocked) return
  document.body.style.overflow = previousBodyOverflow
  isBodyScrollLocked = false
  window.removeEventListener('keydown', handleKeydown)
}

const lockBackgroundScroll = () => {
  if (isBodyScrollLocked) return
  previousBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  isBodyScrollLocked = true
  window.addEventListener('keydown', handleKeydown)
}

function handleKeydown(event) {
  if (event.key === 'Escape') {
    closeDialog()
  }
}

const closeDialog = () => {
  emit('update:modelValue', false)
}

const logout = () => {
  emit('logout')
}

const displayName = computed(() => props.user?.name || props.user?.username || '创作者')
const displayEmail = computed(() => props.user?.email || '未绑定邮箱')
const avatarChar = computed(() => displayName.value.slice(0, 1) || '创')
const roleLabel = computed(() => {
  if (props.user?.is_admin || props.user?.role === 'admin') {
    return '管理员'
  }

  if (props.user?.role) {
    return props.user.role
  }

  return '创作者'
})
const profileCards = computed(() => props.stats.cards || [])
const hasCurrentProject = computed(() => Boolean(props.stats.hasCurrentProject))
const actionHint = computed(() => hasCurrentProject.value ? '' : '请先创建项目')

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      lockBackgroundScroll()
    } else {
      unlockBackgroundScroll()
    }
  },
  { immediate: true },
)

onBeforeUnmount(unlockBackgroundScroll)
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
        <div v-if="error" class="profile-error" role="alert">{{ error }}</div>
        <div v-if="loading" class="profile-loading">正在同步个人中心数据...</div>

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

        <section class="profile-quick-panel" aria-labelledby="profile-quick-title">
          <div class="profile-section-title">
            <h3 id="profile-quick-title">快捷操作</h3>
            <span v-if="actionHint">{{ actionHint }}</span>
          </div>
          <div class="profile-action-grid">
            <button class="editor-tool is-primary" type="button" :disabled="!hasCurrentProject"
              :title="actionHint" @click="emit('continue-edit')">
              继续编辑当前剧本
            </button>
            <button class="editor-tool" type="button" @click="emit('open-library')">打开剧本库</button>
            <button class="editor-tool" type="button" @click="emit('switch-template')">切换默认模板</button>
            <button class="editor-tool" type="button" :disabled="!hasCurrentProject"
              :title="actionHint" @click="emit('revalidate')">
              重新校验格式
            </button>
          </div>
        </section>

        <div class="profile-preference-panel">
          <div>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.spark" :key="path" :d="path" />
            </svg>
          </div>
          <p>{{ roleLabel }}正在使用「{{ stats.workspaceName || 'AI 小说转剧本' }}」。后续生成剧本时，会优先沿用当前默认生成方式、剧本草稿和最近项目上下文。</p>
        </div>
      </div>

      <footer class="dialog-actions">
        <button class="editor-tool" type="button" @click="closeDialog">关闭</button>
        <button class="editor-tool is-primary" type="button" @click="logout">退出登录</button>
      </footer>
    </section>
  </div>
</template>
