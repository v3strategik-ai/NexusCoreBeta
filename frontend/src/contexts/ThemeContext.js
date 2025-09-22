import React, { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext()

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Check localStorage first, then system preference
    const savedTheme = localStorage.getItem('nexus-theme')
    if (savedTheme) {
      return savedTheme
    }
    
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
    
    return 'light'
  })

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    localStorage.setItem('nexus-theme', newTheme)
  }

  const setLightTheme = () => {
    setTheme('light')
    localStorage.setItem('nexus-theme', 'light')
  }

  const setDarkTheme = () => {
    setTheme('dark')
    localStorage.setItem('nexus-theme', 'dark')
  }

  const setSystemTheme = () => {
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    setTheme(systemTheme)
    localStorage.setItem('nexus-theme', systemTheme)
  }

  useEffect(() => {
    const root = window.document.documentElement
    
    // Remove previous theme classes
    root.classList.remove('light', 'dark')
    
    // Add current theme class
    root.classList.add(theme)
    
    // Update CSS custom properties for theme
    if (theme === 'dark') {
      // Dark theme variables
      root.style.setProperty('--background', '222.2% 84% 4.9%')
      root.style.setProperty('--foreground', '210 40% 98%')
      root.style.setProperty('--card', '222.2% 84% 4.9%')
      root.style.setProperty('--card-foreground', '210 40% 98%')
      root.style.setProperty('--popover', '222.2% 84% 4.9%')
      root.style.setProperty('--popover-foreground', '210 40% 98%')
      root.style.setProperty('--primary', '217.2 91.2% 59.8%')
      root.style.setProperty('--primary-foreground', '222.2 84% 4.9%')
      root.style.setProperty('--secondary', '217.2 32.6% 17.5%')
      root.style.setProperty('--secondary-foreground', '210 40% 98%')
      root.style.setProperty('--muted', '217.2 32.6% 17.5%')
      root.style.setProperty('--muted-foreground', '215 20.2% 65.1%')
      root.style.setProperty('--accent', '217.2 32.6% 17.5%')
      root.style.setProperty('--accent-foreground', '210 40% 98%')
      root.style.setProperty('--destructive', '0 62.8% 30.6%')
      root.style.setProperty('--destructive-foreground', '210 40% 98%')
      root.style.setProperty('--border', '217.2 32.6% 17.5%')
      root.style.setProperty('--input', '217.2 32.6% 17.5%')
      root.style.setProperty('--ring', '224.3 76.3% 94.1%')
    } else {
      // Light theme variables
      root.style.setProperty('--background', '0 0% 100%')
      root.style.setProperty('--foreground', '222.2 84% 4.9%')
      root.style.setProperty('--card', '0 0% 100%')
      root.style.setProperty('--card-foreground', '222.2 84% 4.9%')
      root.style.setProperty('--popover', '0 0% 100%')
      root.style.setProperty('--popover-foreground', '222.2 84% 4.9%')
      root.style.setProperty('--primary', '221.2 83.2% 53.3%')
      root.style.setProperty('--primary-foreground', '210 40% 98%')
      root.style.setProperty('--secondary', '210 40% 96%')
      root.style.setProperty('--secondary-foreground', '222.2 84% 4.9%')
      root.style.setProperty('--muted', '210 40% 96%')
      root.style.setProperty('--muted-foreground', '215.4 16.3% 46.9%')
      root.style.setProperty('--accent', '210 40% 96%')
      root.style.setProperty('--accent-foreground', '222.2 84% 4.9%')
      root.style.setProperty('--destructive', '0 84.2% 60.2%')
      root.style.setProperty('--destructive-foreground', '210 40% 98%')
      root.style.setProperty('--border', '214.3 31.8% 91.4%')
      root.style.setProperty('--input', '214.3 31.8% 91.4%')
      root.style.setProperty('--ring', '221.2 83.2% 53.3%')
    }
  }, [theme])

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      // Only update if user hasn't manually set a preference
      const savedTheme = localStorage.getItem('nexus-theme')
      if (!savedTheme) {
        setTheme(mediaQuery.matches ? 'dark' : 'light')
      }
    }

    mediaQuery.addListener(handleChange)
    return () => mediaQuery.removeListener(handleChange)
  }, [])

  const value = {
    theme,
    toggleTheme,
    setLightTheme,
    setDarkTheme,
    setSystemTheme,
    isLight: theme === 'light',
    isDark: theme === 'dark'
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}