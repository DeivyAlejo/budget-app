import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import { setAuthToken, setUnauthorizedHandler } from '../api/client'

type AuthContextValue = {
  token: string | null
  login: (tokenValue: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const TOKEN_STORAGE_KEY = 'budget_app_token'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => {
    const savedToken = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (savedToken) {
      setAuthToken(savedToken)
    }
    return savedToken
  })

  useEffect(() => {
    setUnauthorizedHandler(() => {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      setAuthToken(null)
      setToken(null)
    })

    return () => {
      setUnauthorizedHandler(null)
    }
  }, [])

  const value = useMemo(
    () => ({
      token,
      login: (tokenValue: string) => {
        localStorage.setItem(TOKEN_STORAGE_KEY, tokenValue)
        setAuthToken(tokenValue)
        setToken(tokenValue)
      },
      logout: () => {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        setAuthToken(null)
        setToken(null)
      },
    }),
    [token],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return ctx
}
