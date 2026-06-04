import { useEffect, useState } from 'react'
import client from '../api/client'
import toast from 'react-hot-toast'

const autoSlug = name => name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

export default function TenantAdmin() {
  const [tenants, setTenants]       = useState([])
  const [expanded, setExpanded]     = useState(null)
  const [users, setUsers]           = useState({})
  const [createModal, setCreateModal] = useState(false)
  const [userModal, setUserModal]   = useState(null)
  const [tenantForm, setTenantForm] = useState({ name: '', slug: '' })
  const [userForm, setUserForm]     = useState({ username: '', password: '', email: '', is_admin: false })
  const [saving, setSaving]         = useState(false)

  const load = async () => {
    try {
      const { data } = await client.get('/tenants/')
      setTenants(data)
    } catch { toast.error('Failed to load tenants') }
  }

  useEffect(() => { load() }, [])

  const loadUsers = async (tenantId) => {
    try {
      const { data } = await client.get(`/tenants/${tenantId}/users`)
      setUsers(u => ({ ...u, [tenantId]: data }))
    } catch { toast.error('Failed to load users') }
  }

  const toggleExpand = id => {
    if (expanded === id) { setExpanded(null); return }
    setExpanded(id)
    if (!users[id]) loadUsers(id)
  }

  const openUserModal = (tenantId) => {
    setUserModal(tenantId)
    setUserForm({ username: '', password: '', email: '', is_admin: false })
    if (!users[tenantId]) loadUsers(tenantId)
  }

  const createTenant = async () => {
    if (!tenantForm.name || !tenantForm.slug) { toast.error('Fill all fields'); return }
    setSaving(true)
    try {
      await client.post('/tenants/', tenantForm)
      toast.success('Tenant created')
      setCreateModal(false)
      setTenantForm({ name: '', slug: '' })
      load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  const toggleActive = async t => {
    try {
      await client.put(`/tenants/${t.id}`, { is_active: !t.is_active })
      toast.success(t.is_active ? 'Tenant deactivated' : 'Tenant activated')
      load()
    } catch { toast.error('Error') }
  }

  const createUser = async () => {
    if (!userForm.username || !userForm.password) { toast.error('Username and password required'); return }
    setSaving(true)
    try {
      await client.post(`/tenants/${userModal}/users`, userForm)
      toast.success('User created')
      loadUsers(userModal)
      setUserModal(null)
    } catch (e) { toast.error(e.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  const deleteUser = async (tenantId, userId) => {
    if (!confirm('Delete this user?')) return
    try {
      await client.delete(`/tenants/${tenantId}/users/${userId}`)
      toast.success('User deleted')
      loadUsers(tenantId)
    } catch { toast.error('Error') }
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div>
          <h4 className="fw-bold mb-0">Tenant Management</h4>
          <small className="text-muted">All organizations registered on this platform</small>
        </div>
        <button
          className="btn btn-primary"
          style={{background:'var(--vs-primary)',borderColor:'var(--vs-primary)'}}
          onClick={() => { setTenantForm({ name: '', slug: '' }); setCreateModal(true) }}
        >
          <i className="bi bi-plus-lg me-1"></i>New Tenant
        </button>
      </div>

      {tenants.length === 0 && (
        <div className="text-center text-muted py-5">
          <i className="bi bi-building fs-1 d-block mb-2"></i>No tenants yet
        </div>
      )}

      {tenants.map(t => (
        <div key={t.id} className="card border-0 shadow-sm mb-3">
          <div
            className="card-header d-flex justify-content-between align-items-center flex-wrap gap-2"
            style={{background:'var(--vs-primary)',color:'#fff',cursor:'pointer'}}
            onClick={() => toggleExpand(t.id)}
          >
            <div className="d-flex align-items-center gap-3">
              <i className={`bi bi-chevron-${expanded === t.id ? 'down' : 'right'}`}></i>
              <div>
                <div className="fw-bold">{t.name}</div>
                <div style={{fontSize:'.72rem',opacity:.7}}>
                  code: <strong>{t.slug}</strong>
                  <span className="ms-2">{t.member_count} members</span>
                  <span className="ms-2">{t.user_count} users</span>
                </div>
              </div>
            </div>
            <div className="d-flex gap-2 align-items-center" onClick={e => e.stopPropagation()}>
              <span className={`badge ${t.is_active ? 'bg-success' : 'bg-secondary'}`}>
                {t.is_active ? 'Active' : 'Inactive'}
              </span>
              <button className="btn btn-sm btn-outline-light" onClick={() => toggleActive(t)}>
                {t.is_active ? 'Deactivate' : 'Activate'}
              </button>
              <button className="btn btn-sm btn-outline-light" onClick={() => openUserModal(t.id)}>
                <i className="bi bi-person-plus me-1"></i>Add User
              </button>
            </div>
          </div>

          {expanded === t.id && (
            <div className="card-body p-0">
              {!users[t.id] ? (
                <div className="text-center py-3">
                  <div className="spinner-border spinner-border-sm text-primary"></div>
                </div>
              ) : users[t.id].length === 0 ? (
                <div className="text-center text-muted py-3 small">No users in this tenant</div>
              ) : (
                <table className="table table-sm mb-0">
                  <thead style={{background:'#f8f9fa'}}>
                    <tr>
                      <th>Username</th><th>Email</th><th>Role</th><th>Status</th><th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {users[t.id].map(u => (
                      <tr key={u.id}>
                        <td className="fw-semibold">{u.username}</td>
                        <td className="text-muted">{u.email || '—'}</td>
                        <td>
                          <span className={`badge ${u.is_admin ? 'bg-warning text-dark' : 'bg-light text-muted'}`}>
                            {u.is_admin ? 'Admin' : 'User'}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${u.is_active ? 'bg-success' : 'bg-secondary'}`}>
                            {u.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn btn-sm btn-outline-danger py-0 px-1"
                            onClick={() => deleteUser(t.id, u.id)}
                          >
                            <i className="bi bi-trash"></i>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      ))}

      {/* Create Tenant Modal */}
      {createModal && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header" style={{background:'var(--vs-primary)',color:'#fff'}}>
                <h5 className="modal-title">Create New Tenant</h5>
                <button className="btn-close btn-close-white" onClick={() => setCreateModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label className="form-label fw-semibold">Organization Name *</label>
                  <input
                    type="text" className="form-control"
                    value={tenantForm.name}
                    onChange={e => setTenantForm(f => ({...f, name: e.target.value, slug: autoSlug(e.target.value)}))}
                    placeholder="Accra Savings Group"
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label fw-semibold">Group Code *</label>
                  <input
                    type="text" className="form-control"
                    value={tenantForm.slug}
                    onChange={e => setTenantForm(f => ({...f, slug: e.target.value}))}
                    placeholder="accra-savings"
                  />
                  <div className="form-text">Users type this on the login page. Lowercase, hyphens only.</div>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setCreateModal(false)}>Cancel</button>
                <button
                  className="btn btn-primary"
                  style={{background:'var(--vs-primary)',borderColor:'var(--vs-primary)'}}
                  onClick={createTenant} disabled={saving}
                >
                  {saving && <span className="spinner-border spinner-border-sm me-1"></span>}
                  Create Tenant
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add User Modal */}
      {userModal && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header" style={{background:'#27ae60',color:'#fff'}}>
                <h5 className="modal-title">
                  Add User — {tenants.find(t => t.id === userModal)?.name}
                </h5>
                <button className="btn-close btn-close-white" onClick={() => setUserModal(null)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label className="form-label fw-semibold">Username *</label>
                  <input
                    type="text" className="form-control"
                    value={userForm.username}
                    onChange={e => setUserForm(f => ({...f, username: e.target.value}))}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label fw-semibold">Password *</label>
                  <input
                    type="password" className="form-control"
                    value={userForm.password}
                    onChange={e => setUserForm(f => ({...f, password: e.target.value}))}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label fw-semibold">Email</label>
                  <input
                    type="email" className="form-control"
                    value={userForm.email}
                    onChange={e => setUserForm(f => ({...f, email: e.target.value}))}
                  />
                </div>
                <div className="form-check">
                  <input
                    className="form-check-input" type="checkbox"
                    id="isAdminCheck"
                    checked={userForm.is_admin}
                    onChange={e => setUserForm(f => ({...f, is_admin: e.target.checked}))}
                  />
                  <label className="form-check-label" htmlFor="isAdminCheck">
                    Grant admin access
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setUserModal(null)}>Cancel</button>
                <button className="btn btn-success" onClick={createUser} disabled={saving}>
                  {saving && <span className="spinner-border spinner-border-sm me-1"></span>}
                  Create User
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
