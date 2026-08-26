import { Link, useNavigate } from 'react-router-dom';

function Navbar() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    navigate('/login');
  };

  return (
    <nav style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '16px 24px',
      borderBottom: '1px solid #e5e4e7',
    }}>
      <Link to="/" style={{ fontWeight: 'bold', textDecoration: 'none', color: 'inherit' }}>
        SmartEstate AI
      </Link>

      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
        <Link to="/search">Search</Link>

        {!token && (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}

        {token && role === 'buyer' && <Link to="/buyer">Dashboard</Link>}
        {token && role === 'agent' && <Link to="/agent">Dashboard</Link>}
        {token && role === 'admin' && <Link to="/admin">Dashboard</Link>}

        {token && (
          <button onClick={handleLogout} style={{ padding: '6px 12px' }}>
            Logout
          </button>
        )}
      </div>
    </nav>
  );
}

export default Navbar;