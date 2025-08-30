import { TrendingUp, TrendingDown, Award, DollarSign, BarChart3 } from 'lucide-react'
import './StockCard.css'

function StockCard({ stockAnalysis, rank, isDemo = false }) {
  const { stock_data, ai_analysis } = stockAnalysis
  const isPositive = stock_data.change_percent >= 0

  const formatNumber = (num) => {
    if (num >= 1e12) return `$${(num / 1e12).toFixed(1)}T`
    if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`
    if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`
    return `$${num.toFixed(2)}`
  }

  const formatVolume = (volume) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(1)}B`
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(1)}M`
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(1)}K`
    return volume.toString()
  }

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981' // green
    if (score >= 60) return '#f59e0b' // yellow
    if (score >= 40) return '#f97316' // orange
    return '#ef4444' // red
  }

  const getRankBadgeColor = (rank) => {
    if (rank === 1) return '#ffd700' // gold
    if (rank === 2) return '#c0c0c0' // silver
    if (rank === 3) return '#cd7f32' // bronze
    return '#6b7280' // gray
  }

  return (
    <div className={`stock-card ${isDemo ? 'demo-card' : ''}`}>
      {isDemo && (
        <div className="demo-badge">
          Demo Data
        </div>
      )}
      <div className="stock-card-header">
        <div className="stock-info">
          <div className="stock-symbol-container">
            <h2 className="stock-symbol">{stock_data.symbol}</h2>
            <div 
              className="rank-badge" 
              style={{ backgroundColor: getRankBadgeColor(rank) }}
            >
              <Award size={12} />
              #{rank}
            </div>
          </div>
          <div className="stock-price">
            <span className="current-price">{formatNumber(stock_data.current_price)}</span>
            <div className={`change ${isPositive ? 'positive' : 'negative'}`}>
              {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              <span>{isPositive ? '+' : ''}{stock_data.change_percent.toFixed(2)}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="stock-metrics">
        <div className="metric">
          <DollarSign size={16} />
          <div>
            <span className="metric-label">Previous Close</span>
            <span className="metric-value">{formatNumber(stock_data.previous_close)}</span>
          </div>
        </div>
        <div className="metric">
          <BarChart3 size={16} />
          <div>
            <span className="metric-label">Volume</span>
            <span className="metric-value">{formatVolume(stock_data.volume)}</span>
          </div>
        </div>
        {stock_data.market_cap && (
          <div className="metric">
            <DollarSign size={16} />
            <div>
              <span className="metric-label">Market Cap</span>
              <span className="metric-value">{formatNumber(stock_data.market_cap)}</span>
            </div>
          </div>
        )}
      </div>

      <div className="ai-analysis">
        <div className="score-container">
          <div className="score-label">
            {ai_analysis.analyses.length > 1 ? 'Average AI Score' : 'AI Score'}
          </div>
          <div 
            className="score-circle"
            style={{ borderColor: getScoreColor(Math.round(ai_analysis.average_score)) }}
          >
            <span 
              className="score-value"
              style={{ color: getScoreColor(Math.round(ai_analysis.average_score)) }}
            >
              {Math.round(ai_analysis.average_score)}
            </span>
          </div>
        </div>

        {ai_analysis.analyses.length > 1 ? (
          <div className="multi-ai-analyses">
            <h4>AI Analyses ({ai_analysis.analyses.length} models)</h4>
            <div className="ai-models">
              {ai_analysis.analyses.map((analysis, index) => (
                <div key={index} className="ai-model">
                  <div className="ai-model-header">
                    <span className="ai-model-name">{analysis.ai_model.replace('_', ' ')}</span>
                    <span 
                      className="ai-model-score"
                      style={{ color: getScoreColor(analysis.score) }}
                    >
                      {analysis.score}
                    </span>
                  </div>
                  <p className="ai-model-reason">{analysis.reason}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="reason">
            <h4>Analysis</h4>
            <p>{ai_analysis.analyses[0].reason}</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default StockCard