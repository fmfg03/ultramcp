import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import UltraMCPDashboard from './components/UltraMCPDashboard'
import './styles/globals.css'

function App() {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <Router>
        <div className="min-h-screen bg-background text-foreground">
          <Routes>
            <Route path="/" element={<UltraMCPDashboard />} />
            <Route path="/dashboard" element={<UltraMCPDashboard />} />
            {/* Future routes for specific service dashboards */}
            <Route path="/services/cod" element={<div>Chain-of-Debate Dashboard</div>} />
            <Route path="/services/security" element={<div>Security Dashboard</div>} />
            <Route path="/services/memory" element={<div>Memory Dashboard</div>} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  )
}

export default App