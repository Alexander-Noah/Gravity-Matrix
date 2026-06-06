<script setup>
defineProps({
  analysisMetrics: { type: Array, required: true },
  iconPaths: { type: Object, required: true },
  insightItems: { type: Array, required: true },
  projectProgress: { type: Number, default: 0 },
  projectStages: { type: Array, required: true },
  projectTitle: { type: String, default: '未创建项目' },
})

defineEmits(['show-analysis'])
</script>

<template>
  <aside class="support-column" aria-label="项目与分析侧栏">
    <section class="workbench-side-panel progress-card" aria-labelledby="project-progress-title">
      <div class="side-panel-title">
        <div>
          <span>项目进度</span>
          <h2 id="project-progress-title">{{ projectTitle }}</h2>
        </div>
      </div>

      <div class="progress-readout">
        <div class="progress-track" role="progressbar" aria-label="项目完成进度" :aria-valuenow="projectProgress" aria-valuemin="0" aria-valuemax="100">
          <span :style="{ width: `${projectProgress}%` }"></span>
        </div>
        <strong>{{ projectProgress }}%</strong>
      </div>

      <ol class="stage-list">
        <li v-for="stage in projectStages" :key="stage.label" :class="`is-${stage.status}`">
          <span class="stage-marker">
            <svg v-if="stage.status === 'done'" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.check" :key="path" :d="path" />
            </svg>
          </span>
          <span>{{ stage.label }}</span>
          <strong>{{ stage.note || (stage.status === 'active' ? '进行中' : stage.status === 'done' ? '完成' : '待开始') }}</strong>
        </li>
      </ol>
    </section>

    <section class="workbench-side-panel analysis-card" aria-labelledby="analysis-title">
      <div class="side-panel-title">
        <div>
          <span>AI 解析结果</span>
          <h2 id="analysis-title">结构概览</h2>
        </div>
        <button class="side-link" type="button" @click="$emit('show-analysis')">详情</button>
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

      <dl class="insight-list">
        <div v-for="item in insightItems" :key="item.label || item.title">
          <dt>{{ item.label || item.title }}</dt>
          <dd>{{ item.value || item.description }}</dd>
        </div>
      </dl>
    </section>
  </aside>
</template>
