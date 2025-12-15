import React, {useEffect, useState} from 'react'
import ibmLogo from './assets/ibm-logo.png'

// API base can be configured with VITE_API_URL for Vercel deployments.
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export default function App(){
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(()=>{
    const apiBase = (API_BASE || '')
    const url = (apiBase || '') + '/api/portfolio?enrich=1'

    const fetchOnce = () => {
      fetch(url)
        .then(r=>{ if(!r.ok) throw new Error(r.statusText); return r.json() })
        .then(j=>{ setData(j); setLoading(false); })
        .catch(e=>{ setError(e.message); setLoading(false); })
    }

    // initial fetch
    fetchOnce()

    // try SSE, fallback to polling every 5s
    let es = null
    let pollId = null
    try {
      const sseUrl = (apiBase ? apiBase + '/sse' : '/sse')
      if (typeof EventSource !== 'undefined') {
        es = new EventSource(sseUrl)
        es.onmessage = (e) => {
          try {
            const j = JSON.parse(e.data)
            setData(j)
            setLoading(false)
          } catch(err) {
            console.warn('Failed to parse SSE event', err)
          }
        }
        es.onerror = (err) => {
          // SSE failed; fallback to polling
          try { es.close() } catch (e){}
          es = null
          if (!pollId) pollId = setInterval(fetchOnce, 5000)
        }
      } else {
        pollId = setInterval(fetchOnce, 5000)
      }
    } catch(err) {
      // fallback to polling
      pollId = setInterval(fetchOnce, 5000)
    }

    return ()=>{
      if (es) try{ es.close() }catch(e){}
      if (pollId) clearInterval(pollId)
    }
  },[])

  if(loading) return <div className="app-container">Loading...</div>
  if(error) return <div className="app-container">Error: {error}</div>

  const cash = data.cash || 0
  const transactions = (data.transactions || []).slice().reverse()

  // Use enriched data from backend when available
  const positionsArray = data.positionsArray || Object.entries(data.positions || {}).map(([sym, info]) => ({
    symbol: sym,
    quantity: info.quantity || 0,
    avg_price: info.avg_price || 0,
    price: info.price || info.last_price || info.avg_price || 0,
    value: ((info.price || info.last_price || info.avg_price || 0) * (info.quantity || 0))
  }))

  const totalValue = data.total_value || positionsArray.reduce((s, p) => s + (p.value || 0), cash)

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
          <div className="hero-label">Valeur actuelle du portefeuille</div>
          <div className="hero-balance">${totalValue.toFixed(2)}</div>
          <div className="hero-change">Cash: ${cash.toFixed(2)} • Positions: ${ (totalValue - cash).toFixed(2) }</div>
        </div>
        <div>
          <div style={{fontSize:12,opacity:0.9}}>Plagists Wallet</div>
          <img src={ibmLogo} alt="IBM" style={{height:34,marginTop:6}} />
        </div>
      </div>

      <div className="card">
        <h5>Actions</h5>
        {positionsArray.length ? (
          <table className="positions-table">
            <thead><tr><th>Symbol</th><th>Qty</th><th>Avg</th><th>Price</th><th>Value</th></tr></thead>
            <tbody>
              {positionsArray.map(p => (
                <tr key={p.symbol}><td>{p.symbol}</td><td>{p.quantity}</td><td>${p.avg_price.toFixed(2)}</td><td>${p.price.toFixed(2)}</td><td>${p.value.toFixed(2)}</td></tr>
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
