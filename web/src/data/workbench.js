export const navItems = [
  { label: '工作台', icon: 'home', active: true },
  { label: '我的项目', icon: 'folder', active: false },
  { label: '模板中心', icon: 'grid', active: false },
  { label: '剧本库', icon: 'book', active: false },
  { label: '帮助文档', icon: 'help', active: false },
]

export const quickActions = [
  { label: '编辑剧本章节', time: '2 分钟前' },
  { label: '生成剧本（YAML）', time: '5 分钟前' },
  { label: '导入小说《星辰之下》', time: '1 小时前' },
]

export const workflowSteps = [
  { number: '1', title: '导入小说', description: '上传或粘贴小说内容', status: 'done' },
  { number: '2', title: 'AI 解析', description: '智能识别人物、场景与剧情', status: 'done' },
  { number: '3', title: '生成剧本', description: '一键生成结构化剧本', status: 'current' },
  { number: '4', title: '编辑与导出', description: '在线编辑并导出剧本', status: 'upcoming' },
]

export const projectStages = [
  { label: '小说导入', status: 'done', note: '' },
  { label: 'AI内容解析', status: 'done', note: '' },
  { label: '生成剧本', status: 'active', note: '进行中' },
  { label: '编辑与导出', status: 'pending', note: '待开始' },
]

export const analysisMetrics = [
  { label: '人物', value: '12', icon: 'users', tone: 'violet' },
  { label: '场景', value: '28', icon: 'scene', tone: 'blue' },
  { label: '章节', value: '5', icon: 'chapter', tone: 'mint' },
  { label: '冲突事件', value: '16', icon: 'conflict', tone: 'orange' },
]

export const insightItems = [
  { label: '故事类型', value: '现代 / 都市 / 成长' },
  { label: '核心主题', value: '梦想、友情、成长' },
  { label: '故事基调', value: '积极 / 温暖' },
  { label: '建议剧本类型', value: '电视剧（30 集）' },
]

export const scriptChapters = [
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

export const yamlLines = [
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

export const previewDialogues = [
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

export const iconPaths = {
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
