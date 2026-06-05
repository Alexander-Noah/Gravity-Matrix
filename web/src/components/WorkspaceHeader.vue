<script setup>
defineProps({
  iconPaths: { type: Object, required: true },
})
</script>

<template>
  <header class="workspace-header">
    <div class="title-block">
      <h1>小说转剧本工作台</h1>
      <p>从小说到剧本，只需几步</p>
    </div>

    <div class="top-actions" aria-label="快捷操作">
      <button class="guide-button" type="button">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.shield" :key="path" :d="path" />
        </svg>
        <span>使用指南</span>
      </button>
      <button class="notification-button" type="button" aria-label="查看通知">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.bell" :key="path" :d="path" />
        </svg>
        <span aria-hidden="true"></span>
      </button>
      <button class="profile-button" type="button">
        <span class="avatar" aria-hidden="true">创</span>
        <span>创作者</span>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
        </svg>
      </button>
    </div>
  </header>
</template>
