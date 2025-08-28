import { useState } from 'react'
import { TrendingUp, BarChart3, Brain, Target, Shield, Zap, Users, Star } from 'lucide-react'
import StockCard from './StockCard'
import './Welcome.css'

function Welcome({ dashboardData, onShowAuth }) {
  const [activeFeature, setActiveFeature] = useState(0)

  const features = [
    {
      icon: <Brain size={24} />,
      title: "AI-Powered Analysis",
      description: "Get insights from multiple AI models including Warren Buffet, Peter Lynch, and DCF analysis strategies."
    },
    {
      icon: <BarChart3 size={24} />,
      title: "Real-Time Data",
      description: "Access up-to-date stock prices, market data, and comprehensive financial metrics."
    },
    {
      icon: <Target size={24} />,
      title: "Personalized Tracking",
      description: "Create your custom watchlist and get tailored analysis for the stocks you care about."
    },
    {
      icon: <Shield size={24} />,
      title: "Risk Assessment",
      description: "Understand potential risks and opportunities with detailed risk factor analysis."
    }
  ]

  const plans = [
    {
      name: "Free",
      price: "$0",
      maxStocks: 5,
      features: ["Track up to 5 stocks", "Basic AI analysis", "Daily updates"],
      recommended: false
    },
    {
      name: "Pro",
      price: "$9.99",
      maxStocks: 25,
      features: ["Track up to 25 stocks", "Advanced AI models", "Real-time updates", "Risk analysis"],
      recommended: true
    },
    {
      name: "Expert",
      price: "$19.99",
      maxStocks: 100,
      features: ["Track up to 100 stocks", "All AI models", "Premium insights", "Portfolio analysis"],
      recommended: false
    }
  ]

  return (
    <div className="welcome-container">
      <div className="hero-section">
        <div className="hero-content">
          <div className="hero-text">
            <h1>
              <TrendingUp className="hero-icon" />
              AI Stock Dashboard
            </h1>
            <p className="hero-subtitle">
              Make smarter investment decisions with AI-powered stock analysis
            </p>
            <p className="hero-description">
              Get insights from legendary investment strategies, real-time market data, 
              and comprehensive risk analysis all in one dashboard.
            </p>
            <div className="hero-actions">
              <button onClick={onShowAuth} className="cta-button primary">
                <Users size={16} />
                Start Free Trial
              </button>
              <button onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })} 
                      className="cta-button secondary">
                Learn More
              </button>
            </div>
          </div>
          <div className="hero-stats">
            <div className="stat-item">
              <Zap size={20} />
              <div>
                <div className="stat-number">3+</div>
                <div className="stat-label">AI Models</div>
              </div>
            </div>
            <div className="stat-item">
              <BarChart3 size={20} />
              <div>
                <div className="stat-number">Real-time</div>
                <div className="stat-label">Market Data</div>
              </div>
            </div>
            <div className="stat-item">
              <Shield size={20} />
              <div>
                <div className="stat-number">100%</div>
                <div className="stat-label">Secure</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section id="demo" className="demo-section">
        <div className="section-header">
          <h2>See It In Action</h2>
          <p>Here's how our AI analyzes stocks using different investment strategies</p>
        </div>
        
        {dashboardData?.stocks && dashboardData.stocks.length > 0 && (
          <div className="demo-dashboard">
            <div className="demo-notice">
              <Star size={16} />
              <span>Live Demo Data - Sign up to track your own stocks!</span>
            </div>
            <div className="stocks-grid">
              {dashboardData.stocks.map((stockAnalysis, index) => (
                <StockCard 
                  key={stockAnalysis.stock_data.symbol} 
                  stockAnalysis={stockAnalysis}
                  rank={index + 1}
                  isDemo={true}
                />
              ))}
            </div>
          </div>
        )}
      </section>

      <section id="features" className="features-section">
        <div className="section-header">
          <h2>Powerful Features</h2>
          <p>Everything you need to make informed investment decisions</p>
        </div>
        
        <div className="features-grid">
          {features.map((feature, index) => (
            <div 
              key={index}
              className={`feature-card ${activeFeature === index ? 'active' : ''}`}
              onMouseEnter={() => setActiveFeature(index)}
            >
              <div className="feature-icon">
                {feature.icon}
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="pricing" className="pricing-section">
        <div className="section-header">
          <h2>Choose Your Plan</h2>
          <p>Start with our free plan and upgrade as your portfolio grows</p>
        </div>
        
        <div className="pricing-grid">
          {plans.map((plan, index) => (
            <div key={index} className={`pricing-card ${plan.recommended ? 'recommended' : ''}`}>
              {plan.recommended && <div className="recommended-badge">Most Popular</div>}
              <div className="plan-header">
                <h3>{plan.name}</h3>
                <div className="plan-price">
                  <span className="price">{plan.price}</span>
                  <span className="period">/month</span>
                </div>
              </div>
              <div className="plan-features">
                <div className="max-stocks">Track up to <strong>{plan.maxStocks} stocks</strong></div>
                <ul>
                  {plan.features.map((feature, fIndex) => (
                    <li key={fIndex}>{feature}</li>
                  ))}
                </ul>
              </div>
              <button 
                onClick={onShowAuth} 
                className={`plan-button ${plan.recommended ? 'primary' : 'secondary'}`}
              >
                Get Started
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Start Investing Smarter?</h2>
          <p>Join thousands of investors who use AI to make better decisions</p>
          <button onClick={onShowAuth} className="cta-button primary large">
            <Users size={20} />
            Create Your Free Account
          </button>
        </div>
      </section>
    </div>
  )
}

export default Welcome
