import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles/global.css'
import App from './App'

// StrictMode removed for production — it double-invokes effects/callbacks in dev
// causing duplicate SSE events and timer double-fires in manual mode
ReactDOM.createRoot(document.getElementById('root')).render(
  <App />
)
