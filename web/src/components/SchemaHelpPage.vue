<script setup>
defineProps({
  content: { type: Object, required: true },
  iconPaths: { type: Object, required: true },
})

defineEmits(['back'])
</script>

<template>
  <div class="schema-doc-page">
    <section class="schema-doc-hero" aria-labelledby="schema-doc-title">
      <div>
        <span>辅助文档</span>
        <h2 id="schema-doc-title">YAML Schema 说明</h2>
        <p>用于检查 AI 生成剧本的结构字段，帮助编辑、校验和导出保持一致。</p>
      </div>
      <button class="editor-tool" type="button" @click="$emit('back')">
        <svg class="reverse-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.arrow" :key="path" :d="path" />
        </svg>
        <span>返回剧本编辑</span>
      </button>
    </section>

    <section class="schema-doc-grid">
      <article class="schema-doc-card schema-field-card" aria-labelledby="field-title">
        <div class="schema-doc-card-header">
          <h3 id="field-title">字段说明</h3>
          <span>{{ content.fields.length }} 个字段</span>
        </div>
        <div class="schema-table-wrap">
          <table class="schema-field-table">
            <thead>
              <tr>
                <th>字段</th>
                <th>类型</th>
                <th>必填</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="field in content.fields" :key="field.name">
                <td><code>{{ field.name }}</code></td>
                <td>{{ field.type }}</td>
                <td>{{ field.required ? '是' : '否' }}</td>
                <td>{{ field.description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="schema-doc-card" aria-labelledby="required-title">
        <div class="schema-doc-card-header">
          <h3 id="required-title">必填字段</h3>
          <span>最小可导出结构</span>
        </div>
        <ul class="required-field-list">
          <li v-for="field in content.requiredFields" :key="field">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconPaths.check" :key="path" :d="path" />
            </svg>
            <code>{{ field }}</code>
          </li>
        </ul>
      </article>

      <article class="schema-doc-card schema-example-card" aria-labelledby="example-title">
        <div class="schema-doc-card-header">
          <h3 id="example-title">示例 YAML</h3>
          <span>可作为结构参考</span>
        </div>
        <pre><code><span v-for="line in content.exampleYaml" :key="line">{{ line }}</span></code></pre>
      </article>

      <article class="schema-doc-card" aria-labelledby="reason-title">
        <div class="schema-doc-card-header">
          <h3 id="reason-title">设计原因</h3>
          <span>面向编辑与导出</span>
        </div>
        <div class="schema-reason-list">
          <p v-for="reason in content.reasons" :key="reason">{{ reason }}</p>
        </div>
      </article>
    </section>
  </div>
</template>
