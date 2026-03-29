/**
 * Notification Item Component - Displays individual notification
 */
import React from 'react'
import useNotificationStore from '../../store/notificationStore'

const NotificationItem = ({ notification, onClick, showActions = true }) => {
  const { markAsRead, removeNotification } = useNotificationStore()

  const handleMarkAsRead = (e) => {
    e.stopPropagation()
    if (!notification.is_read) {
      markAsRead(notification.id)
    }
  }

  const handleRemove = (e) => {
    e.stopPropagation()
    removeNotification(notification.id)
  }

  const handleClick = () => {
    // Mark as read when clicked
    if (!notification.is_read) {
      markAsRead(notification.id)
    }

    // Call external onClick handler
    if (onClick) {
      onClick(notification)
    }
  }

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'price_drop':
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M7 14l3-3 3 3 5-5-1.5-1.5L12 12 9 9l-2 2z"/>
            </svg>
          </div>
        )
      case 'new_recommendation':
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </div>
        )
      case 'back_in_stock':
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
            </svg>
          </div>
        )
      default:
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
        )
    }
  }

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInSeconds = Math.floor((now - date) / 1000)

    if (diffInSeconds < 60) return 'Just now'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
    return `${Math.floor(diffInSeconds / 86400)}d ago`
  }

  return (
    <div
      className={`p-4 border-b border-gray-100 cursor-pointer transition-colors hover:bg-gray-50 ${
        !notification.is_read ? 'bg-blue-50' : 'bg-white'
      }`}
      onClick={handleClick}
    >
      <div className="flex items-start space-x-3">
        {/* Notification Icon */}
        {getNotificationIcon(notification.type)}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className={`text-sm font-medium ${
                !notification.is_read ? 'text-gray-900' : 'text-gray-700'
              }`}>
                {notification.title}
              </p>
              <p className={`mt-1 text-sm ${
                !notification.is_read ? 'text-gray-600' : 'text-gray-500'
              }`}>
                {notification.message}
              </p>

              {/* Additional data display */}
              {notification.data && notification.data.product_name && (
                <p className="mt-1 text-xs text-gray-500">
                  Product: {notification.data.product_name}
                </p>
              )}

              {notification.data && notification.data.old_price && notification.data.new_price && (
                <p className="mt-1 text-xs text-green-600">
                  ₹{notification.data.old_price} → ₹{notification.data.new_price}
                  {notification.data.pct_change && (
                    <span className="ml-1">({notification.data.pct_change}%)</span>
                  )}
                </p>
              )}
            </div>

            {/* Actions */}
            {showActions && (
              <div className="flex items-center space-x-2 ml-2">
                {!notification.is_read && (
                  <button
                    onClick={handleMarkAsRead}
                    className="text-xs text-blue-600 hover:text-blue-800"
                    title="Mark as read"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                    </svg>
                  </button>
                )}
                <button
                  onClick={handleRemove}
                  className="text-xs text-gray-400 hover:text-gray-600"
                  title="Remove"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <p className="mt-2 text-xs text-gray-400">
            {formatTimeAgo(notification.created_at)}
          </p>
        </div>

        {/* Unread indicator */}
        {!notification.is_read && (
          <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
        )}
      </div>
    </div>
  )
}

export default NotificationItem