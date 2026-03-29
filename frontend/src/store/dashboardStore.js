/**
 * Dashboard state management with Zustand
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import dashboardService from '../services/dashboardService'

const useDashboardStore = create(
  devtools(
    (set, get) => ({
      // Dashboard data
      overview: null,
      recommendations: [],
      trackedProducts: [],
      priceAlerts: [],
      recentNotifications: [],
      analytics: null,
      personalInsights: null,

      // UI state
      isLoading: false,
      isRefreshing: false,
      error: null,
      lastUpdated: null,
      selectedTab: 'overview',
      viewMode: 'grid', // grid or list

      // Preferences
      preferences: {
        showRecommendations: true,
        showPriceAlerts: true,
        showTrackedProducts: true,
        showNotifications: true,
        recommendationsLimit: 10,
        trackedProductsLimit: 20,
        autoRefresh: true,
        refreshInterval: 5 * 60 * 1000 // 5 minutes
      },

      // Actions
      loadDashboard: async (forceRefresh = false) => {
        const { isLoading } = get()
        if (isLoading) return // Prevent concurrent loads

        set({
          isLoading: !forceRefresh,
          isRefreshing: forceRefresh,
          error: null
        })

        try {
          const dashboardData = await dashboardService.getCachedDashboardData(forceRefresh)

          set({
            overview: dashboardData,
            recommendations: dashboardData.recommendations || [],
            trackedProducts: dashboardData.tracked_products || [],
            priceAlerts: dashboardData.price_alerts || [],
            recentNotifications: dashboardData.recent_notifications || [],
            analytics: dashboardData.analytics || null,
            isLoading: false,
            isRefreshing: false,
            lastUpdated: new Date(),
            error: null
          })

          // Load additional data if needed
          if (dashboardData.recommendations?.length === 0) {
            await get().loadRecommendations()
          }

        } catch (error) {
          console.error('Dashboard load error:', error)
          set({
            isLoading: false,
            isRefreshing: false,
            error: 'Failed to load dashboard data. Please try again.'
          })
        }
      },

      loadRecommendations: async (limit = 10, includeViewed = false) => {
        try {
          const recommendations = await dashboardService.getRecommendations(limit, includeViewed)
          set({ recommendations })
        } catch (error) {
          console.error('Recommendations load error:', error)
        }
      },

      trackRecommendationAction: async (recommendationId, action) => {
        try {
          await dashboardService.trackRecommendationFeedback(recommendationId, action)

          // Update local state
          const { recommendations } = get()
          const updatedRecommendations = recommendations.map(rec =>
            rec.id === recommendationId
              ? { ...rec, user_action: action, shown_to_user: ['viewed', 'clicked'].includes(action) }
              : rec
          )

          set({ recommendations: updatedRecommendations })

          // Track analytics
          await dashboardService.trackInteraction(action, 'recommendation', recommendationId)

        } catch (error) {
          console.error('Recommendation tracking error:', error)
        }
      },

      quickTrackProduct: async (productId) => {
        try {
          await dashboardService.quickTrackProduct(productId)

          // Refresh tracked products
          await get().refreshTrackedProducts()

          return { success: true, message: 'Product tracked successfully!' }
        } catch (error) {
          console.error('Quick track error:', error)
          return { success: false, message: 'Failed to track product. Please try again.' }
        }
      },

      quickCreateAlert: async (productId, targetPrice) => {
        try {
          await dashboardService.quickCreatePriceAlert(productId, targetPrice)

          // Refresh price alerts
          await get().refreshPriceAlerts()

          return { success: true, message: 'Price alert created successfully!' }
        } catch (error) {
          console.error('Quick alert error:', error)
          return { success: false, message: 'Failed to create price alert. Please try again.' }
        }
      },

      markNotificationRead: async (notificationId) => {
        try {
          await dashboardService.markNotificationAsRead(notificationId)

          // Update local state
          const { recentNotifications } = get()
          const updatedNotifications = recentNotifications.map(notif =>
            notif.id === notificationId ? { ...notif, is_read: true } : notif
          )

          set({ recentNotifications: updatedNotifications })

        } catch (error) {
          console.error('Mark notification read error:', error)
        }
      },

      refreshTrackedProducts: async () => {
        try {
          const overview = await dashboardService.getDashboardOverview()
          set({ trackedProducts: overview.tracked_products || [] })
        } catch (error) {
          console.error('Refresh tracked products error:', error)
        }
      },

      refreshPriceAlerts: async () => {
        try {
          const overview = await dashboardService.getDashboardOverview()
          set({ priceAlerts: overview.price_alerts || [] })
        } catch (error) {
          console.error('Refresh price alerts error:', error)
        }
      },

      loadAnalytics: async (days = 30) => {
        try {
          const analytics = await dashboardService.getUserAnalytics(days)
          set({ analytics })
        } catch (error) {
          console.error('Analytics load error:', error)
        }
      },

      loadPersonalInsights: async () => {
        try {
          const insights = await dashboardService.getPersonalInsights()
          set({ personalInsights: insights })
        } catch (error) {
          console.error('Personal insights load error:', error)
        }
      },

      setSelectedTab: (tab) => {
        set({ selectedTab: tab })

        // Track tab view
        dashboardService.trackInteraction('tab_view', 'dashboard', null, { tab })
      },

      setViewMode: (mode) => {
        set({ viewMode: mode })
        localStorage.setItem('dashboard_view_mode', mode)
      },

      updatePreferences: async (newPreferences) => {
        try {
          const updatedPrefs = { ...get().preferences, ...newPreferences }
          await dashboardService.updateDashboardPreferences(updatedPrefs)

          set({ preferences: updatedPrefs })
          localStorage.setItem('dashboard_preferences', JSON.stringify(updatedPrefs))

          return { success: true }
        } catch (error) {
          console.error('Preferences update error:', error)
          return { success: false, error: 'Failed to update preferences' }
        }
      },

      clearError: () => set({ error: null }),

      clearCache: () => {
        dashboardService.clearCache()
        set({
          overview: null,
          recommendations: [],
          trackedProducts: [],
          priceAlerts: [],
          recentNotifications: [],
          analytics: null,
          personalInsights: null,
          lastUpdated: null
        })
      },

      // Utility functions
      getUnviewedRecommendationsCount: () => {
        const { recommendations } = get()
        return recommendations.filter(rec => !rec.shown_to_user).length
      },

      getTriggeredAlertsCount: () => {
        const { priceAlerts } = get()
        return priceAlerts.filter(alert => alert.status === 'triggered').length
      },

      getUnreadNotificationsCount: () => {
        const { recentNotifications } = get()
        return recentNotifications.filter(notif => !notif.is_read).length
      },

      getEngagementLevel: () => {
        const { analytics } = get()
        if (!analytics) return 'unknown'

        const score = analytics.engagement_score || 0
        if (score >= 70) return 'high'
        if (score >= 40) return 'medium'
        return 'low'
      },

      // Auto-refresh functionality
      startAutoRefresh: () => {
        const { preferences } = get()
        if (!preferences.autoRefresh) return

        const interval = setInterval(() => {
          const state = get()
          if (state.selectedTab === 'overview' && !state.isLoading) {
            state.loadDashboard(true)
          }
        }, preferences.refreshInterval)

        set({ refreshInterval: interval })
      },

      stopAutoRefresh: () => {
        const { refreshInterval } = get()
        if (refreshInterval) {
          clearInterval(refreshInterval)
          set({ refreshInterval: null })
        }
      },

      // Initialize store
      initialize: () => {
        // Load saved preferences
        const savedPrefs = localStorage.getItem('dashboard_preferences')
        if (savedPrefs) {
          try {
            const preferences = JSON.parse(savedPrefs)
            set({ preferences: { ...get().preferences, ...preferences } })
          } catch (error) {
            console.warn('Failed to parse saved dashboard preferences')
          }
        }

        // Load saved view mode
        const savedViewMode = localStorage.getItem('dashboard_view_mode')
        if (savedViewMode) {
          set({ viewMode: savedViewMode })
        }

        // Start auto-refresh if enabled
        const { preferences } = get()
        if (preferences.autoRefresh) {
          get().startAutoRefresh()
        }

        // Load initial dashboard data
        get().loadDashboard()
      }
    }),
    {
      name: 'dashboard-store',
    }
  )
)

export default useDashboardStore