/**
 * Authentication service for API calls
 */
import api from './api'

export const authService = {
  /**
   * Register a new user
   */
  register: async (userData) => {
    const response = await api.post('/auth/register', userData)
    const { access_token, refresh_token } = response.data

    // Store tokens
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)

    return response.data
  },

  /**
   * Login with email and password
   */
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials)
    const { access_token, refresh_token } = response.data

    // Store tokens
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)

    return response.data
  },

  /**
   * Logout user
   */
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  /**
   * Get current user profile
   */
  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token')
  },
}

export default authService
