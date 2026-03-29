/**
 * Real-Time Toast Notification Component
 */
import React, { useState, useEffect } from 'react'
import useNotificationStore from '../../store/notificationStore'

const RealTimeToast = () => {
  const [activeToasts, setActiveToasts] = useState([])
  const { notifications } = useNotificationStore()

  useEffect(() => {
    // Listen for new notifications and show as toasts
    const unsubscribe = useNotificationStore.subscribe(
      (state) => state.notifications,
      (currentNotifications, previousNotifications) => {
        // Find newly added notifications
        if (previousNotifications) {
          const newNotifications = currentNotifications.filter(
            (current) => !previousNotifications.some(prev => prev.id === current.id)
          )

          // Add new notifications as toasts
          newNotifications.forEach((notification) => {
            showToast(notification)
          })
        }
      }
    )

    return unsubscribe
  }, [])

  const showToast = (notification) => {
    const toast = {
      id: notification.id,
      notification,
      timestamp: Date.now()
    }

    setActiveToasts(prev => [...prev, toast])

    // Auto-remove toast after 5 seconds
    setTimeout(() => {
      removeToast(toast.id)
    }, 5000)
  }

  const removeToast = (toastId) => {
    setActiveToasts(prev => prev.filter(toast => toast.id !== toastId))
  }

  const handleToastClick = (toast) => {
    // Mark as read and remove toast
    const { markAsRead } = useNotificationStore.getState()
    if (!toast.notification.is_read) {
      markAsRead(toast.notification.id)
    }
    removeToast(toast.id)
  }

  const getToastStyle = (type) => {
    switch (type) {
      case 'price_drop':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'new_recommendation':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      case 'back_in_stock':
        return 'bg-purple-50 border-purple-200 text-purple-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getToastIcon = (type) => {
    switch (type) {
      case 'price_drop':
        return (
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
            </svg>
          </div>
        )
      case 'new_recommendation':
        return (
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </div>
        )
      case 'back_in_stock':
        return (
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
        )
      default:
        return (
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
        )
    }
  }

  if (activeToasts.length === 0) {
    return null
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {activeToasts.map((toast, index) => (
        <div
          key={toast.id}
          className={`transform transition-all duration-300 ease-in-out ${
            index === 0 ? 'translate-x-0 opacity-100' : 'translate-x-2 opacity-95'
          }`}
          style={{
            transform: `translateY(${index * -8}px) translateX(${index * 4}px)`,
            zIndex: 50 - index
          }}
        >
          <div
            className={`max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden cursor-pointer hover:shadow-xl transition-shadow ${getToastStyle(toast.notification.type)}`}
            onClick={() => handleToastClick(toast)}
          >
            <div className="p-4">
              <div className="flex items-start">
                {getToastIcon(toast.notification.type)}
                <div className="ml-3 w-0 flex-1 pt-0.5">
                  <p className="text-sm font-medium">
                    {toast.notification.title}
                  </p>
                  <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                    {toast.notification.message}
                  </p>

                  {/* Show price info for price drop notifications */}
                  {toast.notification.type === 'price_drop' && toast.notification.data && (
                    <div className="mt-2 text-sm">
                      {toast.notification.data.old_price && toast.notification.data.new_price && (
                        <div className="flex items-center space-x-1 text-green-600">
                          <span className="line-through text-gray-500">
                            ₹{toast.notification.data.old_price}
                          </span>
                          <span>→</span>
                          <span className="font-semibold">
                            ₹{toast.notification.data.new_price}
                          </span>
                          {toast.notification.data.pct_change && (
                            <span className="text-xs">
                              ({toast.notification.data.pct_change}%)
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="ml-4 flex-shrink-0 flex">
                  <button
                    className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeToast(toast.id)
                    }}
                  >
                    <span className="sr-only">Close</span>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Progress bar for auto-dismiss */}
            <div className="bg-gray-200 h-1">
              <div
                className="bg-gray-400 h-1 transition-all duration-5000 ease-linear"
                style={{
                  width: '100%',
                  animation: 'shrink 5000ms linear forwards'
                }}
              />
            </div>
          </div>
        </div>
      ))}

      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  )
}

export default RealTimeToast