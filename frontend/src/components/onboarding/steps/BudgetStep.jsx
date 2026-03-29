/**
 * Budget Step - Set budget ranges per category
 */
import React, { useState } from 'react'

const BudgetStep = ({ onNext, onPrevious, isSubmitting, canGoBack }) => {
  const [budgetRanges, setBudgetRanges] = useState({})

  const handleNext = () => {
    onNext({ budget_ranges: budgetRanges })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Set your budget</h2>
        <p className="text-gray-600">Define your spending preferences (optional, you can skip this)</p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          💡 <strong>Tip:</strong> Setting a budget helps us show you relevant products within your price range
        </p>
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

export default BudgetStep