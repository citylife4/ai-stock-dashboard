import { useState, useEffect } from 'react'
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, Clock } from 'lucide-react'
import './App.css'
import StockCard from './components/StockCard'
import { fetchDashboard, refreshDashboard } from './services/api'

function App() {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)

  const loadDashboard = async () => {
    try {
      setError(null)
      const data = await fetchDashboard()
      setDashboardData(data)
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error('Error loading dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      setError(null)
      await refreshDashboard()
      // Wait a moment for the backend to process
      setTimeout(() => {
        loadDashboard()
        setRefreshing(false)
      }, 2000)
    } catch (err) {
      setError('Failed to refresh dashboard')
      setRefreshing(false)
      console.error('Error refreshing dashboard:', err)
    }
  }

  useEffect(() => {
    loadDashboard()
    // Auto-refresh every 5 minutes
    const interval = setInterval(loadDashboard, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const formatLastUpdated = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  if (loading) {
    return (
      <div className="app">
        <div className="loading-container">
          <RefreshCw className="loading-spinner" />
          <p>Loading AI Stock Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>
            <TrendingUp className="header-icon" />
            AI Stock Dashboard
          </h1>
          <div className="header-actions">
            <div className="last-updated">
              <Clock size={16} />
              <span>Updated: {dashboardData?.last_updated ? formatLastUpdated(dashboardData.last_updated) : 'Never'}</span>
            </div>
            <button 
              onClick={handleRefresh} 
              disabled={refreshing}
              className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
            >
              <RefreshCw className={refreshing ? 'spinning' : ''} size={16} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        {error && (
          <div className="error-message">
            <p>{error}</p>
            <button onClick={loadDashboard}>Try Again</button>
          </div>
        )}

        {dashboardData && (
          <>
            <div className="dashboard-stats">
              <div className="stat-card">
                <DollarSign size={20} />
                <div>
                  <h3>Total Stocks</h3>
                  <p>{dashboardData.total_stocks}</p>
                </div>
              </div>
              <div className="stat-card">
                <TrendingUp size={20} />
                <div>
                  <h3>Top Score</h3>
                  <p>{dashboardData.stocks[0]?.ai_analysis.score || 'N/A'}</p>
                </div>
              </div>
              <div className="stat-card">
                <TrendingDown size={20} />
                <div>
                  <h3>Lowest Score</h3>
                  <p>{dashboardData.stocks[dashboardData.stocks.length - 1]?.ai_analysis.score || 'N/A'}</p>
                </div>
              </div>
            </div>

            <div className="stocks-grid">
              {dashboardData.stocks.map((stockAnalysis, index) => (
                <StockCard 
                  key={stockAnalysis.stock_data.symbol} 
                  stockAnalysis={stockAnalysis}
                  rank={index + 1}
                />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App
