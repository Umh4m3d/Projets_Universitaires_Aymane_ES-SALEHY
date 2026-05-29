import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On app load, check if we have a valid token already
  useEffect(() => {
    const token = sessionStorage.getItem('access_token')
    if (token) {
      api.get('/users/me')
        .then(({ data }) => setUser(data))
        .catch(() => {
          sessionStorage.removeItem('access_token')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    sessionStorage.setItem('access_token', data.access_token)
    const me = await api.get('/users/me')
    setUser(me.data)
    return me.data
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch (_) {}
    sessionStorage.removeItem('access_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
