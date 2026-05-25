import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { authService } from "../services/authService";
import { inviteService } from "../services/inviteService";

export default function InviteSignupPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [invite, setInvite] = useState(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const loadInvite = async () => {
      try {
        const data = await inviteService.accept(token);
        setInvite(data);
      } catch (requestError) {
        setError(requestError.response?.data?.detail || "Unable to validate invite.");
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      loadInvite();
    } else {
      setError("Invite token is missing.");
      setLoading(false);
    }
  }, [token]);

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await authService.sendOtp({
        email: invite.email,
        purpose: "signup",
        invite_token: token,
        name,
      });
      navigate("/otp", {
        state: { email: invite.email, purpose: "signup", inviteToken: token, name },
      });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to send signup OTP.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="center-card">Validating your invite...</div>;
  }

  return (
    <section className="auth-card">
      <h1>Activate your access</h1>
      <p>Finish your first-time signup with the invited email and a one-time password.</p>
      {invite ? (
        <form onSubmit={submit}>
          <label>
            Invited email
            <input disabled type="email" value={invite.email} />
          </label>
          <label>
            Full name
            <input
              required
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="John Doe"
            />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? "Sending..." : "Send signup OTP"}
          </button>
        </form>
      ) : (
        <p className="error-text">{error}</p>
      )}
    </section>
  );
}
