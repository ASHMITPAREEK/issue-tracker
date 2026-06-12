import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">Mini Issue Tracker</Link>
      </div>
      {user && (
        <div className="navbar-actions">
          <span data-testid="nav-username">{user.name}</span>
          <button onClick={handleLogout} data-testid="logout-button">
            Logout
          </button>
        </div>
      )}
    </nav>
  )
}
