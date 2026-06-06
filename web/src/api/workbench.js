import { http } from './http'

export const listProjects = async ({ limit = 20, offset = 0 } = {}) => {
  const response = await http.get('/projects', {
    params: { limit, offset },
  })

  return response.data
}

export const createProject = async ({ title, author, chapters }) => {
  const response = await http.post('/projects', {
    title,
    author,
    chapters,
  })

  return response.data
}

export const startAnalysisJob = async (projectId) => {
  const response = await http.post(`/projects/${projectId}/analysis-jobs`)

  return response.data
}

export const getJob = async (jobId) => {
  const response = await http.get(`/jobs/${jobId}`)

  return response.data
}

export const getProjectAnalysis = async (projectId) => {
  const response = await http.get(`/projects/${projectId}/analysis`)

  return response.data
}

export const getProjectWorkbench = async (projectId) => {
  const response = await http.get(`/projects/${projectId}/workbench`)

  return response.data
}

export const startScriptJob = async (projectId) => {
  const response = await http.post(`/projects/${projectId}/script-jobs`)

  return response.data
}

export const rerunScriptJob = async (projectId) => {
  const response = await http.post(`/projects/${projectId}/script-jobs/rerun`)

  return response.data
}

export const getProjectScript = async (projectId) => {
  const response = await http.get(`/projects/${projectId}/script`)

  return response.data
}

export const validateProjectScript = async (projectId, yaml) => {
  const response = await http.post(`/projects/${projectId}/script/validate`, { yaml })

  return response.data
}

export const diagnoseProjectScriptDraft = async (projectId, yaml) => {
  const response = await http.post(`/projects/${projectId}/script/diagnosis`, { yaml })

  return response.data
}

export const getProjectReadiness = async (projectId) => {
  const response = await http.get(`/projects/${projectId}/readiness`)
  return response.data
}

export const saveProjectScript = async (projectId, yaml) => {
  const response = await http.put(`/projects/${projectId}/script`, { yaml })
  return response.data
}

export const updateGenerationSettings = async (projectId, settings) => {
  const response = await http.post(`/projects/${projectId}/generation-settings`, settings)
  return response.data
}

export const rerunAnalysisJob = async (projectId) => {
  const response = await http.post(`/projects/${projectId}/analysis-jobs/rerun`)
  return response.data
}

export const addProjectScene = async (projectId, sceneData) => {
  const response = await http.post(`/projects/${projectId}/scenes`, sceneData)
  return response.data
}

export const exportProjectMarkdown = async (projectId) => {
  const response = await http.get(`/projects/${projectId}/script/export/markdown`, {
    responseType: 'blob'
  })
  return response.data
}

export const exportProjectTxt = async (projectId) => {
  const response = await http.get(`/projects/${projectId}/script/export/txt`, {
    responseType: 'blob'
  })
  return response.data
}

export const deleteProject = async (projectId) => {
  const response = await http.delete(`/projects/${projectId}`)
  return response.data
}

export const getScriptTemplates = async () => {
  const response = await http.get('/templates')
  return response.data
}

export const updateProject = async (projectId, data) => {
  const response = await http.patch(`/projects/${projectId}`, data)
  return response.data
}

export const cloneProject = async (projectId) => {
  const response = await http.post(`/projects/${projectId}/clone`)
  return response.data
}

export const previewImport = async (data) => {
  const response = await http.post('/import/preview', data)
  return response.data
}

export const getProjectsDashboard = async () => {
  const response = await http.get('/projects/dashboard')
  return response.data
}

export const getScriptsLibrary = async () => {
  const response = await http.get('/scripts/library')
  return response.data
}
