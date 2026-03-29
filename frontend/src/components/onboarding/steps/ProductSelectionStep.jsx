/**
 * Product Selection Step - Select initial products to seed recommendations
 */
import React, { useState } from 'react'

const ProductSelectionStep = ({ onNext, onPrevious, isSubmitting, canGoBack }) => {
  const [selectedProductIds, setSelectedProductIds] = useState([])

  const handleNext = () => {
    onNext({ product_ids: selectedProductIds })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Add initial products</h2>
        <p className="text-gray-600">Track products to seed your AI recommendations (optional)</p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          💡 <strong>Tip:</strong> Tracking products helps our AI learn your preferences for better recommendations
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

export default ProductSelectionStep