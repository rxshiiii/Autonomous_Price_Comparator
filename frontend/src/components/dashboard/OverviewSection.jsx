/**
 * Overview Section Component - Main dashboard overview with key metrics
 */
import React from 'react'

const OverviewSection = ({ overview, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded mb-4"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    )
  }

  const summary = overview?.summary || {}

  const stats = [
    {
      name: 'AI Recommendations',
      value: summary.total_recommendations || 0,
      change: summary.unviewed_recommendations || 0,
      changeLabel: 'unviewed',
      icon: '🤖',
      color: 'blue'
    },
    {
      name: 'Tracked Products',
      value: summary.tracked_products_count || 0,
      change: summary.triggered_alerts_count || 0,
      changeLabel: 'alerts triggered',
      icon: '📊',
      color: 'green'
    },
    {
      name: 'Price Alerts',
      value: summary.active_alerts_count || 0,
      change: summary.triggered_alerts_count || 0,
      changeLabel: 'triggered',
      icon: '🔔',
      color: 'yellow'
    },
    {
      name: 'Notifications',
      value: (overview?.recent_notifications || []).length,
      change: summary.unread_notifications || 0,
      changeLabel: 'unread',
      icon: '📬',
      color: 'purple'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {stats.map((stat, index) => (
        <div key={stat.name} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className={`w-8 h-8 bg-${stat.color}-100 rounded-lg flex items-center justify-center`}>
                <span className="text-lg">{stat.icon}</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">{stat.name}</dt>
                <dd>
                  <div className="text-lg font-medium text-gray-900">{stat.value}</div>
                </dd>
              </dl>
            </div>
          </div>
          {stat.change > 0 && (
            <div className="mt-2">
              <div className={`text-sm text-${stat.color}-600`}>
                {stat.change} {stat.changeLabel}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default OverviewSection