const express = require('express')
const path = require('path')
const fs = require('fs')
const fetch = global.fetch || require('node-fetch')
require('dotenv').config({ path: path.join(__dirname, '..', '.env') })

const app = express()
const PORT = process.env.PORT || 8000
const PORTFOLIO_FILE = process.env.PORTFOLIO_FILE || path.join(__dirname, '..', 'portfolio.json')

app.use(express.json())

app.get('/api/portfolio', async (req, res) => {
  try {
    if (!fs.existsSync(PORTFOLIO_FILE)) {
      return res.json({ cash: 0.0, positions: {}, transactions: [] })
    }
    const txt = fs.readFileSync(PORTFOLIO_FILE, 'utf-8')
    const j = JSON.parse(txt)

    // If client requests enrichment, attempt to fetch live prices (AlphaVantage)
    const enrich = req.query.enrich === '1' || req.query.enrich === 'true'
    if (!enrich) return res.json(j)

    const ALPHA = process.env.ALPHA_VANTAGE_KEY
    const positions = j.positions || {}
    const symbols = Object.keys(positions)
    const enriched = {}
    if (ALPHA && symbols.length) {
      // Parallel requests to AlphaVantage GLOBAL_QUOTE and OVERVIEW
      await Promise.all(symbols.map(async (sym) => {
        try {
          const gqUrl = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${encodeURIComponent(sym)}&apikey=${ALPHA}`
          const ovUrl = `https://www.alphavantage.co/query?function=OVERVIEW&symbol=${encodeURIComponent(sym)}&apikey=${ALPHA}`
          const [gqRes, ovRes] = await Promise.all([fetch(gqUrl), fetch(ovUrl)])
          if (!gqRes.ok) throw new Error(`GLOBAL_QUOTE failed for ${sym}`)
          const gq = await gqRes.json()
          const quote = gq['Global Quote'] || {}
          let price = quote['05. price'] || null
          if (price) price = Number(price)

          let marketCap = null
          let pe = null
          if (ovRes.ok) {
            const ov = await ovRes.json()
            marketCap = ov['MarketCapitalization'] || null
            pe = ov['PERatio'] || ov['PE'] || null
          }

          const qty = positions[sym].quantity || 0
          const avg = positions[sym].avg_price || 0
          const usedPrice = price || avg
          enriched[sym] = {
            quantity: qty,
            avg_price: avg,
            price: usedPrice,
            marketCap,
            PER: pe,
            value: usedPrice * qty,
          }
        } catch (e) {
          // On error, fallback to avg price
          const qty = positions[sym].quantity || 0
          const avg = positions[sym].avg_price || 0
          enriched[sym] = { quantity: qty, avg_price: avg, price: avg, value: avg * qty }
        }
      }))
    } else {
      // No API key — fallback to avg price
      symbols.forEach((sym) => {
        const qty = positions[sym].quantity || 0
        const avg = positions[sym].avg_price || 0
        enriched[sym] = { quantity: qty, avg_price: avg, price: avg, value: avg * qty }
      })
    }

    // compute total value
    const cash = j.cash || 0
    const positionsArray = Object.entries(enriched).map(([sym, info]) => ({ symbol: sym, ...info }))
    const totalPositions = positionsArray.reduce((s, p) => s + (p.value || 0), 0)
    const total_value = cash + totalPositions

    return res.json({ ...j, positions: enriched, positionsArray, total_value })
  } catch (e) {
    return res.status(500).json({ error: String(e) })
  }
})

// serve static build if present
const staticDir = path.join(__dirname, 'dist')
if (fs.existsSync(staticDir)) {
  app.use(express.static(staticDir))
  app.get('*', (req, res) => {
    res.sendFile(path.join(staticDir, 'index.html'))
  })
} else {
  app.get('/', (req, res) => res.send('React app not built. Run `npm run build` in the web folder.'))
}

app.listen(PORT, () => console.log(`Web server listening on http://0.0.0.0:${PORT}`))
