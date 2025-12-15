import React, {useEffect, useState} from 'react'
import ibmLogo from './assets/ibm-logo.png'

// API base can be configured with VITE_API_URL for Vercel deployments.
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export default function App(){
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(()=>{
    const url = (API_BASE || '') + '/api/portfolio'
    fetch(url)
      .then(r=>{ if(!r.ok) throw new Error(r.statusText); return r.json() })
      .then(j=>{ setData(j); setLoading(false) })
      .catch(e=>{ setError(e.message); setLoading(false) })
  },[])

  if(loading) return <div className="app-container">Loading...</div>
  if(error) return <div className="app-container">Error: {error}</div>

  const cash = data.cash || 0
  const positions = data.positions || {}
  const transactions = (data.transactions || []).slice().reverse()

  const rows = Object.entries(positions).map(([sym,info])=>{
    const q = info.quantity||0
    const avg = info.avg_price||0
    const price = info.last_price || avg
    const value = price * q
    return {sym,q,avg,price,value}
  })

  const totalValue = rows.reduce((s,r)=>s+r.value, cash)

  return (
    <div className="app-container">
      <div className="brand-bar">
        <div className="brand-left">
          <div style={{display:'flex',alignItems:'center',gap:10}}>
            <div className="brand-title">Plagists Wallet <span style={{fontWeight:500,opacity:0.9}}>×</span></div>
            <img src={ibmLogo} alt="IBM" className="brand-logo" />
          </div>
          <div className="brand-sub">Portefeuille collaboratif — Plagists Wallet x IBM</div>
        </div>
        <div>
          <button className="refresh-btn" onClick={()=>window.location.reload()}>Refresh</button>
        </div>
      </div>

      <div className="hero-card">
        <div className="hero-left">
          <div className="hero-label">Total balance</div>
          <div className="hero-balance">${totalValue.toFixed(2)}</div>
          <div className="hero-change">Cash: ${cash.toFixed(2)} • Positions: ${ (totalValue - cash).toFixed(2) }</div>
        </div>
        <div>
          <div style={{fontSize:12,opacity:0.9}}>Plagists Wallet</div>
          <img src={ibmLogo} alt="IBM" style={{height:34,marginTop:6}} />
        </div>
      </div>

      <div className="card">
        <h5>Positions</h5>
        {rows.length ? (
          <table className="positions-table">
            <thead><tr><th>Symbol</th><th>Qty</th><th>Avg</th><th>Price</th><th>Value</th></tr></thead>
            <tbody>
              {rows.map(r=> (
                <tr key={r.sym}><td>{r.sym}</td><td>{r.q}</td><td>${r.avg.toFixed(2)}</td><td>${r.price.toFixed(2)}</td><td>${r.value.toFixed(2)}</td></tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="small muted">No positions.</p>
        )}
        <p className="small muted mt-2"><strong>Total approx:</strong> ${totalValue.toFixed(2)}</p>
      </div>

      <div className="card">
        <h5>Recent Transactions</h5>
        {transactions.length ? (
          <div>
            {transactions.map((t, idx)=> (
              <div key={idx} className="small" style={{padding:'8px 0',borderBottom:'1px solid #f1f5f9'}}><strong>{t.timestamp}</strong> — {t.quantity} x {t.symbol} @ ${t.price.toFixed(2)} <span className="muted">({t.rationale})</span></div>
            ))}
          </div>
        ) : (<p className="small muted">No transactions yet.</p>)}
      </div>

    </div>
  )
}
