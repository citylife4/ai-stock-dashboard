import axios from 'axios'

// Use relative URL for API calls - nginx will proxy to backend
const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 100000,
})

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