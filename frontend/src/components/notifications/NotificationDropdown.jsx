/**
 * Notification Dropdown Component - Shows notification list in dropdown
 */
import React, { useState, useRef, useEffect } from 'react'
import useNotificationStore from '../../store/notificationStore'
import NotificationBadge from './NotificationBadge'
import NotificationItem from './NotificationItem'

const NotificationDropdown = () => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  const {
    notifications,
    unreadCount,
    isConnected,
    isConnecting,
    connectionError,
    connect,
    disconnect,
    markAllAsRead,
    autoConnect
  } = useNotificationStore()

  // Auto-connect on mount if user is logged in
  useEffect(() => {
    autoConnect()
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  const handleNotificationClick = (notification) => {
    console.log('Notification clicked:', notification)
    // Handle navigation based on notification type
    // You can add routing logic here
  }

  const handleMarkAllAsRead = () => {
    markAllAsRead()
  }

  const handleRetryConnection = () => {
    connect()
  }

  const recentNotifications = notifications.slice(0, 10) // Show latest 10

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Notification Badge Button */}
      <button
        onClick={handleToggle}
        className="relative p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        title={`${unreadCount} unread notifications`}
      >
        <NotificationBadge />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                Notifications
                {unreadCount > 0 && (
                  <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                    {unreadCount} new
                  </span>
                )}
              </h3>
              <div className="flex items-center space-x-2">
                {/* Connection Status */}
                <div className={`flex items-center text-xs ${
                  isConnected ? 'text-green-600' : 'text-gray-500'
                }`}>
                  <div className={`w-2 h-2 rounded-full mr-1 ${
                    isConnected ? 'bg-green-400' : 'bg-gray-400'
                  }`} />
                  {isConnecting ? 'Connecting...' : isConnected ? 'Live' : 'Offline'}
                </div>

                {/* Mark All as Read */}
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllAsRead}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Mark all read
                  </button>
                )}
              </div>
            </div>

            {/* Connection Error */}
            {connectionError && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                <div className="flex items-center justify-between">
                  <span>Connection error: {connectionError}</span>
                  <button
                    onClick={handleRetryConnection}
                    className="ml-2 text-red-600 hover:text-red-800 underline"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Notification List */}
          <div className="max-h-64 overflow-y-auto">
            {recentNotifications.length > 0 ? (
              <div className="divide-y divide-gray-100">
                {recentNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onClick={handleNotificationClick}
                    showActions={true}
                  />
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
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
                <p className="mt-2 text-sm font-medium">No notifications</p>
                <p className="text-xs">When you receive notifications, they'll appear here.</p>
              </div>
            )}
          </div>

          {/* Footer */}
          {recentNotifications.length > 0 && (
            <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => {
                  setIsOpen(false)
                  // Navigate to full notifications page
                  // You can add routing logic here
                }}
                className="w-full text-center text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                View all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default NotificationDropdown