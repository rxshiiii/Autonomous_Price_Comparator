/**
 * Dashboard service for API calls and data management
 */
import apiClient from './api'

class DashboardService {
  /**
   * Get comprehensive dashboard overview data
   */
  async getDashboardOverview() {
    try {
      const response = await apiClient.get('/dashboard/overview')
      return response.data
    } catch (error) {
      console.error('Dashboard overview fetch error:', error)
      throw error
    }
  }

  /**
   * Get user recommendations with product details
   */
  async getRecommendations(limit = 10, includeViewed = false) {
    try {
      const response = await apiClient.get('/dashboard/recommendations', {
        params: { limit, include_viewed: includeViewed }
      })
      return response.data
    } catch (error) {
      console.error('Recommendations fetch error:', error)
      throw error
    }
  }

  /**
   * Track user interaction with a recommendation
   */
  async trackRecommendationFeedback(recommendationId, action, sessionId = null) {
    try {
      const response = await apiClient.post(`/dashboard/recommendations/${recommendationId}/feedback`, {
        action,
        session_id: sessionId
      })
      return response.data
    } catch (error) {
      console.error('Recommendation feedback error:', error)
      throw error
    }
  }

  /**
   * Get user analytics and engagement insights
   */
  async getUserAnalytics(days = 30) {
    try {
      const response = await apiClient.get('/dashboard/analytics', {
        params: { days }
      })
      return response.data
    } catch (error) {
      console.error('User analytics fetch error:', error)
      throw error
    }
  }

  /**
   * Track user interaction for analytics
   */
  async trackInteraction(actionType, resourceType, resourceId = null, metadata = {}) {
    try {
      // This would integrate with the analytics service
      console.log('Tracking interaction:', { actionType, resourceType, resourceId, metadata })

      // For now, we'll implement this as a fire-and-forget call
      // In production, this should be queued or batched for performance
      await apiClient.post('/analytics/track', {
        action_type: actionType,
        resource_type: resourceType,
        resource_id: resourceId,
        metadata
      })
    } catch (error) {
      // Don't throw on tracking errors - just log them
      console.warn('Analytics tracking error (non-critical):', error)
    }
  }

  /**
   * Get cached dashboard data or fetch fresh
   */
  async getCachedDashboardData(forceRefresh = false) {
    const cacheKey = 'dashboard_overview'
    const cacheExpiry = 30 * 60 * 1000 // 30 minutes

    if (!forceRefresh) {
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        const { data, timestamp } = JSON.parse(cached)
        if (Date.now() - timestamp < cacheExpiry) {
          return data
        }
      }
    }

    try {
      const freshData = await this.getDashboardOverview()

      // Cache the fresh data
      localStorage.setItem(cacheKey, JSON.stringify({
        data: freshData,
        timestamp: Date.now()
      }))

      return freshData
    } catch (error) {
      // If fresh fetch fails, return stale cache if available
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        const { data } = JSON.parse(cached)
        console.warn('Using stale dashboard data due to fetch error')
        return data
      }
      throw error
    }
  }

  /**
   * Clear dashboard cache
   */
  clearCache() {
    localStorage.removeItem('dashboard_overview')
  }

  /**
   * Batch track multiple interactions for performance
   */
  async batchTrackInteractions(interactions) {
    try {
      await apiClient.post('/analytics/batch-track', {
        interactions
      })
    } catch (error) {
      console.warn('Batch analytics tracking error (non-critical):', error)
    }
  }

  /**
   * Get product price history for charts
   */
  async getProductPriceHistory(productId, days = 30) {
    try {
      const response = await apiClient.get(`/products/${productId}/price-history`, {
        params: { days }
      })
      return response.data
    } catch (error) {
      console.error('Price history fetch error:', error)
      throw error
    }
  }

  /**
   * Quick actions for dashboard interactions
   */
  async quickTrackProduct(productId) {
    try {
      const response = await apiClient.post('/products/track', { product_id: productId })

      // Track the interaction
      await this.trackInteraction('track', 'product', productId, {
        source: 'dashboard_quick_action'
      })

      return response.data
    } catch (error) {
      console.error('Quick track product error:', error)
      throw error
    }
  }

  async quickCreatePriceAlert(productId, targetPrice, alertType = 'below_price') {
    try {
      const response = await apiClient.post('/price-alerts', {
        product_id: productId,
        target_price: targetPrice,
        alert_type: alertType
      })

      // Track the interaction
      await this.trackInteraction('create_alert', 'product', productId, {
        target_price: targetPrice,
        alert_type: alertType,
        source: 'dashboard_quick_action'
      })

      return response.data
    } catch (error) {
      console.error('Quick create alert error:', error)
      throw error
    }
  }

  async markNotificationAsRead(notificationId) {
    try {
      const response = await apiClient.patch(`/notifications/${notificationId}/read`)

      // Track the interaction
      await this.trackInteraction('mark_read', 'notification', notificationId)

      return response.data
    } catch (error) {
      console.error('Mark notification read error:', error)
      throw error
    }
  }

  /**
   * Search products with caching
   */
  async searchProducts(query, filters = {}, page = 1, limit = 20) {
    try {
      const response = await apiClient.get('/products/search', {
        params: { q: query, page, limit, ...filters }
      })

      // Track search interaction
      await this.trackInteraction('search', 'product', null, {
        query,
        filters,
        results_count: response.data?.total || 0
      })

      return response.data
    } catch (error) {
      console.error('Product search error:', error)
      throw error
    }
  }

  /**
   * Get personalized insights
   */
  async getPersonalInsights() {
    try {
      const response = await apiClient.get('/analytics/insights')
      return response.data
    } catch (error) {
      console.error('Personal insights fetch error:', error)
      throw error
    }
  }

  /**
   * Update dashboard preferences
   */
  async updateDashboardPreferences(preferences) {
    try {
      const response = await apiClient.put('/dashboard/preferences', preferences)
      return response.data
    } catch (error) {
      console.error('Dashboard preferences update error:', error)
      throw error
    }
  }

  /**
   * Export user data (for GDPR compliance)
   */
  async exportUserData() {
    try {
      const response = await apiClient.get('/dashboard/export', {
        responseType: 'blob'
      })

      // Create download link
      const blob = new Blob([response.data], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `dashboard-export-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      await this.trackInteraction('export_data', 'dashboard')

      return true
    } catch (error) {
      console.error('Data export error:', error)
      throw error
    }
  }
}

// Create singleton instance
const dashboardService = new DashboardService()

export default dashboardService