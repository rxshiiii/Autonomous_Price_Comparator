/**
 * Zustand store for notification state management
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import websocketService from '../services/websocketService'

const useNotificationStore = create(
  devtools(
    (set, get) => ({
      // State
      notifications: [],
      unreadCount: 0,
      isConnected: false,
      isConnecting: false,
      connectionError: null,
      lastUpdate: null,

      // Connection management
      connect: async () => {
        set({ isConnecting: true, connectionError: null })

        try {
          await websocketService.connect()

          // Set up event listeners
          const unsubscribeNotification = websocketService.on('notification', (notificationData) => {
            get().addNotification(notificationData)
          })

          const unsubscribeInitialData = websocketService.on('initial_data', (data) => {
            get().setInitialData(data)
          })

          const unsubscribeSystem = websocketService.on('system', (data) => {
            console.log('System message:', data.message)
          })

          const unsubscribeError = websocketService.on('error', (data) => {
            set({ connectionError: data.message })
          })

          // Store unsubscribe functions for cleanup
          set({
            isConnected: true,
            isConnecting: false,
            _unsubscribeFunctions: [
              unsubscribeNotification,
              unsubscribeInitialData,
              unsubscribeSystem,
              unsubscribeError
            ]
          })

          // Set up connection status callbacks
          websocketService.onConnect(() => {
            set({ isConnected: true, connectionError: null })
          })

          websocketService.onDisconnect(() => {
            set({ isConnected: false })
          })

        } catch (error) {
          console.error('Failed to connect to websocket:', error)
          set({
            isConnecting: false,
            connectionError: error.message || 'Connection failed'
          })
        }
      },

      disconnect: () => {
        // Clean up event listeners
        const { _unsubscribeFunctions } = get()
        if (_unsubscribeFunctions) {
          _unsubscribeFunctions.forEach(unsubscribe => unsubscribe())
        }

        websocketService.disconnect()
        set({
          isConnected: false,
          isConnecting: false,
          _unsubscribeFunctions: null
        })
      },

      // Notification management
      addNotification: (notification) => {
        const { notifications, unreadCount } = get()

        // Check if notification already exists
        const exists = notifications.some(n => n.id === notification.id)
        if (exists) return

        // Add to notifications array (newest first)
        const updatedNotifications = [notification, ...notifications].slice(0, 100) // Keep max 100

        // Update unread count if notification is unread
        const newUnreadCount = notification.is_read ? unreadCount : unreadCount + 1

        set({
          notifications: updatedNotifications,
          unreadCount: newUnreadCount,
          lastUpdate: Date.now()
        })

        // Show browser notification if supported and enabled
        get().showBrowserNotification(notification)
      },

      setInitialData: (data) => {
        set({
          notifications: data.recent_notifications || [],
          unreadCount: data.unread_count || 0,
          lastUpdate: Date.now()
        })
      },

      markAsRead: async (notificationId) => {
        const { notifications, unreadCount } = get()

        // Find and update notification
        const updatedNotifications = notifications.map(notification => {
          if (notification.id === notificationId && !notification.is_read) {
            return { ...notification, is_read: true }
          }
          return notification
        })

        // Calculate new unread count
        const wasUnread = notifications.find(n => n.id === notificationId && !n.is_read)
        const newUnreadCount = wasUnread ? Math.max(0, unreadCount - 1) : unreadCount

        set({
          notifications: updatedNotifications,
          unreadCount: newUnreadCount,
          lastUpdate: Date.now()
        })

        // Send to server
        websocketService.markAsRead(notificationId)
      },

      markAllAsRead: async () => {
        const { notifications } = get()

        // Mark all as read
        const updatedNotifications = notifications.map(notification => ({
          ...notification,
          is_read: true
        }))

        set({
          notifications: updatedNotifications,
          unreadCount: 0,
          lastUpdate: Date.now()
        })

        // Send to server
        websocketService.markAllAsRead()
      },

      removeNotification: (notificationId) => {
        const { notifications, unreadCount } = get()

        const notificationToRemove = notifications.find(n => n.id === notificationId)
        const updatedNotifications = notifications.filter(n => n.id !== notificationId)

        // Update unread count if removed notification was unread
        const newUnreadCount = notificationToRemove && !notificationToRemove.is_read
          ? Math.max(0, unreadCount - 1)
          : unreadCount

        set({
          notifications: updatedNotifications,
          unreadCount: newUnreadCount,
          lastUpdate: Date.now()
        })
      },

      clearAllNotifications: () => {
        set({
          notifications: [],
          unreadCount: 0,
          lastUpdate: Date.now()
        })
      },

      // Browser notifications
      showBrowserNotification: (notification) => {
        // Check if browser notifications are supported and permitted
        if ('Notification' in window && Notification.permission === 'granted') {
          try {
            const browserNotification = new Notification(notification.title, {
              body: notification.message,
              icon: '/favicon.ico', // Add your app icon path
              tag: notification.id, // Prevents duplicate notifications
              requireInteraction: false,
              silent: false
            })

            // Auto close after 5 seconds
            setTimeout(() => {
              browserNotification.close()
            }, 5000)

            // Handle click to focus app
            browserNotification.onclick = () => {
              window.focus()
              browserNotification.close()
              // Optionally navigate to specific page based on notification type
            }

          } catch (error) {
            console.error('Failed to show browser notification:', error)
          }
        }
      },

      requestNotificationPermission: async () => {
        if ('Notification' in window) {
          const permission = await Notification.requestPermission()
          return permission === 'granted'
        }
        return false
      },

      // Utilities
      getUnreadNotifications: () => {
        const { notifications } = get()
        return notifications.filter(n => !n.is_read)
      },

      getNotificationsByType: (type) => {
        const { notifications } = get()
        return notifications.filter(n => n.type === type)
      },

      getRecentNotifications: (hours = 24) => {
        const { notifications } = get()
        const cutoff = Date.now() - (hours * 60 * 60 * 1000)
        return notifications.filter(n => {
          const notificationTime = new Date(n.created_at).getTime()
          return notificationTime >= cutoff
        })
      },

      // Auto-connect helper
      autoConnect: () => {
        const token = localStorage.getItem('access_token')
        if (token && !get().isConnected && !get().isConnecting) {
          get().connect()
        }
      },

      // Status
      getConnectionStatus: () => {
        const { isConnected, isConnecting, connectionError } = get()
        return {
          isConnected,
          isConnecting,
          connectionError,
          wsStatus: websocketService.getStatus()
        }
      }
    }),
    {
      name: 'notification-store', // for debugging
    }
  )
)

export default useNotificationStore