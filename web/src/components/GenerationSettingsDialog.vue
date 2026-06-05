<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  options: { type: Object, required: true },
  initialSettings: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const selectedType = ref('')
const selectedStyle = ref('')
const selectedContents = ref([])

const defaultSettings = computed(() => ({
  scriptType: props.options.scriptTypes[0],
  adaptationStyle: props.options.adaptationStyles[0],
  contentOptions: props.options.contentOptions.slice(0, 2),
}))

const resetForm = () => {
  const source = props.initialSettings || defaultSettings.value
  selectedType.value = source.scriptType
  selectedStyle.value = source.adaptationStyle
  selectedContents.value = [...source.contentOptions]
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      resetForm()
    }
  },
  { immediate: true },
)

const closeDialog = () => {
  emit('update:modelValue', false)
}

const confirmSettings = () => {
  emit('confirm', {
    scriptType: selectedType.value,
    adaptationStyle: selectedStyle.value,
    contentOptions: [...selectedContents.value],
  })
}
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="dialog-backdrop" role="presentation" @click.self="closeDialog">
      <section class="generation-dialog" role="dialog" aria-modal="true" aria-labelledby="generation-dialog-title">
        <header class="dialog-header">
          <div>
            <span>生成设置</span>
            <h2 id="generation-dialog-title">配置剧本生成偏好</h2>
          </div>
          <button class="dialog-close" type="button" aria-label="关闭生成设置" @click="closeDialog">×</button>
        </header>

        <div class="dialog-body">
          <fieldset class="setting-group">
            <legend>剧本类型</legend>
            <div class="segmented-grid">
              <label v-for="type in options.scriptTypes" :key="type" class="choice-pill">
                <input v-model="selectedType" type="radio" name="script-type" :value="type" />
                <span>{{ type }}</span>
              </label>
            </div>
          </fieldset>

          <fieldset class="setting-group">
            <legend>改编风格</legend>
            <div class="segmented-grid">
              <label v-for="style in options.adaptationStyles" :key="style" class="choice-pill">
                <input v-model="selectedStyle" type="radio" name="adaptation-style" :value="style" />
                <span>{{ style }}</span>
              </label>
            </div>
          </fieldset>

          <fieldset class="setting-group">
            <legend>生成内容选项</legend>
            <div class="checkbox-grid">
              <label v-for="content in options.contentOptions" :key="content" class="checkbox-choice">
                <input v-model="selectedContents" type="checkbox" :value="content" />
                <span>{{ content }}</span>
              </label>
            </div>
          </fieldset>
        </div>

        <footer class="dialog-actions">
          <button class="editor-tool" type="button" @click="closeDialog">取消</button>
          <button class="editor-tool is-primary" type="button" @click="confirmSettings">确认生成</button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>
