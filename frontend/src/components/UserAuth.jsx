import { useState } from 'react'
import { UserPlus, LogIn, Eye, EyeOff } from 'lucide-react'
import './UserAuth.css'

function UserAuth({ onLogin, onClose }) {
  const [isLoginMode, setIsLoginMode] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    subscription_tier: 'free'
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      if (isLoginMode) {
        // Login
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          
          // Handle validation errors (422) which come as an array
          if (Array.isArray(errorData.detail)) {
            const errorMessages = errorData.detail.map(err => err.msg).join(', ')
            throw new Error(errorMessages)
          }
          
          // Handle other errors
          throw new Error(errorData.detail || 'Invalid email or password')
        }

        const data = await response.json()
        localStorage.setItem('userToken', data.access_token)
        localStorage.setItem('userData', JSON.stringify(data.user))
        onLogin(data.user)
        onClose()
      } else {
        // Register
        const response = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData)
        })

        if (!response.ok) {
          const errorData = await response.json()
          
          // Handle validation errors (422) which come as an array
          if (Array.isArray(errorData.detail)) {
            const errorMessages = errorData.detail.map(err => err.msg).join(', ')
            throw new Error(errorMessages)
          }
          
          // Handle other errors
          throw new Error(errorData.detail || 'Registration failed')
        }

        const data = await response.json()
        // Auto-login after registration
        const loginResponse = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password
          })
        })

        if (loginResponse.ok) {
          const loginData = await loginResponse.json()
          localStorage.setItem('userToken', loginData.access_token)
          localStorage.setItem('userData', JSON.stringify(loginData.user))
          onLogin(loginData.user)
          onClose()
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="auth-overlay">
      <div className="auth-modal">
        <div className="auth-header">
          <h2>
            {isLoginMode ? (
              <>
                <LogIn size={24} />
                Welcome Back
              </>
            ) : (
              <>
                <UserPlus size={24} />
                Create Account
              </>
            )}
          </h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {!isLoginMode && (
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                required={!isLoginMode}
                placeholder="Enter your username (3+ characters)"
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                required
                placeholder={isLoginMode ? "Enter your password" : "8+ characters, letters & numbers"}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {!isLoginMode && (
            <div className="form-group">
              <label htmlFor="subscription_tier">Subscription Plan</label>
              <select
                id="subscription_tier"
                name="subscription_tier"
                value={formData.subscription_tier}
                onChange={handleInputChange}
                required={!isLoginMode}
              >
                <option value="free">Free (5 stocks)</option>
                <option value="pro">Pro (10 stocks)</option>
                <option value="expert">Expert (20 stocks)</option>
              </select>
            </div>
          )}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? 'Please wait...' : (isLoginMode ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="auth-switch">
          {isLoginMode ? (
            <p>
              Don't have an account?{' '}
              <button 
                type="button" 
                onClick={() => setIsLoginMode(false)}
                className="switch-mode"
              >
                Sign up
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button 
                type="button" 
                onClick={() => setIsLoginMode(true)}
                className="switch-mode"
              >
                Sign in
              </button>
            </p>
          )}
        </div>

        <div className="subscription-info">
          <h3>Subscription Plans</h3>
          <div className="plans">
            <div className="plan">
              <strong>Free:</strong> Track up to 5 stocks, Basic AI analysis
            </div>
            <div className="plan">
              <strong>Pro:</strong> Track up to 10 stocks, Multiple AI models
            </div>
            <div className="plan">
              <strong>Expert:</strong> Track up to 20 stocks, All AI models
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserAuth