<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createNovel,
  downloadScriptYaml,
  extractCharacters,
  extractScenes,
  generateNovelYaml,
  generateSceneContent,
  saveCharacters,
  saveSceneContent,
  saveScenes,
  saveScriptYaml,
} from '../api/novelScript'
import { getApiErrorMessage } from '../api/http'

const title = ref('雨夜重逢')
const content = ref('')
const novelId = ref(null)
const scriptId = ref(null)
const chapterCount = ref(0)
const characters = ref([])
const scenes = ref([])
const activeResultTab = ref('characters')
const selectedSceneId = ref('')
const sceneContentById = reactive({})
const yamlText = ref('')
const notice = ref('')
const loading = reactive({
  submit: false,
  characters: false,
  saveCharacters: false,
  scenes: false,
  saveScenes: false,
  sceneContent: false,
  yaml: false,
  saveYaml: false,
  download: false,
})

const selectedScene = computed(() => scenes.value.find((scene) => scene.id === selectedSceneId.value) || scenes.value[0])
const selectedSceneContent = computed(() => sceneContentById[selectedScene.value?.id] || [])
const canUseNovel = computed(() => Boolean(novelId.value))

const setError = (error) => {
  notice.value = getApiErrorMessage(error)
  ElMessage.error(notice.value)
}

const handleFileChange = async (file) => {
  const text = await file.raw.text()
  content.value = text
  if (!title.value || title.value === '雨夜重逢') {
    title.value = file.name.replace(/\.[^.]+$/, '')
  }
}

const submitNovel = async () => {
  loading.submit = true
  try {
    const result = await createNovel({ title: title.value, content: content.value })
    novelId.value = result.novel_id
    chapterCount.value = result.chapter_count
    characters.value = []
    scenes.value = []
    yamlText.value = ''
    scriptId.value = null
    notice.value = `已提交小说，识别到 ${result.chapter_count} 个章节。`
    ElMessage.success(notice.value)
  } catch (error) {
    setError(error)
  } finally {
    loading.submit = false
  }
}

const runExtractCharacters = async () => {
  loading.characters = true
  try {
    const result = await extractCharacters(novelId.value)
    characters.value = result.characters
    notice.value = `已识别 ${characters.value.length} 位人物。`
  } catch (error) {
    setError(error)
  } finally {
    loading.characters = false
  }
}

const confirmCharacters = async () => {
  loading.saveCharacters = true
  try {
    const result = await saveCharacters(novelId.value, characters.value)
    characters.value = result.characters
    notice.value = '人物确认结果已保存。'
    ElMessage.success(notice.value)
  } catch (error) {
    setError(error)
  } finally {
    loading.saveCharacters = false
  }
}

const runExtractScenes = async () => {
  loading.scenes = true
  try {
    const result = await extractScenes(novelId.value)
    scenes.value = result.scenes
    selectedSceneId.value = scenes.value[0]?.id || ''
    notice.value = `已识别 ${scenes.value.length} 个场景。`
  } catch (error) {
    setError(error)
  } finally {
    loading.scenes = false
  }
}

const persistScenes = async () => {
  if (!scenes.value.length) return
  loading.saveScenes = true
  try {
    const result = await saveScenes(novelId.value, scenes.value)
    scenes.value = result.scenes
    notice.value = '场景修改已保存。'
  } catch (error) {
    setError(error)
  } finally {
    loading.saveScenes = false
  }
}

const persistEditedSceneContent = async () => {
  const entries = Object.entries(sceneContentById)
  for (const [sceneId, contentItems] of entries) {
    if (Array.isArray(contentItems)) {
      const result = await saveSceneContent(sceneId, contentItems)
      sceneContentById[sceneId] = result.content
    }
  }
}

const runGenerateSceneContent = async () => {
  if (!selectedScene.value) return
  await persistScenes()
  loading.sceneContent = true
  try {
    const result = await generateSceneContent(selectedScene.value.id)
    sceneContentById[selectedScene.value.id] = result.content
    notice.value = `已生成 ${selectedScene.value.title} 的结构化内容。`
  } catch (error) {
    setError(error)
  } finally {
    loading.sceneContent = false
  }
}

const runGenerateYaml = async () => {
  loading.yaml = true
  try {
    await persistScenes()
    await persistEditedSceneContent()
    const result = await generateNovelYaml(novelId.value)
    yamlText.value = result.yaml
    scriptId.value = result.script_id
    notice.value = '完整 YAML 已生成并通过后端校验。'
    ElMessage.success(notice.value)
  } catch (error) {
    setError(error)
  } finally {
    loading.yaml = false
  }
}

const saveYaml = async () => {
  if (!scriptId.value) {
    ElMessage.warning('请先生成完整 YAML。')
    return
  }
  loading.saveYaml = true
  try {
    const result = await saveScriptYaml(scriptId.value, yamlText.value)
    yamlText.value = result.yaml
    notice.value = 'YAML 修改已保存。'
    ElMessage.success(notice.value)
  } catch (error) {
    setError(error)
  } finally {
    loading.saveYaml = false
  }
}

const downloadYaml = async () => {
  if (!scriptId.value) {
    ElMessage.warning('请先生成完整 YAML。')
    return
  }
  loading.download = true
  try {
    const blob = await downloadScriptYaml(scriptId.value)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `novel-script-${scriptId.value}.yaml`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    setError(error)
  } finally {
    loading.download = false
  }
}

const addCharacter = () => {
  characters.value.push({
    id: `char_${String(characters.value.length + 1).padStart(3, '0')}`,
    name: '',
    aliases: [],
    role: '角色',
    description: '',
    is_confirmed: false,
  })
}

const aliasText = (character) => character.aliases.join('，')
const updateAliases = (character, value) => {
  character.aliases = value.split(/[，,]/).map((item) => item.trim()).filter(Boolean)
}
</script>

<template>
  <div class="novel-yaml-page">
    <section class="novel-yaml-column source-column">
      <div class="panel-title-row">
        <div>
          <h2>小说原文</h2>
          <p>上传 TXT 或粘贴正文，系统会先拆章节再进入识别流程。</p>
        </div>
        <el-tag v-if="novelId" type="success">ID {{ novelId }}</el-tag>
      </div>

      <el-form label-position="top">
        <el-form-item label="小说标题">
          <el-input v-model="title" maxlength="255" show-word-limit />
        </el-form-item>
        <el-form-item label="上传 TXT">
          <el-upload :auto-upload="false" accept=".txt" :limit="1" :on-change="handleFileChange">
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="小说正文">
          <el-input v-model="content" type="textarea" :rows="22" resize="none" placeholder="粘贴小说正文..." />
        </el-form-item>
      </el-form>

      <div class="action-row">
        <el-button type="primary" :disabled="!title || !content" :loading="loading.submit" @click="submitNovel">
          提交小说
        </el-button>
        <el-tag v-if="chapterCount">章节 {{ chapterCount }}</el-tag>
      </div>
      <p v-if="notice" class="flow-notice">{{ notice }}</p>
    </section>

    <section class="novel-yaml-column result-column">
      <el-tabs v-model="activeResultTab" class="result-tabs">
        <el-tab-pane label="人物" name="characters">
          <div class="toolbar-row">
            <el-button :disabled="!canUseNovel" :loading="loading.characters" @click="runExtractCharacters">
              识别人物
            </el-button>
            <el-button :disabled="!characters.length" @click="addCharacter">添加人物</el-button>
            <el-button type="primary" :disabled="!characters.length" :loading="loading.saveCharacters" @click="confirmCharacters">
              保存人物确认
            </el-button>
          </div>

          <el-empty v-if="!characters.length" description="提交小说后识别人物" />
          <div v-else class="editable-list">
            <div v-for="character in characters" :key="character.id" class="edit-row">
              <el-input v-model="character.name" placeholder="姓名" />
              <el-input :model-value="aliasText(character)" placeholder="别名，用逗号分隔" @update:model-value="updateAliases(character, $event)" />
              <el-input v-model="character.role" placeholder="角色" />
              <el-input v-model="character.description" type="textarea" :rows="2" placeholder="人物描述" />
              <el-checkbox v-model="character.is_confirmed">已确认</el-checkbox>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="场景" name="scenes">
          <div class="toolbar-row">
            <el-button :disabled="!canUseNovel" :loading="loading.scenes" @click="runExtractScenes">识别场景</el-button>
            <el-button :disabled="!scenes.length" :loading="loading.saveScenes" @click="persistScenes">保存场景修改</el-button>
            <el-button type="primary" :disabled="!selectedScene" :loading="loading.sceneContent" @click="runGenerateSceneContent">
              生成当前场景内容
            </el-button>
          </div>

          <el-empty v-if="!scenes.length" description="识别人物后继续识别场景" />
          <div v-else class="scene-layout">
            <el-menu :default-active="selectedSceneId" class="scene-menu" @select="selectedSceneId = $event">
              <el-menu-item v-for="scene in scenes" :key="scene.id" :index="scene.id">
                {{ scene.title || scene.id }}
              </el-menu-item>
            </el-menu>

            <div v-if="selectedScene" class="scene-editor">
              <el-input v-model="selectedScene.title" placeholder="场景标题" />
              <div class="two-field-grid">
                <el-input v-model="selectedScene.location" placeholder="地点" />
                <el-input v-model="selectedScene.time" placeholder="时间" />
              </div>
              <el-input v-model="selectedScene.summary" type="textarea" :rows="3" placeholder="场景摘要" />
              <el-input v-model="selectedScene.source_text" type="textarea" :rows="5" readonly />
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="结构化内容" name="content">
          <el-empty v-if="!selectedSceneContent.length" description="选择场景后生成内容" />
          <div v-else class="content-list">
            <div v-for="(item, index) in selectedSceneContent" :key="index" class="content-item" :class="{ 'is-review': item.need_review }">
              <div class="content-meta">
                <el-tag :type="item.need_review ? 'warning' : 'success'">{{ item.type }}</el-tag>
                <el-tag v-if="item.need_review" type="warning">需要复核</el-tag>
                <span>置信度 {{ Math.round(item.confidence * 100) }}%</span>
              </div>
              <div class="two-field-grid">
                <el-input v-if="item.type === 'dialogue'" v-model="item.speaker" placeholder="speaker，未知写 unknown" />
                <el-input v-else v-model="item.actor" placeholder="actor" />
                <el-input v-model="item.emotion" placeholder="emotion" />
              </div>
              <el-input v-model="item.text" type="textarea" :rows="2" placeholder="剧本内容" />
              <el-input v-model="item.source_text" type="textarea" :rows="2" readonly />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>

    <section class="novel-yaml-column yaml-column">
      <div class="panel-title-row">
        <div>
          <h2>YAML 预览</h2>
          <p>后端由 JSON 转换为 YAML，中文使用 allow_unicode 保留。</p>
        </div>
      </div>
      <div class="toolbar-row">
        <el-button type="primary" :disabled="!scenes.length" :loading="loading.yaml" @click="runGenerateYaml">
          生成完整 YAML
        </el-button>
        <el-button :disabled="!scriptId" :loading="loading.saveYaml" @click="saveYaml">保存修改</el-button>
        <el-button :disabled="!scriptId" :loading="loading.download" @click="downloadYaml">下载 YAML</el-button>
      </div>
      <el-input v-model="yamlText" class="yaml-editor" type="textarea" :rows="34" resize="none" placeholder="生成后的 YAML 会出现在这里，可直接修改。" />
    </section>
  </div>
</template>
