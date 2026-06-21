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
const accountStatus = computed(() => props.user ? '已登录' : '未登录')
const roleLabel = computed(() => {
  if (props.user?.is_admin || props.user?.role === 'admin') {
    return '管理员'
  }

  if (props.user?.role) {
    return props.user.role
  }

  return '创作者'
})
const accountRows = computed(() => [
  { label: '昵称', value: displayName.value },
  { label: '邮箱', value: displayEmail.value },
  { label: '身份', value: roleLabel.value },
  { label: '账号状态', value: accountStatus.value },
])
const preferenceRows = computed(() => [
  { label: '默认生成方式', value: props.stats.selectedTemplate || '影视剧剧本模板' },
  { label: '界面语言', value: '中文' },
])

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

        <section class="profile-section" aria-labelledby="profile-account-title">
          <h3 id="profile-account-title">基本资料</h3>
          <dl class="profile-info-grid">
            <div v-for="row in accountRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd>{{ row.value }}</dd>
            </div>
          </dl>
        </section>

        <section class="profile-section" aria-labelledby="profile-security-title">
          <h3 id="profile-security-title">账号安全</h3>
          <dl class="profile-info-grid">
            <div>
              <dt>登录方式</dt>
              <dd>邮箱和密码</dd>
            </div>
            <div>
              <dt>密码状态</dt>
              <dd>已加密保存</dd>
            </div>
          </dl>
        </section>

        <section class="profile-section" aria-labelledby="profile-preference-title">
          <h3 id="profile-preference-title">个人偏好</h3>
          <dl class="profile-info-grid">
            <div v-for="row in preferenceRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd>{{ row.value }}</dd>
            </div>
          </dl>
        </section>
      </div>

      <footer class="dialog-actions">
        <button class="editor-tool" type="button" @click="closeDialog">关闭</button>
        <button class="editor-tool is-primary" type="button" @click="logout">退出登录</button>
      </footer>
    </section>
  </div>
</template>
