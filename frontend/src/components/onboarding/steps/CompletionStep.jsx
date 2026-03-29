/**
 * Completion Step - Onboarding complete, celebrate and redirect
 */
import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const CompletionStep = ({ onNext, isSubmitting }) => {
  const navigate = useNavigate()

  // Auto-navigate after a delay
  useEffect(() => {
    const timer = setTimeout(() => {
      navigate('/dashboard')
    }, 3000)

    return () => clearTimeout(timer)
  }, [navigate])

  const handleContinue = () => {
    navigate('/dashboard')
  }

  return (
    <div className="space-y-6 text-center py-8">
      {/* Celebration animation */}
      <div className="space-y-4">
        <div className="w-24 h-24 mx-auto bg-green-100 rounded-full flex items-center justify-center animate-bounce">
          <span className="text-5xl">🎉</span>
        </div>

        <h2 className="text-3xl font-bold text-gray-900">You're all set!</h2>
        <p className="text-gray-600 text-lg">
          Your personalized price tracking dashboard is ready to go.
        </p>
      </div>

      {/* What's next */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-left">
        <h4 className="font-semibold text-gray-900 mb-3">What happens next:</h4>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-center">
            <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center mr-2 text-xs">✓</span>
            AI algorithms are learning your preferences
          </li>
          <li className="flex items-center">
            <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center mr-2 text-xs">✓</span>
            Your personalized recommendations will be ready soon
          </li>
          <li className="flex items-center">
            <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center mr-2 text-xs">✓</span>
            You'll get instant alerts for price drops on tracked products
          </li>
          <li className="flex items-center">
            <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center mr-2 text-xs">✓</span>
            Start comparing prices and saving money today!
          </li>
        </ul>
      </div>

      {/* Buttons */}
      <div>
        <button
          onClick={handleContinue}
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          {isSubmitting ? 'Loading...' : 'Go to Dashboard'}
        </button>
        <p className="text-sm text-gray-600 mt-4">
          Redirecting in 3 seconds...
        </p>
      </div>
    </div>
  )
}

export default CompletionStep