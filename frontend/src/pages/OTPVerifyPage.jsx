import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { authService } from "../services/authService";

export default function OTPVerifyPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const state = location.state || {};
  const [otp, setOtp] = useState("");
  const [seconds, setSeconds] = useState(45);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const payload = useMemo(
    () => ({
      email: state.email || "",
      purpose: state.purpose || "login",
      invite_token: state.inviteToken,
      name: state.name,
    }),
    [state],
  );

  useEffect(() => {
    if (!payload.email) {
      navigate("/login", { replace: true });
      return;
    }

    const timer = window.setInterval(() => {
      setSeconds((current) => (current > 0 ? current - 1 : 0));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [payload.email]);

  const verify = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await authService.verifyOtp({ ...payload, otp });
      login(response);
      navigate("/dashboard");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "OTP verification failed.");
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    try {
      await authService.sendOtp(payload);
      setSeconds(45);
      setError("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to resend OTP.");
    }
  };

  return (
    <section className="auth-card">
      <h1>Enter your code</h1>
      <p>We sent a 6-digit code to {payload.email}.</p>
      <form onSubmit={verify}>
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
        <button className="primary-button" disabled={loading} type="submit">
          {loading ? "Verifying..." : "Verify"}
        </button>
      </form>
      <button className="ghost-button" disabled={seconds > 0} type="button" onClick={resend}>
        {seconds > 0 ? `Resend in ${seconds}s` : "Resend OTP"}
      </button>
    </section>
  );
}
