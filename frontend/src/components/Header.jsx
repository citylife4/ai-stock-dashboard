import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { 
  TrendingUp, 
  User, 
  LogOut, 
  Settings, 
  List, 
  Menu, 
  X,
  RefreshCw,
  Clock
} from 'lucide-react'
import UserAuth from './UserAuth'
import UserStockManager from './UserStockManager'
import './Header.css'

const Header = ({ 
  user, 
  onLogin, 
  onLogout, 
  dashboardData,
  onRefresh,
  refreshing,
  updateStatus
}) => {
  const [showUserAuth, setShowUserAuth] = useState(false)
  const [showStockManager, setShowStockManager] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  // Check if current user is admin
  const isUserAdmin = () => {
    return user && (user.is_admin === true || user.username === 'admin')
  }

  const handleUserLogin = (userData) => {
    console.log('Header: User login data:', userData)
    onLogin(userData)
    setShowUserAuth(false)
  }

  const handleUserLogout = () => {
    onLogout()
    setMobileMenuOpen(false)
    if (location.pathname === '/admin') {
      navigate('/')
    }
  }

  const formatLastUpdated = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  const closeMobileMenu = () => {
    setMobileMenuOpen(false)
  }

  return (
    <>
      <header className="app-header">
        <div className="header-content">
          {/* Logo/Brand */}
          <div className="header-brand">
            <Link to="/" className="brand-link" onClick={closeMobileMenu}>
              <TrendingUp className="brand-icon" />
              <span className="brand-text">AI Stock Dashboard</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="header-nav desktop-nav">
            {user && (
              <>
                {/* Refresh Button */}
                {onRefresh && location.pathname === '/' && (
                  <button 
                    onClick={onRefresh}
                    className={`refresh-btn ${refreshing || updateStatus?.update_in_progress ? 'refreshing' : ''}`}
                    disabled={refreshing || updateStatus?.update_in_progress}
                    title="Refresh dashboard data"
                  >
                    <RefreshCw size={16} className={refreshing || updateStatus?.update_in_progress ? 'spinning' : ''} />
                    <span className="refresh-text">
                      {refreshing || updateStatus?.update_in_progress ? 'Updating...' : 'Refresh'}
                    </span>
                  </button>
                )}

                {/* Last Updated */}
                {dashboardData && location.pathname === '/' && (
                  <div className="last-updated">
                    <Clock size={16} />
                    <span>Updated: {dashboardData.last_updated ? formatLastUpdated(dashboardData.last_updated) : 'Never'}</span>
                  </div>
                )}
              </>
            )}
          </nav>

          {/* User Section */}
          <div className="header-user">
            {user ? (
              <>
                {/* Desktop User Menu */}
                <div className="user-menu desktop-user">
                  <div className="user-info">
                    <User size={16} />
                    <span className="username">{user.username}</span>
                    <span className="subscription-badge">{user.subscription_tier}</span>
                    {dashboardData && (
                      <span className="stock-count" title="Stocks tracked / Maximum allowed">
                        {dashboardData.total_stocks || 0}/{user.max_stocks}
                      </span>
                    )}
                  </div>
                  
                  <div className="user-actions">
                    <button 
                      onClick={() => setShowStockManager(true)}
                      className="action-btn manage-stocks-btn"
                      title="Manage your stocks"
                    >
                      <List size={16} />
                      <span>Manage Stocks</span>
                    </button>
                    
                    {isUserAdmin() && (
                      <button 
                        onClick={() => navigate('/admin')}
                        className="action-btn admin-btn"
                        title="Admin Dashboard"
                      >
                        <Settings size={16} />
                        <span>Admin</span>
                      </button>
                    )}
                    
                    <button 
                      onClick={handleUserLogout} 
                      className="action-btn logout-btn"
                      title="Logout"
                    >
                      <LogOut size={16} />
                      <span>Logout</span>
                    </button>
                  </div>
                </div>

                {/* Mobile Menu Button */}
                <button 
                  className="mobile-menu-btn"
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  aria-label="Toggle menu"
                >
                  {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
              </>
            ) : (
              <button 
                onClick={() => setShowUserAuth(true)}
                className="login-btn"
              >
                <User size={16} />
                <span>Login</span>
              </button>
            )}
          </div>
        </div>

        {/* Mobile Menu */}
        {user && mobileMenuOpen && (
          <div className="mobile-menu">
            <div className="mobile-user-info">
              <div className="mobile-user-details">
                <User size={20} />
                <div>
                  <div className="mobile-username">{user.username}</div>
                  <div className="mobile-subscription">{user.subscription_tier}</div>
                  {dashboardData && (
                    <div className="mobile-stock-count">
                      {dashboardData.total_stocks || 0}/{user.max_stocks} stocks
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="mobile-menu-actions">
              {onRefresh && location.pathname === '/' && (
                <button 
                  onClick={() => {
                    onRefresh()
                    closeMobileMenu()
                  }}
                  className={`mobile-action-btn ${refreshing || updateStatus?.update_in_progress ? 'refreshing' : ''}`}
                  disabled={refreshing || updateStatus?.update_in_progress}
                >
                  <RefreshCw size={16} className={refreshing || updateStatus?.update_in_progress ? 'spinning' : ''} />
                  <span>{refreshing || updateStatus?.update_in_progress ? 'Updating...' : 'Refresh Data'}</span>
                </button>
              )}

              <button 
                onClick={() => {
                  setShowStockManager(true)
                  closeMobileMenu()
                }}
                className="mobile-action-btn"
              >
                <List size={16} />
                <span>Manage Stocks</span>
              </button>
              
              {isUserAdmin() && (
                <button 
                  onClick={() => {
                    navigate('/admin')
                    closeMobileMenu()
                  }}
                  className="mobile-action-btn"
                >
                  <Settings size={16} />
                  <span>Admin Dashboard</span>
                </button>
              )}
              
              <button 
                onClick={handleUserLogout}
                className="mobile-action-btn logout"
              >
                <LogOut size={16} />
                <span>Logout</span>
              </button>
            </div>

            {dashboardData && location.pathname === '/' && (
              <div className="mobile-last-updated">
                <Clock size={14} />
                <span>Last updated: {dashboardData.last_updated ? formatLastUpdated(dashboardData.last_updated) : 'Never'}</span>
              </div>
            )}
          </div>
        )}
      </header>

      {/* Auth Modal */}
      {showUserAuth && (
        <UserAuth 
          onLogin={handleUserLogin}
          onClose={() => setShowUserAuth(false)}
        />
      )}
      
      {/* Stock Manager Modal */}
      {showStockManager && user && (
        <UserStockManager 
          user={user}
          onClose={() => setShowStockManager(false)}
        />
      )}
    </>
  )
}

export default Header
