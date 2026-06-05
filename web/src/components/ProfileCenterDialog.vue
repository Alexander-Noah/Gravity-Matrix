<script setup>
defineProps({
  iconPaths: { type: Object, required: true },
  modelValue: { type: Boolean, default: false },
  user: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue', 'logout'])

const closeDialog = () => {
  emit('update:modelValue', false)
}

const logout = () => {
  emit('logout')
}
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
          <div class="profile-avatar" aria-hidden="true">{{ user?.name?.slice(0, 1) || '创' }}</div>
          <div>
            <strong>{{ user?.name || '创作者' }}</strong>
            <span>{{ user?.email || '尚未同步邮箱' }}</span>
          </div>
        </div>

        <dl class="profile-info-grid">
          <div>
            <dt>账号状态</dt>
            <dd>已登录</dd>
          </div>
          <div>
            <dt>创作身份</dt>
            <dd>{{ user?.role || '小说作者' }}</dd>
          </div>
          <div>
            <dt>默认工作区</dt>
            <dd>AI 小说转剧本</dd>
          </div>
          <div>
            <dt>内容授权</dt>
            <dd>本人有权处理</dd>
          </div>
        </dl>

        <div class="profile-preference-panel">
          <div>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.spark" :key="path" :d="path" />
            </svg>
          </div>
          <p>后续生成剧本时，将优先保留你的模板选择、剧本编辑状态和最近导出记录。</p>
        </div>
      </div>

      <footer class="dialog-actions">
        <button class="editor-tool" type="button" @click="closeDialog">关闭</button>
        <button class="editor-tool is-primary" type="button" @click="logout">退出登录</button>
      </footer>
    </section>
  </div>
</template>
