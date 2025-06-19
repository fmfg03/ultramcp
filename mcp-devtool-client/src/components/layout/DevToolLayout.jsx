import React from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import StatusBar from './StatusBar'

const DevToolLayout = () => {
  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <Header />
        
        {/* Main content */}
        <main className="flex-1 overflow-auto p-4">
          <Outlet />
        </main>
        
        {/* Status bar */}
        <StatusBar />
      </div>
    </div>
  )
}

export default DevToolLayout

