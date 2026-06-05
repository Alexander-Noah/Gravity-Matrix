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

const projectStages = [
  { label: '小说导入', status: 'done', note: '' },
  { label: 'AI内容解析', status: 'done', note: '' },
  { label: '生成剧本', status: 'active', note: '进行中' },
  { label: '编辑与导出', status: 'pending', note: '待开始' },
]

const analysisMetrics = [
  { label: '人物', value: '12', icon: 'users', tone: 'violet' },
  { label: '场景', value: '28', icon: 'scene', tone: 'blue' },
  { label: '章节', value: '5', icon: 'chapter', tone: 'mint' },
  { label: '冲突事件', value: '16', icon: 'conflict', tone: 'orange' },
]

const insightItems = [
  { label: '故事类型', value: '现代 / 都市 / 成长' },
  { label: '核心主题', value: '梦想、友情、成长' },
  { label: '故事基调', value: '积极 / 温暖' },
  { label: '建议剧本类型', value: '电视剧（30 集）' },
]

const scriptChapters = [
  {
    title: '第 1 章 初入城市',
    open: true,
    scenes: [
      { label: '场景 1-1 地铁站相遇', active: true },
      { label: '场景 1-2 出租屋', active: false },
      { label: '场景 1-3 公司面试', active: false },
    ],
  },
  { title: '第 2 章 梦想启航', open: false, scenes: [] },
  { title: '第 3 章 现实的挑战', open: false, scenes: [] },
  { title: '第 4 章 友情的考验', open: false, scenes: [] },
  { title: '第 5 章 破茧成蝶', open: false, scenes: [] },
]

const yamlLines = [
  [{ text: 'script:', tone: 'key' }],
  [{ text: 'title:', tone: 'key' }, { text: ' "星辰之下"', tone: 'string' }],
  [{ text: 'original_novel:', tone: 'key' }, { text: ' "星辰之下"', tone: 'string' }],
  [{ text: 'author:', tone: 'key' }, { text: ' "AI Script Studio"', tone: 'string' }],
  [{ text: 'version:', tone: 'key' }, { text: ' "1.0"', tone: 'string' }],
  [{ text: 'format:', tone: 'key' }, { text: ' "电视剧"', tone: 'string' }],
  [{ text: 'total_chapters:', tone: 'key' }, { text: ' 5', tone: 'number' }],
  [],
  [{ text: 'characters:', tone: 'key' }],
  [{ text: '  - id:', tone: 'key' }, { text: ' char_001', tone: 'value' }],
  [{ text: '    name:', tone: 'key' }, { text: ' 林晓', tone: 'string' }],
  [{ text: '    role:', tone: 'key' }, { text: ' 主角', tone: 'value' }],
  [{ text: '    gender:', tone: 'key' }, { text: ' 女', tone: 'value' }],
  [{ text: '    age:', tone: 'key' }, { text: ' 24', tone: 'number' }],
  [{ text: '    description:', tone: 'key' }, { text: ' 怀揣音乐梦想的年轻人', tone: 'string' }],
  [],
  [{ text: 'chapters:', tone: 'key' }],
  [{ text: '  - id:', tone: 'key' }, { text: ' ch_001', tone: 'value' }],
  [{ text: '    title:', tone: 'key' }, { text: ' 初入城市', tone: 'string' }],
  [{ text: '    summary:', tone: 'key' }, { text: ' 林晓来到大城市，开始新的生活与挑战', tone: 'string' }],
  [{ text: '    scenes:', tone: 'key' }],
  [{ text: '      - id:', tone: 'key' }, { text: ' sc_001_001', tone: 'value' }],
  [{ text: '        title:', tone: 'key' }, { text: ' 地铁站相遇', tone: 'string' }],
  [{ text: '        location:', tone: 'key' }, { text: ' 地铁站', tone: 'value' }],
  [{ text: '        time:', tone: 'key' }, { text: ' 傍晚', tone: 'value' }],
  [{ text: '        characters:', tone: 'key' }],
  [{ text: '          - char_001', tone: 'value' }],
  [{ text: '          - char_002', tone: 'value' }],
]

const previewDialogues = [
  {
    speaker: '林晓',
    note: '（自言自语）',
    line: '这座城市，真的能实现我的梦想吗？',
  },
  {
    speaker: '苏晴',
    note: '（微笑）',
    line: '需要帮助吗？看起来你有点迷路了。',
  },
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
  spark: ['M12 3.75 13.3 8.7 18.25 10 13.3 11.3 12 16.25 10.7 11.3 5.75 10 10.7 8.7z', 'M18.25 15.25 18.85 17.15 20.75 17.75 18.85 18.35 18.25 20.25 17.65 18.35 15.75 17.75 17.65 17.15z'],
  users: ['M9.25 11.25a3 3 0 1 0 0-6 3 3 0 0 0 0 6z', 'M4.5 19.25c.65-3.05 2.25-4.75 4.75-4.75s4.1 1.7 4.75 4.75', 'M16.2 10.75a2.35 2.35 0 1 0 0-4.7', 'M14.9 14.35c2 .25 3.35 1.9 3.85 4.9'],
  scene: ['M4.25 17.75V6.25h15.5v11.5z', 'm7 14 3.25-3.5 2.2 2.35 1.55-1.65 2.75 2.8', 'M8.25 9.25h.01'],
  chapter: ['M6 4.75h9.75L18 7v12.25H6z', 'M15.75 4.75V7H18', 'M8.75 10.25h6.5', 'M8.75 13.25h6.5', 'M8.75 16.25h4.25'],
  conflict: ['M12 4.5 20.25 18.75H3.75z', 'M12 9v3.75', 'M12 15.75h.01'],
  format: ['M5.25 6.75h13.5', 'M5.25 11.25h8.5', 'M5.25 15.75h13.5', 'M16 9.5l2.75 2.75L16 15'],
  copy: ['M8 8h10.25v10.25H8z', 'M5.75 15.75h-1.5v-12h12v1.5'],
  download: ['M12 4.75v9', 'M8.25 10.25 12 14l3.75-3.75', 'M5 18.75h14'],
  plus: ['M12 5.75v12.5', 'M5.75 12h12.5'],
  more: ['M7.25 12h.01', 'M12 12h.01', 'M16.75 12h.01'],
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

      <div class="content-grid">
        <div class="support-column">
          <section class="work-card progress-card" aria-labelledby="project-progress-title">
            <div class="work-card-header">
              <div class="card-title">
                <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="path in iconPaths.folder" :key="path" :d="path" />
                </svg>
                <h2 id="project-progress-title">项目进度</h2>
              </div>
              <button class="card-link" type="button">
                <span>查看全部</span>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
                </svg>
              </button>
            </div>

            <div class="project-summary">
              <div>
                <h3>《星辰之下》改编项目</h3>
                <button class="title-edit" type="button" aria-label="编辑项目名称">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.edit" :key="path" :d="path" />
                  </svg>
                </button>
              </div>
              <div class="progress-meter">
                <div class="progress-track" role="progressbar" aria-label="项目完成进度" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100">
                  <span></span>
                </div>
                <strong>75%</strong>
              </div>
            </div>

            <ul class="stage-list">
              <li v-for="stage in projectStages" :key="stage.label" :class="`is-${stage.status}`">
                <span class="stage-marker">
                  <svg v-if="stage.status === 'done'" viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.check" :key="path" :d="path" />
                  </svg>
                </span>
                <span>{{ stage.label }}</span>
                <strong v-if="stage.note">{{ stage.note }}</strong>
              </li>
            </ul>
          </section>

          <section class="work-card analysis-card" aria-labelledby="analysis-title">
            <div class="work-card-header">
              <div class="card-title">
                <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="path in iconPaths.spark" :key="path" :d="path" />
                </svg>
                <h2 id="analysis-title">AI 解析结果概览</h2>
              </div>
              <button class="card-link" type="button">
                <span>查看详情</span>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
                </svg>
              </button>
            </div>

            <div class="metric-grid">
              <article v-for="metric in analysisMetrics" :key="metric.label" class="metric-tile" :class="`tone-${metric.tone}`">
                <span class="metric-icon">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths[metric.icon]" :key="path" :d="path" />
                  </svg>
                </span>
                <span>{{ metric.label }}</span>
                <strong>{{ metric.value }}</strong>
              </article>
            </div>

            <div class="insight-block">
              <h3>智能分析</h3>
              <dl>
                <div v-for="item in insightItems" :key="item.label">
                  <dt>{{ item.label }}：</dt>
                  <dd>{{ item.value }}</dd>
                </div>
              </dl>
            </div>
          </section>
        </div>

        <div class="main-column">
          <section class="script-panel" aria-labelledby="script-title">
            <div class="script-panel-header">
              <div>
                <h2 id="script-title">生成的剧本（YAML）</h2>
                <span>自动保存中...</span>
              </div>
              <div class="editor-actions" aria-label="剧本操作">
                <button class="editor-tool" type="button">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.format" :key="path" :d="path" />
                  </svg>
                  <span>格式说明</span>
                </button>
                <button class="editor-tool is-safe" type="button">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.shield" :key="path" :d="path" />
                  </svg>
                  <span>校验</span>
                </button>
                <button class="editor-tool" type="button">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.copy" :key="path" :d="path" />
                  </svg>
                  <span>复制</span>
                </button>
                <button class="editor-tool is-primary" type="button">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.download" :key="path" :d="path" />
                  </svg>
                  <span>导出</span>
                  <svg class="button-chevron" viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
                  </svg>
                </button>
              </div>
            </div>

            <div class="script-editor-layout">
              <aside class="structure-pane" aria-label="剧本结构">
                <div class="structure-heading">
                  <h3>剧本结构</h3>
                  <button class="icon-button" type="button" aria-label="更多结构操作">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path v-for="path in iconPaths.more" :key="path" :d="path" />
                    </svg>
                  </button>
                </div>

                <ul class="chapter-tree">
                  <li v-for="chapter in scriptChapters" :key="chapter.title" :class="{ 'is-open': chapter.open }">
                    <button class="chapter-row" type="button">
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
                      </svg>
                      <span>{{ chapter.title }}</span>
                    </button>
                    <ul v-if="chapter.scenes.length" class="scene-list">
                      <li v-for="scene in chapter.scenes" :key="scene.label">
                        <button class="scene-row" :class="{ 'is-active': scene.active }" type="button">
                          {{ scene.label }}
                        </button>
                      </li>
                    </ul>
                  </li>
                </ul>

                <button class="add-scene-button" type="button">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.plus" :key="path" :d="path" />
                  </svg>
                  <span>添加场景</span>
                </button>
              </aside>

              <div class="code-pane" aria-label="YAML 剧本文档">
                <button class="code-more" type="button" aria-label="更多编辑器操作">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconPaths.more" :key="path" :d="path" />
                  </svg>
                </button>
                <pre><code><span v-for="(line, index) in yamlLines" :key="index" class="code-line"><span class="line-number">{{ index + 1 }}</span><span class="line-content"><template v-for="(token, tokenIndex) in line" :key="`${index}-${tokenIndex}`"><span :class="`yaml-${token.tone}`">{{ token.text }}</span></template></span></span></code></pre>
              </div>
            </div>
          </section>

          <section class="preview-panel" aria-labelledby="preview-title">
            <div class="preview-header">
              <h2 id="preview-title">剧本预览</h2>
              <button class="preview-toggle" type="button">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="path in iconPaths.format" :key="path" :d="path" />
                </svg>
                <span>切换视图</span>
              </button>
            </div>

            <div class="preview-body">
              <article class="scene-preview">
                <div class="scene-meta">
                  <h3>场景 1-1 地铁站相遇</h3>
                  <p>内景 / 地铁站 / 傍晚</p>
                </div>
                <p class="scene-action">人头攒动的地铁站，广播声回荡。林晓背着吉他包，低头看着手机，神情略显迷茫。</p>
              </article>

              <div class="dialogue-preview">
                <article v-for="dialogue in previewDialogues" :key="dialogue.speaker" class="dialogue-line">
                  <h3>{{ dialogue.speaker }}</h3>
                  <span>{{ dialogue.note }}</span>
                  <p>{{ dialogue.line }}</p>
                </article>
              </div>

              <div class="subway-visual" aria-label="地铁站场景示意图" role="img">
                <span class="station-light"></span>
                <span class="train-body"></span>
                <span class="train-window window-one"></span>
                <span class="train-window window-two"></span>
                <span class="platform-line"></span>
                <span class="commuter commuter-one"></span>
                <span class="commuter commuter-two"></span>
                <span class="commuter commuter-three"></span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>
