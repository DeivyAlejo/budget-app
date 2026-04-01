import axios from 'axios'

const host = typeof window === 'undefined' ? 'localhost' : window.location.hostname
const fallbackApiBaseUrl = `http://${host}:8000/api/v1`

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || fallbackApiBaseUrl

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

let unauthorizedHandler: (() => void) | null = null
let redirectingToLogin = false

export const setUnauthorizedHandler = (handler: (() => void) | null) => {
  unauthorizedHandler = handler
}

export const setAuthToken = (token: string | null) => {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete apiClient.defaults.headers.common.Authorization
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      setAuthToken(null)
      unauthorizedHandler?.()

      if (
        typeof window !== 'undefined' &&
        window.location.pathname !== '/login' &&
        !redirectingToLogin
      ) {
        redirectingToLogin = true
        window.location.assign('/login')
      }
    }

    return Promise.reject(error)
  },
)
