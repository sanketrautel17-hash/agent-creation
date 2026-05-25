import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();
  const homePath = isAuthenticated ? "/dashboard" : "/";
  const logoutPath = "/login";

  return (
    <header className="navbar">
      <Link className="brand" to={homePath}>
        Doctor AI
      </Link>
      <nav className="nav-actions">
        {isAuthenticated ? (
          <>
            <span className="user-chip">{user?.name}</span>
            <button
              className="ghost-button"
              type="button"
              onClick={() => {
                logout();
                navigate(logoutPath);
              }}
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/">Home</Link>
            <Link to="/login">Login</Link>
            <Link to="/signup">User Signup</Link>
          </>
        )}
      </nav>
    </header>
  );
}
