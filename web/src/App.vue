<script setup>
const navItems = [
  { label: '工作台', icon: 'home', active: true },
  { label: '我的项目', icon: 'folder', active: false },
  { label: '模板中心', icon: 'grid', active: false },
  { label: '剧本库', icon: 'book', active: false },
  { label: '帮助文档', icon: 'help', active: false },
]

const quickActions = [
  { label: '编辑剧本章节', time: '2 分钟前' },
  { label: '生成剧本（YAML）', time: '5 分钟前' },
  { label: '导入小说《星辰之下》', time: '1 小时前' },
]

const workflowSteps = [
  { number: '1', title: '导入小说', description: '上传或粘贴小说内容', status: 'done' },
  { number: '2', title: 'AI 解析', description: '智能识别人物、场景与剧情', status: 'done' },
  { number: '3', title: '生成剧本', description: '一键生成结构化剧本', status: 'current' },
  { number: '4', title: '编辑与导出', description: '在线编辑并导出剧本', status: 'upcoming' },
]

const iconPaths = {
  home: ['M3.5 10.5 12 3.75l8.5 6.75', 'M5.75 9.5v9.25h12.5V9.5', 'M9.5 18.75v-5h5v5'],
  folder: ['M3.75 6.5h6l1.6 2h8.9v9.75H3.75z', 'M3.75 8.5h16.5'],
  grid: ['M4.25 4.25h6v6h-6z', 'M13.75 4.25h6v6h-6z', 'M4.25 13.75h6v6h-6z', 'M13.75 13.75h6v6h-6z'],
  book: ['M5 4.75h6.25c1.1 0 2 .9 2 2v12.5c0-.8-.65-1.45-1.45-1.45H5z', 'M13.25 6.75c0-1.1.9-2 2-2H19v13.05h-3.75c-1.1 0-2 .9-2 2z'],
  help: ['M12 20.25a8.25 8.25 0 1 0 0-16.5 8.25 8.25 0 0 0 0 16.5z', 'M9.85 9.25A2.3 2.3 0 0 1 12.2 7.5c1.35 0 2.35.82 2.35 2.05 0 1.02-.56 1.55-1.45 2.08-.78.46-1.1.95-1.1 1.72', 'M12 16.35h.01'],
  eye: ['M3.75 12s2.7-4.5 8.25-4.5 8.25 4.5 8.25 4.5-2.7 4.5-8.25 4.5S3.75 12 3.75 12z', 'M12 14.25a2.25 2.25 0 1 0 0-4.5 2.25 2.25 0 0 0 0 4.5z'],
  trash: ['M5.5 7.25h13', 'M9.25 7.25v-2h5.5v2', 'M7.25 7.25l.75 12h8l.75-12', 'M10.25 10.75v5.25', 'M13.75 10.75v5.25'],
  edit: ['M5.25 17.75l.7-3.45 8.45-8.45 2.75 2.75-8.45 8.45z', 'M13.2 7.05l2.75 2.75', 'M5.25 17.75h12.5'],
  shield: ['M12 3.75 18.75 6v5.1c0 4.05-2.7 7.35-6.75 9.15-4.05-1.8-6.75-5.1-6.75-9.15V6z', 'M9.75 11.75 11.3 13.3l3.2-3.6'],
  bell: ['M17.25 10.5a5.25 5.25 0 0 0-10.5 0c0 4-1.75 4.75-1.75 4.75h14s-1.75-.75-1.75-4.75z', 'M10 18.25a2.25 2.25 0 0 0 4 0'],
  check: ['M5.75 12.25 10 16.5 18.25 7.5'],
  chevron: ['M8.75 5.75 15 12l-6.25 6.25'],
  arrow: ['M9 5.75 15.25 12 9 18.25'],
}
</script>

<template>
  <div class="app-shell">
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
            <span class="plan-badge">Pro</span>
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

    <main class="workspace" aria-label="工作区">
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

      <section class="workflow-stepper" aria-label="小说转剧本流程">
        <ol>
          <li
            v-for="(step, index) in workflowSteps"
            :key="step.title"
            class="workflow-step"
            :class="`is-${step.status}`"
            :aria-current="step.status === 'current' ? 'step' : undefined"
          >
            <span class="step-marker">
              <svg v-if="step.status === 'done'" viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconPaths.check" :key="path" :d="path" />
              </svg>
              <span v-else>{{ step.number }}</span>
            </span>
            <span class="step-copy">
              <strong>{{ step.number }} {{ step.title }}</strong>
              <span>{{ step.description }}</span>
            </span>
            <svg v-if="index < workflowSteps.length - 1" class="step-arrow" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
            </svg>
          </li>
        </ol>
      </section>

      <div class="skeleton-grid" aria-hidden="true">
        <span></span>
        <span></span>
      </div>
    </main>
  </div>
</template>
