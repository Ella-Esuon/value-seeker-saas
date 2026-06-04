import { useEffect, useState } from 'react'
import client from '../api/client'
import toast from 'react-hot-toast'

const fmt = n => Number(n||0).toLocaleString('en-GH', {minimumFractionDigits:2})
const today = () => new Date().toISOString().split('T')[0]
const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const MONTH_FULL  = ['January','February','March','April','May','June','July','August','September','October','November','December']

export default function Contributions() {
  const [year, setYear] = useState(new Date().getFullYear())
  const [grid, setGrid] = useState(null)
  const [members, setMembers] = useState([])
  const [modal, setModal] = useState(false)
  const [form, setForm] = useState({ member_id:'', month: new Date().getMonth()+1, year: new Date().getFullYear(), amount:'', date_paid: today(), notes:'' })
  const [saving, setSaving] = useState(false)

  const loadGrid = async () => {
    const { data } = await client.get(`/contributions/yearly-grid?year=${year}`)
    setGrid(data)
  }
  const loadMembers = async () => {
    const { data } = await client.get('/members/')
    setMembers(data)
  }
  useEffect(() => { loadGrid() }, [year])
  useEffect(() => { loadMembers() }, [])

  const openModal = (memberId, month, yr) => {
    setForm({ member_id: memberId||'', month: month||(new Date().getMonth()+1), year: yr||year, amount:'', date_paid: today(), notes:'' })
    setModal(true)
  }

  const save = async () => {
    if (!form.member_id || !form.amount || !form.date_paid) { toast.error('Fill all required fields'); return }
    setSaving(true)
    try {
      await client.post('/contributions/', { ...form, member_id: parseInt(form.member_id), month: parseInt(form.month), year: parseInt(form.year), amount: parseFloat(form.amount) })
      toast.success('Contribution recorded')
      setModal(false)
      if (parseInt(form.year) !== year) setYear(parseInt(form.year))
      else loadGrid()
    } catch (e) { toast.error(e.response?.data?.detail || 'Error')
    } finally { setSaving(false) }
  }

  const del = async (id) => {
    if (!confirm('Delete this contribution?')) return
    try { await client.delete(`/contributions/${id}`); toast.success('Deleted'); loadGrid() }
    catch { toast.error('Could not delete') }
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div><h4 className="fw-bold mb-0">Monthly Contributions</h4><small className="text-muted">Click any <strong>+</strong> cell to record a payment</small></div>
        <button className="btn btn-primary" style={{background:'var(--vs-primary)',borderColor:'var(--vs-primary)'}} onClick={() => openModal()}>
          <i className="bi bi-plus-lg me-1"></i>Record Contribution
        </button>
      </div>

      {/* Year Nav */}
      <div className="card border-0 shadow-sm mb-3 p-3">
        <div className="d-flex align-items-center gap-3 flex-wrap">
          <button className="btn btn-outline-primary btn-sm" onClick={() => setYear(y => y-1)}><i className="bi bi-chevron-left"></i> Prev</button>
          <h5 className="mb-0 fw-bold px-2">{year}</h5>
          <button className="btn btn-outline-primary btn-sm" onClick={() => setYear(y => y+1)}>Next <i className="bi bi-chevron-right"></i></button>
          {grid && <span className="ms-auto text-muted small">Year total: GH₵{fmt(grid.grand_year_total)} · All-time: GH₵{fmt(grid.grand_cumulative)}</span>}
        </div>
      </div>

      {/* Grid */}
      <div className="card border-0 shadow-sm">
        <div className="contrib-grid-wrap">
          {!grid ? <div className="text-center py-5"><div className="spinner-border text-primary"></div></div> : (
            <table className="table contrib-grid mb-0">
              <thead>
                <tr>
                  <th style={{textAlign:'left'}}>Member</th>
                  {MONTH_NAMES.map(m => <th key={m}>{m}</th>)}
                  <th style={{background:'#122840',color:'var(--vs-accent)'}}>Year Total</th>
                  <th style={{background:'#7a5000',color:'#ffe4b0'}}>All-time</th>
                </tr>
              </thead>
              <tbody>
                {grid.members.map(row => (
                  <tr key={row.member_id}>
                    <td>
                      <div className="fw-semibold" style={{fontSize:'.82rem'}}>{row.member_name}</div>
                      <div style={{fontSize:'.7rem',color:'#999'}}>{row.membership_id}</div>
                    </td>
                    {Array.from({length:12},(_,i) => {
                      const m = i+1
                      const paid = row.months[m]
                      return paid ? (
                        <td key={m} className="cell-paid" title={`GH₵${fmt(paid.amount)}`}>
                          <div style={{position:'relative',display:'inline-block',width:'100%',textAlign:'center'}}>
                            {fmt(paid.amount)}
                            {paid.ids.map(id => (
                              <button key={id} className="del-x" onClick={e => { e.stopPropagation(); del(id) }}>×</button>
                            ))}
                          </div>
                        </td>
                      ) : (
                        <td key={m} className="cell-empty" title={`Record ${MONTH_FULL[i]} ${year}`} onClick={() => openModal(row.member_id, m, year)}>+</td>
                      )
                    })}
                    <td className="cell-total">GH₵{fmt(row.year_total)}</td>
                    <td className="cell-cumul">GH₵{fmt(row.cumulative_total)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td className="fw-bold">TOTAL</td>
                  {Array.from({length:12},(_,i) => {
                    const v = grid.col_totals[String(i+1)] || 0
                    return <td key={i} className={v > 0 ? 'text-success fw-bold' : 'text-muted'}>{v > 0 ? fmt(v) : '—'}</td>
                  })}
                  <td className="cell-total">GH₵{fmt(grid.grand_year_total)}</td>
                  <td className="cell-cumul">GH₵{fmt(grid.grand_cumulative)}</td>
                </tr>
              </tfoot>
            </table>
          )}
        </div>
      </div>

      {/* Modal */}
      {modal && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header" style={{background:'var(--vs-primary)',color:'#fff'}}>
                <h5 className="modal-title">Record Contribution</h5>
                <button className="btn-close btn-close-white" onClick={() => setModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label className="form-label fw-semibold">Member *</label>
                  <select className="form-select" value={form.member_id} onChange={e => setForm(f=>({...f,member_id:e.target.value}))}>
                    <option value="">— Select Member —</option>
                    {members.map(m => <option key={m.id} value={m.id}>{m.name} ({m.membership_id})</option>)}
                  </select>
                </div>
                <div className="row g-3 mb-3">
                  <div className="col-6">
                    <label className="form-label fw-semibold">Month *</label>
                    <select className="form-select" value={form.month} onChange={e => setForm(f=>({...f,month:e.target.value}))}>
                      {MONTH_FULL.map((m,i) => <option key={i+1} value={i+1}>{m}</option>)}
                    </select>
                  </div>
                  <div className="col-6">
                    <label className="form-label fw-semibold">Year *</label>
                    <input type="number" className="form-control" value={form.year} onChange={e => setForm(f=>({...f,year:e.target.value}))} />
                  </div>
                </div>
                <div className="mb-3">
                  <label className="form-label fw-semibold">Amount (GH₵) *</label>
                  <input type="number" className="form-control" min="0" step="0.01" value={form.amount} onChange={e => setForm(f=>({...f,amount:e.target.value}))} placeholder="5000" />
                </div>
                <div className="mb-3">
                  <label className="form-label fw-semibold">Date Paid *</label>
                  <input type="date" className="form-control" value={form.date_paid} onChange={e => setForm(f=>({...f,date_paid:e.target.value}))} />
                </div>
                <div className="mb-0">
                  <label className="form-label fw-semibold">Notes</label>
                  <input className="form-control" value={form.notes} onChange={e => setForm(f=>({...f,notes:e.target.value}))} placeholder="Optional" />
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setModal(false)}>Cancel</button>
                <button className="btn btn-primary" style={{background:'var(--vs-primary)',borderColor:'var(--vs-primary)'}} onClick={save} disabled={saving}>
                  {saving && <span className="spinner-border spinner-border-sm me-1"></span>}Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
