/**
 * Onboarding Wizard - Multi-step user preference collection
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import apiClient from '../../services/api'

import WelcomeStep from './steps/WelcomeStep'
import PreferencesStep from './steps/PreferencesStep'
import BudgetStep from './steps/BudgetStep'
import ProductSelectionStep from './steps/ProductSelectionStep'
import NotificationStep from './steps/NotificationStep'
import CompletionStep from './steps/CompletionStep'

const OnboardingWizard = () => {
  const navigate = useNavigate()
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [stepData, setStepData] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Get onboarding progress
  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ['onboarding-progress'],
    queryFn: async () => {
      const response = await apiClient.get('/onboarding/progress')
      return response.data
    }
  })

  // Complete step mutation
  const completeStepMutation = useMutation({
    mutationFn: async ({ step, data }) => {
      const response = await apiClient.post('/onboarding/step/complete', {
        step,
        data
      })
      return response.data
    }
  })

  // Skip onboarding mutation
  const skipMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/onboarding/skip')
      return response.data
    }
  })

  const steps = [
    { name: 'welcome', component: WelcomeStep, label: 'Welcome' },
    { name: 'preferences', component: PreferencesStep, label: 'Preferences' },
    { name: 'budget', component: BudgetStep, label: 'Budget' },
    { name: 'products', component: ProductSelectionStep, label: 'Initial Products' },
    { name: 'notifications', component: NotificationStep, label: 'Notifications' },
    { name: 'complete', component: CompletionStep, label: 'Complete' }
  ]

  const currentStep = steps[currentStepIndex]
  const CurrentStepComponent = currentStep.component

  const handleNext = async (data) => {
    setIsSubmitting(true)
    try {
      // Save step data
      setStepData(prev => ({ ...prev, [currentStep.name]: data }))

      // Complete step in backend
      await completeStepMutation.mutateAsync({
        step: currentStep.name,
        data
      })

      // Move to next step
      if (currentStepIndex < steps.length - 1) {
        setCurrentStepIndex(prev => prev + 1)
      } else {
        // Onboarding complete, redirect to dashboard
        navigate('/dashboard')
      }
    } catch (error) {
      console.error('Step completion error:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSkip = async () => {
    try {
      await skipMutation.mutateAsync()
      navigate('/dashboard')
    } catch (error) {
      console.error('Skip onboarding error:', error)
    }
  }

  const handlePrevious = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1)
    }
  }

  const progressPercentage = ((currentStepIndex + 1) / steps.length) * 100

  if (progressLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full mx-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-semibold text-gray-900 text-center">Loading Onboarding</h3>
        </div>
      </div>
    )
  }

  // If onboarding is already complete, redirect to dashboard
  if (progress?.is_completed) {
    navigate('/dashboard')
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 text-center mb-2">
            Welcome to Price Comparator! 🎉
          </h1>
          <p className="text-center text-gray-600">
            Let's set up your personalized product tracking experience
          </p>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStepIndex + 1} of {steps.length}
            </span>
            <span className="text-sm text-gray-600">
              {currentStep.label}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
        </div>

        {/* Step indicators */}
        <div className="flex justify-between mb-8">
          {steps.map((step, index) => (
            <div key={step.name} className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm transition-colors ${
                  index <= currentStepIndex
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {index + 1}
              </div>
              <span className="text-xs text-gray-600 mt-1 hidden sm:block">
                {step.label}
              </span>
            </div>
          ))}
        </div>

        {/* Current step */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <CurrentStepComponent
            onNext={handleNext}
            onPrevious={handlePrevious}
            onSkip={handleSkip}
            isSubmitting={isSubmitting}
            canGoBack={currentStepIndex > 0}
            canSkip={currentStepIndex < steps.length - 1}
            stepData={stepData[currentStep.name] || {}}
          />
        </div>

        {/* Skip link */}
        {currentStepIndex < steps.length - 1 && (
          <div className="text-center mt-6">
            <button
              onClick={handleSkip}
              disabled={isSubmitting}
              className="text-gray-600 hover:text-gray-800 text-sm underline transition-colors"
            >
              Skip onboarding
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default OnboardingWizard