import React, { createContext, useContext, useReducer, useEffect } from 'react'
import { useWebSocket } from './WebSocketContext'

const MCPContext = createContext()

export const useMCP = () => {
  const context = useContext(MCPContext)
  if (!context) {
    throw new Error('useMCP must be used within a MCPProvider')
  }
  return context
}

// MCP State management
const initialState = {
  // Agent execution
  agents: [
    { id: 'complete_mcp_agent', name: 'Complete MCP Agent', description: 'Full orchestration with reasoning, reward, and contradiction' },
    { id: 'reasoning_agent', name: 'Reasoning Agent', description: 'Specialized reasoning with contradiction analysis' },
    { id: 'builder_agent', name: 'Builder Agent', description: 'Content and code generation specialist' },
  ],
  currentExecution: null,
  executionHistory: [],
  
  // Graph visualization
  currentGraph: null,
  graphNodes: [],
  graphEdges: [],
  nodeStates: {},
  
  // Langwatch data
  sessions: [],
  currentSession: null,
  logs: [],
  metrics: {
    totalTokens: 0,
    avgResponseTime: 0,
    successRate: 0,
    contradictionsApplied: 0,
  },
  
  // Debugger
  debugSessions: [],
  currentDebugSession: null,
  playbackState: 'stopped', // stopped, playing, paused
  
  // System status
  systemStatus: {
    mcpServer: 'disconnected',
    langwatchService: 'disconnected',
    localLLMs: {
      mistral: 'unknown',
      llama: 'unknown',
      deepseek: 'unknown',
    },
  },
}

const mcpReducer = (state, action) => {
  switch (action.type) {
    case 'SET_CURRENT_EXECUTION':
      return {
        ...state,
        currentExecution: action.payload,
      }
    
    case 'ADD_EXECUTION_TO_HISTORY':
      return {
        ...state,
        executionHistory: [action.payload, ...state.executionHistory.slice(0, 49)], // Keep last 50
      }
    
    case 'UPDATE_GRAPH':
      return {
        ...state,
        currentGraph: action.payload.graph,
        graphNodes: action.payload.nodes,
        graphEdges: action.payload.edges,
      }
    
    case 'UPDATE_NODE_STATE':
      return {
        ...state,
        nodeStates: {
          ...state.nodeStates,
          [action.payload.nodeId]: action.payload.state,
        },
      }
    
    case 'ADD_LOG_ENTRY':
      return {
        ...state,
        logs: [action.payload, ...state.logs.slice(0, 999)], // Keep last 1000 logs
      }
    
    case 'UPDATE_METRICS':
      return {
        ...state,
        metrics: {
          ...state.metrics,
          ...action.payload,
        },
      }
    
    case 'SET_CURRENT_SESSION':
      return {
        ...state,
        currentSession: action.payload,
      }
    
    case 'ADD_SESSION':
      return {
        ...state,
        sessions: [action.payload, ...state.sessions.slice(0, 99)], // Keep last 100 sessions
      }
    
    case 'SET_DEBUG_SESSION':
      return {
        ...state,
        currentDebugSession: action.payload,
      }
    
    case 'UPDATE_PLAYBACK_STATE':
      return {
        ...state,
        playbackState: action.payload,
      }
    
    case 'UPDATE_SYSTEM_STATUS':
      return {
        ...state,
        systemStatus: {
          ...state.systemStatus,
          ...action.payload,
        },
      }
    
    default:
      return state
  }
}

export const MCPProvider = ({ children }) => {
  const [state, dispatch] = useReducer(mcpReducer, initialState)
  const { socket, isConnected, on } = useWebSocket()

  useEffect(() => {
    if (!isConnected || !socket) return

    // Listen for real-time updates from the MCP system
    const unsubscribers = [
      on('execution_started', (data) => {
        dispatch({ type: 'SET_CURRENT_EXECUTION', payload: data })
        dispatch({ type: 'ADD_LOG_ENTRY', payload: {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          level: 'info',
          message: `Execution started: ${data.agent} - ${data.prompt.substring(0, 100)}...`,
          source: 'execution',
          data,
        }})
      }),

      on('execution_completed', (data) => {
        dispatch({ type: 'ADD_EXECUTION_TO_HISTORY', payload: data })
        dispatch({ type: 'SET_CURRENT_EXECUTION', payload: null })
        dispatch({ type: 'ADD_LOG_ENTRY', payload: {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          level: 'info',
          message: `Execution completed: ${data.status}`,
          source: 'execution',
          data,
        }})
      }),

      on('graph_updated', (data) => {
        dispatch({ type: 'UPDATE_GRAPH', payload: data })
      }),

      on('node_state_changed', (data) => {
        dispatch({ type: 'UPDATE_NODE_STATE', payload: data })
        dispatch({ type: 'ADD_LOG_ENTRY', payload: {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          level: 'debug',
          message: `Node ${data.nodeId} state: ${data.state}`,
          source: 'graph',
          data,
        }})
      }),

      on('langwatch_event', (data) => {
        dispatch({ type: 'ADD_LOG_ENTRY', payload: {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          level: data.level || 'info',
          message: data.message,
          source: 'langwatch',
          data,
        }})
        
        if (data.type === 'metrics_update') {
          dispatch({ type: 'UPDATE_METRICS', payload: data.metrics })
        }
      }),

      on('contradiction_detected', (data) => {
        dispatch({ type: 'ADD_LOG_ENTRY', payload: {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          level: 'warning',
          message: `🔥 Contradiction detected: ${data.reason}`,
          source: 'contradiction',
          data,
        }})
        
        dispatch({ type: 'UPDATE_METRICS', payload: {
          contradictionsApplied: state.metrics.contradictionsApplied + 1,
        }})
      }),

      on('system_status_update', (data) => {
        dispatch({ type: 'UPDATE_SYSTEM_STATUS', payload: data })
      }),
    ]

    return () => {
      unsubscribers.forEach(unsub => unsub && unsub())
    }
  }, [isConnected, socket, on, state.metrics.contradictionsApplied])

  // Actions
  const actions = {
    executeAgent: (agentId, prompt, options = {}) => {
      if (!isConnected) {
        console.warn('Cannot execute agent: WebSocket not connected')
        return
      }

      const executionData = {
        id: `exec_${Date.now()}`,
        agent: agentId,
        prompt,
        options,
        timestamp: new Date().toISOString(),
        status: 'running',
      }

      dispatch({ type: 'SET_CURRENT_EXECUTION', payload: executionData })
      socket.emit('execute_agent', executionData)
    },

    stopExecution: () => {
      if (state.currentExecution && isConnected) {
        socket.emit('stop_execution', { id: state.currentExecution.id })
      }
    },

    loadDebugSession: (sessionId) => {
      if (isConnected) {
        socket.emit('load_debug_session', { sessionId })
      }
    },

    replaySession: (sessionId, fromStep = 0) => {
      if (isConnected) {
        dispatch({ type: 'UPDATE_PLAYBACK_STATE', payload: 'playing' })
        socket.emit('replay_session', { sessionId, fromStep })
      }
    },

    pausePlayback: () => {
      dispatch({ type: 'UPDATE_PLAYBACK_STATE', payload: 'paused' })
      if (isConnected) {
        socket.emit('pause_playback')
      }
    },

    stopPlayback: () => {
      dispatch({ type: 'UPDATE_PLAYBACK_STATE', payload: 'stopped' })
      if (isConnected) {
        socket.emit('stop_playback')
      }
    },

    reinjectInput: (sessionId, stepId, newInput) => {
      if (isConnected) {
        socket.emit('reinject_input', { sessionId, stepId, newInput })
      }
    },

    clearLogs: () => {
      dispatch({ type: 'ADD_LOG_ENTRY', payload: [] })
    },

    exportSession: (sessionId) => {
      if (isConnected) {
        socket.emit('export_session', { sessionId })
      }
    },
  }

  const value = {
    ...state,
    ...actions,
    dispatch,
  }

  return (
    <MCPContext.Provider value={value}>
      {children}
    </MCPContext.Provider>
  )
}

