const express = require('express')
const path = require('path')
const fs = require('fs')

const app = express()
const PORT = process.env.PORT || 8000
const PORTFOLIO_FILE = process.env.PORTFOLIO_FILE || path.join(__dirname, '..', 'portfolio.json')

app.use(express.json())

app.get('/api/portfolio', (req, res) => {
  try {
    if (!fs.existsSync(PORTFOLIO_FILE)) {
      return res.json({ cash: 0.0, positions: {}, transactions: [] })
    }
    const txt = fs.readFileSync(PORTFOLIO_FILE, 'utf-8')
    const j = JSON.parse(txt)
    return res.json(j)
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
