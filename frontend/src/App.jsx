import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom'
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, Clock, Settings, User, LogOut, List } from 'lucide-react'
import './App.css'
import StockCard from './components/StockCard'
import AdminDashboard from './components/AdminDashboard'
import UserAuth from './components/UserAuth'
import UserStockManager from './components/UserStockManager'
import Welcome from './components/Welcome'

import { fetchDashboard, refreshDashboard, getStatus, initializeAuth, getAuthToken, initializeUserAuth, getCurrentUser, logout } from './services/api'

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [updateStatus, setUpdateStatus] = useState(null)
  const [user, setUser] = useState(null)
  const [showUserAuth, setShowUserAuth] = useState(false)
  const [showStockManager, setShowStockManager] = useState(false)
  const navigate = useNavigate()
  const isAuthenticated = !!getAuthToken()

  useEffect(() => {
    // Check for existing user session
    initializeUserAuth()
    const userData = getCurrentUser()
    console.log('Initial user data from localStorage:', userData)
    if (userData) {
      setUser(userData)
    }
  }, [])

  const handleUserLogin = (userData) => {
    console.log('User login data:', userData)
    setUser(userData)
  }

  // Debug effect to watch user state changes
  useEffect(() => {
    console.log('User state changed:', user)
  }, [user])

  const handleUserLogout = () => {
    logout()
    setUser(null)
    loadDashboard() // Reload dashboard without user context
  }

  // Check if current user is admin
  const isUserAdmin = () => {
    console.log('Checking admin status:', { user, is_admin: user?.is_admin, username: user?.username })
    return user && (user.is_admin === true || user.username === 'admin')
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

  const checkUpdateStatus = async () => {
    try {
      const status = await getStatus()
      setUpdateStatus(status)
      
      // If an update was in progress and now it's complete, reload dashboard
      if (refreshing && !status.update_in_progress) {
        setRefreshing(false)
        await loadDashboard()
      }
    } catch (err) {
      console.error('Error checking status:', err)
    }
  }

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      setError(null)
      const response = await refreshDashboard()
      
      if (response.status === 'in_progress') {
        // Update was already running
        setUpdateStatus({ update_in_progress: true })
      } else {
        // New update started
        setUpdateStatus({ update_in_progress: true })
      }
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

  // Poll for update status when refreshing
  useEffect(() => {
    if (refreshing || updateStatus?.update_in_progress) {
      const statusInterval = setInterval(checkUpdateStatus, 2000) // Check every 2 seconds
      return () => clearInterval(statusInterval)
    }
  }, [refreshing, updateStatus?.update_in_progress])

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

  // Show welcome page for unauthenticated users
  if (!user) {
    return (
      <div className="app">
        <Welcome 
          dashboardData={dashboardData} 
          onShowAuth={() => setShowUserAuth(true)} 
        />
        
        {showUserAuth && (
          <UserAuth 
            onLogin={handleUserLogin}
            onClose={() => setShowUserAuth(false)}
          />
        )}
      </div>
    )
  }

  // Show authenticated dashboard
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>
            <TrendingUp className="header-icon" />
            AI Stock Dashboard
          </h1>
          <div className="header-actions">
            <button 
              onClick={handleRefresh}
              className={`refresh-btn ${refreshing || updateStatus?.update_in_progress ? 'refreshing' : ''}`}
              disabled={refreshing || updateStatus?.update_in_progress}
            >
              <RefreshCw size={16} className={refreshing || updateStatus?.update_in_progress ? 'spinning' : ''} />
              {refreshing || updateStatus?.update_in_progress ? 'Updating...' : 'Refresh'}
            </button>
            
            <div className="last-updated">
              <Clock size={16} />
              <span>Updated: {dashboardData?.last_updated ? formatLastUpdated(dashboardData.last_updated) : 'Never'}</span>
            </div>
            <div className="user-menu">
              <div className="user-info">
                <User size={16} />
                <span>{user.username}</span>
                <span className="subscription-badge">{user.subscription_tier}</span>
                <span className="stock-count">{dashboardData?.total_stocks || 0}/{user.max_stocks}</span>
              </div>
              <button 
                onClick={() => setShowStockManager(true)}
                className="manage-stocks-btn"
                title="Manage your stocks"
              >
                <List size={16} />
                Manage Stocks
              </button>
              <button onClick={handleUserLogout} className="logout-btn">
                <LogOut size={16} />
                Logout
              </button>
            </div>
            {console.log('Render time admin check:', { user, isAdmin: isUserAdmin() })}
            {isUserAdmin() ? (
              <button 
                onClick={() => navigate('/admin')}
                className="admin-btn"
              >
                <Settings size={16} />
                Admin
              </button>
            ) : null}
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

        {/* Show empty state if user has no stocks */}
        {dashboardData && dashboardData.total_stocks === 0 && !error && (
          <div className="empty-dashboard">
            <div className="empty-state">
              <TrendingUp size={64} className="empty-icon" />
              <h2>Start Your Investment Journey</h2>
              <p>You haven't added any stocks to track yet. Add some stocks to see AI-powered analysis and insights.</p>
              <button 
                onClick={() => setShowStockManager(true)}
                className="add-stocks-btn"
              >
                <List size={16} />
                Add Your First Stock
              </button>
            </div>
          </div>
        )}

        {dashboardData && dashboardData.total_stocks > 0 && (
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
              <div className="stat-card subscription-card">
                <User size={20} />
                <div>
                  <h3>Plan</h3>
                  <p>{user.subscription_tier.toUpperCase()}</p>
                </div>
              </div>
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
      
      {showStockManager && user && (
        <UserStockManager 
          user={user}
          onClose={() => setShowStockManager(false)}
        />
      )}
    </div>
  )
}

function AdminPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)

  // Check if user is logged in and is admin
  useEffect(() => {
    const checkAdminAccess = async () => {
      try {
        const currentUser = await getCurrentUser()
        if (!currentUser || !currentUser.is_admin) {
          // Not an admin, redirect to home
          navigate('/')
          return
        }
        setUser(currentUser)
      } catch (error) {
        // Not logged in or invalid token, redirect to home
        navigate('/')
      }
    }

    checkAdminAccess()
  }, [navigate])

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  // Show loading while checking admin access
  if (!user) {
    return <div>Loading...</div>
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
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Router>
  )
}

export default App
