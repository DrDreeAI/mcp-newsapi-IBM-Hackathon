import React, {useEffect, useState} from 'react'

export default function App(){
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(()=>{
    fetch('/api/portfolio')
      .then(r=>{ if(!r.ok) throw new Error(r.statusText); return r.json() })
      .then(j=>{ setData(j); setLoading(false) })
      .catch(e=>{ setError(e.message); setLoading(false) })
  },[])

  if(loading) return <div className="container py-5">Loading...</div>
  if(error) return <div className="container py-5 text-danger">Error: {error}</div>

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
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="h3">Portfolio Dashboard (React)</h1>
        <button className="btn btn-sm btn-outline-secondary" onClick={()=>window.location.reload()}>Refresh</button>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <h5 className="card-title">Cash</h5>
          <p className="card-text fs-4">${cash.toFixed(2)}</p>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <h5 className="card-title">Positions</h5>
          {rows.length ? (
            <div className="table-responsive">
              <table className="table table-sm">
                <thead><tr><th>Symbol</th><th>Qty</th><th>Avg</th><th>Price</th><th>Value</th></tr></thead>
                <tbody>
                  {rows.map(r=> (
                    <tr key={r.sym}><td>{r.sym}</td><td>{r.q}</td><td>${r.avg.toFixed(2)}</td><td>${r.price.toFixed(2)}</td><td>${r.value.toFixed(2)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mb-0">No positions.</p>
          )}
          <p className="mt-3"><strong>Total approx:</strong> ${totalValue.toFixed(2)}</p>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <h5 className="card-title">Recent Transactions</h5>
          {transactions.length ? (
            <ul className="list-group list-group-flush">
              {transactions.map((t, idx)=> (
                <li key={idx} className="list-group-item small"><strong>{t.timestamp}</strong> — {t.quantity} x {t.symbol} @ ${t.price.toFixed(2)} ({t.rationale})</li>
              ))}
            </ul>
          ) : (<p className="mb-0">No transactions yet.</p>)}
        </div>
      </div>

    </div>
  )
}
