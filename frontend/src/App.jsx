import { useState } from 'react'
import DecisionView from './components/DecisionView'
import AccuracyView from './components/AccuracyView'
import { validCutoff } from './config'
import './App.css'

export default function App() {
  const [tab, setTab] = useState('decision')
  const [cutoff, setCutoff] = useState('09:00')
  const ok = validCutoff(cutoff)

  return (
    <div className="app">
      <h1>UK Wind Forecast Monitor</h1>
      <p className="note">
        National wind generation (Elexon BMRS: WINDFOR forecasts, FUELHH actuals) for
        day-ahead purchase decisions made in January 2026.
      </p>

      <div className="topbar">
        <div className="tabs">
          <button className={tab === 'decision' ? 'active' : ''} onClick={() => setTab('decision')}>
            1. Decision view
          </button>
          <button className={tab === 'accuracy' ? 'active' : ''} onClick={() => setTab('accuracy')}>
            2. Forecast accuracy
          </button>
        </div>
        <label>Decision time (D-1, London){' '}
          <input type="time" value={cutoff} onChange={(e) => setCutoff(e.target.value)} />
        </label>
      </div>

      {!ok && <p className="error">Enter a valid decision time.</p>}
      {ok && tab === 'decision' && <DecisionView cutoff={cutoff} />}
      {ok && tab === 'accuracy' && <AccuracyView cutoff={cutoff} />}
    </div>
  )
}