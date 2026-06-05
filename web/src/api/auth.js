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

export const getAuthSession = () => ({
  token: localStorage.getItem(TOKEN_KEY),
  user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
})

export const clearAuthSession = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const register = async ({ name, email, password }) => {
  const response = await http.post('/auth/register', {
    name,
    email,
    password,
  })

  saveAuthSession(response.data)
  return response.data
}

export const login = async ({ email, password }) => {
  const response = await http.post('/auth/login', {
    email,
    password,
  })

  saveAuthSession(response.data)
  return response.data
}

export const fetchCurrentUser = async () => {
  const response = await http.get('/auth/me')

  if (response.data) {
    localStorage.setItem(USER_KEY, JSON.stringify(response.data))
  }

  return response.data
}
