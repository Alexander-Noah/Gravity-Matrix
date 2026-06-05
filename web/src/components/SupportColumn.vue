<script setup>
defineProps({
  analysisMetrics: { type: Array, required: true },
  iconPaths: { type: Object, required: true },
  insightItems: { type: Array, required: true },
  projectStages: { type: Array, required: true },
})
</script>

<template>
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
</template>
