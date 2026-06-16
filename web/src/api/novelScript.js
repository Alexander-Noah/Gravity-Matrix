import { http } from './http'

export const createNovel = async ({ title, content }) => {
  const response = await http.post('/novels', { title, content })
  return response.data
}

export const extractCharacters = async (novelId) => {
  const response = await http.post(`/novels/${novelId}/extract-characters`)
  return response.data
}

export const saveCharacters = async (novelId, characters) => {
  const response = await http.put(`/novels/${novelId}/characters`, { characters })
  return response.data
}

export const extractScenes = async (novelId) => {
  const response = await http.post(`/novels/${novelId}/extract-scenes`)
  return response.data
}

export const saveScenes = async (novelId, scenes) => {
  const response = await http.put(`/novels/${novelId}/scenes`, { scenes })
  return response.data
}

export const generateSceneContent = async (sceneId) => {
  const response = await http.post(`/scenes/${sceneId}/generate-content`)
  return response.data
}

export const saveSceneContent = async (sceneId, content) => {
  const response = await http.put(`/scenes/${sceneId}/content`, { content })
  return response.data
}

export const generateNovelYaml = async (novelId) => {
  const response = await http.post(`/novels/${novelId}/generate-yaml`)
  return response.data
}

export const saveScriptYaml = async (scriptId, yaml) => {
  const response = await http.put(`/scripts/${scriptId}`, { yaml })
  return response.data
}

export const downloadScriptYaml = async (scriptId) => {
  const response = await http.get(`/scripts/${scriptId}/download`, {
    responseType: 'blob',
  })
  return response.data
}
