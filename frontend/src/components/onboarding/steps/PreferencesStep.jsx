/**
 * Preferences Step - Select product categories and interests
 */
import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../../../services/api'

const PreferencesStep = ({ onNext, onPrevious, isSubmitting, canGoBack }) => {
  const [selectedCategories, setSelectedCategories] = useState([])
  const [selectedInterests, setSelectedInterests] = useState([])

  // Get available categories
  const { data: categoriesData, isLoading: categoriesLoading } = useQuery({
    queryKey: ['onboarding-categories'],
    queryFn: async () => {
      const response = await apiClient.get('/onboarding/categories')
      return response.data
    }
  })

  const handleNext = () => {
    if (selectedCategories.length > 0) {
      onNext({
        categories: selectedCategories,
        interests: selectedInterests
      })
    }
  }

  if (categoriesLoading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      </div>
    )
  }

  const categories = categoriesData?.categories || []

  const handleCategoryChange = (categoryId) => {
    setSelectedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">What interests you?</h2>
        <p className="text-gray-600">
          Select at least one category to get personalized recommendations
        </p>
      </div>

      {/* Categories grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {categories.map(category => (
          <button
            key={category.id}
            onClick={() => handleCategoryChange(category.id)}
            className={`p-4 rounded-lg border-2 transition-all text-left ${
              selectedCategories.includes(category.id)
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <div className="flex items-center">
              <span className="text-3xl mr-3">{category.icon}</span>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">{category.name}</h4>
                <p className="text-sm text-gray-600">{category.description}</p>
              </div>
              {selectedCategories.includes(category.id) && (
                <svg className="w-5 h-5 text-blue-600 ml-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          </button>
        ))}
      </div>

      {selectedCategories.length === 0 && (
        <p className="text-center text-sm text-red-600 bg-red-50 p-3 rounded">
          Please select at least one category to continue
        </p>
      )}

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
          disabled={selectedCategories.length === 0 || isSubmitting}
          className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Loading...' : 'Continue'}
        </button>
      </div>
    </div>
  )
}

export default PreferencesStep