export const navItems = [
  { id: 'workbench', label: '工作台', icon: 'home' },
  { id: 'projects', label: '我的项目', icon: 'folder' },
  { id: 'templates', label: '模板中心', icon: 'grid' },
  { id: 'library', label: '剧本库', icon: 'book' },
  { id: 'help', label: '帮助文档', icon: 'help' },
]

export const quickActions = [
  { label: '编辑剧本章节', time: '2 分钟前' },
  { label: '生成剧本（YAML）', time: '5 分钟前' },
  { label: '导入小说《星辰之下》', time: '1 小时前' },
]

export const generationSettingOptions = {
  scriptTypes: ['影视剧', '短剧', '话剧', '分镜剧本'],
  adaptationStyles: ['忠于原文', '精简剧情', '强化冲突', '增强对白'],
  contentOptions: ['动作描写', '情绪提示', '镜头建议', '转场提示'],
}

export const schemaValidationMock = {
  yamlValid: true,
  requiredFieldsValid: true,
  chapterCount: 5,
  sceneCount: 28,
  checkedAt: '尚未手动校验',
  message: '当前 YAML 结构可用于生成剧本编辑稿。',
}

export const workflowSteps = [
  { number: '1', title: '导入小说', description: '上传或粘贴小说内容', status: 'done' },
  { number: '2', title: 'AI 解析', description: '智能识别人物、场景与剧情', status: 'done' },
  { number: '3', title: '生成剧本', description: '一键生成结构化剧本', status: 'current' },
  { number: '4', title: '编辑与导出', description: '在线编辑并导出剧本', status: 'upcoming' },
]

export const importWorkflowSteps = [
  { number: '1', title: '导入小说', description: '上传或粘贴小说内容', status: 'current' },
  { number: '2', title: 'AI 解析', description: '智能识别人物、场景与剧情', status: 'upcoming' },
  { number: '3', title: '生成剧本', description: '一键生成结构化剧本', status: 'upcoming' },
  { number: '4', title: '编辑与导出', description: '在线编辑并导出剧本', status: 'upcoming' },
]

export const analysisWorkflowSteps = [
  { number: '1', title: '导入小说', description: '上传或粘贴小说内容', status: 'done' },
  { number: '2', title: 'AI 解析', description: '智能识别人物、场景与剧情', status: 'current' },
  { number: '3', title: '生成剧本', description: '一键生成结构化剧本', status: 'upcoming' },
  { number: '4', title: '编辑与导出', description: '在线编辑并导出剧本', status: 'upcoming' },
]

export const previewWorkflowSteps = [
  { number: '1', title: '导入小说', description: '上传或粘贴小说内容', status: 'done' },
  { number: '2', title: 'AI 解析', description: '智能识别人物、场景与剧情', status: 'done' },
  { number: '3', title: '生成剧本', description: '一键生成结构化剧本', status: 'done' },
  { number: '4', title: '编辑与导出', description: '在线编辑并导出剧本', status: 'current' },
]

export const defaultNovelText = `第1章 初入城市
林晓拖着行李箱走出地铁站，城市的傍晚像一层淡金色的雾。她背着旧吉他，低头确认地址，却发现手机只剩下百分之三的电。

第2章 梦想启航
苏晴在出租屋门口等她，两个人合租的第一晚并不宽裕，但窗外的灯光让林晓第一次觉得自己真的抵达了梦想开始的地方。

第3章 现实的挑战
面试并不顺利，制作人只听了三十秒就打断了她。林晓把简历攥得很紧，仍然礼貌地说谢谢，走出写字楼后却忍不住红了眼眶。

第4章 友情的考验
苏晴偷偷把林晓的 demo 发给小剧场导演，林晓知道后很生气。她以为好友不理解她的坚持，却没有发现苏晴已经替她跑了很多路。

第5章 破茧成蝶
小剧场的灯亮起，林晓站在舞台中央唱出第一句歌词。台下的掌声不算热烈，却足够让她重新相信，慢慢来也可以走到远方。`

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

export const analysisCharacters = [
  { name: '林晓', role: '主角', age: '24', trait: '怀揣音乐梦想，敏感但坚定' },
  { name: '苏晴', role: '室友 / 盟友', age: '25', trait: '行动力强，习惯用实际帮助表达关心' },
  { name: '周亦辰', role: '制作人', age: '32', trait: '克制冷静，代表行业门槛与现实压力' },
  { name: '小剧场导演', role: '机会提供者', age: '38', trait: '关注真实表达，推动林晓完成转折' },
]

export const analysisScenes = [
  { title: '地铁站出口', chapter: '第1章', time: '傍晚', mood: '陌生、迷茫' },
  { title: '合租出租屋', chapter: '第2章', time: '夜晚', mood: '局促、温暖' },
  { title: '音乐公司面试间', chapter: '第3章', time: '下午', mood: '紧张、受挫' },
  { title: '小剧场后台', chapter: '第5章', time: '演出前', mood: '忐忑、蓄势' },
]

export const plotEvents = [
  { step: '01', chapter: '第1章', title: '抵达城市', detail: '林晓带着吉他来到陌生城市，建立主角目标和孤独感。' },
  { step: '02', chapter: '第2章', title: '获得陪伴', detail: '苏晴接纳林晓，合租关系成为后续情感支点。' },
  { step: '03', chapter: '第3章', title: '面试受挫', detail: '制作人的打断让主角第一次直面行业现实。' },
  { step: '04', chapter: '第4章', title: '好友误会', detail: '苏晴越界帮忙，引发友情冲突，也埋下机会。' },
  { step: '05', chapter: '第5章', title: '舞台试炼', detail: '林晓完成公开演出，故事进入阶段性成长。' },
]

export const characterRelations = [
  { source: '林晓', target: '苏晴', relation: '室友 / 朋友', note: '支持与误会并存，是情绪转折的主要关系。' },
  { source: '林晓', target: '周亦辰', relation: '求职者 / 评审', note: '体现行业规则和主角自我怀疑。' },
  { source: '苏晴', target: '小剧场导演', relation: '推荐人 / 导演', note: '推动林晓获得第一次舞台机会。' },
]

export const dialogueExtracts = [
  { speaker: '林晓', scene: '地铁站出口', line: '这座城市，真的能实现我的梦想吗？', intent: '表达不确定和核心目标' },
  { speaker: '苏晴', scene: '出租屋', line: '先把今晚安顿好，梦想明天继续追。', intent: '缓和压力，建立陪伴感' },
  { speaker: '周亦辰', scene: '面试间', line: '技巧不错，但我听不到你自己的声音。', intent: '制造打击，指出成长方向' },
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

export const scriptPreviewScenes = [
  {
    title: '场景 1-1 地铁站相遇',
    meta: '内景 / 地铁站 / 傍晚',
    characters: ['林晓', '苏晴'],
    action: '人头攒动的地铁站，广播声回荡。林晓背着吉他包，低头看着手机，神情略显迷茫。手机电量只剩百分之三，她抬头望向出口指示牌。',
    dialogues: [
      { speaker: '林晓', line: '这座城市，真的能实现我的梦想吗？' },
      { speaker: '苏晴', line: '需要帮忙吗？看起来你有点迷路了。' },
    ],
  },
  {
    title: '场景 1-2 出租屋夜谈',
    meta: '内景 / 出租屋 / 夜晚',
    characters: ['林晓', '苏晴'],
    action: '小小的出租屋里，纸箱还没拆完。窗外灯光落在旧吉他上，林晓终于松下一口气。',
    dialogues: [
      { speaker: '苏晴', line: '先把今晚安顿好，梦想明天继续追。' },
      { speaker: '林晓', line: '我怕自己坚持不到被人看见的那一天。' },
    ],
  },
  {
    title: '场景 1-3 公司面试',
    meta: '内景 / 音乐公司面试间 / 下午',
    characters: ['林晓', '周亦辰'],
    action: '会议室的白光很亮。周亦辰合上简历，林晓攥紧背包带，努力保持礼貌的微笑。',
    dialogues: [
      { speaker: '周亦辰', line: '技巧不错，但我听不到你自己的声音。' },
      { speaker: '林晓', line: '我可以再试一次，请给我一分钟。' },
    ],
  },
]

export const schemaHelpContent = {
  fields: [
    { name: 'script.title', type: 'string', required: true, description: '剧本标题，用于导出文件名和预览页标题。' },
    { name: 'script.format', type: 'string', required: true, description: '剧本类型，例如影视剧、短剧、话剧或分镜剧本。' },
    { name: 'characters[].name', type: 'string', required: true, description: '人物名称，需与场景中的出场人物保持一致。' },
    { name: 'chapters[].scenes[]', type: 'array', required: true, description: '章节内的场景列表，是生成标准剧本文本的主要来源。' },
    { name: 'dialogues[].line', type: 'string', required: false, description: '对白正文，可由 AI 提取后继续人工调整。' },
  ],
  requiredFields: ['script.title', 'script.format', 'characters[].name', 'chapters[].title', 'chapters[].scenes[].title'],
  exampleYaml: [
    'script:',
    '  title: "星辰之下"',
    '  format: "影视剧"',
    'characters:',
    '  - id: char_001',
    '    name: 林晓',
    'chapters:',
    '  - id: ch_001',
    '    title: 初入城市',
    '    scenes:',
    '      - id: sc_001_001',
    '        title: 地铁站相遇',
    '        location: 地铁站',
    '        time: 傍晚',
  ],
  reasons: [
    '用 YAML 保留章节、场景、人物和对白之间的结构关系，便于后续校验和导出。',
    '必填字段只覆盖生成剧本所需的最小骨架，减少创作者在早期编辑时的负担。',
    '字段命名尽量接近剧本制作语境，让非技术用户也能判断内容是否放在正确位置。',
  ],
}

export const iconPaths = {
  home: ['M3.5 10.5 12 3.75l8.5 6.75', 'M5.75 9.5v9.25h12.5V9.5', 'M9.5 18.75v-5h5v5'],
  upload: ['M12 15.25V4.75', 'M8.25 8.5 12 4.75 15.75 8.5', 'M5 14.75v3.75h14v-3.75'],
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
  refresh: ['M18.25 8.75A6.25 6.25 0 0 0 7 6.25L5.25 8', 'M5.75 15.25A6.25 6.25 0 0 0 17 17.75L18.75 16', 'M18.25 5.5v3.25H15', 'M5.75 18.5v-3.25H9'],
  link: ['M9.25 13.75 14.75 8.25', 'M10.75 6.25l.85-.85a3.2 3.2 0 0 1 4.55 4.5l-.9.9', 'M13.25 17.75l-.85.85a3.2 3.2 0 0 1-4.55-4.5l.9-.9'],
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
  file: ['M6 4.75h8.25L18 8.5v10.75H6z', 'M14.25 4.75V8.5H18', 'M8.75 12.25h6.5', 'M8.75 15.25h4.5'],
  text: ['M5.25 6.75h13.5', 'M5.25 10.75h13.5', 'M5.25 14.75h9.5', 'M5.25 18.25h6.25'],
}
