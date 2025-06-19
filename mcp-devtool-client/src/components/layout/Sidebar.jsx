import React from 'react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { 
  Home,
  Bot,
  GitBranch,
  Activity,
  Bug,
  Terminal,
  Settings,
  Zap
} from 'lucide-react'

const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: Home,
    description: 'System overview and metrics'
  },
  {
    name: 'Agent Execution',
    href: '/agents',
    icon: Bot,
    description: 'Execute and monitor MCP agents'
  },
  {
    name: 'Graph Visualization',
    href: '/graph',
    icon: GitBranch,
    description: 'LangGraph flow visualization'
  },
  {
    name: 'Langwatch Panel',
    href: '/langwatch',
    icon: Activity,
    description: 'Real-time monitoring and analytics'
  },
  {
    name: 'Debugger',
    href: '/debugger',
    icon: Bug,
    description: 'Session replay and debugging'
  },
  {
    name: 'Terminal',
    href: '/terminal',
    icon: Terminal,
    description: 'CLI interface and commands'
  },
]

const Sidebar = () => {
  return (
    <div className="devtool-sidebar w-64 flex flex-col">
      {/* Logo and title */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-sidebar-foreground">MCP DevTool</h1>
            <p className="text-xs text-sidebar-foreground/60">Agentius Cockpit</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                isActive
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                  : 'text-sidebar-foreground'
              )
            }
          >
            <item.icon className="w-5 h-5" />
            <div className="flex-1">
              <div>{item.name}</div>
              <div className="text-xs opacity-60">{item.description}</div>
            </div>
          </NavLink>
        ))}
      </nav>

      {/* Settings */}
      <div className="p-4 border-t border-sidebar-border">
        <NavLink
          to="/settings"
          className="flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
        >
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </NavLink>
      </div>
    </div>
  )
}

export default Sidebar

