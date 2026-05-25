import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { authService } from "../services/authService";

const LOGIN_TABS = {
  user: "user",
  admin: "admin",
};

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

export default function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [activeTab, setActiveTab] = useState(LOGIN_TABS.user);
  const [step, setStep] = useState("collect");
  const [patientEmail, setPatientEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [seconds, setSeconds] = useState(45);
  const [adminEmail, setAdminEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const userOtpPayload = useMemo(
    () => ({
      email: patientEmail,
      purpose: "login",
    }),
    [patientEmail],
  );

  useEffect(() => {
    const state = location.state || {};
    if (!state.email || !state.purpose) {
      return;
    }

    if (state.purpose === "signup") {
      navigate("/signup", { replace: true, state });
      return;
    }

    setActiveTab(LOGIN_TABS.user);
    setPatientEmail(state.email);
    setStep("verify");
  }, [location.state, navigate]);

  useEffect(() => {
    if (activeTab !== LOGIN_TABS.user || step !== "verify") {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setSeconds((current) => (current > 0 ? current - 1 : 0));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [activeTab, step]);

  const switchTab = (nextTab) => {
    setActiveTab(nextTab);
    setStep("collect");
    setOtp("");
    setError("");
    setSeconds(45);
  };

  const sendUserOtp = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await authService.sendOtp(userOtpPayload);
      setStep("verify");
      setSeconds(45);
    } catch (requestError) {
      setError(formatApiError(requestError, "Unable to send OTP."));
    } finally {
      setLoading(false);
    }
  };

  const verifyUserOtp = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await authService.verifyOtp({ ...userOtpPayload, otp });
      login(response);
      navigate("/dashboard");
    } catch (requestError) {
      setError(formatApiError(requestError, "OTP verification failed."));
    } finally {
      setLoading(false);
    }
  };

  const resendOtp = async () => {
    setLoading(true);
    setError("");
    try {
      await authService.sendOtp(userOtpPayload);
      setSeconds(45);
    } catch (requestError) {
      setError(formatApiError(requestError, "Unable to resend OTP."));
    } finally {
      setLoading(false);
    }
  };

  const submitAdminLogin = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await authService.adminLogin({ email: adminEmail, password });
      login(response);
      navigate("/dashboard");
    } catch (requestError) {
      setError(formatApiError(requestError, "Unable to sign in."));
    } finally {
      setLoading(false);
    }
  };

  const authTitle =
    activeTab === LOGIN_TABS.admin
      ? "Admin login"
      : step === "verify"
        ? "Enter your verification code"
        : "User login";

  const authDescription =
    activeTab === LOGIN_TABS.admin
      ? "Sign in with your email and password to manage invites, sessions, and workspace access."
      : step === "verify"
        ? `We sent a 6-digit code to ${userOtpPayload.email}.`
        : "Users sign in with a one-time password to access their care workspace securely.";

  return (
    <div className="auth-workspace">
      <aside className="auth-showcase">
        <div className="auth-showcase-minimal">
          <div className="auth-brand-row">
            <span className="auth-brand-mark">
              <BrandPulseIcon />
            </span>
            <span>CareAI Dashboard</span>
          </div>
          <p className="auth-kicker">Unified clinical workspace</p>
        </div>
      </aside>

      <section className="auth-panel">
        <div className="auth-panel-shell">
          <div className="auth-panel-top">
            <div>
              <p className="auth-kicker">{activeTab === LOGIN_TABS.admin ? "Admin access" : "User access"}</p>
              <h2>{authTitle}</h2>
              <p>{authDescription}</p>
            </div>
            <div className="auth-mode-switch auth-mode-switch-dashboard" role="tablist" aria-label="Login mode">
              <button
                className={activeTab === LOGIN_TABS.user ? "auth-mode-tab auth-mode-tab-active" : "auth-mode-tab"}
                type="button"
                onClick={() => switchTab(LOGIN_TABS.user)}
              >
                User Login
              </button>
              <button
                className={activeTab === LOGIN_TABS.admin ? "auth-mode-tab auth-mode-tab-active" : "auth-mode-tab"}
                type="button"
                onClick={() => switchTab(LOGIN_TABS.admin)}
              >
                Admin Login
              </button>
            </div>
          </div>

          {activeTab === LOGIN_TABS.user ? (
            step === "verify" ? (
              <form className="auth-form-grid" onSubmit={verifyUserOtp}>
                <label>
                  One-time password
                  <input
                    required
                    inputMode="numeric"
                    maxLength={6}
                    minLength={6}
                    value={otp}
                    onChange={(event) => setOtp(event.target.value.replace(/\D/g, ""))}
                    placeholder="123456"
                  />
                </label>
                {error ? <p className="error-text">{error}</p> : null}
                <div className="button-row">
                  <button className="primary-button" disabled={loading} type="submit">
                    {loading ? "Verifying..." : "Verify OTP"}
                  </button>
                  <button className="ghost-button" disabled={loading || seconds > 0} type="button" onClick={resendOtp}>
                    {seconds > 0 ? `Resend in ${seconds}s` : "Resend OTP"}
                  </button>
                  <button className="ghost-button" type="button" onClick={() => setStep("collect")}>
                    Back
                  </button>
                </div>
              </form>
            ) : (
              <form className="auth-form-grid" onSubmit={sendUserOtp}>
                <label>
                  Email
                  <input
                    required
                    type="email"
                    value={patientEmail}
                    onChange={(event) => setPatientEmail(event.target.value)}
                    placeholder="patient@example.com"
                  />
                </label>

                {error ? <p className="error-text">{error}</p> : null}

                <div className="button-row">
                  <button className="primary-button" disabled={loading} type="submit">
                    {loading ? "Sending OTP..." : "Continue"}
                  </button>
                </div>
              </form>
            )
          ) : (
            <form className="auth-form-grid" onSubmit={submitAdminLogin}>
              <label>
                Admin email
                <input
                  required
                  type="email"
                  value={adminEmail}
                  onChange={(event) => setAdminEmail(event.target.value)}
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
          )}

          <div className="auth-alt-route">
            <span>User signup is on a separate page.</span>
            <Link to="/signup">Open user signup</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
