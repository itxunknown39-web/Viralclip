import { useEffect, useState } from 'react'
import { HashRouter, Route, Routes, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Header from './components/Header.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Create from './pages/Create.jsx'
import Results from './pages/Results.jsx'
import History from './pages/History.jsx'
import Settings from './pages/Settings.jsx'
import { getDevices } from './api/client.js'

function Shell() {
  const [devices, setDevices] = useState(null)
  const location = useLocation()

  useEffect(() => {
    getDevices().then(setDevices).catch(() => setDevices(null))
  }, [location.pathname])

  return (
    <div className="shell">
      <Sidebar />
      <div className="main">
        <Header devices={devices} />
        <div className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/create" element={<Create />} />
            <Route path="/results/:jobId" element={<Results />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <HashRouter>
      <Shell />
    </HashRouter>
  )
}