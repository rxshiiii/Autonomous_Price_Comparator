/**
 * Welcome Step - Introduction and data usage consent
 */
import React, { useState } from 'react'

const WelcomeStep = ({ onNext, onSkip, isSubmitting, canSkip }) => {
  const [agreedToTerms, setAgreedToTerms] = useState(false)

  const handleNext = () => {
    if (agreedToTerms) {
      onNext({})
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
          <span className="text-3xl">🎯</span>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Price Comparator!</h2>
        <p className="text-gray-600">
          Your personal shopping companion for finding the best deals across India's top e-commerce platforms.
        </p>
      </div>

      {/* Features overview */}
      <div className="space-y-3">
        <h3 className="font-semibold text-gray-900">What you can do:</h3>
        <ul className="space-y-2">
          {[
            { icon: '🤖', text: 'Get AI-powered product recommendations based on your preferences' },
            { icon: '💰', text: 'Track product prices and get instant alerts when they drop' },
            { icon: '🔍', text: 'Compare prices across multiple platforms simultaneously' },
            { icon: '📊', text: 'View detailed price history and trends' },
            { icon: '⭐', text: 'Save your favorite products and track them' }
          ].map((feature, idx) => (
            <li key={idx} className="flex items-start">
              <span className="text-lg mr-3">{feature.icon}</span>
              <span className="text-gray-700">{feature.text}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Terms and consent */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <label className="flex items-start cursor-pointer">
          <input
            type="checkbox"
            checked={agreedToTerms}
            onChange={(e) => setAgreedToTerms(e.target.checked)}
            className="w-5 h-5 text-blue-600 rounded mt-1 mr-3"
          />
          <span className="text-sm text-gray-700">
            I understand that my search history, preferences, and product tracking data will be used to improve recommendations and provide personalized alerts. I agree to the{' '}
            <a href="/terms" className="text-blue-600 hover:underline">
              Terms of Service
            </a>
            {' '}and{' '}
            <a href="/privacy" className="text-blue-600 hover:underline">
              Privacy Policy
            </a>
          </span>
        </label>
      </div>

      {/* Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleNext}
          disabled={!agreedToTerms || isSubmitting}
          className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Loading...' : 'Get Started'}
        </button>
        {canSkip && (
          <button
            onClick={onSkip}
            className="px-6 bg-gray-200 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors"
          >
            Skip
          </button>
        )}
      </div>
    </div>
  )
}

export default WelcomeStep