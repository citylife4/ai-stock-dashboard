import { useState, useEffect } from 'react'
import { Plus, Trash2, Search, TrendingUp, AlertCircle, Check, X } from 'lucide-react'
import { getUserStocks, addUserStock, removeUserStock } from '../services/api'
import './UserStockManager.css'

function UserStockManager({ user, onClose }) {
  const [userStocks, setUserStocks] = useState([])
  const [newSymbol, setNewSymbol] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [searchResults, setSearchResults] = useState([])

  // Popular stock suggestions
  const popularStocks = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC',
    'ORCL', 'CRM', 'ADBE', 'PYPL', 'ZOOM', 'UBER', 'LYFT', 'TWTR', 'SNAP', 'SPOT'
  ]

  useEffect(() => {
    loadUserStocks()
  }, [])

  const loadUserStocks = async () => {
    try {
      setLoading(true)
      setError(null) // Clear any previous errors
      const response = await getUserStocks()
      setUserStocks(response.symbols || [])
      
      // If user has no stocks, show a helpful message instead of an error
      if (!response.symbols || response.symbols.length === 0) {
        setSuccess('Ready to add your first stock! Search for a symbol below.')
      }
    } catch (err) {
      console.error('Error loading user stocks:', err)
      // More detailed error message
      if (err.response?.status === 401) {
        setError('Please log in to view your stocks')
      } else if (err.response?.status === 403) {
        setError('Access denied. Please check your permissions.')
      } else {
        setError(`Failed to load your stocks: ${err.response?.data?.detail || err.message || 'Unknown error'}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleAddStock = async (symbol) => {
    if (!symbol) return
    
    const upperSymbol = symbol.toUpperCase()
    
    // Check if already tracking
    if (userStocks.includes(upperSymbol)) {
      setError(`You are already tracking ${upperSymbol}`)
      return
    }

    // Check stock limit
    if (userStocks.length >= user.max_stocks) {
      setError(`Stock limit reached. Your ${user.subscription_tier} plan allows ${user.max_stocks} stocks.`)
      return
    }

    try {
      setLoading(true)
      setError(null)
      await addUserStock(upperSymbol)
      setSuccess(`Added ${upperSymbol} to your tracking list`)
      setNewSymbol('')
      await loadUserStocks()
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to add ${upperSymbol}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveStock = async (symbol) => {
    try {
      setLoading(true)
      setError(null)
      await removeUserStock(symbol)
      setSuccess(`Removed ${symbol} from your tracking list`)
      await loadUserStocks()
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to remove ${symbol}`)
    } finally {
      setLoading(false)
    }
  }

  const filterPopularStocks = () => {
    return popularStocks.filter(stock => 
      !userStocks.includes(stock) && 
      (newSymbol === '' || stock.toLowerCase().includes(newSymbol.toLowerCase()))
    ).slice(0, 10)
  }

  const clearMessages = () => {
    setError(null)
    setSuccess(null)
  }

  const getSubscriptionColor = (tier) => {
    const colors = {
      free: '#6b7280',
      pro: '#3b82f6', 
      expert: '#8b5cf6'
    }
    return colors[tier] || colors.free
  }

  return (
    <div className="stock-manager-overlay">
      <div className="stock-manager-modal">
        <div className="stock-manager-header">
          <h2>
            <TrendingUp size={20} />
            Manage Your Stocks
          </h2>
          <button onClick={onClose} className="close-btn">
            <X size={20} />
          </button>
        </div>

        <div className="user-plan-info">
          <div className="plan-badge" style={{ backgroundColor: getSubscriptionColor(user.subscription_tier) }}>
            {user.subscription_tier.toUpperCase()} Plan
          </div>
          <div className="stock-limit">
            {userStocks.length}/{user.max_stocks} stocks tracked
          </div>
        </div>

        {(error || success) && (
          <div className={`message ${error ? 'error' : 'success'}`}>
            {error ? <AlertCircle size={16} /> : <Check size={16} />}
            <span>{error || success}</span>
            <button onClick={clearMessages} className="message-close">
              <X size={16} />
            </button>
          </div>
        )}

        <div className="add-stock-section">
          <h3>Add New Stock</h3>
          <div className="add-stock-form">
            <div className="search-container">
              <Search size={16} />
              <input
                type="text"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                placeholder="Enter stock symbol (e.g., AAPL)"
                onKeyPress={(e) => e.key === 'Enter' && handleAddStock(newSymbol)}
                disabled={loading || userStocks.length >= user.max_stocks}
              />
            </div>
            <button 
              onClick={() => handleAddStock(newSymbol)}
              disabled={loading || !newSymbol || userStocks.length >= user.max_stocks}
              className="add-btn"
            >
              <Plus size={16} />
              Add
            </button>
          </div>

          {userStocks.length < user.max_stocks && (
            <div className="popular-stocks">
              <h4>Popular Stocks</h4>
              <div className="stock-suggestions">
                {filterPopularStocks().map(symbol => (
                  <button
                    key={symbol}
                    onClick={() => handleAddStock(symbol)}
                    className="suggestion-btn"
                    disabled={loading}
                  >
                    {symbol}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="tracked-stocks-section">
          <h3>Your Tracked Stocks ({userStocks.length})</h3>
          {loading && userStocks.length === 0 ? (
            <div className="loading">Loading your stocks...</div>
          ) : userStocks.length === 0 ? (
            <div className="empty-state">
              <TrendingUp size={32} />
              <p>No stocks tracked yet</p>
              <p>Add some stocks above to start tracking them</p>
            </div>
          ) : (
            <div className="stocks-list">
              {userStocks.map(symbol => (
                <div key={symbol} className="stock-item">
                  <span className="stock-symbol">{symbol}</span>
                  <button
                    onClick={() => handleRemoveStock(symbol)}
                    className="remove-btn"
                    disabled={loading}
                    title={`Remove ${symbol}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="stock-manager-footer">
          <button onClick={onClose} className="close-button">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default UserStockManager