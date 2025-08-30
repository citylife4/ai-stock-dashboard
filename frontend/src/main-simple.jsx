import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import SimpleApp from './SimpleApp.jsx'

console.log('main.jsx loading...')

try {
  const rootElement = document.getElementById('root')
  console.log('Root element found:', rootElement)
  
  if (!rootElement) {
    throw new Error('Root element not found')
  }
  
  const root = createRoot(rootElement)
  console.log('React root created')
  
  root.render(
    <StrictMode>
      <SimpleApp />
    </StrictMode>
  )
  console.log('SimpleApp rendered')
} catch (error) {
  console.error('Error in main.jsx:', error)
  document.body.innerHTML += `<div style="color: red; padding: 20px; border: 2px solid red; margin: 20px;">
    <h2>Render Error</h2>
    <p><strong>Error:</strong> ${error.message}</p>
    <p><strong>Stack:</strong> ${error.stack}</p>
  </div>`
}
