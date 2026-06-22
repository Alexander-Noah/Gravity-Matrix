<script setup>
import { computed, onBeforeUnmount, reactive, watch } from 'vue'

const props = defineProps({
  iconPaths: { type: Object, required: true },
  modelValue: { type: Boolean, default: false },
  stats: { type: Object, default: () => ({}) },
  user: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  llmConfig: { type: Object, default: null },
  llmSaving: { type: Boolean, default: false },
  llmTesting: { type: Boolean, default: false },
  llmTestResult: { type: Object, default: null },
})

const emit = defineEmits([
  'update:modelValue',
  'logout',
  'save-llm-config',
  'test-llm',
])

const llmForm = reactive({
  provider: 'openai_compatible',
  base_url: '',
  model: '',
  api_key: '',
  testPrompt: '请用一句话回复：大模型配置已连通。',
})

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
const llmStatus = computed(() => props.llmConfig?.configured ? '已配置' : '未配置')
const llmKeyStatus = computed(() => props.llmConfig?.has_api_key ? '已保存' : '未保存')
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
  { label: '大模型配置', value: llmStatus.value },
])
const canSaveLlm = computed(() => llmForm.base_url.trim() && llmForm.model.trim())
const providerOptions = [
  { label: 'OpenAI 兼容接口', value: 'openai_compatible' },
  { label: '本地 Ollama', value: 'ollama' },
]

const applyLlmConfig = (config) => {
  llmForm.provider = config?.provider || 'openai_compatible'
  llmForm.base_url = config?.base_url || ''
  llmForm.model = config?.model || ''
  llmForm.api_key = ''
}

const saveLlmConfig = () => {
  emit('save-llm-config', {
    provider: llmForm.provider,
    base_url: llmForm.base_url.trim(),
    model: llmForm.model.trim(),
    api_key: llmForm.api_key.trim(),
  })
}

const testLlm = () => {
  emit('test-llm', llmForm.testPrompt.trim() || '请用一句话回复：大模型配置已连通。')
}

watch(
  () => props.llmConfig,
  (config) => {
    applyLlmConfig(config)
  },
  { immediate: true },
)

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

        <section class="profile-section" aria-labelledby="profile-llm-title">
          <div class="profile-section-title">
            <h3 id="profile-llm-title">AI 大模型 API</h3>
            <span>{{ llmStatus }}</span>
          </div>
          <div class="profile-llm-form">
            <label class="profile-field">
              <span>接口类型</span>
              <select v-model="llmForm.provider">
                <option v-for="option in providerOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
            <label class="profile-field">
              <span>Base URL</span>
              <input v-model="llmForm.base_url" type="url" placeholder="例如：https://api.deepseek.com/v1" />
            </label>
            <label class="profile-field">
              <span>模型名称</span>
              <input v-model="llmForm.model" type="text" placeholder="例如：deepseek-chat" />
            </label>
            <label class="profile-field">
              <span>API Key · {{ llmKeyStatus }}</span>
              <input v-model="llmForm.api_key" type="password" autocomplete="off" placeholder="留空则保留已保存的 Key" />
            </label>
            <label class="profile-field is-wide">
              <span>测试提示词</span>
              <textarea v-model="llmForm.testPrompt" rows="2"></textarea>
            </label>
          </div>
          <div v-if="llmTestResult" class="profile-llm-result" role="status">
            <strong>{{ llmTestResult.model }} 连接成功</strong>
            <p>{{ llmTestResult.content }}</p>
          </div>
          <div class="profile-inline-actions">
            <button class="editor-tool" type="button" :disabled="llmTesting || !canSaveLlm" @click="testLlm">
              {{ llmTesting ? '测试中...' : '测试连接' }}
            </button>
            <button class="editor-tool is-primary" type="button" :disabled="llmSaving || !canSaveLlm" @click="saveLlmConfig">
              {{ llmSaving ? '保存中...' : '保存配置' }}
            </button>
          </div>
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
