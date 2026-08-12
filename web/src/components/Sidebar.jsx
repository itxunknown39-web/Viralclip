import { NavLink } from 'react-router-dom'

const ITEMS = [
  { to: '/', label: 'Dashboard', icon: '▦' },
  { to: '/create', label: 'New Project', icon: '＋' },
  { to: '/history', label: 'History', icon: '◷' },
  { to: '/settings', label: 'Settings', icon: '⚙' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo">
        <span className="logo-mark">V</span>
        <div className="logo-text">
          <strong>ViralCut</strong>
          <span>AI</span>
        </div>
      </div>
      <nav className="nav">
        {ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}