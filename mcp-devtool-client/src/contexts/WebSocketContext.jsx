import React, { createContext, useContext, useEffect, useState } from 'react'
import { io } from 'socket.io-client'

const WebSocketContext = createContext()

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')

  useEffect(() => {
    // Connect to the MCP backend WebSocket
    const newSocket = io('ws://localhost:8124', {
      transports: ['websocket'],
      autoConnect: true,
    })

    newSocket.on('connect', () => {
      console.log('🔌 WebSocket connected')
      setIsConnected(true)
      setConnectionStatus('connected')
    })

    newSocket.on('disconnect', () => {
      console.log('🔌 WebSocket disconnected')
      setIsConnected(false)
      setConnectionStatus('disconnected')
    })

    newSocket.on('connect_error', (error) => {
      console.error('🔌 WebSocket connection error:', error)
      setConnectionStatus('error')
    })

    newSocket.on('reconnect', () => {
      console.log('🔌 WebSocket reconnected')
      setIsConnected(true)
      setConnectionStatus('connected')
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  const emit = (event, data) => {
    if (socket && isConnected) {
      socket.emit(event, data)
    } else {
      console.warn('🔌 WebSocket not connected, cannot emit:', event)
    }
  }

  const on = (event, callback) => {
    if (socket) {
      socket.on(event, callback)
      return () => socket.off(event, callback)
    }
  }

  const off = (event, callback) => {
    if (socket) {
      socket.off(event, callback)
    }
  }

  const value = {
    socket,
    isConnected,
    connectionStatus,
    emit,
    on,
    off,
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

