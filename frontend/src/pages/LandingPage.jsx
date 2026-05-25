import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <section className="landing-shell">
      <div className="landing-hero">
        <div className="landing-copy">
          <p className="eyebrow">Doctor AI</p>
          <h1>Your clinic&apos;s private AI care companion</h1>
          <p className="lead">
            Invite patients into a secure voice-first care experience for appointment support,
            follow-up care, and prescription guidance with OTP-based access.
          </p>
          <div className="button-row">
            <Link className="primary-button" to="/login">
              Login
            </Link>
            <Link className="ghost-button" to="/signup">
              User Signup
            </Link>
            <Link className="ghost-button" to="/invite/accept">
              Accept invite
            </Link>
          </div>
        </div>

        <div className="landing-panel">
          <div className="feature-card">
            <strong>Invite-only onboarding</strong>
            <p>Admins control access while patients sign in with a simple OTP flow.</p>
          </div>
          <div className="feature-card">
            <strong>Voice-ready sessions</strong>
            <p>Start guided AI sessions for appointments, follow-up care, and prescriptions.</p>
          </div>
          <div className="feature-card">
            <strong>Shared admin workspace</strong>
            <p>Track invites, patient activity, and agent sessions in one protected dashboard.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
