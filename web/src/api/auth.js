import { http } from './http'

const TOKEN_KEY = 'gm_auth_token'
const USER_KEY = 'gm_auth_user'
const ACTIVE_SESSION_KEY = 'gm_active_auth_session'

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

export const markSessionAuthenticated = () => {
  sessionStorage.setItem(ACTIVE_SESSION_KEY, '1')
}

export const hasActiveAuthSession = () => sessionStorage.getItem(ACTIVE_SESSION_KEY) === '1'

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
  sessionStorage.removeItem(ACTIVE_SESSION_KEY)
}

export const register = async ({ name, email, password }) => {
  const response = await http.post('/auth/register', {
    name,
    email,
    password,
  })

  saveAuthSession(response.data)
  markSessionAuthenticated()
  return response.data
}

export const login = async ({ email, password }) => {
  const response = await http.post('/auth/login', {
    email,
    password,
  })

  saveAuthSession(response.data)
  markSessionAuthenticated()
  return response.data
}

export const fetchCurrentUser = async () => {
  const response = await http.get('/auth/me')

  if (response.data) {
    localStorage.setItem(USER_KEY, JSON.stringify(response.data))
  }

  return response.data
}
