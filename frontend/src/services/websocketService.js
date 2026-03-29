/**
 * WebSocket service for real-time notifications
 */

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

class WebSocketService {
  constructor() {
    this.socket = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 1000 // Start with 1 second
    this.listeners = new Map() // Map event types to callback arrays
    this.isConnected = false
    this.isConnecting = false
    this.shouldReconnect = true
    this.connectionCallbacks = []
    this.disconnectionCallbacks = []
  }

  /**
   * Connect to WebSocket server with JWT authentication
   */
  connect() {
    if (this.isConnected || this.isConnecting) {
      console.log('WebSocket: Already connected or connecting')
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      try {
        const token = localStorage.getItem('access_token')
        if (!token) {
          console.error('WebSocket: No access token found')
          reject(new Error('No access token'))
          return
        }

        this.isConnecting = true
        const wsUrl = `${WS_BASE_URL}/api/v1/ws/ws?token=${encodeURIComponent(token)}`

        console.log('WebSocket: Connecting to', wsUrl.replace(/token=[^&]+/, 'token=***'))

        this.socket = new WebSocket(wsUrl)

        this.socket.onopen = (event) => {
          console.log('WebSocket: Connected successfully')
          this.isConnected = true
          this.isConnecting = false
          this.reconnectAttempts = 0
          this.reconnectInterval = 1000

          // Notify connection callbacks
          this.connectionCallbacks.forEach(callback => {
            try {
              callback(event)
            } catch (err) {
              console.error('WebSocket: Connection callback error:', err)
            }
          })

          resolve()
        }

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (err) {
            console.error('WebSocket: Failed to parse message:', err)
          }
        }

        this.socket.onclose = (event) => {
          console.log('WebSocket: Connection closed', event.code, event.reason)
          this.isConnected = false
          this.isConnecting = false

          // Notify disconnection callbacks
          this.disconnectionCallbacks.forEach(callback => {
            try {
              callback(event)
            } catch (err) {
              console.error('WebSocket: Disconnection callback error:', err)
            }
          })

          // Attempt reconnection if needed
          if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }

        this.socket.onerror = (error) => {
          console.error('WebSocket: Error occurred:', error)
          this.isConnecting = false

          if (this.reconnectAttempts === 0) {
            reject(error)
          }
        }

      } catch (err) {
        console.error('WebSocket: Connection setup failed:', err)
        this.isConnecting = false
        reject(err)
      }
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    console.log('WebSocket: Disconnecting...')
    this.shouldReconnect = false

    if (this.socket) {
      this.socket.close(1000, 'Client disconnect')
      this.socket = null
    }

    this.isConnected = false
    this.isConnecting = false
    this.reconnectAttempts = 0
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  scheduleReconnect() {
    if (!this.shouldReconnect) return

    this.reconnectAttempts++
    const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000)

    console.log(`WebSocket: Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`)

    setTimeout(() => {
      if (this.shouldReconnect && !this.isConnected) {
        this.connect().catch(err => {
          console.error('WebSocket: Reconnection failed:', err)
        })
      }
    }, delay)
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(data) {
    console.log('WebSocket: Received message:', data.type, data)

    // Handle different message types
    switch (data.type) {
      case 'notification':
        this.emit('notification', data.data)
        break
      case 'initial_data':
        this.emit('initial_data', data.data)
        break
      case 'pong':
        this.emit('pong', data)
        break
      case 'error':
        this.emit('error', data)
        console.error('WebSocket: Server error:', data.message)
        break
      case 'system':
        this.emit('system', data)
        break
      default:
        this.emit('message', data)
        break
    }
  }

  /**
   * Send message to server
   */
  send(message) {
    if (!this.isConnected || !this.socket) {
      console.warn('WebSocket: Cannot send message, not connected')
      return false
    }

    try {
      this.socket.send(JSON.stringify(message))
      return true
    } catch (err) {
      console.error('WebSocket: Failed to send message:', err)
      return false
    }
  }

  /**
   * Send ping to server
   */
  ping() {
    return this.send({
      type: 'ping',
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Mark notification as read
   */
  markAsRead(notificationId) {
    return this.send({
      type: 'mark_as_read',
      notification_id: notificationId
    })
  }

  /**
   * Mark all notifications as read
   */
  markAllAsRead() {
    return this.send({
      type: 'mark_all_read'
    })
  }

  /**
   * Request recent notifications
   */
  getRecentNotifications(limit = 20) {
    return this.send({
      type: 'get_recent',
      limit: limit
    })
  }

  /**
   * Subscribe to event
   */
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, [])
    }
    this.listeners.get(eventType).push(callback)

    // Return unsubscribe function
    return () => this.off(eventType, callback)
  }

  /**
   * Unsubscribe from event
   */
  off(eventType, callback) {
    if (!this.listeners.has(eventType)) return

    const callbacks = this.listeners.get(eventType)
    const index = callbacks.indexOf(callback)
    if (index !== -1) {
      callbacks.splice(index, 1)
    }
  }

  /**
   * Emit event to listeners
   */
  emit(eventType, data) {
    if (!this.listeners.has(eventType)) return

    const callbacks = this.listeners.get(eventType)
    callbacks.forEach(callback => {
      try {
        callback(data)
      } catch (err) {
        console.error(`WebSocket: Event callback error for ${eventType}:`, err)
      }
    })
  }

  /**
   * Register connection callback
   */
  onConnect(callback) {
    this.connectionCallbacks.push(callback)
  }

  /**
   * Register disconnection callback
   */
  onDisconnect(callback) {
    this.disconnectionCallbacks.push(callback)
  }

  /**
   * Get connection status
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts
    }
  }

  /**
   * Auto-connect if user is logged in
   */
  autoConnect() {
    const token = localStorage.getItem('access_token')
    if (token && !this.isConnected && !this.isConnecting) {
      this.connect().catch(err => {
        console.error('WebSocket: Auto-connect failed:', err)
      })
    }
  }

  /**
   * Handle token refresh - reconnect with new token
   */
  refreshToken() {
    if (this.isConnected) {
      console.log('WebSocket: Token refreshed, reconnecting...')
      this.disconnect()
      setTimeout(() => this.autoConnect(), 1000)
    }
  }
}

// Create singleton instance
const websocketService = new WebSocketService()

// Listen for token changes in localStorage
window.addEventListener('storage', (e) => {
  if (e.key === 'access_token') {
    if (e.newValue) {
      // New token available
      websocketService.refreshToken()
    } else {
      // Token removed (logout)
      websocketService.disconnect()
    }
  }
})

export default websocketService