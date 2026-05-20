import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import CandidatePage from './pages/CandidatePage.jsx'

export default function App() {
  return (
    <div className="layout">
      <div className="topbar">
        <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>
          <h1>TraqCheck</h1>
        </Link>
        <span className="tag">Resume intake & document collection</span>
      </div>

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/candidates/:id" element={<CandidatePage />} />
      </Routes>
    </div>
  )
}
