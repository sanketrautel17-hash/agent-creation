import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { authService } from "../services/authService";

export default function LoginPage() {
  const [mode, setMode] = useState("patient");
  const [patientEmail, setPatientEmail] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (mode === "admin") {
        const response = await authService.adminLogin({ email: adminEmail, password });
        login(response);
        navigate("/dashboard");
      } else {
        await authService.sendOtp({ email: patientEmail, purpose: "login" });
        navigate("/otp", { state: { email: patientEmail, purpose: "login" } });
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          (mode === "admin" ? "Unable to sign in." : "Unable to send OTP."),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Welcome back</h1>
      <p>
        Patients sign in with OTP. Admins sign in with their email and password.
      </p>
      <div className="auth-mode-switch" role="tablist" aria-label="Sign-in type">
        <button
          className={mode === "patient" ? "auth-mode-tab auth-mode-tab-active" : "auth-mode-tab"}
          type="button"
          onClick={() => {
            setMode("patient");
            setError("");
          }}
        >
          Patient OTP
        </button>
        <button
          className={mode === "admin" ? "auth-mode-tab auth-mode-tab-active" : "auth-mode-tab"}
          type="button"
          onClick={() => {
            setMode("admin");
            setError("");
          }}
        >
          Admin Password
        </button>
      </div>
      <form onSubmit={submit}>
        <label>
          Email
          <input
            required
            type="email"
            value={mode === "admin" ? adminEmail : patientEmail}
            onChange={(event) =>
              mode === "admin"
                ? setAdminEmail(event.target.value)
                : setPatientEmail(event.target.value)
            }
            placeholder={mode === "admin" ? "admin@clinic.com" : "patient@example.com"}
          />
        </label>
        {mode === "admin" ? (
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
        ) : null}
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" disabled={loading} type="submit">
          {loading ? (mode === "admin" ? "Signing in..." : "Sending...") : mode === "admin" ? "Sign in" : "Send OTP"}
        </button>
      </form>
    </section>
  );
}
