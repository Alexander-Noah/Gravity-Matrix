export const appRoutes = [
  {
    id: 'auth',
    path: '/auth',
    title: '登录注册',
    description: '登录或创建账号，进入 AI 小说转剧本工作台',
  },
  {
    id: 'workbench',
    path: '/workbench',
    title: 'AI小说转剧本工作台',
    description: '按流程完成小说导入、AI解析、剧本编辑与导出',
  },
  {
    id: 'templates',
    path: '/templates',
    title: '模板中心',
    description: '选择剧本生成规则模板，统一后续 YAML 结构、字段和场景组织方式',
  },
  {
    id: 'library',
    path: '/library',
    title: '剧本库',
    description: '管理已生成的剧本草稿、版本和导出文件',
  },
  {
    id: 'help',
    path: '/help',
    title: '帮助文档',
    description: 'AI 小说转剧本流程与剧本 YAML Schema 定义',
  },
]

export const defaultRoute = appRoutes[0]

export const getRouteById = (id) => appRoutes.find((route) => route.id === id) || defaultRoute

export const getRouteByPath = (path) => appRoutes.find((route) => route.path === path) || defaultRoute
