import { useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

function App() {
  const [start, setStart] = useState('LAX')
  const [targets, setTargets] = useState('OAK,SJC')
  const [maxIterations, setMaxIterations] = useState(50000)
  const [timeLimit, setTimeLimit] = useState(5)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    const body = {
      start: start.trim().toUpperCase(),
      targets: targets.split(/[ ,]+/).map((s) => s.trim()).filter(Boolean),
      max_iterations: Number(maxIterations) || undefined,
      time_limit: Number(timeLimit) || undefined,
    }

    try {
      const res = await fetch(`${API_BASE}/itinerary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || res.statusText)
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  const exampleFill = () => {
    setStart('LAX')
    setTargets('OAK,SJC')
    setMaxIterations(50000)
    setTimeLimit(5)
    setResult(null)
    setError(null)
  }

  return (
    <div className="app-container">
      <h1>Flight Itinerary Planner</h1>
      <form onSubmit={submit} className="planner-form">
        <label>
          Start IATA:
          <input value={start} onChange={(e) => setStart(e.target.value)} />
        </label>

        <label>
          Targets (comma or space separated):
          <input value={targets} onChange={(e) => setTargets(e.target.value)} />
        </label>

        <label>
          Max Iterations:
          <input type="number" value={maxIterations} onChange={(e) => setMaxIterations(e.target.value)} />
        </label>

        <label>
          Time Limit (s):
          <input type="number" step="0.5" value={timeLimit} onChange={(e) => setTimeLimit(e.target.value)} />
        </label>

        <div className="buttons">
          <button type="submit" disabled={loading}>{loading ? 'Searching...' : 'Find Itinerary'}</button>
          <button type="button" onClick={exampleFill}>Load Example</button>
        </div>
      </form>

      <div className="result">
        {error && <div className="error">Error: {error}</div>}
        {result && (
          <div>
            <h2>Result</h2>
            <p><strong>Path:</strong> {result.path.join(' → ')}</p>
            <p><strong>Total distance:</strong> {result.cost.toFixed(1)}</p>
          </div>
        )}
      </div>

      <div className="notes">
        <p>API Base URL: <code>{API_BASE}</code></p>
        <p>If the backend is running on a different host/port, set <code>VITE_API_BASE</code> in your environment.</p>
      </div>
    </div>
  )
}

export default App
