/**
 * Notification Step - Configure notification preferences
 */
import React, { useState } from 'react'

const NotificationStep = ({ onNext, onPrevious, isSubmitting, canGoBack }) => {
  const [prefs, setPrefs] = useState({
    websocket_enabled: true,
    email_enabled: true,
    max_notifications_per_day: 5,
    price_drop_threshold: 10
  })

  const handleNext = () => {
    onNext(prefs)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Notification preferences</h2>
        <p className="text-gray-600">Choose how you want to receive updates</p>
      </div>

      {/* Notification channels */}
      <div className="space-y-3">
        <label className="flex items-center p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
          <input
            type="checkbox"
            checked={prefs.websocket_enabled}
            onChange={(e) => setPrefs(prev => ({ ...prev, websocket_enabled: e.target.checked }))}
            className="w-5 h-5 text-blue-600 rounded"
          />
          <div className="ml-3 flex-1">
            <h4 className="font-medium text-gray-900">Real-time notifications</h4>
            <p className="text-sm text-gray-600">Get instant alerts while you're browsing</p>
          </div>
        </label>

        <label className="flex items-center p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
          <input
            type="checkbox"
            checked={prefs.email_enabled}
            onChange={(e) => setPrefs(prev => ({ ...prev, email_enabled: e.target.checked }))}
            className="w-5 h-5 text-blue-600 rounded"
          />
          <div className="ml-3 flex-1">
            <h4 className="font-medium text-gray-900">Email notifications</h4>
            <p className="text-sm text-gray-600">Get important updates via email</p>
          </div>
        </label>
      </div>

      {/* Settings */}
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Maximum notifications per day
          </label>
          <select
            value={prefs.max_notifications_per_day}
            onChange={(e) => setPrefs(prev => ({ ...prev, max_notifications_per_day: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {[3, 5, 10, 20, 50].map(num => (
              <option key={num} value={num}>{num} notifications</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Minimum price drop threshold
          </label>
          <select
            value={prefs.price_drop_threshold}
            onChange={(e) => setPrefs(prev => ({ ...prev, price_drop_threshold: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {[5, 10, 15, 20, 25].map(pct => (
              <option key={pct} value={pct}>{pct}%</option>
            ))}
          </select>
        </div>
      </div>

      {/* Buttons */}
      <div className="flex gap-3">
        {canGoBack && (
          <button
            onClick={onPrevious}
            className="px-6 bg-gray-200 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors"
          >
            Back
          </button>
        )}
        <button
          onClick={handleNext}
          disabled={isSubmitting}
          className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Loading...' : 'Continue'}
        </button>
      </div>
    </div>
  )
}

export default NotificationStep