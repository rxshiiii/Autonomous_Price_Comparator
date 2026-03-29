/**
 * Price Tracking Panel Component - Display tracked products with price trends
 */
import React from 'react'
import useDashboardStore from '../../store/dashboardStore'

const PriceTrackingPanel = ({ limit = 8, showAll = false }) => {
  const { trackedProducts, priceAlerts, isLoading } = useDashboardStore()

  const displayProducts = showAll ? trackedProducts : trackedProducts.slice(0, limit)

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Price Tracking</h3>
        <div className="space-y-4">
          {[...Array(limit)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-2"></div>
              <div className="h-16 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return '📈'
      case 'down': return '📉'
      default: return '➡️'
    }
  }

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'up': return 'text-red-600'
      case 'down': return 'text-green-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">📊 Price Tracking</h3>
        {!showAll && trackedProducts.length > limit && (
          <button className="text-blue-600 hover:text-blue-800 text-sm">
            View all ({trackedProducts.length})
          </button>
        )}
      </div>

      {displayProducts.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
            <span className="text-2xl">📊</span>
          </div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">Start tracking products</h4>
          <p className="text-gray-600 text-sm">
            Track products you're interested in to monitor price changes and get alerts!
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayProducts.map((item) => (
            <div key={item.id} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
              <img
                src={item.product?.image_url || '/placeholder-product.png'}
                alt={item.product?.name}
                className="w-12 h-12 rounded object-cover"
              />
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-gray-900 truncate">
                  {item.product?.name}
                </h4>
                <p className="text-sm text-gray-600">
                  ₹{item.product?.current_price}
                </p>
              </div>
              <div className="text-right">
                <div className={`flex items-center text-sm ${getTrendColor(item.price_trend)}`}>
                  <span className="mr-1">{getTrendIcon(item.price_trend)}</span>
                  {item.price_change_percent !== 0 && (
                    <span>{Math.abs(item.price_change_percent).toFixed(1)}%</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default PriceTrackingPanel