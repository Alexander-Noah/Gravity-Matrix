export const navItems = [
  { id: 'workbench', label: '工作台', icon: 'home' },
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

export const projectStats = [
  { label: '进行中项目', value: '6', note: '2 个今日更新', tone: 'violet' },
  { label: '已生成剧本', value: '18', note: '本周新增 5 个', tone: 'blue' },
  { label: '待校验 YAML', value: '4', note: '建议优先处理', tone: 'orange' },
  { label: '已导出文件', value: '32', note: '含 TXT / Markdown / PDF', tone: 'mint' },
]

export const projectCards = [
  {
    title: '《星辰之下》改编项目',
    type: '都市成长 / 影视剧',
    status: '编辑中',
    progress: 75,
    updatedAt: '2 分钟前',
    chapters: 5,
    scenes: 28,
    owner: '创作者',
    nextAction: '继续编辑 YAML',
  },
  {
    title: '《雨夜来信》短剧项目',
    type: '悬疑情感 / 短剧',
    status: '待解析',
    progress: 35,
    updatedAt: '昨天 21:40',
    chapters: 12,
    scenes: 0,
    owner: '创作者',
    nextAction: '进入 AI 解析',
  },
  {
    title: '《旧城咖啡馆》话剧稿',
    type: '现实题材 / 话剧',
    status: '待导出',
    progress: 92,
    updatedAt: '3 天前',
    chapters: 8,
    scenes: 36,
    owner: '协作组',
    nextAction: '打开完整预览',
  },
]

export const projectActivities = [
  { title: '编辑《星辰之下》第 1 章场景', time: '2 分钟前', status: '已保存' },
  { title: '生成《雨夜来信》AI 解析草稿', time: '昨天', status: '待确认' },
  { title: '导出《旧城咖啡馆》Markdown 文件', time: '3 天前', status: '已导出' },
]

export const scriptGenerationTemplates = [
  {
    id: 'tv-drama',
    name: '影视剧剧本模板',
    scenario: '适合长篇小说改编为电视剧、网剧或电影分场剧本。',
    features: ['按章节拆分场景', '保留人物动机与动作描写', '适配标准场景标题'],
    fields: ['script', 'characters', 'chapters', 'scenes', 'dialogues'],
    yamlExample: [
      'script:',
      '  template: tv_drama',
      '  format: 影视剧',
      '  logline: 主线故事一句话概述',
      'characters:',
      '  - id: char_001',
      '    name: 林晓',
      '    role: 主角',
      'chapters:',
      '  - id: ch_001',
      '    title: 初入城市',
      '    scenes:',
      '      - id: sc_001_001',
      '        title: 地铁站相遇',
      '        location: 地铁站',
      '        time: 傍晚',
      '        action: 人群涌动，主角拖着行李走出站台。',
      '        dialogues:',
      '          - speaker: 林晓',
      '            line: 这座城市，真的能实现我的梦想吗？',
    ],
  },
  {
    id: 'short-drama',
    name: '短剧剧本模板',
    scenario: '适合高节奏短剧、竖屏剧和强钩子内容生成。',
    features: ['强化开场冲突', '突出反转节点', '每集保留结尾钩子'],
    fields: ['episode', 'hook', 'conflict', 'turning_point', 'dialogues'],
    yamlExample: [
      'episode:',
      '  template: short_drama',
      '  duration: 2-5分钟',
      '  hook: 开场三秒冲突',
      'beats:',
      '  - type: opening_hook',
      '    content: 主角被迫当众证明自己',
      '  - type: reversal',
      '    content: 好友带来隐藏机会',
      'ending_hook:',
      '  question: 主角是否接受新挑战？',
    ],
  },
  {
    id: 'stage-play',
    name: '话剧剧本模板',
    scenario: '适合将小说改编为舞台表演文本和排练稿。',
    features: ['强调舞台调度', '保留幕与场结构', '补充人物入场退场'],
    fields: ['act', 'scene', 'stage_direction', 'characters', 'dialogues'],
    yamlExample: [
      'play:',
      '  template: stage_play',
      '  acts:',
      '    - title: 第一幕',
      '      scenes:',
      '        - title: 出租屋夜谈',
      '          stage_direction: 灯光渐亮，桌上放着旧吉他。',
      '          entrances:',
      '            - 林晓从舞台左侧入场',
      '          dialogues:',
      '            - speaker: 苏晴',
      '              line: 先把今晚安顿好。',
    ],
  },
  {
    id: 'storyboard',
    name: '分镜剧本模板',
    scenario: '适合短视频、广告片、动画和导演分镜草案。',
    features: ['拆分镜号', '补充景别与机位', '保留镜头意图'],
    fields: ['shot', 'camera', 'visual', 'audio', 'transition'],
    yamlExample: [
      'storyboard:',
      '  template: storyboard',
      '  shots:',
      '    - shot_id: shot_001',
      '      camera: 中景，跟拍',
      '      visual: 林晓拖着行李走出地铁站',
      '      audio: 地铁广播与人群声',
      '      transition: 切至手机低电量特写',
    ],
  },
  {
    id: 'audio-drama',
    name: '广播剧模板',
    scenario: '适合音频剧、有声书改编和纯声音叙事。',
    features: ['强化旁白节奏', '补充音效提示', '区分环境声与对白'],
    fields: ['narration', 'sound_effects', 'ambient', 'dialogues', 'music'],
    yamlExample: [
      'audio_drama:',
      '  template: audio_drama',
      '  opening_music: 温暖的钢琴铺底',
      '  scenes:',
      '    - title: 地铁站出口',
      '      ambient: 人群脚步声，远处广播声',
      '      narration: 林晓第一次站在这座城市的傍晚里。',
      '      sound_effects:',
      '        - 手机低电量提示音',
      '      dialogues:',
      '        - speaker: 林晓',
      '          line: 这座城市，真的能实现我的梦想吗？',
    ],
  },
]

export const scriptLibraryStats = [
  { label: '全部剧本', value: '6', note: '覆盖 5 类剧本格式', tone: 'violet' },
  { label: '编辑中', value: '2', note: '最近 24 小时有更新', tone: 'blue' },
  { label: '已完成', value: '1', note: '可进入最终预览', tone: 'mint' },
  { label: '已导出', value: '2', note: '已生成交付文件', tone: 'orange' },
]

export const scriptLibraryItems = [
  {
    id: 'script-001',
    title: '《星辰之下》第一季剧本',
    sourceNovel: '《星辰之下》',
    type: '影视剧',
    chapters: 5,
    scenes: 28,
    dialogues: 146,
    schemaStatus: '校验通过',
    status: '编辑中',
    updatedAt: '2 分钟前',
    tags: ['都市成长', '友情', '长剧'],
  },
  {
    id: 'script-002',
    title: '《雨夜来信》短剧版',
    sourceNovel: '《雨夜来信》',
    type: '短剧',
    chapters: 12,
    scenes: 42,
    dialogues: 218,
    schemaStatus: '校验通过',
    status: '已完成',
    updatedAt: '昨天 21:40',
    tags: ['悬疑', '反转', '竖屏'],
  },
  {
    id: 'script-003',
    title: '《旧城咖啡馆》舞台稿',
    sourceNovel: '《旧城咖啡馆》',
    type: '话剧',
    chapters: 8,
    scenes: 18,
    dialogues: 96,
    schemaStatus: '字段缺失',
    status: '校验异常',
    updatedAt: '3 天前',
    tags: ['现实题材', '舞台调度', '双人戏'],
  },
  {
    id: 'script-004',
    title: '《玻璃海岸》分镜草案',
    sourceNovel: '《玻璃海岸》',
    type: '分镜剧本',
    chapters: 6,
    scenes: 31,
    dialogues: 74,
    schemaStatus: '校验通过',
    status: '草稿',
    updatedAt: '5 天前',
    tags: ['镜头设计', '海边', '青春'],
  },
  {
    id: 'script-005',
    title: '《月台三号》广播剧',
    sourceNovel: '《月台三号》',
    type: '广播剧',
    chapters: 4,
    scenes: 16,
    dialogues: 132,
    schemaStatus: '校验通过',
    status: '已导出',
    updatedAt: '上周五',
    tags: ['音效', '旁白', '治愈'],
  },
  {
    id: 'script-006',
    title: '《雾中塔》电影分场稿',
    sourceNovel: '《雾中塔》',
    type: '影视剧',
    chapters: 10,
    scenes: 37,
    dialogues: 189,
    schemaStatus: '校验通过',
    status: '已导出',
    updatedAt: '上周一',
    tags: ['奇幻', '冒险', '电影'],
  },
]

export const productHelpDocs = {
  brief: {
    eyebrow: 'AI小说转剧本工具帮助文档',
    title: 'AI 小说转剧本工具',
    description:
      'AI小说转剧本工具是一款面向小说作者、编剧和内容创作者的辅助创作工具。系统可以将小说文本自动解析，并转换为结构化的 YAML 剧本初稿。本工具生成的剧本不是最终成稿，而是可编辑、可修改、可继续打磨的剧本初稿。',
  },
  intro: [
    '通过该工具，作者可以快速完成从小说文本到剧本结构的初步改编，包括章节识别、人物提取、场景拆分、对白生成、动作描写整理和剧本预览导出等流程。',
    '工具的核心目标是降低小说改编门槛，让作者先获得结构清晰的初稿，再继续进行创作判断、对白润色和节奏调整。',
  ],
  requirements: [
    '支持导入或粘贴小说文本。',
    '自动识别章节结构，并整理可用于后续解析的内容。',
    '从小说中提取人物、场景、剧情事件、对白、动作描写和人物关系。',
    '根据解析结果和模板规则生成结构化 YAML 剧本。',
    '支持在线编辑、Schema 校验、剧本预览与 YAML、TXT、Markdown、PDF 导出。',
  ],
  workflow: [
    { step: '01', title: '导入小说文本', detail: '用户可以上传小说文件，或直接粘贴小说正文内容。' },
    { step: '02', title: '章节自动识别', detail: '系统会自动识别小说中的章节结构，并整理为后续 AI 解析可使用的输入。' },
    { step: '03', title: 'AI 内容解析', detail: '系统会从小说中提取人物、场景、剧情事件、对白、动作描写和人物关系。' },
    { step: '04', title: '选择剧本模板', detail: '用户可以选择影视剧、短剧、话剧、分镜剧本或广播剧等不同生成模板。' },
    { step: '05', title: '生成 YAML 剧本', detail: '系统根据解析结果和模板规则生成结构化 YAML 剧本。' },
    { step: '06', title: '在线编辑与校验', detail: '用户可以在 YAML 编辑器中修改内容，并使用 Schema 校验功能检查格式是否正确。' },
    { step: '07', title: '剧本预览与导出', detail: '用户可以将 YAML 剧本转换为可读的剧本文本，并导出为 YAML、TXT、Markdown 或 PDF 文件。' },
  ],
  importMethods: ['上传 .txt 文件', '上传 .docx 文件', '直接粘贴小说正文', '从示例小说导入'],
  chapterPatterns: ['第一章', '第1章', 'Chapter 1', '第一回', '第一节'],
  analysisSections: [
    {
      title: '人物识别',
      description: '系统会识别小说中的主要人物和配角，并尽量提取人物身份、性格、关系和出场章节。',
      example: ['characters:', '  - id: char_001', '    name: 林默', '    role: 主角', '    description: 冷静、谨慎的青年'],
    },
    {
      title: '场景识别',
      description: '系统会根据小说中的地点、时间和情节变化拆分场景。',
      example: ['scenes:', '  - id: sc_001', '    title: 教室里的相遇', '    location: 教室', '    time: 上午'],
    },
    {
      title: '剧情事件提取',
      description: '系统会提取每章中的关键事件，用于辅助生成剧本结构。',
      example: ['events:', '  - 林默进入教室', '  - 苏晴发现异常', '  - 两人开始调查真相'],
    },
    {
      title: '对白与动作提取',
      description: '系统会区分小说中的人物对白和动作描写。',
      example: ['actions:', '  - 林默推开教室门，环顾四周。', '', 'dialogues:', '  - character: 林默', '    emotion: 疑惑', '    line: 这里怎么一个人都没有？'],
    },
  ],
  schemaFields: [
    { name: 'script', type: 'object', required: true, description: '剧本根节点。' },
    { name: 'title', type: 'string', required: true, description: '剧本标题。' },
    { name: 'original_novel', type: 'string', required: false, description: '原小说名称。' },
    { name: 'author', type: 'string', required: false, description: '作者或生成者。' },
    { name: 'version', type: 'string', required: false, description: '剧本版本。' },
    { name: 'format', type: 'string', required: true, description: '剧本类型，如影视剧、短剧、话剧。' },
    { name: 'total_chapters', type: 'number', required: true, description: '原小说章节数量。' },
    { name: 'characters', type: 'array', required: true, description: '人物列表。' },
    { name: 'chapters', type: 'array', required: true, description: '章节列表。' },
    { name: 'scenes', type: 'array', required: true, description: '场景列表。' },
    { name: 'actions', type: 'array', required: false, description: '动作描写。' },
    { name: 'dialogues', type: 'array', required: false, description: '人物对白。' },
    { name: 'emotion', type: 'string', required: false, description: '人物说话情绪。' },
    { name: 'line', type: 'string', required: true, description: '台词内容。' },
  ],
  requiredFields: ['script', 'title', 'format', 'total_chapters', 'characters', 'chapters', 'scenes', 'line'],
  exampleYaml: [
    'script:',
    '  title: "星辰之下"',
    '  original_novel: "星辰之下"',
    '  author: "AI Script Studio"',
    '  version: "1.0"',
    '  format: "影视剧"',
    '  total_chapters: 5',
    '',
    '  characters:',
    '    - id: char_001',
    '      name: 林默',
    '      role: 主角',
    '      gender: 男',
    '      age: 24',
    '      description: 怀揣音乐梦想的年轻人',
    '',
    '  chapters:',
    '    - id: ch_001',
    '      title: 初入城市',
    '      summary: 林默来到大城市，开始新的生活与挑战',
    '      scenes:',
    '        - id: sc_001_001',
    '          title: 地铁站相遇',
    '          location: 地铁站',
    '          time: 傍晚',
    '          characters:',
    '            - char_001',
    '            - char_002',
    '          actions:',
    '            - 林默拖着行李箱走出地铁站。',
    '          dialogues:',
    '            - character: 林默',
    '              emotion: 自言自语',
    '              line: 这座城市，真的能实现我的梦想吗？',
  ],
  designReasons: [
    '本 Schema 按照“剧本创作流程”进行设计。',
    '首先，小说原文通常以章节为单位组织，因此 Schema 保留 chapters 字段，用于对应小说原始章节，方便作者追溯剧本内容来源。',
    '其次，剧本创作通常以场景为基本单位，因此每个章节下设计 scenes 字段，用于描述具体场景，包括场景标题、地点、时间、出场人物等信息。',
    '再次，剧本的核心内容由人物、动作和对白组成，因此 Schema 中设计了 characters、actions 和 dialogues 字段，让小说叙述内容被拆分为更适合剧本表达的结构。',
    '最后，为了方便后续编辑、校验和导出，Schema 采用统一字段命名和分层结构，使前端可以根据 YAML 内容生成剧本预览、格式检查和多格式导出文件。',
  ],
  faq: [
    { question: '生成的剧本可以直接使用吗？', answer: '生成结果是剧本初稿，不是最终成稿。作者可以在 YAML 编辑器中继续修改对白、场景、动作和剧情内容。' },
    { question: 'YAML 格式错误怎么办？', answer: '可以点击“校验”按钮，系统会检查 YAML 缩进、字段缺失和结构错误，并提示具体问题。' },
    { question: '可以导出哪些格式？', answer: '系统支持导出 YAML、TXT、Markdown 和 PDF 格式。其中 YAML 适合后续程序读取和编辑，TXT、Markdown、PDF 适合阅读、分享和归档。' },
    { question: '模板中心有什么作用？', answer: '模板中心用于选择不同的剧本生成规则。例如，影视剧模板更适合长篇改编，短剧模板更强调快节奏和冲突，分镜模板会生成镜头、画面和转场信息。' },
    { question: '剧本库有什么作用？', answer: '剧本库用于管理已生成的剧本草稿和版本。用户可以在剧本库中继续编辑、预览、导出或复制已有剧本。' },
  ],
}

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
