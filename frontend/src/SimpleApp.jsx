import { useState, useEffect } from 'react'
import './App.css'

function SimpleApp() {
  const [message, setMessage] = useState('Loading...')
  const [data, setData] = useState(null)

  useEffect(() => {
    console.log('SimpleApp mounted')
    setMessage('SimpleApp loaded successfully!')
    
    // Test API call
    fetch('/api/v1/dashboard')
      .then(response => response.json())
      .then(apiData => {
        console.log('API data received:', apiData)
        setData(apiData)
      })
      .catch(error => {
        console.error('API error:', error)
        setMessage('API call failed: ' + error.message)
      })
  }, [])

  return (
    <div className="app">
      <header style={{ padding: '20px', background: '#f0f0f0', marginBottom: '20px' }}>
        <h1>🚀 AI Stock Dashboard - Simple Version</h1>
        <p>{message}</p>
      </header>
      
      <main style={{ padding: '20px' }}>
        {data ? (
          <div>
            <h2>✅ API Connected Successfully</h2>
            <p>Found {data.total_stocks} stocks</p>
            <p>Subscription: {data.subscription_tier}</p>
            <p>Sample data: {data.is_sample_data ? 'Yes' : 'No'}</p>
            
            {data.stocks && data.stocks.length > 0 && (
              <div>
                <h3>Stocks:</h3>
                {data.stocks.map((stock, index) => (
                  <div key={index} style={{ 
                    border: '1px solid #ccc', 
                    padding: '10px', 
                    margin: '10px 0',
                    borderRadius: '5px'
                  }}>
                    <h4>{stock.stock_data.symbol}</h4>
                    <p>Price: ${stock.stock_data.current_price}</p>
                    <p>AI Score: {stock.ai_analysis.average_score}/100</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div>
            <p>Loading dashboard data...</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default SimpleApp
