<script setup>
import { computed, ref } from 'vue'

defineProps({
  iconPaths: { type: Object, required: true },
})

const emit = defineEmits(['authenticated'])

const mode = ref('login')
const fullName = ref('')
const email = ref('')
const password = ref('')
const agreeTerms = ref(false)
const notice = ref('')

const isRegister = computed(() => mode.value === 'register')
const submitLabel = computed(() => (isRegister.value ? '创建账号' : '登录工作台'))
const helperText = computed(() =>
  isRegister.value ? '已有账号？返回登录' : '还没有账号？创建一个',
)

const switchMode = () => {
  mode.value = isRegister.value ? 'login' : 'register'
  notice.value = ''
}

const submitAuth = () => {
  if (isRegister.value && !fullName.value.trim()) {
    notice.value = '请输入创作者名称。'
    return
  }

  if (!email.value.trim() || !password.value.trim()) {
    notice.value = '请输入邮箱和密码。'
    return
  }

  if (isRegister.value && password.value.length < 6) {
    notice.value = '密码至少需要 6 位。'
    return
  }

  if (isRegister.value && !agreeTerms.value) {
    notice.value = '请先确认同意使用规范。'
    return
  }

  notice.value = isRegister.value ? '账号已创建，正在进入工作台。' : '登录成功，正在进入工作台。'
  emit('authenticated')
}
</script>

<template>
  <main class="auth-page" aria-labelledby="auth-title">
    <section class="auth-brand-panel" aria-label="产品说明">
      <div class="auth-brand-mark">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.edit" :key="path" :d="path" />
        </svg>
      </div>
      <div>
        <span>AI小说转剧本</span>
        <h1>把长篇小说整理成可编辑的剧本初稿。</h1>
        <p>登录后继续导入小说、查看 AI 解析结果、编辑 YAML 剧本并导出成常用格式。</p>
      </div>
      <ul class="auth-feature-list">
        <li>
          <strong>章节识别</strong>
          <span>校验 3 章以上文本并保留原文结构。</span>
        </li>
        <li>
          <strong>结构化生成</strong>
          <span>输出人物、场景、动作和对白 YAML。</span>
        </li>
        <li>
          <strong>编辑导出</strong>
          <span>在线校验 Schema，导出 YAML、TXT、Markdown、PDF。</span>
        </li>
      </ul>
    </section>

    <section class="auth-form-panel" aria-label="登录注册表单">
      <div class="auth-form-header">
        <span>{{ isRegister ? '创建创作者账号' : '欢迎回来' }}</span>
        <h2 id="auth-title">{{ isRegister ? '注册账号' : '登录账号' }}</h2>
        <p>{{ isRegister ? '保存项目、模板选择和剧本版本。' : '进入你的小说改编工作台。' }}</p>
      </div>

      <div class="auth-tabs" role="tablist" aria-label="账号操作">
        <button :class="{ 'is-active': !isRegister }" type="button" role="tab" @click="mode = 'login'">登录</button>
        <button :class="{ 'is-active': isRegister }" type="button" role="tab" @click="mode = 'register'">注册</button>
      </div>

      <form class="auth-form" @submit.prevent="submitAuth">
        <label v-if="isRegister" class="auth-field">
          <span>创作者名称</span>
          <input v-model="fullName" autocomplete="name" type="text" placeholder="例如：林默" />
        </label>

        <label class="auth-field">
          <span>邮箱</span>
          <input v-model="email" autocomplete="email" type="email" placeholder="creator@example.com" />
        </label>

        <label class="auth-field">
          <span>密码</span>
          <input v-model="password" :autocomplete="isRegister ? 'new-password' : 'current-password'" type="password" placeholder="至少 6 位" />
        </label>

        <label v-if="isRegister" class="auth-check">
          <input v-model="agreeTerms" type="checkbox" />
          <span>我确认仅上传本人有权处理的小说内容。</span>
        </label>

        <p v-if="notice" class="auth-notice">{{ notice }}</p>

        <button class="auth-submit" type="submit">{{ submitLabel }}</button>
      </form>

      <button class="auth-switch" type="button" @click="switchMode">{{ helperText }}</button>
    </section>
  </main>
</template>
