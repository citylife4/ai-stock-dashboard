import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom'
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, Clock, Settings, User, LogOut } from 'lucide-react'
import './App.css'
import StockCard from './components/StockCard'
import AdminLogin from './components/AdminLogin'
import AdminDashboard from './components/AdminDashboard'
import UserAuth from './components/UserAuth'
import { fetchDashboard, refreshDashboard, adminLogin, initializeAuth, getAuthToken } from './services/api'

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [user, setUser] = useState(null)
  const [showUserAuth, setShowUserAuth] = useState(false)
  const navigate = useNavigate()
  const isAuthenticated = !!getAuthToken()

  useEffect(() => {
    // Check for existing user session
    const userData = localStorage.getItem('userData')
    if (userData) {
      setUser(JSON.parse(userData))
    }
  }, [])

  const handleUserLogin = (userData) => {
    setUser(userData)
  }

  const handleUserLogout = () => {
    localStorage.removeItem('userToken')
    localStorage.removeItem('userData')
    setUser(null)
    loadDashboard() // Reload dashboard without user context
  }

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
            
            {user ? (
              <div className="user-menu">
                <div className="user-info">
                  <User size={16} />
                  <span>{user.username}</span>
                  <span className="subscription-badge">{user.subscription_tier}</span>
                  <span className="stock-count">{dashboardData?.total_stocks || 0}/{user.max_stocks}</span>
                </div>
                <button onClick={handleUserLogout} className="logout-btn">
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            ) : (
              <button 
                onClick={() => setShowUserAuth(true)}
                className="login-btn"
              >
                <User size={16} />
                Login / Sign Up
              </button>
            )}
            
            {isAuthenticated ? (
              <button 
                onClick={() => navigate('/admin')}
                className="admin-btn"
              >
                <Settings size={16} />
                Admin
              </button>
            ) : (
              <Link to="/admin/login" className="admin-link">
                <Settings size={16} />
                Admin
              </Link>
            )}
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
            {/* Show API errors if any */}
            {dashboardData.errors && dashboardData.errors.length > 0 && (
              <div className="api-errors">
                <h3>⚠️ API Issues Detected</h3>
                <div className="error-list">
                  {dashboardData.errors.map((apiError, index) => (
                    <div key={index} className={`error-item ${apiError.type}`}>
                      <strong>{apiError.symbol}:</strong> {apiError.message}
                    </div>
                  ))}
                </div>
              </div>
            )}

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
                  <p>{dashboardData.stocks && dashboardData.stocks.length > 0 ? Math.round(dashboardData.stocks[0].ai_analysis.average_score) : 'N/A'}</p>
                </div>
              </div>
              <div className="stat-card">
                <TrendingDown size={20} />
                <div>
                  <h3>Lowest Score</h3>
                  <p>{dashboardData.stocks && dashboardData.stocks.length > 0 ? Math.round(dashboardData.stocks[dashboardData.stocks.length - 1].ai_analysis.average_score) : 'N/A'}</p>
                </div>
              </div>
              {user && (
                <div className="stat-card subscription-card">
                  <User size={20} />
                  <div>
                    <h3>Plan</h3>
                    <p>{user.subscription_tier.toUpperCase()}</p>
                  </div>
                </div>
              )}
            </div>

            <div className="stocks-grid">
              {dashboardData.stocks && dashboardData.stocks.map((stockAnalysis, index) => (
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
      
      {showUserAuth && (
        <UserAuth 
          onLogin={handleUserLogin}
          onClose={() => setShowUserAuth(false)}
        />
      )}
    </div>
  )
}

function AdminLoginPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleLogin = async (username, password) => {
    setLoading(true)
    setError(null)

    try {
      await adminLogin(username, password)
      navigate('/admin')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return <AdminLogin onLogin={handleLogin} error={error} loading={loading} />
}

function AdminPage() {
  const navigate = useNavigate()

  const handleLogout = () => {
    navigate('/')
  }

  return <AdminDashboard onLogout={handleLogout} />
}

function App() {
  useEffect(() => {
    // Initialize authentication on app start
    initializeAuth()
  }, [])

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Router>
  )
}

export default App
