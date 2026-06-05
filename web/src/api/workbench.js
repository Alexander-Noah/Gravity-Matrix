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
