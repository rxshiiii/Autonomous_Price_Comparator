/**
 * Dashboard Layout Component - Main layout wrapper for dashboard pages
 */
import React from 'react'

const DashboardLayout = ({ children, user, onLogout }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Optional: Add sidebar, footer, or other layout elements here */}
    </div>
  )
}

export default DashboardLayout