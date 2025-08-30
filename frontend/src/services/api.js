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

// Error handling helper
const handleApiError = (error, context = '') => {
  console.error(`API Error ${context}:`, error)
  
  let errorMessage = 'An unexpected error occurred'
  let errorCode = 'UNKNOWN_ERROR'
  
  if (error.response) {
    // Server responded with error status
    const status = error.response.status
    const data = error.response.data
    
    errorCode = `HTTP_${status}`
    
    if (data && typeof data === 'object') {
      if (data.detail) {
        errorMessage = Array.isArray(data.detail) 
          ? data.detail.map(err => `${err.loc?.join('.')} - ${err.msg}`).join(', ')
          : data.detail
      } else if (data.message) {
        errorMessage = data.message
      } else if (data.error) {
        errorMessage = data.error
      }
    } else if (typeof data === 'string') {
      errorMessage = data
    }
    
    // Specific error messages for common status codes
    switch (status) {
      case 401:
        errorMessage = `Authentication failed: ${errorMessage}`
        break
      case 403:
        errorMessage = `Access denied: ${errorMessage}`
        break
      case 404:
        errorMessage = `Not found: ${errorMessage}`
        break
      case 422:
        errorMessage = `Validation error: ${errorMessage}`
        break
      case 503:
        errorMessage = `Service unavailable: ${errorMessage}`
        break
    }
  } else if (error.request) {
    // Network error
    errorMessage = 'Network error - unable to reach the server'
    errorCode = 'NETWORK_ERROR'
  } else if (error.code === 'ECONNABORTED') {
    // Timeout error
    errorMessage = 'Request timeout - the server took too long to respond'
    errorCode = 'TIMEOUT_ERROR'
  }
  
  // Create enhanced error object
  const enhancedError = new Error(errorMessage)
  enhancedError.code = errorCode
  enhancedError.status = error.response?.status
  enhancedError.originalError = error
  
  return enhancedError
}

export const fetchDashboard = async () => {
  try {
    const response = await api.get('/dashboard')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching dashboard')
  }
}

export const refreshDashboard = async () => {
  try {
    const response = await api.post('/refresh')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'refreshing dashboard')
  }
}

export const getStatus = async () => {
  try {
    const response = await api.get('/status')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching status')
  }
}

export const getStockAnalysis = async (symbol) => {
  try {
    const response = await api.get(`/stocks/${symbol}`)
    return response.data
  } catch (error) {
    throw handleApiError(error, `fetching stock ${symbol}`)
  }
}

// Admin API functions
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
    throw handleApiError(error, 'fetching stock list')
  }
}

export const addStock = async (symbol) => {
  try {
    const response = await api.post('/admin/stocks', { symbol })
    return response.data
  } catch (error) {
    throw handleApiError(error, `adding stock ${symbol}`)
  }
}

export const removeStock = async (symbol) => {
  try {
    const response = await api.delete(`/admin/stocks/${symbol}`)
    return response.data
  } catch (error) {
    throw handleApiError(error, `removing stock ${symbol}`)
  }
}

export const getPrompts = async () => {
  try {
    const response = await api.get('/admin/prompts')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching prompts')
  }
}

export const updatePrompts = async (aiAnalysisPrompt) => {
  try {
    const response = await api.put('/admin/prompts', { ai_analysis_prompt: aiAnalysisPrompt })
    return response.data
  } catch (error) {
    throw handleApiError(error, 'updating prompts')
  }
}

export const getAuditLogs = async (limit = 100) => {
  try {
    const response = await api.get(`/admin/logs?limit=${limit}`)
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching audit logs')
  }
}

export const getAnalysisLogs = async (limit = 100) => {
  try {
    const response = await api.get(`/admin/analysis-logs?limit=${limit}`)
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching analysis logs')
  }
}

export const getConfig = async () => {
  try {
    const response = await api.get('/admin/config')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching config')
  }
}

export const updateConfig = async (config) => {
  try {
    const response = await api.put('/admin/config', config)
    return response.data
  } catch (error) {
    throw handleApiError(error, 'updating config')
  }
}

export const forceRefresh = async () => {
  try {
    const response = await api.post('/admin/refresh')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'forcing refresh')
  }
}

// User management API functions
export const getUsers = async () => {
  try {
    const response = await api.get('/admin/users')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching users')
  }
}

export const updateUser = async (userId, updateData) => {
  try {
    const response = await api.put(`/admin/users/${userId}`, updateData)
    return response.data
  } catch (error) {
    throw handleApiError(error, `updating user ${userId}`)
  }
}

export const deleteUser = async (userId) => {
  try {
    const response = await api.delete(`/admin/users/${userId}`)
    return response.data
  } catch (error) {
    throw handleApiError(error, `deleting user ${userId}`)
  }
}

// User authentication API functions

export const getAdminUserStocks = async (userId) => {
  try {
    const response = await api.get(`/admin/users/${userId}/stocks`)
    return response.data
  } catch (error) {
    throw handleApiError(error, `fetching user stocks for ${userId}`)
  }
}

export const getAdminStats = async () => {
  try {
    const response = await api.get('/admin/stats')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching admin stats')
  }
}

// User authentication API functions
export const register = async (userData) => {
  try {
    const response = await api.post('/auth/register', userData)
    return response.data
  } catch (error) {
    throw handleApiError(error, 'registering user')
  }
}

export const login = async (credentials) => {
  try {
    const response = await api.post('/auth/login', credentials)
    const { access_token, user } = response.data
    setAuthToken(access_token)
    localStorage.setItem('userToken', access_token)
    localStorage.setItem('currentUser', JSON.stringify(user))
    return response.data
  } catch (error) {
    throw handleApiError(error, 'logging in user')
  }
}

export const logout = () => {
  setAuthToken(null)
  localStorage.removeItem('userToken')
  localStorage.removeItem('currentUser')
}

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('currentUser')
  return userStr ? JSON.parse(userStr) : null
}

export const initializeUserAuth = () => {
  const token = localStorage.getItem('userToken')
  if (token) {
    setAuthToken(token)
  }
  return token
}

export const addUserStock = async (symbol) => {
  try {
    const response = await api.post(`/auth/stocks/${symbol}`)
    return response.data
  } catch (error) {
    throw handleApiError(error, `adding user stock ${symbol}`)
  }
}

export const removeUserStock = async (symbol) => {
  try {
    const response = await api.delete(`/auth/stocks/${symbol}`)
    return response.data
  } catch (error) {
    throw handleApiError(error, `removing user stock ${symbol}`)
  }
}

export const getUserStocks = async () => {
  try {
    const response = await api.get('/auth/stocks')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching user stocks')
  }
}

export const getAvailableStocks = async () => {
  try {
    const response = await api.get('/available-stocks')
    return response.data
  } catch (error) {
    throw handleApiError(error, 'fetching available stocks')
  }
}