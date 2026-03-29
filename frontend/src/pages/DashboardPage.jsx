import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { authService } from '../services/authService'
import useDashboardStore from '../store/dashboardStore'
import useNotificationStore from '../store/notificationStore' // From Phase 5
import NotificationDropdown from '../components/notifications/NotificationDropdown' // From Phase 5

// Dashboard components (will be created next)
import DashboardLayout from '../components/dashboard/DashboardLayout'
import OverviewSection from '../components/dashboard/OverviewSection'
import RecommendationsPanel from '../components/dashboard/RecommendationsPanel'
import PriceTrackingPanel from '../components/dashboard/PriceTrackingPanel'
import QuickActions from '../components/dashboard/QuickActions'
import AnalyticsWidget from '../components/dashboard/AnalyticsWidget'
import WelcomeBanner from '../components/dashboard/WelcomeBanner'

function DashboardPage() {
  const navigate = useNavigate()

  // User data from existing auth system
  const { data: user, isLoading: userLoading, error: userError } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authService.getCurrentUser,
    retry: false,
  })

  // Dashboard state management
  const {
    overview,
    isLoading,
    isRefreshing,
    error,
    selectedTab,
    viewMode,
    lastUpdated,
    loadDashboard,
    setSelectedTab,
    clearError,
    initialize,
    getUnviewedRecommendationsCount,
    getTriggeredAlertsCount,
    getUnreadNotificationsCount,
    getEngagementLevel
  } = useDashboardStore()

  // Notification integration from Phase 5
  const { autoConnect } = useNotificationStore()

  // Initialize dashboard and notifications
  useEffect(() => {
    if (user) {
      initialize()
      autoConnect() // Connect to real-time notifications
    }
  }, [user, initialize, autoConnect])

  const handleLogout = () => {
    authService.logout()
    navigate('/login')
  }

  const handleRefresh = () => {
    clearError()
    loadDashboard(true)
  }

  // Loading state
  if (userLoading || (isLoading && !overview)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full mx-4">
          <div className="flex items-center justify-center mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">Loading Dashboard</h3>
          <p className="text-sm text-gray-600 text-center">
            Preparing your personalized product tracking hub...
          </p>
        </div>
      </div>
    )
  }

  // Error state
  if (userError && !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Access Error</h3>
            <p className="text-sm text-gray-600 mb-4">Failed to load user data</p>
            <button
              onClick={() => navigate('/login')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Get summary stats for quick overview
  const summaryStats = {
    unviewedRecommendations: getUnviewedRecommendationsCount(),
    triggeredAlerts: getTriggeredAlertsCount(),
    unreadNotifications: getUnreadNotificationsCount(),
    engagementLevel: getEngagementLevel()
  }

  return (
    <DashboardLayout user={user} onLogout={handleLogout}>
      {/* Header with user info and notifications */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                Dashboard
              </h1>
              {isRefreshing && (
                <div className="ml-3 flex items-center text-sm text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                  Refreshing...
                </div>
              )}
            </div>

            <div className="flex items-center space-x-4">
              {/* Refresh button */}
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
                title="Refresh dashboard"
              >
                <svg className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>

              {/* Notifications from Phase 5 */}
              <NotificationDropdown />

              {/* User menu */}
              <div className="flex items-center">
                <span className="text-sm text-gray-700 mr-3">
                  Welcome, {user?.full_name || user?.email}!
                </span>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main dashboard content */}
      <div className="flex-1 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

          {/* Welcome banner for new users or important updates */}
          <WelcomeBanner
            user={user}
            summaryStats={summaryStats}
            onDismiss={() => {}}
          />

          {/* Error message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Dashboard Error</h3>
                  <div className="mt-1 text-sm text-red-700">{error}</div>
                  <div className="mt-3">
                    <button
                      onClick={handleRefresh}
                      className="bg-red-100 text-red-800 px-3 py-1 rounded text-sm hover:bg-red-200 transition-colors"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab navigation */}
          <div className="mb-8">
            <nav className="flex space-x-8">
              {[
                { key: 'overview', label: 'Overview', count: null },
                { key: 'recommendations', label: 'AI Recommendations', count: summaryStats.unviewedRecommendations },
                { key: 'tracking', label: 'Price Tracking', count: summaryStats.triggeredAlerts },
                { key: 'analytics', label: 'Insights', count: null }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setSelectedTab(tab.key)}
                  className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                    selectedTab === tab.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                  {tab.count > 0 && (
                    <span className="ml-2 bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab content */}
          <div className="space-y-8">
            {selectedTab === 'overview' && (
              <>
                <OverviewSection overview={overview} isLoading={isLoading} />
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <RecommendationsPanel limit={6} />
                  <PriceTrackingPanel limit={8} />
                </div>
                <QuickActions />
              </>
            )}

            {selectedTab === 'recommendations' && (
              <RecommendationsPanel showAll={true} />
            )}

            {selectedTab === 'tracking' && (
              <PriceTrackingPanel showAll={true} />
            )}

            {selectedTab === 'analytics' && (
              <AnalyticsWidget detailed={true} />
            )}
          </div>

          {/* Last updated indicator */}
          {lastUpdated && (
            <div className="mt-8 text-center">
              <p className="text-sm text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()} •
                <button
                  onClick={handleRefresh}
                  className="ml-1 text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Refresh now
                </button>
              </p>
            </div>
          )}

        </div>
      </div>
    </DashboardLayout>
  )
}

export default DashboardPage

export default DashboardPage
