import { useEffect, useState } from 'react'
import client from '../api/client'
import toast from 'react-hot-toast'

const fmt = n => Number(n||0).toLocaleString('en-GH', {minimumFractionDigits:2})
const today = () => new Date().toISOString().split('T')[0]

const STATUS_BADGE = {
  pending:   'badge-pending',
  approved:  'badge-active',
  active:    'badge-active',
  paid:      'badge-paid',
  rejected:  'badge-rejected',
  defaulted: 'badge-defaulted',
}

export default function Loans() {
  const [loans, setLoans]       = useState([])
  const [members, setMembers]   = useState([])
  const [statusF, setStatusF]   = useState('')
  const [memberF, setMemberF]   = useState('')
  const [modal, setModal]       = useState(null)
  const [selected, setSelected] = useState(null)
  const [schedule, setSchedule] = useState(null)
  const [saving, setSaving]     = useState(false)

  const [loanForm, setLoanForm] = useState({ member_id:'', amount:'', interest_rate:'15', term_months:'12', date_applied: today(), purpose:'', notes:'' })
  const [repForm, setRepForm]   = useState({ amount:'', date_paid: today(), notes:'' })
  const [approveDate, setApproveDate] = useState(today())

  const load = async () => {
    let url = '/loans/?'
    if (statusF) url += `status=${statusF}&`
    if (memberF) url += `member_id=${memberF}&`
    const { data } = await client.get(url)
    setLoans(data)
  }
  useEffect(() => { load() }, [statusF, memberF])
  useEffect(() => { client.get('/members/').then(r => setMembers(r.data)) }, [])

  const openSchedule = async (loan) => {
    const { data } = await client.get(`/loans/${loan.id}/schedule`)
    setSchedule(data); setSelected(loan); setModal('schedule')
  }

  const openRepay = (loan) => { setSelected(loan); setRepForm({ amount: String(loan.monthly_installment||''), date_paid: today(), notes:'' }); setModal('repay') }

  const createLoan = async () => {
    if (!loanForm.member_id || !loanForm.amount || !loanForm.term_months) { toast.error('Fill required fields'); return }
    setSaving(true)
    try {
      await client.post('/loans/', { ...loanForm, member_id: parseInt(loanForm.member_id), amount: parseFloat(loanForm.amount), interest_rate: parseFloat(loanForm.interest_rate||0), term_months: parseInt(loanForm.term_months) })
      toast.success('Loan application created'); setModal(null); load()
    } catch(e) { toast.error(e.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  const approveLoan = async () => {
    try {
      await client.put(`/loans/${selected.id}/approve?date_issued=${approveDate}`)
      toast.success('Loan approved and activated'); setModal(null); load()
    } catch(e) { toast.error(e.response?.data?.detail || 'Error') }
  }

  const rejectLoan = async (loan) => {
    if (!confirm('Reject this loan?')) return
    try { await client.put(`/loans/${loan.id}/reject`); toast.success('Loan rejected'); load() }
    catch { toast.error('Error') }
  }

  const saveRepayment = async () => {
    if (!repForm.amount || !repForm.date_paid) { toast.error('Fill required fields'); return }
    setSaving(true)
    try {
      await client.post(`/loans/${selected.id}/repayments`, { amount: parseFloat(repForm.amount), date_paid: repForm.date_paid, notes: repForm.notes||null })
      toast.success('Repayment recorded'); setModal(null); load()
    } catch(e) { toast.error(e.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  const delRepayment = async (loan, repId) => {
    if (!confirm('Delete this repayment?')) return
    try { await client.delete(`/loans/${loan.id}/repayments/${repId}`); toast.success('Deleted'); load() }
    catch { toast.error('Error') }
  }

  const delLoan = async (loan) => {
    if (!confirm(`Delete loan #${loan.id}?`)) return
    try { await client.delete(`/loans/${loan.id}`); toast.success('Loan deleted'); load() }
    catch { toast.error('Error') }
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div><h4 className="fw-bold mb-0">Loans</h4><small className="text-muted">{loans.length} loans</small></div>
        <button className="btn btn-primary" style={{background:'var(--vs-primary)',borderColor:'var(--vs-primary)'}} onClick={() => { setLoanForm({ member_id:'',amount:'',interest_rate:'15',term_months:'12',date_applied:today(),purpose:'',notes:'' }); setModal('create') }}>
          <i className="bi bi-plus-lg me-1"></i>New Loan Application
        </button>
      </div>

      {/* Filters */}
      <div className="card border-0 shadow-sm mb-3 p-3">
        <div className="d-flex gap-2 flex-wrap">
          <select className="form-select" style={{maxWidth:200}} value={memberF} onChange={e => setMemberF(e.target.value)}>
            <option value="">All Members</option>
            {members.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <select className="form-select" style={{maxWidth:160}} value={statusF} onChange={e => setStatusF(e.target.value)}>
            <option value="">All Status</option>
            {['pending','active','paid','rejected','defaulted'].map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
          </select>
        </div>
      </div>

      {/* Loan Cards */}
      {loans.length === 0 && <div className="text-center text-muted py-5"><i className="bi bi-inbox fs-1 d-block mb-2"></i>No loans found</div>}
      {loans.map(loan => {
        const pct = loan.amount > 0 ? Math.min(100, (loan.repaid_principal / loan.amount) * 100) : 0
        const barColor = loan.status === 'paid' ? 'bg-success' : loan.status === 'defaulted' ? 'bg-danger' : 'bg-warning'
        return (
          <div key={loan.id} className="loan-card">
            <div className="loan-card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
              <div>
                <strong>{loan.member_name}</strong>
                <span className="opacity-75 ms-2 small">{loan.membership_id}</span>
                <span className="ms-2 text-muted small">· Loan #{loan.id}</span>
              </div>
              <div className="d-flex align-items-center gap-2 flex-wrap">
                <span className={`badge ${STATUS_BADGE[loan.status]} rounded px-2 py-1`}>{loan.status.toUpperCase()}</span>
                {loan.status === 'pending' && <>
                  <button className="btn btn-sm btn-success" onClick={() => { setSelected(loan); setApproveDate(today()); setModal('approve') }}>Approve</button>
                  <button className="btn btn-sm btn-outline-danger" onClick={() => rejectLoan(loan)}>Reject</button>
                </>}
                {loan.status === 'active' && <>
                  <button className="btn btn-sm" style={{background:'var(--vs-accent)',color:'white'}} onClick={() => openRepay(loan)}><i className="bi bi-plus me-1"></i>Repayment</button>
                </>}
                <button className="btn btn-sm btn-outline-light" onClick={() => openSchedule(loan)}>Schedule</button>
                <button className="btn btn-sm btn-outline-light" onClick={() => delLoan(loan)}><i className="bi bi-trash"></i></button>
              </div>
            </div>
            <div className="p-3">
              <div className="row g-2 text-center mb-3">
                {[
                  ['Principal',`GH₵${fmt(loan.amount)}`,'text-dark'],
                  [`Interest (${loan.interest_rate}%)`, `GH₵${fmt(loan.amount * loan.interest_rate / 100)}`,'text-warning'],
                  ['Monthly Install.',`GH₵${fmt(loan.monthly_installment)}`,'text-primary'],
                  ['Term',`${loan.term_months} months`,'text-dark'],
                  ['Repaid (Principal)',`GH₵${fmt(loan.repaid_principal)}`,'text-success'],
                  ['Balance',`GH₵${fmt(loan.balance)}`,loan.balance>0?'text-danger':'text-success'],
                ].map(([l,v,c]) => (
                  <div key={l} className="col-6 col-md-4 col-lg-2">
                    <div className="small text-muted">{l}</div>
                    <div className={`fw-bold ${c}`} style={{fontSize:'.9rem'}}>{v}</div>
                  </div>
                ))}
              </div>
              <div className="mb-2">
                <div className="d-flex justify-content-between small text-muted mb-1">
                  <span>{loan.payments_made} payments made</span>
                  <span>{pct.toFixed(1)}% repaid</span>
                </div>
                <div className="progress"><div className={`progress-bar ${barColor}`} style={{width:`${pct}%`}}></div></div>
              </div>
              <div className="small text-muted mt-2">
                Applied: {loan.date_applied}
                {loan.date_issued && <> · Issued: {loan.date_issued}</>}
                {loan.due_date && <> · Due: {loan.due_date}</>}
                {loan.purpose && <> · {loan.purpose}</>}
              </div>

              {/* Repayments */}
              {loan.repayments.length > 0 && (
                <div className="mt-3">
                  <div className="fw-semibold small mb-1 text-muted">Repayment History</div>
                  <div className="table-responsive">
                    <table className="table table-sm vs-table mb-0" style={{fontSize:'.78rem'}}>
                      <thead><tr><th>#</th><th>Date</th><th>Amount</th><th>Principal</th><th>Interest</th><th>Balance</th><th></th></tr></thead>
                      <tbody>
                        {loan.repayments.map(r => (
                          <tr key={r.id}>
                            <td>{r.payment_number}</td>
                            <td>{r.date_paid}</td>
                            <td>GH₵{fmt(r.amount)}</td>
                            <td className="text-primary">GH₵{fmt(r.principal_paid)}</td>
                            <td className="text-warning">GH₵{fmt(r.interest_paid)}</td>
                            <td className={r.balance_after>0?'text-danger':'text-success'}>GH₵{fmt(r.balance_after)}</td>
                            <td><button className="btn btn-sm btn-outline-danger py-0 px-1" onClick={() => delRepayment(loan,r.id)}><i className="bi bi-x"></i></button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      })}

      {/* Create Loan Modal */}
      {modal === 'create' && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header" style={{background:'var(--vs-primary)',color:'#fff'}}>
                <h5 className="modal-title">New Loan Application</h5>
                <button className="btn-close btn-close-white" onClick={() => setModal(null)}></button>
              </div>
              <div className="modal-body">
                <div className="row g-3">
                  <div className="col-12">
                    <label className="form-label fw-semibold">Member *</label>
                    <select className="form-select" value={loanForm.member_id} onChange={e => setLoanForm(f=>({...f,member_id:e.target.value}))}>
                      <option value="">— Select Member —</option>
                      {members.map(m => <option key={m.id} value={m.id}>{m.name} ({m.membership_id})</option>)}
                    </select>
                  </div>
                  <div className="col-md-4">
                    <label className="form-label fw-semibold">Loan Amount (GH₵) *</label>
                    <input type="number" className="form-control" value={loanForm.amount} onChange={e => setLoanForm(f=>({...f,amount:e.target.value}))} placeholder="10000" />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label fw-semibold">Interest Rate (% p.a.) *</label>
                    <input type="number" className="form-control" value={loanForm.interest_rate} onChange={e => setLoanForm(f=>({...f,interest_rate:e.target.value}))} />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label fw-semibold">Term (months) *</label>
                    <input type="number" className="form-control" value={loanForm.term_months} onChange={e => setLoanForm(f=>({...f,term_months:e.target.value}))} />
                  </div>
                  {loanForm.amount && loanForm.interest_rate !== '' && loanForm.term_months && (
                    <div className="col-12">
                      <div className="alert alert-info py-2 mb-0">
                        <strong>Monthly Installment: GH₵{fmt(
                          (() => {
                            const P = parseFloat(loanForm.amount), r = parseFloat(loanForm.interest_rate)/100/12, n = parseInt(loanForm.term_months)
                            if (r === 0) return P/n
                            return P * r * Math.pow(1+r,n) / (Math.pow(1+r,n) - 1)
                          })()
                        )}</strong>
                        <span className="text-muted small ms-2">(PMT formula)</span>
                      </div>
                    </div>
                  )}
                  <div className="col-md-6">
                    <label className="form-label fw-semibold">Date Applied *</label>
                    <input type="date" className="form-control" value={loanForm.date_applied} onChange={e => setLoanForm(f=>({...f,date_applied:e.target.value}))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label fw-semibold">Purpose</label>
                    <input className="form-control" value={loanForm.purpose} onChange={e => setLoanForm(f=>({...f,purpose:e.target.value}))} placeholder="Business, Education, etc." />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                <button className="btn btn-primary" style={{background:'var(--vs-primary)',borderColor:'var(--vs-primary)'}} onClick={createLoan} disabled={saving}>Submit Application</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Approve Modal */}
      {modal === 'approve' && selected && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header" style={{background:'#27ae60',color:'#fff'}}>
                <h5 className="modal-title">Approve Loan #{selected.id}</h5>
                <button className="btn-close btn-close-white" onClick={() => setModal(null)}></button>
              </div>
              <div className="modal-body">
                <p>Approving loan of <strong>GH₵{fmt(selected.amount)}</strong> for <strong>{selected.member_name}</strong>.</p>
                <label className="form-label fw-semibold">Disbursement Date *</label>
                <input type="date" className="form-control" value={approveDate} onChange={e => setApproveDate(e.target.value)} />
                <div className="alert alert-success mt-3 py-2 small">Loan will be set to ACTIVE and repayment schedule generated automatically.</div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                <button className="btn btn-success" onClick={approveLoan}>Approve & Disburse</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Repayment Modal */}
      {modal === 'repay' && selected && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header" style={{background:'#27ae60',color:'#fff'}}>
                <h5 className="modal-title">Record Repayment — Loan #{selected.id}</h5>
                <button className="btn-close btn-close-white" onClick={() => setModal(null)}></button>
              </div>
              <div className="modal-body">
                <div className="alert alert-info py-2 small mb-3">
                  <strong>{selected.member_name}</strong> · Balance: GH₵{fmt(selected.balance)} · Monthly Install: GH₵{fmt(selected.monthly_installment)}
                </div>
                <div className="mb-3">
                  <label className="form-label fw-semibold">Amount (GH₵) *</label>
                  <input type="number" className="form-control" value={repForm.amount} onChange={e => setRepForm(f=>({...f,amount:e.target.value}))} />
                </div>
                <div className="mb-3">
                  <label className="form-label fw-semibold">Date Paid *</label>
                  <input type="date" className="form-control" value={repForm.date_paid} onChange={e => setRepForm(f=>({...f,date_paid:e.target.value}))} />
                </div>
                <div className="mb-0">
                  <label className="form-label fw-semibold">Notes</label>
                  <input className="form-control" value={repForm.notes} onChange={e => setRepForm(f=>({...f,notes:e.target.value}))} />
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                <button className="btn btn-success" onClick={saveRepayment} disabled={saving}>Record Payment</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Modal */}
      {modal === 'schedule' && schedule && (
        <div className="modal show d-block" style={{background:'rgba(0,0,0,.5)'}}>
          <div className="modal-dialog modal-lg modal-dialog-scrollable">
            <div className="modal-content">
              <div className="modal-header" style={{background:'var(--vs-primary)',color:'#fff'}}>
                <h5 className="modal-title">Amortization Schedule — Loan #{schedule.loan_id}</h5>
                <button className="btn-close btn-close-white" onClick={() => setModal(null)}></button>
              </div>
              <div className="modal-body p-0">
                <div className="d-flex gap-3 p-3 bg-light border-bottom flex-wrap">
                  {[['Principal',`GH₵${fmt(schedule.principal)}`],['Rate',`${schedule.interest_rate}% p.a.`],['Term',`${schedule.term_months} months`],['Monthly Install.',`GH₵${fmt(schedule.monthly_installment)}`],['Total Interest',`GH₵${fmt(schedule.total_interest)}`],['Total Payable',`GH₵${fmt(schedule.total_payable)}`]].map(([l,v])=>(
                    <div key={l} className="text-center"><div className="small text-muted">{l}</div><div className="fw-bold">{v}</div></div>
                  ))}
                </div>
                <div className="table-responsive">
                  <table className="table vs-table mb-0" style={{fontSize:'.82rem'}}>
                    <thead><tr><th>#</th><th>Monthly Payment</th><th>Principal</th><th>Interest</th><th>Remaining Balance</th></tr></thead>
                    <tbody>
                      {schedule.schedule.map(p => (
                        <tr key={p.payment_number} style={p.payment_number <= selected.payments_made ? {background:'#f0faf5'} : {}}>
                          <td>{p.payment_number}{p.payment_number <= selected.payments_made && <i className="bi bi-check-circle-fill text-success ms-1" style={{fontSize:'.75rem'}}></i>}</td>
                          <td>GH₵{fmt(p.monthly_installment)}</td>
                          <td className="text-primary">GH₵{fmt(p.principal)}</td>
                          <td className="text-warning">GH₵{fmt(p.interest)}</td>
                          <td className={p.balance === 0 ? 'text-success fw-bold' : ''}>GH₵{fmt(p.balance)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
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
