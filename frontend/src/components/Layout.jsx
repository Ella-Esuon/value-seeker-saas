import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const NAV = [
  { to: '/',              icon: 'bi-speedometer2',                   label: 'Dashboard'     },
  { to: '/members',       icon: 'bi-people-fill',                    label: 'Members'       },
  { to: '/contributions', icon: 'bi-piggy-bank-fill',                label: 'Contributions' },
  { to: '/loans',         icon: 'bi-cash-coin',                      label: 'Loans'         },
  { to: '/reports',       icon: 'bi-file-earmark-bar-graph-fill',    label: 'Reports'       },
]

const SUPERADMIN_NAV = [
  { to: '/tenants', icon: 'bi-building-gear', label: 'Tenant Management' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const handleLogout = () => { logout(); navigate('/login') }

  const navItems = user?.is_superadmin ? SUPERADMIN_NAV : NAV

  return (
    <div>
      {/* Sidebar */}
      <div className={`vs-sidebar ${open ? 'open' : ''}`}>
        <div className="vs-sidebar-brand">
          <i className="bi bi-gem me-2"></i>VALUE SEEKER
          <div style={{fontSize:'.7rem',color:'rgba(255,255,255,.5)',fontWeight:400,marginTop:2}}>
            {user?.is_superadmin ? 'System Administrator' : (user?.tenant_name || 'Financial Management')}
          </div>
        </div>
        <nav className="mt-2 flex-grow-1">
          {navItems.map(n => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) => `vs-nav-link${isActive ? ' active' : ''}`}
              onClick={() => setOpen(false)}
            >
              <i className={`bi ${n.icon}`}></i>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div style={{padding:'1rem',borderTop:'1px solid rgba(255,255,255,.1)'}}>
          {user?.is_superadmin && (
            <div style={{color:'rgba(255,165,0,.9)',fontSize:'.7rem',marginBottom:'.4rem',fontWeight:600}}>
              <i className="bi bi-shield-fill me-1"></i>SUPERADMIN
            </div>
          )}
          <div style={{color:'rgba(255,255,255,.5)',fontSize:'.75rem',marginBottom:'.5rem'}}>
            Logged in as <strong style={{color:'#fff'}}>{user?.username}</strong>
          </div>
          <button className="btn btn-sm btn-outline-light w-100" onClick={handleLogout}>
            <i className="bi bi-box-arrow-right me-1"></i>Logout
          </button>
        </div>
      </div>

      {/* Main */}
      <div className="vs-main">
        <div className="vs-topbar">
          <button
            className="btn btn-sm btn-outline-secondary d-md-none"
            onClick={() => setOpen(o => !o)}
          >
            <i className="bi bi-list fs-5"></i>
          </button>
          <div className="d-flex align-items-center gap-2 ms-auto">
            {!user?.is_superadmin && user?.tenant_name && (
              <span className="badge rounded-pill me-1" style={{background:'var(--vs-primary)',fontSize:'.7rem'}}>
                <i className="bi bi-building me-1"></i>{user.tenant_name}
              </span>
            )}
            <i className="bi bi-calendar3 text-muted"></i>
            <span className="text-muted small">{new Date().toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'})}</span>
          </div>
        </div>
        <div className="vs-content">
          <Outlet />
        </div>
      </div>

      {/* Mobile overlay */}
      {open && (
        <div
          style={{position:'fixed',inset:0,background:'rgba(0,0,0,.4)',zIndex:99}}
          onClick={() => setOpen(false)}
        />
      )}
    </div>
  )
}
