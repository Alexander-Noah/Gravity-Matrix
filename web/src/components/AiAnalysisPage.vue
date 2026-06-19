<script setup>
import { computed } from 'vue'

const props = defineProps({
  analysisCharacters: { type: Array, required: true },
  analysisMetrics: { type: Array, required: true },
  analysisScenes: { type: Array, required: true },
  characterRelations: { type: Array, required: true },
  dialogueExtracts: { type: Array, required: true },
  iconPaths: { type: Object, required: true },
  isParsing: { type: Boolean, default: false },
  notice: { type: String, default: '' },
  plotEvents: { type: Array, required: true },
  progress: { type: Number, required: true },
})

defineEmits(['next', 'previous', 'rerun'])

const displayProgress = computed(() => Math.min(100, Math.max(0, Math.round(props.progress || 0))))
const isComplete = computed(() => displayProgress.value >= 100)
const noticeType = computed(() => (/失败|错误|异常/.test(props.notice) ? 'error' : 'info'))
</script>

<template>
  <div class="analysis-workspace">
    <section class="work-card analysis-progress-card" aria-labelledby="analysis-progress-title">
      <div>
        <span class="analysis-eyebrow">本地整理 + AI 解析进度</span>
        <h2 id="analysis-progress-title">{{ isComplete ? '内容结构识别已完成' : '正在识别内容结构' }}</h2>
        <p>{{ isComplete ? '已结合本地章节整理和 AI 解析提取人物、场景、剧情事件、人物关系和对白候选。' : '请等待后端任务完成，完成后再进入剧本生成。' }}</p>
      </div>
      <div class="analysis-progress-side">
        <div class="analysis-progress-meter">
          <el-progress :percentage="displayProgress" :stroke-width="8" />
        </div>
        <div class="analysis-primary-actions" aria-label="解析主操作">
          <el-button class="editor-tool" native-type="button" :disabled="isParsing" @click="$emit('previous')">
            <svg class="reverse-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
            </svg>
            <span>返回导入</span>
          </el-button>
          <el-button class="editor-tool" native-type="button" :loading="isParsing" :disabled="isParsing" @click="$emit('rerun')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.refresh" :key="path" :d="path" />
            </svg>
            <span>重新解析</span>
          </el-button>
          <el-button class="editor-tool is-primary" native-type="button" :disabled="!isComplete || isParsing" @click="$emit('next')">
            <span>生成剧本</span>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
            </svg>
          </el-button>
        </div>
      </div>
    </section>

    <section class="analysis-metrics-row" aria-label="解析指标">
      <article v-for="metric in analysisMetrics" :key="metric.label" class="metric-tile" :class="`tone-${metric.tone}`">
        <span class="metric-icon">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths[metric.icon]" :key="path" :d="path" />
          </svg>
        </span>
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
      </article>
    </section>

    <div class="analysis-grid">
      <section class="work-card analysis-section" aria-labelledby="characters-title">
        <div class="work-card-header">
          <div class="card-title">
            <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.users" :key="path" :d="path" />
            </svg>
            <h2 id="characters-title">人物列表</h2>
          </div>
        </div>
        <div class="entity-list">
          <article v-for="character in analysisCharacters" :key="character.name">
            <strong>{{ character.name }}</strong>
            <span>{{ character.role }} · {{ character.age }}</span>
            <p>{{ character.trait }}</p>
          </article>
        </div>
      </section>

      <section class="work-card analysis-section" aria-labelledby="scenes-title">
        <div class="work-card-header">
          <div class="card-title">
            <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.scene" :key="path" :d="path" />
            </svg>
            <h2 id="scenes-title">场景列表</h2>
          </div>
        </div>
        <div class="scene-chip-list">
          <article v-for="scene in analysisScenes" :key="scene.title">
            <strong>{{ scene.title }}</strong>
            <span>{{ scene.chapter }} / {{ scene.time }}</span>
            <p>{{ scene.mood }}</p>
          </article>
        </div>
      </section>

      <section class="work-card analysis-section timeline-section" aria-labelledby="events-title">
        <div class="work-card-header">
          <div class="card-title">
            <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.conflict" :key="path" :d="path" />
            </svg>
            <h2 id="events-title">剧情事件</h2>
          </div>
        </div>
        <ol class="event-timeline">
          <li v-for="event in plotEvents" :key="event.step">
            <span>{{ event.step }}</span>
            <div>
              <strong>{{ event.title }}</strong>
              <small>{{ event.chapter }}</small>
              <p>{{ event.detail }}</p>
            </div>
          </li>
        </ol>
      </section>

      <section class="work-card analysis-section" aria-labelledby="relations-title">
        <div class="work-card-header">
          <div class="card-title">
            <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.link" :key="path" :d="path" />
            </svg>
            <h2 id="relations-title">人物关系</h2>
          </div>
        </div>
        <div v-if="characterRelations.length" class="relation-list">
          <article v-for="relation in characterRelations" :key="`${relation.source}-${relation.target}`">
            <strong>{{ relation.source }} · {{ relation.target }}</strong>
            <span>{{ relation.relation }}</span>
            <p>{{ relation.note }}</p>
          </article>
        </div>
        <el-empty v-else description="暂无可展示的人物关系，请重新解析或补充更多小说正文。" />
      </section>
    </div>

    <section class="work-card analysis-section dialogue-extract-section" aria-labelledby="dialogue-title">
      <div class="work-card-header">
        <div class="card-title">
          <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.format" :key="path" :d="path" />
          </svg>
          <h2 id="dialogue-title">对白提取结果</h2>
        </div>
      </div>
      <div class="dialogue-extract-grid">
        <article v-for="dialogue in dialogueExtracts" :key="dialogue.line">
          <span>{{ dialogue.scene }}</span>
          <h3>{{ dialogue.speaker }}</h3>
          <p>{{ dialogue.line }}</p>
          <small>{{ dialogue.intent }}</small>
        </article>
      </div>
    </section>

    <el-alert
      v-if="notice"
      class="analysis-alert"
      :closable="false"
      :title="notice"
      :type="noticeType"
      show-icon
    />

    <div class="analysis-actions">
      <el-button class="editor-tool" native-type="button" :disabled="isParsing" @click="$emit('previous')">
        <svg class="reverse-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
        </svg>
        <span>返回导入</span>
      </el-button>
      <div class="analysis-action-group">
        <el-button class="editor-tool" native-type="button" :loading="isParsing" :disabled="isParsing" @click="$emit('rerun')">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.refresh" :key="path" :d="path" />
          </svg>
          <span>重新解析</span>
        </el-button>
        <el-button class="editor-tool is-primary" native-type="button" :disabled="!isComplete || isParsing" @click="$emit('next')">
          <span>生成剧本</span>
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
          </svg>
        </el-button>
      </div>
    </div>
  </div>
</template>
