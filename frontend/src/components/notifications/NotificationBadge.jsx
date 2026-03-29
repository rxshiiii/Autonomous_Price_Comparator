/**
 * Notification Badge Component - Shows unread notification count
 */
import React from 'react'
import useNotificationStore from '../../store/notificationStore'

const NotificationBadge = ({ className = '', showZero = false }) => {
  const { unreadCount, isConnected } = useNotificationStore()

  if (unreadCount === 0 && !showZero) {
    return null
  }

  return (
    <div className={`relative ${className}`}>
      {/* Notification Bell Icon */}
      <svg
        className={`w-6 h-6 ${isConnected ? 'text-gray-600' : 'text-gray-400'} hover:text-gray-800 transition-colors`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>

      {/* Badge */}
      {(unreadCount > 0 || showZero) && (
        <span className="absolute -top-2 -right-2 flex items-center justify-center min-w-5 h-5 px-1 text-xs font-bold text-white bg-red-500 rounded-full">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}

      {/* Connection status indicator */}
      <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${
        isConnected ? 'bg-green-400' : 'bg-gray-400'
      }`} title={isConnected ? 'Connected' : 'Disconnected'} />
    </div>
  )
}

export default NotificationBadge