<script setup>
defineProps({
  iconPaths: { type: Object, required: true },
  navItems: { type: Array, required: true },
})

defineEmits(['select', 'open-recycle-bin'])
</script>

<template>
  <aside class="sidebar" aria-label="主导航">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M5.25 14.75 4 20l5.25-1.25L18.6 9.4a4.15 4.15 0 0 0 1.15-3.65l-.25-1.25-1.25-.25A4.15 4.15 0 0 0 14.6 5.4z" />
          <path d="m13.75 6.25 4 4" />
          <path d="M7 17l-1.25 1.25" />
        </svg>
      </div>
      <div>
        <div class="brand-title">
          <span>AI小说转剧本</span>
        </div>
        <p>让创作，更简单</p>
      </div>
    </div>

    <nav class="primary-nav" aria-label="主菜单">
      <button
        v-for="item in navItems"
        :key="item.label"
        class="nav-item"
        :class="{ 'is-active': item.active }"
        type="button"
        :aria-current="item.active ? 'page' : undefined"
        @click="$emit('select', item.id)"
      >
        <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths[item.icon]" :key="path" :d="path" />
        </svg>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div class="sidebar-spacer" aria-hidden="true"></div>

    <section class="sidebar-panel project-panel" aria-label="项目管理">
      <button class="utility-row" type="button" @click="$emit('open-recycle-bin')">
        <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.trash" :key="path" :d="path" />
        </svg>
        <span>回收站</span>
      </button>
    </section>

  </aside>
</template>
