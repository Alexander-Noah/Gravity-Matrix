<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  description: { type: String, default: '从小说到剧本，只需几步' },
  iconPaths: { type: Object, required: true },
  title: { type: String, default: '小说转剧本工作台' },
})

const emit = defineEmits(['logout', 'open-guide', 'open-profile'])
const isProfileMenuOpen = ref(false)
const profileMenuRef = ref(null)
const showWorkflowBadge = computed(() => props.title.includes('工作台'))

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

const closeProfileMenuOnOutsideClick = (event) => {
  if (!profileMenuRef.value?.contains(event.target)) {
    isProfileMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeProfileMenuOnOutsideClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeProfileMenuOnOutsideClick)
})
</script>

<template>
  <header class="workspace-header">
    <div class="title-block">
      <div class="title-line">
        <h1>{{ title }}</h1>
        <span v-if="showWorkflowBadge" class="header-badge">改编流程</span>
      </div>
      <p>{{ description }}</p>
    </div>

    <div class="top-actions" aria-label="快捷操作">
      <button class="guide-button" type="button" @click="emit('open-guide')">
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

      <div ref="profileMenuRef" class="profile-menu-wrap">
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
