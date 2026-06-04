import { useEffect, useState } from 'react'
import client from '../api/client'
import toast from 'react-hot-toast'

const fmt = n => Number(n||0).toLocaleString('en-KE', {minimumFractionDigits:2})
const today = () => new Date().toISOString().split('T')[0]

const EMPTY = { name:'', phone:'', email:'', address:'', date_joined: today(), status:'active' }

export default function Members() {
  const [members, setMembers] = useState([])
  const [filter, setFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modal, setModal] = useState(null) // null | 'add' | 'edit' | 'view'
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    const { data } = await client.get('/members/' + (statusFilter ? `?status=${statusFilter}` : ''))
    setMembers(data)
  }
  useEffect(() => { load() }, [statusFilter])

  const filtered = members.filter(m =>
    m.name.toLowerCase().includes(filter.toLowerCase()) ||
    m.membership_id?.toLowerCase().includes(filter.toLowerCase())
  )

  const openAdd = () => { setForm(EMPTY); setModal('add') }
  const openEdit = (m) => { setForm({ name:m.name,phone:m.phone||'',email:m.email||'',address:m.address||'',date_joined:m.date_joined,status:m.status }); setSelected(m); setModal('edit') }
  const openView = async (m) => {
    const { data } = await client.get(`/members/${m.id}`)
    setSelected(data); setModal('view')
  }

  const save = async () => {
    if (!form.name || !form.date_joined) { toast.error('Name and date joined are required'); return }
    setSaving(true)
    try {
      if (modal === 'add') {
        await client.post('/members/', form)
        toast.success('Member added successfully')
      } else {
        await client.put(`/members/${selected.id}`, { name:form.name,phone:form.phone||null,email:form.email||null,address:form.address||null,status:form.status })
        toast.success('Member updated')
      }
      setModal(null); load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error saving member')
    } finally { setSaving(false) }
  }

  const del = async (m) => {
    if (!confirm(`Delete "${m.name}"? All their data will be removed.`)) return
    try { await client.delete(`/members/${m.id}`); toast.success('Member deleted'); load() }
    catch { toast.error('Could not delete member') }
  }

  const statusBadge = s => {
    const cls = s === 'active' ? 'badge-active' : 'badge-rejected'
    return <span className={`badge ${cls} rounded px-2`}>{s.toUpperCase()}</span>
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div><h4 className="fw-bold mb-0">Members</h4><small className="text-muted">{members.length} members registered</small></div>
        <button className="btn btn-primary" style={{background:'var(--vs-primary)',borderColor:'var(--vs-primary)'}} onClick={openAdd}>
          <i className="bi bi-person-plus-fill me-1"></i>Add New Member
        </button>
      </div>

      <div className="card border-0 shadow-sm mb-0">
        <div className="card-header bg-white d-flex gap-2 flex-wrap py-3">
          <input className="form-control" style={{maxWidth:280}} placeholder="Search by name or ID…" value={filter} onChange={e => setFilter(e.target.value)} />
          <select className="form-select" style={{maxWidth:160}} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
        <div className="table-responsive">
          <table className="table vs-table mb-0">
            <thead>
              <tr><th>#</th><th>Mbr ID</th><th>Name</th><th>Phone</th><th>Email</th><th>Date Joined</th><th>Status</th><th>Contributions</th><th>Loan Balance</th><th></th></tr>
            </thead>
            <tbody>
              {filtered.length === 0 && <tr><td colSpan="10" className="text-center text-muted py-5">No members found</td></tr>}
              {filtered.map((m,i) => (
                <tr key={m.id}>
                  <td className="text-muted">{i+1}</td>
                  <td><code className="small">{m.membership_id}</code></td>
                  <td className="fw-semibold">{m.name}</td>
                  <td>{m.phone||'—'}</td>
                  <td>{m.email||'—'}</td>
                  <td>{m.date_joined}</td>
                  <td>{statusBadge(m.status)}</td>
                  <td className="text-success fw-bold">KES {fmt(m.total_contributions)}</td>
                  <td className={m.active_loan_balance>0?'text-danger fw-bold':'text-muted'}>KES {fmt(m.active_loan_balance)}</td>
                  <td>
                    <button className="btn btn-sm btn-outline-primary me-1" onClick={() => openView(m)} title="View"><i className="bi bi-eye"></i></button>
                    <button className="btn btn-sm btn-outline-secondary me-1" onClick={() => openEdit(m)} title="Edit"><i className="bi bi-pencil"></i></button>
                    <button className="btn btn-sm btn-outline-danger" onClick={() => del(m)} title="Delete"><i className="bi bi-trash"></i></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Modal */}
      {(modal === 'add' || modal === 'edit') && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header" style={{background:'var(--vs-primary)',color:'#fff'}}>
                <h5 className="modal-title">{modal==='add'?'Add New Member':'Edit Member'}</h5>
                <button className="btn-close btn-close-white" onClick={() => setModal(null)}></button>
              </div>
              <div className="modal-body">
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label fw-semibold">Full Name *</label>
                    <input className="form-control" value={form.name} onChange={e => setForm(f=>({...f,name:e.target.value}))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label fw-semibold">Phone</label>
                    <input className="form-control" value={form.phone} onChange={e => setForm(f=>({...f,phone:e.target.value}))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label fw-semibold">Email</label>
                    <input type="email" className="form-control" value={form.email} onChange={e => setForm(f=>({...f,email:e.target.value}))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label fw-semibold">Date Joined *</label>
                    <input type="date" className="form-control" value={form.date_joined} onChange={e => setForm(f=>({...f,date_joined:e.target.value}))} />
                  </div>
                  <div className="col-md-8">
                    <label className="form-label fw-semibold">Address</label>
                    <input className="form-control" value={form.address} onChange={e => setForm(f=>({...f,address:e.target.value}))} />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label fw-semibold">Status</label>
                    <select className="form-select" value={form.status} onChange={e => setForm(f=>({...f,status:e.target.value}))}>
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                <button className="btn btn-primary" style={{background:'var(--vs-primary)',borderColor:'var(--vs-primary)'}} onClick={save} disabled={saving}>
                  {saving ? <span className="spinner-border spinner-border-sm me-1"></span> : null}
                  {modal === 'add' ? 'Add Member' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Modal */}
      {modal === 'view' && selected && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header" style={{background:'var(--vs-primary)',color:'#fff'}}>
                <h5 className="modal-title"><i className="bi bi-person-circle me-2"></i>{selected.name}</h5>
                <button className="btn-close btn-close-white" onClick={() => setModal(null)}></button>
              </div>
              <div className="modal-body">
                <div className="row g-3 mb-3">
                  <div className="col-sm-4"><div className="text-muted small">Membership ID</div><div className="fw-bold"><code>{selected.membership_id}</code></div></div>
                  <div className="col-sm-4"><div className="text-muted small">Phone</div><div>{selected.phone||'—'}</div></div>
                  <div className="col-sm-4"><div className="text-muted small">Email</div><div>{selected.email||'—'}</div></div>
                  <div className="col-sm-4"><div className="text-muted small">Address</div><div>{selected.address||'—'}</div></div>
                  <div className="col-sm-4"><div className="text-muted small">Date Joined</div><div>{selected.date_joined}</div></div>
                  <div className="col-sm-4"><div className="text-muted small">Status</div><div>{selected.status}</div></div>
                </div>
                <div className="row g-3 mb-3">
                  <div className="col-sm-6 col-md-4">
                    <div className="card border-0 bg-success bg-opacity-10 p-3 text-center">
                      <div className="small text-muted">All-time Contributions</div>
                      <div className="fw-bold text-success">KES {fmt(selected.total_contributions)}</div>
                    </div>
                  </div>
                  <div className="col-sm-6 col-md-4">
                    <div className="card border-0 bg-danger bg-opacity-10 p-3 text-center">
                      <div className="small text-muted">Active Loan Balance</div>
                      <div className="fw-bold text-danger">KES {fmt(selected.active_loan_balance)}</div>
                    </div>
                  </div>
                </div>
                {selected.contribution_history?.length > 0 && (
                  <>
                    <h6 className="fw-bold">Contribution History</h6>
                    {selected.contribution_history.map(yr => (
                      <div key={yr.year} className="mb-2">
                        <div className="d-flex justify-content-between small fw-semibold text-muted mb-1">
                          <span>{yr.year}</span><span>KES {fmt(yr.total)}</span>
                        </div>
                        <div className="d-flex gap-1 flex-wrap">
                          {Array.from({length:12},(_,i)=>{
                            const m = i+1
                            const paid = yr.months[m]
                            const names=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
                            return <span key={m} className={`badge ${paid?'bg-success':'bg-light text-muted'}`} style={{fontSize:'.7rem'}}>{names[i]}{paid?` ${fmt(paid.amount)}`:''}</span>
                          })}
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setModal(null)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
