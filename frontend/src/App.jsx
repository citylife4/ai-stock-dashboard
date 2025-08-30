import { useState, useEffect, useRef } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom'
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, Clock, Settings, User, LogOut, List } from 'lucide-react'
import './App.css'
import StockCard from './components/StockCard'
import AdminDashboard from './components/AdminDashboard'
import UserAuth from './components/UserAuth'
import UserStockManager from './components/UserStockManager'
import Welcome from './components/Welcome'
import Header from './components/Header'

import { fetchDashboard, refreshDashboard, getStatus, initializeAuth, getAuthToken, initializeUserAuth, getCurrentUser, logout } from './services/api'

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [updateStatus, setUpdateStatus] = useState(null)
  const [user, setUser] = useState(null)
  const [showStockManager, setShowStockManager] = useState(false)
  const [lastDashboardLoad, setLastDashboardLoad] = useState(0)
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(false)
  const previousUserRef = useRef(null)
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
    console.log('User login handler called with:', userData)
    setUser(userData)
    // Force dashboard reload after login
    setLastDashboardLoad(0)
    setTimeout(() => {
      loadDashboard(true) // Force load
    }, 200) // Give time for user state to settle
  }

  // Debug effect to watch user state changes
  useEffect(() => {
    console.log('User state changed:', user, 'Previous:', previousUserRef.current)
    
    // Reload dashboard when user transitions from null to logged in
    const wasLoggedOut = previousUserRef.current === null
    const isNowLoggedIn = user !== null
    
    if (wasLoggedOut && isNowLoggedIn) {
      console.log('User logged in, reloading dashboard for authenticated user')
      // Reset debounce timer to allow immediate reload
      setLastDashboardLoad(0)
      // Force immediate dashboard load for login
      setTimeout(() => {
        loadDashboard(true) // Force load
      }, 100) // Small delay to ensure state is settled
    } else if (!wasLoggedOut && !isNowLoggedIn) {
      console.log('User logged out, reloading dashboard for non-authenticated view')
      setLastDashboardLoad(0)
      setTimeout(() => {
        loadDashboard(true) // Force load
      }, 100)
    }
    
    // Update ref for next comparison
    previousUserRef.current = user
  }, [user])

  const handleUserLogout = () => {
    logout()
    setUser(null)
    // Reset debounce timer and reload dashboard for non-authenticated view
    setLastDashboardLoad(0)
    loadDashboard(true) // Force load
  }

  const loadDashboard = async (forceLoad = false) => {
    try {
      // Prevent overlapping requests
      if (isLoadingDashboard) {
        console.log('Dashboard load skipped - already loading')
        return
      }
      
      // Prevent rapid successive calls (debounce) unless forced
      const now = Date.now()
      if (!forceLoad && now - lastDashboardLoad < 5000) { // 5 second minimum between calls
        console.log('Dashboard load debounced - last call was', (now - lastDashboardLoad), 'ms ago')
        return
      }
      
      setIsLoadingDashboard(true)
      setLastDashboardLoad(now)
      
      console.log('Loading dashboard at', new Date().toISOString(), forceLoad ? '(forced)' : '')
      setError(null)
      const data = await fetchDashboard()
      setDashboardData(data)
      console.log('Dashboard loaded successfully')
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error('Error loading dashboard:', err)
    } finally {
      setLoading(false)
      setIsLoadingDashboard(false)
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
  }, []) // Only load once on mount

  // Separate effect for auto-refresh with dynamic intervals
  useEffect(() => {
    if (!user || !dashboardData) return // Don't set up interval until we have user and initial data
    
    const hasPendingAnalysis = dashboardData.errors && 
        dashboardData.errors.some(error => error.type === 'analysis_missing')
    
    const refreshInterval = hasPendingAnalysis ? 30 * 1000 : 5 * 60 * 1000 // 30 seconds vs 5 minutes
    
    console.log('Setting up auto-refresh interval:', refreshInterval / 1000, 'seconds, pending analysis:', hasPendingAnalysis)
    
    const interval = setInterval(() => {
      // Only auto-refresh if user is still on the page and logged in
      if (document.visibilityState === 'visible' && user && !isLoadingDashboard) {
        console.log('Auto-refreshing dashboard')
        loadDashboard()
      } else {
        console.log('Skipping auto-refresh - page not visible, user not logged in, or already loading')
      }
    }, refreshInterval)
    
    return () => {
      console.log('Clearing auto-refresh interval')
      clearInterval(interval)
    }
  }, [dashboardData?.errors?.length, user?.id]) // Only depend on error count and user ID

  // Poll for update status when refreshing
  useEffect(() => {
    if (refreshing || updateStatus?.update_in_progress) {
      const statusInterval = setInterval(checkUpdateStatus, 2000) // Check every 2 seconds
      return () => clearInterval(statusInterval)
    }
  }, [refreshing, updateStatus?.update_in_progress])

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
        <Header 
          user={user}
          onLogin={handleUserLogin}
          onLogout={handleUserLogout}
          dashboardData={dashboardData}
          onRefresh={handleRefresh}
          refreshing={refreshing}
          updateStatus={updateStatus}
        />
        <Welcome 
          dashboardData={dashboardData} 
          onShowAuth={() => {/* Auth handled by Header */}} 
        />
      </div>
    )
  }

  // Show authenticated dashboard
  return (
    <div className="app">
      <Header 
        user={user}
        onLogin={handleUserLogin}
        onLogout={handleUserLogout}
        dashboardData={dashboardData}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        updateStatus={updateStatus}
      />

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
                <h3>⚠️ Stock Analysis Status</h3>
                <div className="error-list">
                  {dashboardData.errors.map((apiError, index) => (
                    <div key={index} className={`error-item ${apiError.type}`}>
                      <strong>{apiError.symbol}:</strong> {apiError.message}
                      {apiError.type === 'analysis_missing' && (
                        <div className="loading-indicator">
                          <RefreshCw className="spinning" size={16} />
                          <span>Analyzing...</span>
                        </div>
                      )}
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
                  <h3>Analyzed</h3>
                  <p>{dashboardData.stocks ? dashboardData.stocks.length : 0}</p>
                </div>
              </div>
              <div className="stat-card">
                <TrendingDown size={20} />
                <div>
                  <h3>Pending</h3>
                  <p>{dashboardData.total_stocks - (dashboardData.stocks ? dashboardData.stocks.length : 0)}</p>
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
              
              {/* Show placeholder cards for stocks being analyzed */}
              {dashboardData.errors && dashboardData.errors
                .filter(error => error.type === 'analysis_missing')
                .map((error, index) => (
                  <div key={`pending-${error.symbol}`} className="stock-card pending">
                    <div className="stock-header">
                      <h3>{error.symbol}</h3>
                      <div className="loading-indicator">
                        <RefreshCw className="spinning" size={20} />
                      </div>
                    </div>
                    <div className="stock-content">
                      <p>Analysis in progress...</p>
                      <p className="analysis-note">This usually takes 30-60 seconds</p>
                    </div>
                  </div>
                ))
              }
            </div>
          </>
        )}
      </main>

      {/* Stock Manager Modal */}
      {showStockManager && (
        <UserStockManager 
          user={user}
          onClose={() => {
            setShowStockManager(false)
            loadDashboard() // Reload dashboard after stock changes
          }}
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
    return (
      <div className="app">
        <Header 
          user={null}
          onLogin={() => {}}
          onLogout={handleLogout}
        />
        <div>Loading...</div>
      </div>
    )
  }

  return (
    <div className="app">
      <Header 
        user={user}
        onLogin={() => {}}
        onLogout={handleLogout}
      />
      <AdminDashboard onLogout={handleLogout} />
    </div>
  )
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
