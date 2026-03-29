/**
 * Quick Actions Component - Quick action buttons for common tasks
 */
import React from 'react'
import { useNavigate } from 'react-router-dom'

const QuickActions = () => {
  const navigate = useNavigate()

  const actions = [
    {
      name: 'Search Products',
      description: 'Find and compare products across platforms',
      icon: '🔍',
      action: () => navigate('/products'),
      color: 'blue'
    },
    {
      name: 'Create Price Alert',
      description: 'Get notified when prices drop',
      icon: '🔔',
      action: () => navigate('/alerts'),
      color: 'yellow'
    },
    {
      name: 'View Recommendations',
      description: 'See AI-powered product suggestions',
      icon: '🤖',
      action: () => navigate('/recommendations'),
      color: 'purple'
    },
    {
      name: 'Track Products',
      description: 'Add products to your watchlist',
      icon: '⭐',
      action: () => navigate('/tracking'),
      color: 'green'
    }
  ]

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">⚡ Quick Actions</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((action) => (
          <button
            key={action.name}
            onClick={action.action}
            className="text-left p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all"
          >
            <div className={`w-8 h-8 bg-${action.color}-100 rounded-lg flex items-center justify-center mb-3`}>
              <span className="text-lg">{action.icon}</span>
            </div>
            <h4 className="font-medium text-gray-900 mb-1">{action.name}</h4>
            <p className="text-sm text-gray-600">{action.description}</p>
          </button>
        ))}
      </div>
    </div>
  )
}

export default QuickActions