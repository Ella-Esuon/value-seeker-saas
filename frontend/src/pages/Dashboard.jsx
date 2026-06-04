import { useEffect, useState } from 'react'
import { Bar, Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, LineElement, PointElement, Title, Tooltip, Legend
} from 'chart.js'
import client from '../api/client'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend)

const fmt = n => Number(n||0).toLocaleString('en-GH', {minimumFractionDigits:2})
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

const STATS = [
  { key:'total_members',            label:'Total Members',            icon:'bi-people-fill',    color:'#1a3a5c', bg:'#e8eef6' },
  { key:'active_members',           label:'Active Members',           icon:'bi-person-check',   color:'#27ae60', bg:'#e8f6ed' },
  { key:'total_annual_contributions',label:'Annual Contributions',    icon:'bi-piggy-bank-fill',color:'#0d6efd', bg:'#e8f0ff' },
  { key:'total_contributions_all_time',label:'All-time Contributions',icon:'bi-graph-up',       color:'#6f42c1', bg:'#f0e8ff' },
  { key:'total_loans_disbursed',    label:'Total Loans Disbursed',    icon:'bi-cash-coin',      color:'#e8a020', bg:'#fff3e0' },
  { key:'total_repayments_received',label:'Repayments Received',      icon:'bi-arrow-down-circle',color:'#17a2b8',bg:'#e0f6fa'},
  { key:'outstanding_loan_balance', label:'Outstanding Balance',      icon:'bi-exclamation-circle',color:'#e74c3c',bg:'#fde8e8'},
  { key:'delinquent_loans_count',   label:'Delinquent Loans',         icon:'bi-alarm',          color:'#fd7e14', bg:'#fff0e0' },
]

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [chartData, setChartData] = useState(null)
  const [loanChart, setLoanChart] = useState(null)
  const year = new Date().getFullYear()

  useEffect(() => {
    const load = async () => {
      const [s, cc, lc] = await Promise.all([
        client.get('/dashboard/'),
        client.get(`/contributions/monthly-chart?year=${year}`),
        client.get(`/loans/monthly-chart?year=${year}`),
      ])
      setStats(s.data)
      setChartData(cc.data)
      setLoanChart(lc.data)
    }
    load()
  }, [])

  const chartOpts = (title) => ({
    responsive: true,
    plugins: { legend: { position: 'top' }, title: { display: true, text: title, font: { size: 13 } } },
    scales: { y: { beginAtZero: true, ticks: { callback: v => `GH₵${v.toLocaleString()}` } } },
  })

  if (!stats) return <div className="d-flex align-items-center justify-content-center" style={{height:300}}><div className="spinner-border text-primary"></div></div>

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h4 className="fw-bold mb-0">Dashboard</h4>
          <small className="text-muted">Financial overview for {year}</small>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="row g-3 mb-4">
        {STATS.map(s => {
          const val = stats[s.key]
          const isAmount = s.key.includes('contribution') || s.key.includes('loan') || s.key.includes('balance') || s.key.includes('repayment')
          const isCurrency = isAmount && !s.key.includes('count')
          return (
            <div key={s.key} className="col-6 col-md-4 col-xl-3">
              <div className="stat-card card p-3 h-100">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <div className="stat-icon" style={{background:s.bg,color:s.color}}>
                    <i className={`bi ${s.icon}`}></i>
                  </div>
                </div>
                <div className="stat-value" style={{color:s.color}}>
                  {isCurrency ? `GH₵${fmt(val)}` : val}
                </div>
                <div className="stat-label mt-1">{s.label}</div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Charts */}
      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <div className="card border-0 shadow-sm p-3">
            {chartData && (
              <Bar
                data={{
                  labels: MONTHS,
                  datasets: [{
                    label: `Monthly Contributions ${year}`,
                    data: chartData.data,
                    backgroundColor: 'rgba(26,58,92,.75)',
                    borderRadius: 6,
                  }]
                }}
                options={chartOpts(`Monthly Contributions — ${year}`)}
              />
            )}
          </div>
        </div>
        <div className="col-12 col-lg-6">
          <div className="card border-0 shadow-sm p-3">
            {loanChart && (
              <Bar
                data={{
                  labels: MONTHS,
                  datasets: [
                    {
                      label: 'Disbursements',
                      data: loanChart.disbursements,
                      backgroundColor: 'rgba(232,160,32,.8)',
                      borderRadius: 6,
                    },
                    {
                      label: 'Repayments',
                      data: loanChart.repayments,
                      backgroundColor: 'rgba(39,174,96,.75)',
                      borderRadius: 6,
                    },
                  ]
                }}
                options={chartOpts(`Loan Activity — ${year}`)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
