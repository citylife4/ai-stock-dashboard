import { useState, useEffect } from 'react'
import { 
  Settings, LogOut, Plus, Trash2, Save, RefreshCw, 
  DollarSign, FileText, History, AlertCircle, Check, X, Database 
} from 'lucide-react'
import { 
  getStockList, addStock, removeStock, 
  getPrompts, updatePrompts, getAuditLogs,
  getConfig, updateConfig, forceRefresh,
  adminLogout 
} from '../services/api'
import './AdminDashboard.css'

function AdminDashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('stocks')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  // Stock management state
  const [stocks, setStocks] = useState([])
  const [newStock, setNewStock] = useState('')

  // Prompt management state
  const [aiPrompt, setAiPrompt] = useState('')
  const [originalPrompt, setOriginalPrompt] = useState('')

  // Configuration state
  const [dataSource, setDataSource] = useState('yahoo')
  const [apiKey, setApiKey] = useState('')
  const [originalDataSource, setOriginalDataSource] = useState('yahoo')
  const [originalApiKey, setOriginalApiKey] = useState('')

  // Audit logs state
  const [auditLogs, setAuditLogs] = useState([])

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      if (activeTab === 'stocks') {
        const stockData = await getStockList()
        setStocks(stockData.symbols)
      } else if (activeTab === 'prompts') {
        const promptData = await getPrompts()
        setAiPrompt(promptData.ai_analysis_prompt)
        setOriginalPrompt(promptData.ai_analysis_prompt)
      } else if (activeTab === 'config') {
        const configData = await getConfig()
        setDataSource(configData.data_source)
        setApiKey(configData.alpha_vantage_api_key)
        setOriginalDataSource(configData.data_source)
        setOriginalApiKey(configData.alpha_vantage_api_key)
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

  const handleAddStock = async (e) => {
    e.preventDefault()
    if (!newStock.trim()) return

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await addStock(newStock.trim().toUpperCase())
      setSuccess(`Successfully added ${newStock.toUpperCase()}`)
      setNewStock('')
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add stock')
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveStock = async (symbol) => {
    if (!confirm(`Are you sure you want to remove ${symbol}?`)) return

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await removeStock(symbol)
      setSuccess(`Successfully removed ${symbol}`)
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove stock')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdatePrompt = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await updatePrompts(aiPrompt)
      setSuccess('Successfully updated AI analysis prompt')
      setOriginalPrompt(aiPrompt)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update prompt')
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

      if (Object.keys(configUpdate).length === 0) {
        setError('No changes to save')
        setLoading(false)
        return
      }

      await updateConfig(configUpdate)
      setSuccess('Successfully updated configuration')
      setOriginalDataSource(dataSource)
      setOriginalApiKey(apiKey)
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

  const hasUnsavedPromptChanges = aiPrompt !== originalPrompt
  const hasUnsavedConfigChanges = dataSource !== originalDataSource || apiKey !== originalApiKey

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
            onClick={() => setActiveTab('stocks')}
            className={`nav-btn ${activeTab === 'stocks' ? 'active' : ''}`}
          >
            <DollarSign size={16} />
            Stock Management
          </button>
          <button 
            onClick={() => setActiveTab('prompts')}
            className={`nav-btn ${activeTab === 'prompts' ? 'active' : ''}`}
          >
            <FileText size={16} />
            Prompt Management
          </button>
          <button 
            onClick={() => setActiveTab('config')}
            className={`nav-btn ${activeTab === 'config' ? 'active' : ''}`}
          >
            <Database size={16} />
            Data Configuration
          </button>
          <button 
            onClick={() => setActiveTab('logs')}
            className={`nav-btn ${activeTab === 'logs' ? 'active' : ''}`}
          >
            <History size={16} />
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

          {activeTab === 'stocks' && (
            <div className="tab-content">
              <div className="section-header">
                <h2>Stock Management</h2>
                <p>Add or remove stocks from the tracking list. Changes take effect immediately.</p>
              </div>

              <div className="add-stock-form">
                <form onSubmit={handleAddStock}>
                  <div className="form-row">
                    <input
                      type="text"
                      value={newStock}
                      onChange={(e) => setNewStock(e.target.value.toUpperCase())}
                      placeholder="Enter stock symbol (e.g., AAPL)"
                      disabled={loading}
                      maxLength={10}
                    />
                    <button type="submit" disabled={loading || !newStock.trim()}>
                      <Plus size={16} />
                      Add Stock
                    </button>
                  </div>
                </form>
              </div>

              <div className="stocks-list">
                <h3>Currently Tracked Stocks ({stocks.length})</h3>
                {loading ? (
                  <div className="loading">
                    <RefreshCw className="spin" size={16} />
                    Loading...
                  </div>
                ) : (
                  <div className="stocks-grid">
                    {stocks.map(symbol => (
                      <div key={symbol} className="stock-item">
                        <span className="stock-symbol">{symbol}</span>
                        <button
                          onClick={() => handleRemoveStock(symbol)}
                          className="remove-btn"
                          disabled={loading || stocks.length <= 1}
                          title={stocks.length <= 1 ? "Cannot remove all stocks" : "Remove stock"}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'prompts' && (
            <div className="tab-content">
              <div className="section-header">
                <h2>Prompt Management</h2>
                <p>Customize the AI analysis prompt. Changes take effect immediately on the next analysis.</p>
              </div>

              <div className="prompt-editor">
                <label htmlFor="ai-prompt">AI Analysis Prompt</label>
                <textarea
                  id="ai-prompt"
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  disabled={loading}
                  rows={15}
                  placeholder="Enter your AI analysis prompt..."
                />
                <div className="prompt-help">
                  <p><strong>Required placeholders:</strong></p>
                  <div className="placeholders">
                    <code>{'{symbol}'}</code>
                    <code>{'{current_price}'}</code>
                    <code>{'{previous_close}'}</code>
                    <code>{'{change_percent}'}</code>
                    <code>{'{volume}'}</code>
                    <code>{'{market_cap}'}</code>
                  </div>
                </div>
                <div className="prompt-actions">
                  <button
                    onClick={handleUpdatePrompt}
                    disabled={loading || !hasUnsavedPromptChanges}
                    className="save-btn"
                  >
                    <Save size={16} />
                    {loading ? 'Saving...' : 'Save Changes'}
                  </button>
                  {hasUnsavedPromptChanges && (
                    <button
                      onClick={() => setAiPrompt(originalPrompt)}
                      className="revert-btn"
                      disabled={loading}
                    >
                      Revert Changes
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'config' && (
            <div className="tab-content">
              <div className="section-header">
                <h2>Data Configuration</h2>
                <p>Configure data source and API settings. Changes take effect immediately.</p>
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
                  </select>
                  <p className="help-text">
                    Yahoo Finance provides free stock data but may have rate limits. 
                    Alpha Vantage requires an API key but offers more reliable data.
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
                  <p>Force an immediate update of stock data using the current configuration.</p>
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
                    <History size={32} />
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