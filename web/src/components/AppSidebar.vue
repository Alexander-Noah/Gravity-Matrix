<script setup>
defineProps({
  iconPaths: { type: Object, required: true },
  navItems: { type: Array, required: true },
  quickActions: { type: Array, required: true },
})
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
      >
        <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths[item.icon]" :key="path" :d="path" />
        </svg>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div class="sidebar-spacer" aria-hidden="true"></div>

    <section class="sidebar-panel project-panel" aria-labelledby="current-project-title">
      <div class="panel-heading">
        <h2 id="current-project-title">当前项目</h2>
        <button class="icon-button" type="button" aria-label="查看当前项目">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.eye" :key="path" :d="path" />
          </svg>
        </button>
      </div>

      <div class="project-row">
        <svg class="item-icon project-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.folder" :key="path" :d="path" />
        </svg>
        <div>
          <strong>《星辰之下》改编项目</strong>
          <span>已保存 2 分钟前</span>
        </div>
      </div>

      <button class="utility-row" type="button">
        <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.trash" :key="path" :d="path" />
        </svg>
        <span>回收站</span>
      </button>
    </section>

    <section class="sidebar-panel actions-panel" aria-labelledby="quick-actions-title">
      <h2 id="quick-actions-title">智能操作</h2>
      <ul class="action-list">
        <li v-for="action in quickActions" :key="action.label">
          <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.edit" :key="path" :d="path" />
          </svg>
          <span>{{ action.label }}</span>
          <time>{{ action.time }}</time>
        </li>
      </ul>
      <button class="link-button" type="button">
        <span>查看全部记录</span>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
        </svg>
      </button>
    </section>
  </aside>
</template>
