import { useState, useEffect } from 'react'
import { 
  Settings, LogOut, User, Users, BarChart3, Crown, Shield, Zap,
  RefreshCw, AlertCircle, Check, X, Edit2, Save, Database, Activity, Brain 
} from 'lucide-react'
import { 
  getUsers, updateUser, getAdminStats, getAuditLogs,
  getConfig, updateConfig, forceRefresh, adminLogout, getAdminUserStocks
} from '../services/api'
import AIConfiguration from './AIConfiguration'
import './AdminDashboard.css'

function AdminDashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('users')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  // User management state
  const [users, setUsers] = useState([])
  const [editingUser, setEditingUser] = useState(null)
  const [editData, setEditData] = useState({})

  // Statistics state
  const [stats, setStats] = useState({
    total_users: 0,
    active_users: 0,
    subscription_tiers: { free: 0, pro: 0, expert: 0 },
    total_stocks_tracked: 0,
    unique_symbols_tracked: 0,
    symbols: []
  })

  // Configuration state
  const [dataSource, setDataSource] = useState('yahoo')
  const [apiKey, setApiKey] = useState('')
  const [polygonApiKey, setPolygonApiKey] = useState('')
  const [aiProvider, setAiProvider] = useState('openai')
  const [aiModel, setAiModel] = useState('gpt-3.5-turbo')
  const [originalDataSource, setOriginalDataSource] = useState('yahoo')
  const [originalApiKey, setOriginalApiKey] = useState('')
  const [originalPolygonApiKey, setOriginalPolygonApiKey] = useState('')
  const [originalAiProvider, setOriginalAiProvider] = useState('openai')
  const [originalAiModel, setOriginalAiModel] = useState('gpt-3.5-turbo')

  // Audit logs state
  const [auditLogs, setAuditLogs] = useState([])

  const subscriptionTiers = [
    { value: 'free', label: 'Free', maxStocks: 5, icon: User, color: '#6b7280' },
    { value: 'pro', label: 'Pro', maxStocks: 10, icon: Crown, color: '#3b82f6' },
    { value: 'expert', label: 'Expert', maxStocks: 20, icon: Shield, color: '#8b5cf6' }
  ]

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      if (activeTab === 'users') {
        const userData = await getUsers()
        setUsers(userData)
      } else if (activeTab === 'stats') {
        const statsData = await getAdminStats()
        setStats(statsData)
      } else if (activeTab === 'config') {
        const configData = await getConfig()
        setDataSource(configData.data_source)
        setApiKey(configData.alpha_vantage_api_key)
        setPolygonApiKey(configData.polygon_api_key)
        setAiProvider(configData.ai_provider)
        setAiModel(configData.ai_model)
        
        setOriginalDataSource(configData.data_source)
        setOriginalApiKey(configData.alpha_vantage_api_key)
        setOriginalPolygonApiKey(configData.polygon_api_key)
        setOriginalAiProvider(configData.ai_provider)
        setOriginalAiModel(configData.ai_model)
      } else if (activeTab === 'logs') {
        const logData = await getAuditLogs(50)
        setAuditLogs(logData.logs)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleEditUser = (user) => {
    setEditingUser(user.id)
    setEditData({
      subscription_tier: user.subscription_tier,
      max_stocks: user.max_stocks,
      is_active: user.is_active
    })
  }

  const handleSaveUser = async (userId) => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await updateUser(userId, editData)
      setSuccess('User updated successfully')
      setEditingUser(null)
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateConfig = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const configUpdate = {}
      
      if (dataSource !== originalDataSource) {
        configUpdate.data_source = dataSource
      }
      
      if (apiKey !== originalApiKey) {
        configUpdate.alpha_vantage_api_key = apiKey
      }

      if (polygonApiKey !== originalPolygonApiKey) {
        configUpdate.polygon_api_key = polygonApiKey
      }

      if (aiProvider !== originalAiProvider) {
        configUpdate.ai_provider = aiProvider
      }

      if (aiModel !== originalAiModel) {
        configUpdate.ai_model = aiModel
      }

      if (Object.keys(configUpdate).length === 0) {
        setError('No changes to save')
        setLoading(false)
        return
      }

      await updateConfig(configUpdate)
      setSuccess('Successfully updated configuration')
      setOriginalDataSource(dataSource)
      setOriginalApiKey(apiKey)
      setOriginalPolygonApiKey(polygonApiKey)
      setOriginalAiProvider(aiProvider)
      setOriginalAiModel(aiModel)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update configuration')
    } finally {
      setLoading(false)
    }
  }

  const handleForceRefresh = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await forceRefresh()
      setSuccess('Stock data refresh initiated successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to refresh data')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    adminLogout()
    onLogout()
  }

  const clearMessages = () => {
    setError(null)
    setSuccess(null)
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  const getTierInfo = (tier) => {
    return subscriptionTiers.find(t => t.value === tier) || subscriptionTiers[0]
  }

  const hasUnsavedConfigChanges = dataSource !== originalDataSource || 
    apiKey !== originalApiKey || 
    polygonApiKey !== originalPolygonApiKey ||
    aiProvider !== originalAiProvider ||
    aiModel !== originalAiModel

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <div className="admin-header-content">
          <h1>
            <Settings size={24} />
            Admin Dashboard
          </h1>
          <button onClick={handleLogout} className="logout-btn">
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </header>

      <div className="admin-content">
        <nav className="admin-nav">
          <button 
            onClick={() => setActiveTab('users')}
            className={`nav-btn ${activeTab === 'users' ? 'active' : ''}`}
          >
            <Users size={16} />
            User Management
          </button>
          <button 
            onClick={() => setActiveTab('stats')}
            className={`nav-btn ${activeTab === 'stats' ? 'active' : ''}`}
          >
            <BarChart3 size={16} />
            Statistics
          </button>
          <button 
            onClick={() => setActiveTab('ai')}
            className={`nav-btn ${activeTab === 'ai' ? 'active' : ''}`}
          >
            <Brain size={16} />
            AI Configuration
          </button>
          <button 
            onClick={() => setActiveTab('config')}
            className={`nav-btn ${activeTab === 'config' ? 'active' : ''}`}
          >
            <Database size={16} />
            System Config
          </button>
          <button 
            onClick={() => setActiveTab('logs')}
            className={`nav-btn ${activeTab === 'logs' ? 'active' : ''}`}
          >
            <Activity size={16} />
            Audit Logs
          </button>
        </nav>

        <main className="admin-main">
          {(error || success) && (
            <div className={`message ${error ? 'error' : 'success'}`}>
              {error ? <AlertCircle size={16} /> : <Check size={16} />}
              <span>{error || success}</span>
              <button onClick={clearMessages} className="message-close">
                <X size={16} />
              </button>
            </div>
          )}

          {activeTab === 'users' && (
            <div className="tab-content">
              <div className="section-header">
                <h2>User Management</h2>
                <p>Manage user accounts, subscription tiers, and stock limits.</p>
              </div>

              <div className="users-container">
                {loading ? (
                  <div className="loading">
                    <RefreshCw className="spin" size={16} />
                    Loading users...
                  </div>
                ) : users.length === 0 ? (
                  <div className="empty-state">
                    <Users size={32} />
                    <p>No users registered yet</p>
                  </div>
                ) : (
                  <div className="users-table">
                    <div className="table-header">
                      <div>User</div>
                      <div>Subscription</div>
                      <div>Stocks</div>
                      <div>Status</div>
                      <div>Actions</div>
                    </div>
                    {users.map(user => {
                      const tierInfo = getTierInfo(user.subscription_tier)
                      const TierIcon = tierInfo.icon
                      
                      return (
                        <div key={user.id} className="table-row">
                          <div className="user-info">
                            <div className="user-details">
                              <span className="username">{user.username}</span>
                              <span className="email">{user.email}</span>
                            </div>
                          </div>
                          
                          <div className="subscription-info">
                            {editingUser === user.id ? (
                              <select
                                value={editData.subscription_tier}
                                onChange={(e) => {
                                  const newTier = e.target.value
                                  const tierInfo = getTierInfo(newTier)
                                  setEditData({
                                    ...editData,
                                    subscription_tier: newTier,
                                    max_stocks: tierInfo.maxStocks
                                  })
                                }}
                              >
                                {subscriptionTiers.map(tier => (
                                  <option key={tier.value} value={tier.value}>
                                    {tier.label}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <div className="tier-badge" style={{ backgroundColor: tierInfo.color }}>
                                <TierIcon size={14} />
                                {tierInfo.label}
                              </div>
                            )}
                          </div>
                          
                          <div className="stocks-info">
                            {editingUser === user.id ? (
                              <input
                                type="number"
                                value={editData.max_stocks}
                                onChange={(e) => setEditData({
                                  ...editData,
                                  max_stocks: parseInt(e.target.value)
                                })}
                                min="1"
                                max="50"
                              />
                            ) : (
                              <span>{user.stock_count}/{user.max_stocks}</span>
                            )}
                          </div>
                          
                          <div className="status-info">
                            {editingUser === user.id ? (
                              <label className="status-toggle">
                                <input
                                  type="checkbox"
                                  checked={editData.is_active}
                                  onChange={(e) => setEditData({
                                    ...editData,
                                    is_active: e.target.checked
                                  })}
                                />
                                Active
                              </label>
                            ) : (
                              <span className={`status ${user.is_active ? 'active' : 'inactive'}`}>
                                {user.is_active ? 'Active' : 'Inactive'}
                              </span>
                            )}
                          </div>
                          
                          <div className="actions">
                            {editingUser === user.id ? (
                              <>
                                <button
                                  onClick={() => handleSaveUser(user.id)}
                                  className="save-btn"
                                  disabled={loading}
                                >
                                  <Save size={14} />
                                </button>
                                <button
                                  onClick={() => setEditingUser(null)}
                                  className="cancel-btn"
                                  disabled={loading}
                                >
                                  <X size={14} />
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => handleEditUser(user)}
                                className="edit-btn"
                                disabled={loading}
                              >
                                <Edit2 size={14} />
                              </button>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="tab-content">
              <div className="section-header">
                <h2>System Statistics</h2>
                <p>Overview of platform usage and user distribution.</p>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">
                    <Users size={24} />
                  </div>
                  <div className="stat-content">
                    <h3>Total Users</h3>
                    <div className="stat-value">{stats.total_users}</div>
                    <div className="stat-subtext">{stats.active_users} active</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon">
                    <BarChart3 size={24} />
                  </div>
                  <div className="stat-content">
                    <h3>Stocks Tracked</h3>
                    <div className="stat-value">{stats.total_stocks_tracked}</div>
                    <div className="stat-subtext">{stats.unique_symbols_tracked} unique symbols</div>
                  </div>
                </div>

                <div className="stat-card tier-distribution">
                  <div className="stat-content">
                    <h3>Subscription Distribution</h3>
                    <div className="tier-stats">
                      {subscriptionTiers.map(tier => {
                        const TierIcon = tier.icon
                        const count = stats.subscription_tiers[tier.value] || 0
                        const percentage = stats.total_users > 0 ? Math.round((count / stats.total_users) * 100) : 0
                        
                        return (
                          <div key={tier.value} className="tier-stat">
                            <div className="tier-stat-header">
                              <TierIcon size={16} style={{ color: tier.color }} />
                              <span>{tier.label}</span>
                            </div>
                            <div className="tier-stat-value">
                              {count} users ({percentage}%)
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {stats.symbols.length > 0 && (
                <div className="tracked-symbols">
                  <h3>Currently Tracked Symbols</h3>
                  <div className="symbols-grid">
                    {stats.symbols.map(symbol => (
                      <span key={symbol} className="symbol-badge">{symbol}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="tab-content">
              <AIConfiguration />
            </div>
          )}

          {activeTab === 'config' && (
            <div className="tab-content">
              <div className="section-header">
                <h2>System Configuration</h2>
                <p>Configure data source and AI settings for the platform.</p>
              </div>

              <div className="config-section">
                <div className="form-group">
                  <label htmlFor="data-source">Data Source</label>
                  <select
                    id="data-source"
                    value={dataSource}
                    onChange={(e) => setDataSource(e.target.value)}
                    disabled={loading}
                  >
                    <option value="yahoo">Yahoo Finance</option>
                    <option value="alpha_vantage">Alpha Vantage</option>
                    <option value="polygon">Polygon.io</option>
                  </select>
                  <p className="help-text">
                    Yahoo Finance provides free stock data but may have rate limits. 
                    Alpha Vantage and Polygon.io require API keys but offer more reliable data.
                  </p>
                </div>

                <div className="form-group">
                  <label htmlFor="api-key">Alpha Vantage API Key</label>
                  <input
                    type="text"
                    id="api-key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your Alpha Vantage API key"
                    disabled={loading}
                  />
                  <p className="help-text">
                    Required only when using Alpha Vantage. Get your free API key from{' '}
                    <a href="https://www.alphavantage.co/support/#api-key" target="_blank" rel="noopener noreferrer">
                      Alpha Vantage
                    </a>
                  </p>
                </div>

                <div className="form-group">
                  <label htmlFor="polygon-api-key">Polygon.io API Key</label>
                  <input
                    type="text"
                    id="polygon-api-key"
                    value={polygonApiKey}
                    onChange={(e) => setPolygonApiKey(e.target.value)}
                    placeholder="Enter your Polygon.io API key"
                    disabled={loading}
                  />
                  <p className="help-text">
                    Required only when using Polygon.io. Get your API key from{' '}
                    <a href="https://polygon.io/dashboard/signup" target="_blank" rel="noopener noreferrer">
                      Polygon.io
                    </a>
                  </p>
                </div>

                <div className="section-divider">
                  <h3>AI Configuration</h3>
                  <p>Configure which AI provider and model to use for stock analysis.</p>
                </div>

                <div className="form-group">
                  <label htmlFor="ai-provider">AI Provider</label>
                  <select
                    id="ai-provider"
                    value={aiProvider}
                    onChange={(e) => setAiProvider(e.target.value)}
                    disabled={loading}
                  >
                    <option value="openai">OpenAI</option>
                    <option value="groq">Groq</option>
                  </select>
                  <p className="help-text">
                    Choose the AI provider for stock analysis. Requires corresponding API keys to be set in environment variables.
                  </p>
                </div>

                <div className="form-group">
                  <label htmlFor="ai-model">AI Model</label>
                  <select
                    id="ai-model"
                    value={aiModel}
                    onChange={(e) => setAiModel(e.target.value)}
                    disabled={loading}
                  >
                    {aiProvider === 'openai' ? (
                      <>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="gpt-4">GPT-4</option>
                        <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
                      </>
                    ) : (
                      <>
                        <option value="llama3-70b-8192">Llama 3 70B</option>
                        <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                        <option value="gemma-7b-it">Gemma 7B</option>
                      </>
                    )}
                  </select>
                  <p className="help-text">
                    Select the specific model to use with the chosen AI provider.
                  </p>
                </div>

                <div className="config-actions">
                  <button
                    onClick={handleUpdateConfig}
                    disabled={loading || !hasUnsavedConfigChanges}
                    className="save-btn"
                  >
                    <Save size={16} />
                    {loading ? 'Saving...' : 'Save Configuration'}
                  </button>
                  {hasUnsavedConfigChanges && (
                    <button
                      onClick={() => {
                        setDataSource(originalDataSource)
                        setApiKey(originalApiKey)
                        setPolygonApiKey(originalPolygonApiKey)
                        setAiProvider(originalAiProvider)
                        setAiModel(originalAiModel)
                      }}
                      className="revert-btn"
                      disabled={loading}
                    >
                      Revert Changes
                    </button>
                  )}
                </div>
              </div>

              <div className="refresh-section">
                <div className="section-header">
                  <h3>Manual Refresh</h3>
                  <p>Force an immediate update of stock data for all users.</p>
                </div>
                <button
                  onClick={handleForceRefresh}
                  disabled={loading}
                  className="refresh-btn"
                >
                  <RefreshCw className={loading ? 'spinning' : ''} size={16} />
                  {loading ? 'Refreshing...' : 'Refresh Stock Data'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="tab-content">
              <div className="section-header">
                <h2>Audit Logs</h2>
                <p>Track all administrative actions and changes made to the system.</p>
              </div>

              <div className="logs-container">
                {loading ? (
                  <div className="loading">
                    <RefreshCw className="spin" size={16} />
                    Loading logs...
                  </div>
                ) : auditLogs.length === 0 ? (
                  <div className="empty-state">
                    <Activity size={32} />
                    <p>No audit logs found</p>
                  </div>
                ) : (
                  <div className="logs-list">
                    {auditLogs.map((log, index) => (
                      <div key={index} className="log-item">
                        <div className="log-header">
                          <span className="log-action">{log.action.replace('_', ' ')}</span>
                          <span className="log-timestamp">{formatTimestamp(log.timestamp)}</span>
                        </div>
                        <div className="log-details">{log.details}</div>
                        <div className="log-user">by {log.admin_user}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default AdminDashboard