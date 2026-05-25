import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { authService } from "../services/authService";
import { inviteService } from "../services/inviteService";

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

export default function SignupPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const inviteToken = searchParams.get("token") || location.state?.inviteToken || "";
  const stateEmail = location.state?.purpose === "signup" ? location.state?.email || "" : "";
  const [step, setStep] = useState(stateEmail ? "verify" : "collect");
  const [invite, setInvite] = useState(stateEmail ? { email: stateEmail } : null);
  const [inviteLoading, setInviteLoading] = useState(Boolean(inviteToken && !stateEmail));
  const [name, setName] = useState(location.state?.name || "");
  const [otp, setOtp] = useState("");
  const [seconds, setSeconds] = useState(45);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const otpPayload = useMemo(
    () => ({
      email: invite?.email || "",
      purpose: "signup",
      invite_token: inviteToken || undefined,
      name,
    }),
    [invite?.email, inviteToken, name],
  );

  useEffect(() => {
    if (!inviteToken || stateEmail) {
      setInviteLoading(false);
      return;
    }

    let cancelled = false;
    const loadInvite = async () => {
      setInviteLoading(true);
      setError("");
      try {
        const data = await inviteService.accept(inviteToken);
        if (!cancelled) {
          setInvite(data);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(formatApiError(requestError, "Unable to validate invite."));
        }
      } finally {
        if (!cancelled) {
          setInviteLoading(false);
        }
      }
    };

    void loadInvite();
    return () => {
      cancelled = true;
    };
  }, [inviteToken, stateEmail]);

  useEffect(() => {
    if (step !== "verify") {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setSeconds((current) => (current > 0 ? current - 1 : 0));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [step]);

  const sendOtp = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (!inviteToken) {
        throw new Error("Signup requires a valid invite link.");
      }

      await authService.sendOtp(otpPayload);
      setStep("verify");
      setSeconds(45);
    } catch (requestError) {
      setError(formatApiError(requestError, "Unable to send OTP."));
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await authService.verifyOtp({ ...otpPayload, otp });
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
      await authService.sendOtp(otpPayload);
      setSeconds(45);
    } catch (requestError) {
      setError(formatApiError(requestError, "Unable to resend OTP."));
    } finally {
      setLoading(false);
    }
  };

  const signupTitle = step === "verify" ? "Enter your verification code" : "Create your user account";
  const signupDescription =
    step === "verify"
      ? `We sent a 6-digit code to ${otpPayload.email}.`
      : "Activate your invited access with a one-time password and finish setting up your workspace.";

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
          <p className="auth-kicker">Invite-only onboarding</p>
        </div>
      </aside>

      <section className="auth-panel">
        <div className="auth-panel-shell">
          <div className="auth-panel-top">
            <div>
              <p className="auth-kicker">User signup</p>
              <h2>{signupTitle}</h2>
              <p>{signupDescription}</p>
            </div>
          </div>

          {step === "verify" ? (
            <form className="auth-form-grid" onSubmit={verifyOtp}>
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
            <form className="auth-form-grid" onSubmit={sendOtp}>
              <label>
                Invited email
                <input
                  disabled
                  type="email"
                  value={invite?.email || ""}
                  placeholder={inviteLoading ? "Validating invite..." : "Open from your invite email"}
                />
              </label>
              <label>
                Full name
                <input
                  required
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Dr. Sarah Smith"
                  disabled={!invite || inviteLoading}
                />
              </label>

              {!inviteToken ? (
                <p className="auth-inline-note">
                  Signup is invite-only. Open this page from your clinic invite link to activate access.
                </p>
              ) : null}

              {error ? <p className="error-text">{error}</p> : null}

              <div className="button-row">
                <button className="primary-button" disabled={loading || inviteLoading || !invite} type="submit">
                  {loading ? "Sending OTP..." : "Continue"}
                </button>
              </div>
            </form>
          )}

          <div className="auth-alt-route">
            <span>Already have access?</span>
            <Link to="/login">Open login</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
