<script setup>
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  chapters: { type: Array, required: true },
})

const emit = defineEmits(['confirm', 'update:modelValue'])

const form = reactive({
  chapterTitle: '',
  sceneTitle: '',
  location: '',
  time: '',
  characters: '',
  action: '',
})

const chapterOptions = computed(() => props.chapters.map((chapter) => chapter.title))
const canConfirm = computed(() => form.sceneTitle.trim() && form.location.trim() && form.time.trim())

const resetForm = () => {
  form.chapterTitle = chapterOptions.value[0] || ''
  form.sceneTitle = ''
  form.location = ''
  form.time = ''
  form.characters = ''
  form.action = ''
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      resetForm()
    }
  },
)

const closeDialog = () => {
  emit('update:modelValue', false)
}

const confirmScene = () => {
  if (!canConfirm.value) {
    return
  }

  emit('confirm', { ...form })
}
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="dialog-backdrop" role="presentation" @click.self="closeDialog">
      <section class="generation-dialog add-scene-dialog" role="dialog" aria-modal="true" aria-labelledby="add-scene-title">
        <header class="dialog-header">
          <div>
            <span>场景草稿</span>
            <h2 id="add-scene-title">添加新场景</h2>
          </div>
          <button class="dialog-close" type="button" aria-label="关闭添加场景" @click="closeDialog">×</button>
        </header>

        <div class="dialog-body add-scene-form">
          <label class="form-field">
            <span>所属章节</span>
            <select v-model="form.chapterTitle">
              <option v-for="chapter in chapterOptions" :key="chapter" :value="chapter">{{ chapter }}</option>
            </select>
          </label>

          <label class="form-field">
            <span>场景标题</span>
            <input v-model="form.sceneTitle" type="text" placeholder="例如：雨夜排练室争执" />
          </label>

          <div class="form-field-grid">
            <label class="form-field">
              <span>地点</span>
              <input v-model="form.location" type="text" placeholder="例如：排练室" />
            </label>
            <label class="form-field">
              <span>时间</span>
              <input v-model="form.time" type="text" placeholder="例如：夜晚" />
            </label>
          </div>

          <label class="form-field">
            <span>出场人物</span>
            <input v-model="form.characters" type="text" placeholder="用顿号分隔，例如：角色甲、角色乙" />
          </label>

          <label class="form-field">
            <span>动作摘要</span>
            <textarea v-model="form.action" rows="4" placeholder="写下这个场景最重要的动作、情绪或冲突。"></textarea>
          </label>
        </div>

        <footer class="dialog-actions">
          <button class="editor-tool" type="button" @click="closeDialog">取消</button>
          <button class="editor-tool is-primary" type="button" :disabled="!canConfirm" @click="confirmScene">加入草稿</button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>
