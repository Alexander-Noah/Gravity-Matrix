import { http } from './http'

const TOKEN_KEY = 'gm_auth_token'
const USER_KEY = 'gm_auth_user'

export const saveAuthSession = (payload) => {
  const token = payload.access_token || payload.token
  const user = payload.user

  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  }

  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

export const getAuthSession = () => {
  let user = null

  try {
    user = JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    localStorage.removeItem(USER_KEY)
  }

  return {
    token: localStorage.getItem(TOKEN_KEY),
    user,
  }
}

export const clearAuthSession = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

const createLocalDemoSession = ({ name, email }) => {
  const payload = {
    access_token: 'local-demo-session',
    token_type: 'bearer',
    user: {
      id: 'local-demo-user',
      name: name || email?.split('@')[0] || '创作者',
      email: email || 'demo@gravity-matrix.local',
      role: '本地演示用户',
      demo: true,
    },
  }

  saveAuthSession(payload)
  return payload
}

const shouldUseLocalDemoAuth = (error) =>
  error?.response?.status === 404 || error?.response?.status === 405

export const register = async ({ name, email, password }) => {
  try {
    const response = await http.post('/auth/register', {
      name,
      email,
      password,
    })

    saveAuthSession(response.data)
    return response.data
  } catch (error) {
    if (shouldUseLocalDemoAuth(error)) {
      return createLocalDemoSession({ name, email })
    }

    throw error
  }
}

export const login = async ({ email, password }) => {
  try {
    const response = await http.post('/auth/login', {
      email,
      password,
    })

    saveAuthSession(response.data)
    return response.data
  } catch (error) {
    if (shouldUseLocalDemoAuth(error)) {
      return createLocalDemoSession({ email })
    }

    throw error
  }
}

export const fetchCurrentUser = async () => {
  try {
    const response = await http.get('/auth/me')

    if (response.data) {
      localStorage.setItem(USER_KEY, JSON.stringify(response.data))
    }

    return response.data
  } catch (error) {
    if (shouldUseLocalDemoAuth(error)) {
      return getAuthSession().user
    }

    throw error
  }
}
