import { createContext, useContext, useState } from 'react'
import client from '../api/client'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('vs_user')) } catch { return null }
  })

  const login = async (username, password, group_code) => {
    const { data } = await client.post('/auth/login', { username, password, group_code })
    localStorage.setItem('vs_token', data.access_token)
    localStorage.setItem('vs_user', JSON.stringify({
      username:     data.username,
      is_admin:     data.is_admin,
      is_superadmin: data.is_superadmin,
      tenant_id:    data.tenant_id,
      tenant_name:  data.tenant_name,
    }))
    setUser({
      username:     data.username,
      is_admin:     data.is_admin,
      is_superadmin: data.is_superadmin,
      tenant_id:    data.tenant_id,
      tenant_name:  data.tenant_name,
    })
  }

  const logout = () => {
    localStorage.removeItem('vs_token')
    localStorage.removeItem('vs_user')
    setUser(null)
  }

  return <AuthCtx.Provider value={{ user, login, logout }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
