/**
 * Welcome Banner Component - Greeting and quick stats for users
 */
import React, { useState } from 'react'

const WelcomeBanner = ({ user, summaryStats, onDismiss }) => {
  const [isDismissed, setIsDismissed] = useState(false)

  if (isDismissed) return null

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  const getEngagementMessage = () => {
    const level = summaryStats.engagementLevel
    switch (level) {
      case 'high':
        return "You're making excellent use of the platform! 🚀"
      case 'medium':
        return "You're on track! Keep exploring for better deals. 💪"
      case 'low':
        return "Welcome back! Check out your new recommendations. ✨"
      default:
        return "Welcome to your personalized dashboard! 🎉"
    }
  }

  const handleDismiss = () => {
    setIsDismissed(true)
    onDismiss()
  }

  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 mb-8 text-white relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-10">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="relative">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">
              {getGreeting()}, {user?.full_name?.split(' ')[0] || 'there'}! 👋
            </h2>
            <p className="text-blue-100 mb-4">
              {getEngagementMessage()}
            </p>

            {/* Quick stats */}
            <div className="flex flex-wrap gap-6">
              {summaryStats.unviewedRecommendations > 0 && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-sm">
                    {summaryStats.unviewedRecommendations} new recommendations
                  </span>
                </div>
              )}

              {summaryStats.triggeredAlerts > 0 && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-sm">
                    {summaryStats.triggeredAlerts} price alerts triggered
                  </span>
                </div>
              )}

              {summaryStats.unreadNotifications > 0 && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-red-400 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-sm">
                    {summaryStats.unreadNotifications} unread notifications
                  </span>
                </div>
              )}

              {Object.values(summaryStats).every(val => val === 0 || val === 'unknown') && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-white rounded-full mr-2"></div>
                  <span className="text-sm">All caught up! 🎉</span>
                </div>
              )}
            </div>
          </div>

          {/* Dismiss button */}
          <button
            onClick={handleDismiss}
            className="text-white/70 hover:text-white transition-colors p-1"
            title="Dismiss banner"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Call-to-action based on engagement level */}
        <div className="mt-4 pt-4 border-t border-white/20">
          {summaryStats.engagementLevel === 'low' && (
            <p className="text-sm text-blue-100">
              💡 <strong>Tip:</strong> Track products you're interested in to get personalized price drop alerts!
            </p>
          )}

          {summaryStats.engagementLevel === 'medium' && (
            <p className="text-sm text-blue-100">
              🎯 <strong>Pro tip:</strong> Review your AI recommendations regularly to discover great deals tailored for you.
            </p>
          )}

          {summaryStats.engagementLevel === 'high' && (
            <p className="text-sm text-blue-100">
              🏆 <strong>Keep it up!</strong> You're maximizing your savings potential. Share the platform with friends!
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default WelcomeBanner