import { useState, useEffect } from 'react'
import { 
  Brain, Save, RefreshCw, AlertCircle, Check, X, Settings,
  Eye, EyeOff, Crown, Shield, Zap, User
} from 'lucide-react'
import './AIConfiguration.css'

function AIConfiguration() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  // AI Model configurations
  const [aiModels, setAiModels] = useState([
    {
      id: 'basic',
      name: 'Basic AI Analyst',
      description: 'General purpose stock analysis',
      isActive: true,
      subscriptionTiers: ['free', 'pro', 'expert'],
      icon: Brain,
      color: '#6b7280',
      prompt: ''
    },
    {
      id: 'warren_buffet',
      name: 'Warren Buffet Style',
      description: 'Value investing approach focusing on fundamental analysis',
      isActive: true,
      subscriptionTiers: ['pro', 'expert'],
      icon: Crown,
      color: '#3b82f6',
      prompt: ''
    },
    {
      id: 'peter_lynch',
      name: 'Peter Lynch Style',
      description: 'Growth at reasonable price (GARP) investment strategy',
      isActive: true,
      subscriptionTiers: ['pro', 'expert'],
      icon: Shield,
      color: '#10b981',
      prompt: ''
    },
    {
      id: 'dcf_math',
      name: 'DCF Mathematical',
      description: 'Quantitative analysis using mathematical models',
      isActive: true,
      subscriptionTiers: ['expert'],
      icon: Zap,
      color: '#8b5cf6',
      prompt: ''
    }
  ])

  const [editingModel, setEditingModel] = useState(null)
  const [showPrompt, setShowPrompt] = useState({})

  const subscriptionTiers = [
    { value: 'free', label: 'Free', icon: User, color: '#6b7280' },
    { value: 'pro', label: 'Pro', icon: Crown, color: '#3b82f6' },
    { value: 'expert', label: 'Expert', icon: Shield, color: '#8b5cf6' }
  ]

  const clearMessages = () => {
    setError(null)
    setSuccess(null)
  }

  const handleToggleModel = (modelId) => {
    setAiModels(models => 
      models.map(model => 
        model.id === modelId 
          ? { ...model, isActive: !model.isActive }
          : model
      )
    )
  }

  const handleTierToggle = (modelId, tier) => {
    setAiModels(models => 
      models.map(model => {
        if (model.id === modelId) {
          const newTiers = model.subscriptionTiers.includes(tier)
            ? model.subscriptionTiers.filter(t => t !== tier)
            : [...model.subscriptionTiers, tier]
          return { ...model, subscriptionTiers: newTiers }
        }
        return model
      })
    )
  }

  const handleSaveConfiguration = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      // Here you would typically call an API to save the configuration
      // For now, we'll just simulate a save
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSuccess('AI model configuration saved successfully')
    } catch (err) {
      setError('Failed to save AI configuration')
    } finally {
      setLoading(false)
    }
  }

  const togglePromptVisibility = (modelId) => {
    setShowPrompt(prev => ({
      ...prev,
      [modelId]: !prev[modelId]
    }))
  }

  return (
    <div className="ai-configuration">
      <div className="section-header">
        <h2>
          <Brain size={20} />
          AI Model Configuration
        </h2>
        <p>Configure AI analysis models, subscription access, and prompts.</p>
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

      <div className="ai-models-grid">
        {aiModels.map(model => {
          const ModelIcon = model.icon
          return (
            <div key={model.id} className={`ai-model-card ${!model.isActive ? 'inactive' : ''}`}>
              <div className="model-header">
                <div className="model-icon" style={{ backgroundColor: model.color }}>
                  <ModelIcon size={20} />
                </div>
                <div className="model-info">
                  <h3>{model.name}</h3>
                  <p>{model.description}</p>
                </div>
                <div className="model-toggle">
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={model.isActive}
                      onChange={() => handleToggleModel(model.id)}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
              </div>

              <div className="subscription-access">
                <h4>Subscription Access</h4>
                <div className="tier-toggles">
                  {subscriptionTiers.map(tier => {
                    const TierIcon = tier.icon
                    const isEnabled = model.subscriptionTiers.includes(tier.value)
                    
                    return (
                      <button
                        key={tier.value}
                        onClick={() => handleTierToggle(model.id, tier.value)}
                        className={`tier-btn ${isEnabled ? 'enabled' : 'disabled'}`}
                        style={{
                          borderColor: tier.color,
                          backgroundColor: isEnabled ? tier.color : 'transparent',
                          color: isEnabled ? 'white' : tier.color
                        }}
                        disabled={!model.isActive}
                      >
                        <TierIcon size={14} />
                        {tier.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="prompt-section">
                <div className="prompt-header">
                  <h4>Analysis Prompt</h4>
                  <button
                    onClick={() => togglePromptVisibility(model.id)}
                    className="show-prompt-btn"
                  >
                    {showPrompt[model.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                    {showPrompt[model.id] ? 'Hide' : 'Show'} Prompt
                  </button>
                </div>
                
                {showPrompt[model.id] && (
                  <div className="prompt-content">
                    <textarea
                      value={model.prompt}
                      onChange={(e) => setAiModels(models => 
                        models.map(m => 
                          m.id === model.id 
                            ? { ...m, prompt: e.target.value }
                            : m
                        )
                      )}
                      placeholder={`Enter custom prompt for ${model.name}...`}
                      rows={6}
                      disabled={!model.isActive}
                    />
                    <p className="prompt-help">
                      Use placeholders like {'{symbol}'}, {'{current_price}'}, {'{change_percent}'} for dynamic data injection.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="configuration-actions">
        <button
          onClick={handleSaveConfiguration}
          disabled={loading}
          className="save-btn"
        >
          <Save size={16} />
          {loading ? 'Saving...' : 'Save AI Configuration'}
        </button>
        
        <div className="action-info">
          <p>Changes will affect new analysis requests. Existing cached analyses remain unchanged.</p>
        </div>
      </div>

      <div className="ai-stats">
        <h3>Current AI Model Status</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-label">Active Models:</span>
            <span className="stat-value">{aiModels.filter(m => m.isActive).length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Free Tier Models:</span>
            <span className="stat-value">
              {aiModels.filter(m => m.isActive && m.subscriptionTiers.includes('free')).length}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Pro Tier Models:</span>
            <span className="stat-value">
              {aiModels.filter(m => m.isActive && m.subscriptionTiers.includes('pro')).length}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Expert Tier Models:</span>
            <span className="stat-value">
              {aiModels.filter(m => m.isActive && m.subscriptionTiers.includes('expert')).length}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIConfiguration