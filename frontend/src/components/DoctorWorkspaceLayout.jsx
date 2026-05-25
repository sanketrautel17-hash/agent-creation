import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getAgentMeta, getAgentVisualTone, toAgentCard } from "../constants/doctorWorkspace";

function IconFrame({ children, tone = "default" }) {
  return <span className={`doctor-icon-frame doctor-icon-frame-${tone}`}>{children}</span>;
}

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

function StethoscopeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M7 4v5a5 5 0 0 0 10 0V4M7 7H5a2 2 0 0 1-2-2V4m16 3h2a2 2 0 0 0 2-2V4M12 14v2a4 4 0 0 0 8 0v-1"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
      <circle cx="20" cy="15" r="1.8" fill="none" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function HeartIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 20s-7-4.3-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.7-7 10-7 10Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function PillIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="m10 14 4-4m-8.2 8.2a4.5 4.5 0 0 1 0-6.4l5.5-5.5a4.5 4.5 0 1 1 6.4 6.4l-5.5 5.5a4.5 4.5 0 0 1-6.4 0Z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function BrainIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M9 4a3 3 0 0 0-3 3v.4A3.6 3.6 0 0 0 4 10.7 3.4 3.4 0 0 0 6.1 14 3.3 3.3 0 0 0 9 19h1m4-15a3 3 0 0 1 3 3v.4a3.6 3.6 0 0 1 2 3.3 3.4 3.4 0 0 1-2.1 3.3A3.3 3.3 0 0 1 15 19h-1m0-15v15m-4-9h4m-4 4h4"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="11" cy="11" r="6" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="m20 20-4.2-4.2" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M6 16v-4a6 6 0 1 1 12 0v4l2 2H4l2-2Zm4 3a2 2 0 0 0 4 0"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="8" r="3.2" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M5 20a7 7 0 0 1 14 0" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </svg>
  );
}

function GearIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="m12 3 1.2 2.1 2.4.5-.5 2.4 1.7 1.7-1.7 1.7.5 2.4-2.4.5L12 21l-1.2-2.1-2.4-.5.5-2.4-1.7-1.7 1.7-1.7-.5-2.4 2.4-.5L12 3Zm0 6.2a2.8 2.8 0 1 0 0 5.6 2.8 2.8 0 0 0 0-5.6Z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
}

function getAgentIcon(agent) {
  const tone = getAgentVisualTone(agent);
  if (tone === "followup") {
    return <HeartIcon />;
  }
  if (tone === "prescription") {
    return <PillIcon />;
  }
  return <StethoscopeIcon />;
}

function buildDoctorProfile(user) {
  const name = user?.name || "Doctor";
  const initials = name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
  return {
    name,
    initials: initials || "DR",
    specialty: user?.role === "admin" ? "Clinic Administrator" : "Internal Medicine",
  };
}

export default function DoctorWorkspaceLayout({
  activeAgentId,
  agents = [],
  headerTitle,
  headerSubtitle,
  sidebarContent,
  children,
}) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const doctor = buildDoctorProfile(user);
  const logoutPath = "/login";
  const activeMeta = getAgentMeta(activeAgentId, agents);
  const agentCards = agents.map(toAgentCard);

  return (
    <div className="doctor-workspace">
      <aside className="doctor-sidebar">
        <div className="doctor-sidebar-top">
          <Link className="doctor-brand" to="/dashboard">
            <span className="doctor-brand-mark">
              <BrandPulseIcon />
            </span>
            <span>CareAI Dashboard</span>
          </Link>
          <button className="doctor-mini-button" type="button" aria-label="Workspace settings">
            <GearIcon />
          </button>
        </div>

        <section className="doctor-profile-card">
          <div className="doctor-avatar">{doctor.initials}</div>
          <div>
            <h2>{doctor.name}</h2>
            <p>{doctor.specialty}</p>
          </div>
        </section>

        {sidebarContent ? (
          sidebarContent
        ) : (
          <section className="doctor-sidebar-section">
            <div className="doctor-section-title">
              <IconFrame>
                <BrainIcon />
              </IconFrame>
              <span>AI Care Agents</span>
            </div>
            <div className="doctor-agent-list">
              {agentCards.length ? (
                agentCards.map((agent) => {
                  const isActive = agent.id === activeAgentId;
                  return (
                    <Link
                      key={agent.id}
                      className={`doctor-agent-link ${isActive ? "doctor-agent-link-active" : ""}`}
                      to={`/agents/${agent.id}`}
                    >
                      <IconFrame tone={isActive ? "inverse" : "soft"}>{getAgentIcon(agent)}</IconFrame>
                      <div className="doctor-agent-copy">
                        <strong>{agent.title}</strong>
                        <span>{agent.specialty}</span>
                      </div>
                      <span className={`doctor-agent-state doctor-agent-state-${isActive ? "active" : agent.status}`}>
                        {isActive ? "active" : agent.status}
                      </span>
                    </Link>
                  );
                })
              ) : (
                <p className="doctor-empty-copy">No Eigi agents are available for this workspace yet.</p>
              )}
            </div>
          </section>
        )}

      </aside>

      <section className="doctor-main-shell">
        <header className="doctor-topbar">
          <div className="doctor-topbar-heading">
            <div className="doctor-topbar-icon">
              {getAgentIcon(activeMeta)}
            </div>
            <div>
              <h1>{headerTitle}</h1>
              <p>{headerSubtitle}</p>
            </div>
          </div>
          <div className="doctor-topbar-actions">
            <button className="doctor-mini-button" type="button" aria-label="Search">
              <SearchIcon />
            </button>
            <button className="doctor-mini-button" type="button" aria-label="Notifications">
              <BellIcon />
            </button>
            <div className="doctor-topbar-profile">
              <button className="doctor-mini-button" type="button" aria-label="Profile">
                <UserIcon />
              </button>
              <button
                className="doctor-topbar-logout"
                type="button"
                onClick={() => {
                  logout();
                  navigate(logoutPath);
                }}
              >
                Log out
              </button>
            </div>
          </div>
        </header>

        <main className="doctor-stage">{children}</main>
      </section>
    </div>
  );
}
