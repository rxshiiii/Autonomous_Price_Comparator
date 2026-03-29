/**
 * Recommendations Panel Component - Display AI recommendations with GROQ reasoning
 */
import React from 'react'
import useDashboardStore from '../../store/dashboardStore'

const RecommendationsPanel = ({ limit = 6, showAll = false }) => {
  const { recommendations, isLoading, trackRecommendationAction } = useDashboardStore()

  const displayRecommendations = showAll ? recommendations : recommendations.slice(0, limit)

  const handleRecommendationClick = async (recommendationId, action = 'clicked') => {
    await trackRecommendationAction(recommendationId, action)
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🤖 AI Recommendations</h3>
        <div className="space-y-4">
          {[...Array(limit)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-2"></div>
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">🤖 AI Recommendations</h3>
        {!showAll && recommendations.length > limit && (
          <button className="text-blue-600 hover:text-blue-800 text-sm">
            View all ({recommendations.length})
          </button>
        )}
      </div>

      {displayRecommendations.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-2xl">🤖</span>
          </div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">No recommendations yet</h4>
          <p className="text-gray-600 text-sm">
            Our AI is analyzing your preferences. Check back soon for personalized product recommendations!
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {displayRecommendations.map((recommendation) => (
            <div
              key={recommendation.id}
              className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
              onClick={() => handleRecommendationClick(recommendation.id, 'clicked')}
            >
              <div className="flex items-start space-x-4">
                <img
                  src={recommendation.product?.image_url || '/placeholder-product.png'}
                  alt={recommendation.product?.name}
                  className="w-16 h-16 rounded-lg object-cover"
                />
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {recommendation.product?.name}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">
                    ₹{recommendation.product?.current_price} • {recommendation.product?.platform}
                  </p>
                  <div className="flex items-center mt-2">
                    <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                      {Math.round(recommendation.score * 100)}% match
                    </div>
                    {recommendation.reasoning && (
                      <p className="text-xs text-gray-500 ml-2 truncate">
                        {recommendation.reasoning.slice(0, 100)}...
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default RecommendationsPanel