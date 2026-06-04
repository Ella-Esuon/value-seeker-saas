import { useState } from 'react'
import toast from 'react-hot-toast'

const CURRENT_YEAR = new Date().getFullYear()
const YEARS = Array.from({length:5},(_,i)=>CURRENT_YEAR-i)

const REPORTS = [
  { id:'members',      label:'Member Report',             icon:'bi-people-fill',    desc:'All members with contribution totals and loan summary.' },
  { id:'contributions',label:'Annual Contribution Report',icon:'bi-piggy-bank-fill',desc:'Monthly contribution grid for each member for a selected year.' },
  { id:'loans',        label:'Loan Portfolio Report',     icon:'bi-cash-coin',      desc:'All loans with amounts, rates, repayment status and balances.' },
  { id:'delinquent',   label:'Delinquent Loan Report',    icon:'bi-exclamation-triangle-fill', desc:'Active loans past their due date.' },
]

export default function Reports() {
  const [active, setActive] = useState('members')
  const [year, setYear]     = useState(CURRENT_YEAR)
  const [loading, setLoading] = useState(null)

  const token = localStorage.getItem('vs_token')

  const download = async (type, format) => {
    const key = `${type}-${format}`
    setLoading(key)
    try {
      let url = `/api/reports/${type}/${format}`
      if (type === 'contributions') url += `?year=${year}`
      const resp = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      if (!resp.ok) throw new Error('Failed')
      const blob = await resp.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${type}_report_${type==='contributions'?year:new Date().toISOString().split('T')[0]}.${format}`
      link.click()
      toast.success(`${format.toUpperCase()} downloaded successfully`)
    } catch { toast.error('Failed to generate report') }
    finally { setLoading(null) }
  }

  const report = REPORTS.find(r => r.id === active)

  return (
    <div>
      <div className="mb-4">
        <h4 className="fw-bold mb-0">Reports</h4>
        <small className="text-muted">Generate and export financial reports as PDF or Excel</small>
      </div>

      <div className="row g-4">
        {/* Report selector */}
        <div className="col-md-4">
          <div className="card border-0 shadow-sm">
            <div className="card-header bg-white fw-bold">Select Report</div>
            <div className="list-group list-group-flush">
              {REPORTS.map(r => (
                <button
                  key={r.id}
                  className={`list-group-item list-group-item-action d-flex align-items-center gap-2 py-3 ${active===r.id?'active':''}`}
                  style={active===r.id?{background:'var(--vs-primary)',color:'white',borderColor:'var(--vs-primary)'}:{}}
                  onClick={() => setActive(r.id)}
                >
                  <i className={`bi ${r.icon} fs-5`}></i>
                  <span className="fw-semibold" style={{fontSize:'.88rem'}}>{r.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Report detail + export */}
        <div className="col-md-8">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-header bg-white">
              <h5 className="fw-bold mb-0"><i className={`bi ${report.icon} me-2 text-primary`}></i>{report.label}</h5>
            </div>
            <div className="card-body">
              <p className="text-muted mb-4">{report.desc}</p>

              {active === 'contributions' && (
                <div className="mb-4">
                  <label className="form-label fw-semibold">Select Year</label>
                  <select className="form-select" style={{maxWidth:160}} value={year} onChange={e => setYear(parseInt(e.target.value))}>
                    {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                  </select>
                </div>
              )}

              <div className="d-flex gap-3 flex-wrap mt-2">
                <button
                  className="btn btn-lg d-flex align-items-center gap-2"
                  style={{background:'#c0392b',color:'white',minWidth:180}}
                  onClick={() => download(active,'pdf')}
                  disabled={!!loading}
                >
                  {loading===`${active}-pdf`
                    ? <span className="spinner-border spinner-border-sm"></span>
                    : <i className="bi bi-file-earmark-pdf-fill fs-5"></i>
                  }
                  <div className="text-start">
                    <div className="fw-bold">Download PDF</div>
                    <div style={{fontSize:'.75rem',opacity:.85}}>Printable report</div>
                  </div>
                </button>

                <button
                  className="btn btn-lg d-flex align-items-center gap-2"
                  style={{background:'#1e7e34',color:'white',minWidth:180}}
                  onClick={() => download(active,'excel')}
                  disabled={!!loading}
                >
                  {loading===`${active}-excel`
                    ? <span className="spinner-border spinner-border-sm"></span>
                    : <i className="bi bi-file-earmark-spreadsheet-fill fs-5"></i>
                  }
                  <div className="text-start">
                    <div className="fw-bold">Download Excel</div>
                    <div style={{fontSize:'.75rem',opacity:.85}}>Editable spreadsheet</div>
                  </div>
                </button>
              </div>

              {/* Info cards */}
              <div className="row g-3 mt-4">
                {[
                  {icon:'bi-file-earmark-pdf',label:'PDF',desc:'Formatted for printing, includes company header and styled tables.'},
                  {icon:'bi-file-earmark-spreadsheet',label:'Excel',desc:'All data in rows/columns, easy to filter and analyse in Excel.'},
                ].map(c => (
                  <div key={c.label} className="col-sm-6">
                    <div className="border rounded p-3 h-100">
                      <i className={`bi ${c.icon} fs-3 text-muted d-block mb-2`}></i>
                      <div className="fw-semibold">{c.label} Format</div>
                      <div className="text-muted small mt-1">{c.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
