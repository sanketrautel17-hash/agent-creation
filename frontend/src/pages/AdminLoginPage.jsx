import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { authService } from "../services/authService";

function BrandPulseIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M2 12h4l2.1-6.2L11.8 18l2.2-8h3.1l1.8 2H22"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function formatApiError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback;
}

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await authService.adminLogin({ email, password });
      login(response);
      navigate("/dashboard");
    } catch (requestError) {
      setError(formatApiError(requestError, "Unable to sign in."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-workspace auth-workspace-admin">
      <aside className="auth-showcase auth-showcase-admin">
        <div className="auth-showcase-minimal">
          <div className="auth-brand-row">
            <span className="auth-brand-mark">
              <BrandPulseIcon />
            </span>
            <span>CareAI Admin</span>
          </div>
          <p className="auth-kicker auth-kicker-inverse">Clinic control center</p>
        </div>
      </aside>

      <section className="auth-panel">
        <div className="auth-panel-shell auth-panel-shell-admin">
          <div className="auth-panel-top">
            <div>
              <p className="auth-kicker">Admin access</p>
              <h2>Admin login</h2>
              <p>Sign in with your email and password to manage invites, sessions, and workspace access.</p>
            </div>
          </div>

          <form className="auth-form-grid" onSubmit={submit}>
            <label>
              Admin email
              <input
                required
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="admin@clinic.com"
              />
            </label>
            <label>
              Password
              <input
                required
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
              />
            </label>

            {error ? <p className="error-text">{error}</p> : null}

            <div className="button-row">
              <button className="primary-button primary-button-dark" disabled={loading} type="submit">
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </div>
          </form>

          <div className="auth-alt-route">
            <span>Need the user portal?</span>
            <Link to="/login">Open user login/signup</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
