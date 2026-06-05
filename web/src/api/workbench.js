import { http } from './http'

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
