import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function Login() {
  const [form, setForm] = useState({ group_code: '', username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async e => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(form.username, form.password, form.group_code)
      navigate('/')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid credentials'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-bg">
      <div className="login-card">
        <div className="text-center mb-4">
          <div style={{fontSize:'3rem'}}>💎</div>
          <h3 style={{color:'var(--vs-primary)',fontWeight:700,marginBottom:4}}>VALUE SEEKER</h3>
          <p className="text-muted small mb-0">Financial Management System</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label fw-semibold">Group Code</label>
            <div className="input-group">
              <span className="input-group-text"><i className="bi bi-building"></i></span>
              <input
                type="text" className="form-control" placeholder="e.g. default"
                value={form.group_code}
                onChange={e => setForm(f => ({...f, group_code: e.target.value}))}
                required autoFocus
              />
            </div>
          </div>
          <div className="mb-3">
            <label className="form-label fw-semibold">Username</label>
            <div className="input-group">
              <span className="input-group-text"><i className="bi bi-person"></i></span>
              <input
                type="text" className="form-control" placeholder="Enter username"
                value={form.username}
                onChange={e => setForm(f => ({...f, username: e.target.value}))}
                required
              />
            </div>
          </div>
          <div className="mb-4">
            <label className="form-label fw-semibold">Password</label>
            <div className="input-group">
              <span className="input-group-text"><i className="bi bi-lock"></i></span>
              <input
                type="password" className="form-control" placeholder="Enter password"
                value={form.password}
                onChange={e => setForm(f => ({...f, password: e.target.value}))}
                required
              />
            </div>
          </div>
          <button
            type="submit" className="btn w-100 fw-semibold py-2"
            style={{background:'var(--vs-primary)',color:'white'}}
            disabled={loading}
          >
            {loading ? <><span className="spinner-border spinner-border-sm me-2"></span>Signing in…</> : 'Sign In'}
          </button>
        </form>
        <div className="mt-4 p-3 rounded" style={{background:'#f8f9fa',fontSize:'.75rem',color:'#666'}}>
          <div className="fw-semibold mb-1" style={{color:'#444'}}>Default credentials</div>
          <div>Group: <code>default</code> · User: <code>admin</code> · Pass: <code>ad123</code></div>
          <div className="mt-1">Superadmin: Group: <code>system</code> · User: <code>superadmin</code></div>
        </div>
      </div>
    </div>
  )
}
