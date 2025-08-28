import axios from 'axios'

// Use relative URL for API calls - nginx will proxy to backend
const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 100000,
})

// Auth token management
let authToken = null

export const setAuthToken = (token) => {
  authToken = token
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

export const getAuthToken = () => authToken

export const fetchDashboard = async () => {
  try {
    const response = await api.get('/dashboard')
    return response.data
  } catch (error) {
    console.error('Error fetching dashboard:', error)
    throw error
  }
}

export const refreshDashboard = async () => {
  try {
    const response = await api.post('/refresh')
    return response.data
  } catch (error) {
    console.error('Error refreshing dashboard:', error)
    throw error
  }
}

export const getStatus = async () => {
  try {
    const response = await api.get('/status')
    return response.data
  } catch (error) {
    console.error('Error fetching status:', error)
    throw error
  }
}

export const getStockAnalysis = async (symbol) => {
  try {
    const response = await api.get(`/stocks/${symbol}`)
    return response.data
  } catch (error) {
    console.error(`Error fetching stock ${symbol}:`, error)
    throw error
  }
}

// Admin API functions
export const adminLogin = async (username, password) => {
  try {
    const response = await api.post('/admin/login', { username, password })
    const { access_token } = response.data
    setAuthToken(access_token)
    localStorage.setItem('adminToken', access_token)
    return response.data
  } catch (error) {
    console.error('Error logging in:', error)
    throw error
  }
}

export const adminLogout = () => {
  setAuthToken(null)
  localStorage.removeItem('adminToken')
}

export const initializeAuth = () => {
  const token = localStorage.getItem('adminToken')
  if (token) {
    setAuthToken(token)
  }
  return token
}

export const getStockList = async () => {
  try {
    const response = await api.get('/admin/stocks')
    return response.data
  } catch (error) {
    console.error('Error fetching stock list:', error)
    throw error
  }
}

export const addStock = async (symbol) => {
  try {
    const response = await api.post('/admin/stocks', { symbol })
    return response.data
  } catch (error) {
    console.error('Error adding stock:', error)
    throw error
  }
}

export const removeStock = async (symbol) => {
  try {
    const response = await api.delete(`/admin/stocks/${symbol}`)
    return response.data
  } catch (error) {
    console.error('Error removing stock:', error)
    throw error
  }
}

export const getPrompts = async () => {
  try {
    const response = await api.get('/admin/prompts')
    return response.data
  } catch (error) {
    console.error('Error fetching prompts:', error)
    throw error
  }
}

export const updatePrompts = async (aiAnalysisPrompt) => {
  try {
    const response = await api.put('/admin/prompts', { ai_analysis_prompt: aiAnalysisPrompt })
    return response.data
  } catch (error) {
    console.error('Error updating prompts:', error)
    throw error
  }
}

export const getAuditLogs = async (limit = 100) => {
  try {
    const response = await api.get(`/admin/logs?limit=${limit}`)
    return response.data
  } catch (error) {
    console.error('Error fetching audit logs:', error)
    throw error
  }
}

export const getConfig = async () => {
  try {
    const response = await api.get('/admin/config')
    return response.data
  } catch (error) {
    console.error('Error fetching config:', error)
    throw error
  }
}

export const updateConfig = async (config) => {
  try {
    const response = await api.put('/admin/config', config)
    return response.data
  } catch (error) {
    console.error('Error updating config:', error)
    throw error
  }
}

export const forceRefresh = async () => {
  try {
    const response = await api.post('/admin/refresh')
    return response.data
  } catch (error) {
    console.error('Error forcing refresh:', error)
    throw error
  }
}