<script setup>
const props = defineProps({
  content: { type: Object, required: true },
  iconPaths: { type: Object, required: true },
})

const docNavGroups = [
  {
    label: '文档',
    links: [
      { id: 'overview', label: '工具简介' },
      { id: 'workflow', label: '基本使用流程' },
      { id: 'import', label: '小说导入说明' },
    ],
  },
  {
    label: '解析',
    links: [
      { id: 'analysis', label: 'AI解析说明' },
      { id: 'schema', label: 'YAML剧本格式' },
      { id: 'fields', label: '字段说明' },
    ],
  },
  {
    label: '规范',
    links: [
      { id: 'reasons', label: '设计原因' },
      { id: 'faq', label: '常见问题' },
    ],
  },
]

const fieldCount = props.content.schemaFields.length
</script>

<template>
  <div class="help-docs-page">
    <aside class="help-docs-nav" aria-label="帮助文档目录">
      <div v-for="group in docNavGroups" :key="group.label" class="help-docs-nav-group">
        <span>{{ group.label }}</span>
        <a v-for="link in group.links" :key="link.id" :href="`#${link.id}`">{{ link.label }}</a>
      </div>
    </aside>

    <article class="help-docs-article">
      <section id="overview" class="help-docs-hero" aria-labelledby="help-docs-title">
        <span>{{ content.brief.eyebrow }}</span>
        <h2 id="help-docs-title">{{ content.brief.title }}</h2>
        <p>{{ content.brief.description }}</p>
        <p v-for="paragraph in content.intro" :key="paragraph">{{ paragraph }}</p>
        <div class="help-docs-hero-actions">
          <a href="#schema" class="editor-tool is-primary">阅读 Schema</a>
          <a href="#workflow" class="editor-tool">查看流程</a>
        </div>
      </section>

      <section id="workflow" class="help-doc-section" aria-labelledby="workflow-title">
        <div class="help-doc-section-copy">
          <span>基本使用流程</span>
          <h3 id="workflow-title">导入、解析、选择模板、生成、编辑、导出。</h3>
          <p>工具按小说改编剧本的真实顺序组织流程，每一步都保留可检查、可修改的结果。</p>
        </div>
        <ol class="help-workflow-list">
          <li v-for="step in content.workflow" :key="step.step">
            <strong>{{ step.step }}</strong>
            <div>
              <h4>{{ step.title }}</h4>
              <p>{{ step.detail }}</p>
            </div>
          </li>
        </ol>
      </section>

      <section id="import" class="help-doc-section help-doc-section-split" aria-labelledby="import-title">
        <div class="help-doc-section-copy">
          <span>小说导入说明</span>
          <h3 id="import-title">导入后系统会先整理章节结构，再进入 AI 解析。</h3>
          <p>小说导入页面支持上传文件、粘贴正文和示例导入。系统会识别常见章节标题，并将正文整理为后续 AI 解析可使用的结构化输入。</p>
        </div>
        <div class="help-mini-grid">
          <div>
            <h4>支持方式</h4>
            <ul>
              <li v-for="method in content.importMethods" :key="method">{{ method }}</li>
            </ul>
          </div>
          <div>
            <h4>章节标题示例</h4>
            <ul>
              <li v-for="pattern in content.chapterPatterns" :key="pattern">{{ pattern }}</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="analysis" class="help-doc-section" aria-labelledby="analysis-title">
        <div class="help-doc-section-copy">
          <span>AI解析说明</span>
          <h3 id="analysis-title">从小说中提取人物、场景、事件、对白与动作。</h3>
          <p>AI 解析页展示系统从小说中抽取出的关键信息，帮助作者确认素材是否足够生成剧本初稿。</p>
        </div>
        <div class="help-analysis-grid">
          <article v-for="section in content.analysisSections" :key="section.title" class="help-analysis-card">
            <h4>{{ section.title }}</h4>
            <p>{{ section.description }}</p>
            <pre><code><span v-for="line in section.example" :key="line">{{ line }}</span></code></pre>
          </article>
        </div>
      </section>

      <section id="schema" class="help-doc-section" aria-labelledby="schema-title">
        <div class="help-doc-section-copy">
          <span>YAML剧本格式说明</span>
          <h3 id="schema-title">YAML 适合保存章节、场景、人物、对白、动作等剧本信息。</h3>
          <p>本工具生成的剧本采用 YAML 格式进行组织，结构清晰，方便编辑器校验、剧本预览和多格式导出。</p>
        </div>
        <pre class="help-yaml-block"><code><span v-for="line in content.exampleYaml" :key="line">{{ line }}</span></code></pre>
      </section>

      <section id="fields" class="help-doc-section" aria-labelledby="schema-table-title">
        <div class="help-doc-section-copy">
          <span>{{ fieldCount }} 个字段</span>
          <h3 id="schema-table-title">字段说明。</h3>
          <p>字段表用于定义 YAML 剧本的结构、类型和必填规则。</p>
        </div>
        <div class="help-table-wrap">
          <table class="help-schema-table">
            <thead>
              <tr>
                <th>字段</th>
                <th>类型</th>
                <th>是否必填</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="field in content.schemaFields" :key="field.name">
                <td><code>{{ field.name }}</code></td>
                <td>{{ field.type }}</td>
                <td>{{ field.required ? '必填' : '可选' }}</td>
                <td>{{ field.description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section id="reasons" class="help-doc-section help-doc-section-split" aria-labelledby="schema-reason-title">
        <div class="help-doc-section-copy">
          <span>Schema 设计原因</span>
          <h3 id="schema-reason-title">按照剧本创作流程进行设计。</h3>
          <p>Schema 的目标是让 AI 输出足够结构化，同时让作者仍然能像修改文稿一样继续打磨。</p>
        </div>
        <div class="help-reason-grid">
          <p v-for="reason in content.designReasons" :key="reason">{{ reason }}</p>
        </div>
      </section>

      <section id="faq" class="help-doc-section" aria-labelledby="faq-title">
        <div class="help-doc-section-copy">
          <span>常见问题</span>
          <h3 id="faq-title">导入、校验、导出与管理。</h3>
          <p>以下问题覆盖使用过程中的常见疑问。</p>
        </div>
        <div class="help-faq-list">
          <article v-for="item in content.faq" :key="item.question">
            <h4>{{ item.question }}</h4>
            <p>{{ item.answer }}</p>
          </article>
        </div>
      </section>
    </article>
  </div>
</template>
