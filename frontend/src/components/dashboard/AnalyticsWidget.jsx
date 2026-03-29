/**
 * Analytics Widget Component - Display user analytics and insights
 */
import React from 'react'
import useDashboardStore from '../../store/dashboardStore'

const AnalyticsWidget = ({ detailed = false }) => {
  const { analytics, personalInsights, isLoading, loadAnalytics, loadPersonalInsights } = useDashboardStore()

  React.useEffect(() => {
    if (detailed && !analytics) {
      loadAnalytics()
    }
    if (detailed && !personalInsights) {
      loadPersonalInsights()
    }
  }, [detailed, analytics, personalInsights, loadAnalytics, loadPersonalInsights])

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Your Analytics</h3>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  const getEngagementBadge = (score) => {
    if (score >= 70) {
      return { label: 'High Engagement', color: 'bg-green-100 text-green-800', icon: '🔥' }
    } else if (score >= 40) {
      return { label: 'Medium Engagement', color: 'bg-yellow-100 text-yellow-800', icon: '📈' }
    } else {
      return { label: 'Getting Started', color: 'bg-blue-100 text-blue-800', icon: '🌟' }
    }
  }

  const engagementBadge = getEngagementBadge(analytics?.engagement_score || 0)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Your Analytics</h3>

      {!analytics ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
            <span className="text-2xl">📊</span>
          </div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">Analytics Loading</h4>
          <p className="text-gray-600 text-sm">
            We're analyzing your usage patterns to provide personalized insights.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Engagement Score */}
          <div className="text-center">
            <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mb-2">
              <span className={`${engagementBadge.color} px-2 py-1 rounded-full flex items-center`}>
                <span className="mr-1">{engagementBadge.icon}</span>
                {engagementBadge.label}
              </span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">
              {analytics.engagement_score || 0}
              <span className="text-lg text-gray-500">/100</span>
            </div>
            <p className="text-sm text-gray-600">Engagement Score</p>
          </div>

          {/* Key Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-xl font-semibold text-gray-900">
                {analytics.total_interactions || 0}
              </div>
              <p className="text-xs text-gray-600">Total Interactions</p>
            </div>
            <div className="text-center">
              <div className="text-xl font-semibold text-gray-900">
                {analytics.recommendations_received || 0}
              </div>
              <p className="text-xs text-gray-600">Recommendations</p>
            </div>
          </div>

          {detailed && (
            <>
              {/* Interaction Breakdown */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Activity Breakdown</h4>
                <div className="space-y-2">
                  {Object.entries(analytics.interaction_breakdown || {}).map(([action, count]) => (
                    <div key={action} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 capitalize">
                        {action.replace('_', ' ')}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Personal Insights */}
              {personalInsights?.insights && personalInsights.insights.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">💡 Personal Insights</h4>
                  <div className="space-y-3">
                    {personalInsights.insights.slice(0, 3).map((insight, index) => (
                      <div key={index} className="bg-blue-50 rounded-lg p-3">
                        <h5 className="text-sm font-medium text-blue-900 mb-1">
                          {insight.title}
                        </h5>
                        <p className="text-xs text-blue-700">{insight.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations for Improvement */}
              {personalInsights?.recommendations_for_improvement && personalInsights.recommendations_for_improvement.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">🎯 Tips for You</h4>
                  <div className="space-y-2">
                    {personalInsights.recommendations_for_improvement.slice(0, 2).map((tip, index) => (
                      <div key={index} className="flex items-start">
                        <span className="flex-shrink-0 w-4 h-4 bg-yellow-100 rounded-full flex items-center justify-center mr-2 mt-0.5">
                          <span className="text-xs">💡</span>
                        </span>
                        <p className="text-xs text-gray-600">{tip}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {!detailed && (
            <div className="text-center">
              <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                View Detailed Analytics →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AnalyticsWidget