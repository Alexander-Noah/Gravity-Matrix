export const appRoutes = [
  {
    id: 'workbench',
    path: '/workbench',
    title: 'AI小说转剧本工作台',
    description: '按流程完成小说导入、AI解析、剧本编辑与导出',
  },
  {
    id: 'projects',
    path: '/projects',
    title: '我的项目',
    description: '集中管理小说改编项目和最近编辑记录',
  },
  {
    id: 'templates',
    path: '/templates',
    title: '模板中心',
    description: '管理可复用的剧本结构、场景模板和导出格式',
  },
  {
    id: 'library',
    path: '/library',
    title: '剧本库',
    description: '查看已生成、已导出和归档的剧本文档',
  },
  {
    id: 'help',
    path: '/help',
    title: '帮助文档',
    description: '查看工作台使用说明和常见问题',
  },
]

export const defaultRoute = appRoutes[0]

export const getRouteById = (id) => appRoutes.find((route) => route.id === id) || defaultRoute

export const getRouteByPath = (path) => appRoutes.find((route) => route.path === path) || defaultRoute
