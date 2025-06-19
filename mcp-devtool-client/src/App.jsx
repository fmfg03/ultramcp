import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import './App.css'

// Layout components
import DevToolLayout from './components/layout/DevToolLayout'

// Page components
import Dashboard from './pages/Dashboard'
import AgentExecution from './pages/AgentExecution'
import { GraphVisualization, LangwatchPanel, DebuggerPanel, TerminalPanel } from './pages/index.jsx'

// Context providers
import { WebSocketProvider } from './contexts/WebSocketContext'
import { MCPProvider } from './contexts/MCPContext'

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <WebSocketProvider>
        <MCPProvider>
          <Router>
            <div className="devtool-layout">
              <Routes>
                <Route path="/" element={<DevToolLayout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="agents" element={<AgentExecution />} />
                  <Route path="graph" element={<GraphVisualization />} />
                  <Route path="langwatch" element={<LangwatchPanel />} />
                  <Route path="debugger" element={<DebuggerPanel />} />
                  <Route path="terminal" element={<TerminalPanel />} />
                </Route>
              </Routes>
            </div>
          </Router>
        </MCPProvider>
      </WebSocketProvider>
    </ThemeProvider>
  )
}

export default App

