<script setup>
import { ref } from 'vue'

defineProps({
  description: { type: String, default: '从小说到剧本，只需几步' },
  iconPaths: { type: Object, required: true },
  title: { type: String, default: '小说转剧本工作台' },
})

const emit = defineEmits(['logout', 'open-profile'])
const isProfileMenuOpen = ref(false)

const toggleProfileMenu = () => {
  isProfileMenuOpen.value = !isProfileMenuOpen.value
}

const openProfile = () => {
  isProfileMenuOpen.value = false
  emit('open-profile')
}

const logout = () => {
  isProfileMenuOpen.value = false
  emit('logout')
}
</script>

<template>
  <header class="workspace-header">
    <div class="title-block">
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>
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

      <div class="profile-menu-wrap">
        <button
          class="profile-button"
          type="button"
          :aria-expanded="isProfileMenuOpen"
          aria-haspopup="menu"
          @click="toggleProfileMenu"
        >
          <span class="avatar" aria-hidden="true">创</span>
          <span>创作者</span>
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
          </svg>
        </button>

        <div v-if="isProfileMenuOpen" class="profile-menu" role="menu">
          <button type="button" role="menuitem" @click="openProfile">个人中心</button>
          <button type="button" role="menuitem" @click="logout">退出登录</button>
        </div>
      </div>
    </div>
  </header>
</template>
