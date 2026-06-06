<script setup>
defineProps({
  chapterCount: { type: Number, required: true },
  chapters: { type: Array, required: true },
  fileName: { type: String, default: '' },
  iconPaths: { type: Object, required: true },
  importNotice: { type: String, default: '' },
  isSubmitting: { type: Boolean, default: false },
  isValid: { type: Boolean, required: true },
  novelText: { type: String, required: true },
})

defineEmits(['file-upload', 'next', 'update:novelText'])
</script>

<template>
  <div class="import-workspace">
    <section class="work-card import-card" aria-labelledby="import-title">
      <div class="work-card-header">
        <div class="card-title">
          <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.upload" :key="path" :d="path" />
          </svg>
          <h2 id="import-title">导入小说内容</h2>
        </div>
        <div class="import-header-actions">
          <span class="status-pill" :class="isValid ? 'is-valid' : 'is-warning'">
            {{ isValid ? '章节校验通过' : '至少需要 3 章' }}
          </span>
          <button class="editor-tool is-primary" type="button" :disabled="!isValid || isSubmitting" @click="$emit('next')">
            <span>{{ isSubmitting ? '正在提交项目...' : '下一步：AI解析' }}</span>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
            </svg>
          </button>
        </div>
      </div>

      <div class="import-source-grid">
        <label class="upload-dropzone" for="novel-file">
          <input id="novel-file" type="file" accept=".txt,.docx" @change="$emit('file-upload', $event)" />
          <span class="upload-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.file" :key="path" :d="path" />
            </svg>
          </span>
          <span>上传 txt / docx 文件</span>
          <strong>{{ fileName || '选择文件或拖入此处' }}</strong>
          <small>支持长篇小说，系统将自动识别章节结构</small>
          <em>TXT 可读取正文，DOCX 将先记录文件名</em>
        </label>

        <label class="paste-panel">
          <span>粘贴小说文本</span>
          <textarea
            :value="novelText"
            rows="14"
            spellcheck="false"
            @input="$emit('update:novelText', $event.target.value)"
          ></textarea>
        </label>
      </div>

      <p v-if="importNotice" class="inline-note">{{ importNotice }}</p>

      <div class="chapter-summary">
        <div>
          <span>自动识别章节</span>
          <strong>{{ chapterCount }} 章</strong>
        </div>
        <p>{{ isValid ? '已满足 AI 解析最低要求，可以进入下一步。' : '继续补充文本，系统至少需要识别 3 章。' }}</p>
      </div>

      <ul class="chapter-list" aria-label="章节列表">
        <li v-for="(chapter, index) in chapters" :key="chapter.title" :class="{ 'is-current': index === 0 }">
          <span class="chapter-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <div>
            <strong>{{ chapter.title }}</strong>
            <span>{{ chapter.excerpt }}</span>
          </div>
        </li>
      </ul>

    </section>

    <aside class="work-card novel-preview-card" aria-labelledby="novel-preview-title">
      <div class="work-card-header">
        <div class="card-title">
          <svg class="item-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.text" :key="path" :d="path" />
          </svg>
          <h2 id="novel-preview-title">小说原文预览</h2>
        </div>
        <span class="preview-status">实时预览</span>
      </div>
      <div class="preview-meta-row">
        <span>{{ novelText.length }} 字</span>
        <span>{{ chapterCount }} 章</span>
        <span>{{ isValid ? '可解析' : '待补充' }}</span>
      </div>
      <div class="novel-preview">
        <p v-for="paragraph in novelText.split('\n').filter(Boolean)" :key="paragraph">{{ paragraph }}</p>
      </div>
    </aside>
  </div>
</template>
