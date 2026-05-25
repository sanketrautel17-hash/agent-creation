import { Link } from "react-router-dom";

export default function DoctorSidebarTabs({ activeTab, isAdmin }) {
  const tabs = [
    {
      id: "dashboard",
      label: "Catalog Overview",
      description: "Summary and featured agent activity",
      to: "/dashboard?tab=dashboard",
    },
    {
      id: "agents",
      label: "Eigi Agents",
      description: "Browse the full connected agent catalog",
      to: "/dashboard?tab=agents",
    },
    {
      id: "bulk-calls",
      label: "Bulk Calls",
      description: "Upload a CSV and call contacts with an AI agent",
      to: "/campaigns",
    },
  ];

  if (isAdmin) {
    tabs.push(
      {
        id: "history",
        label: "User History",
        description: "Review user, agent, and conversation link records",
        to: "/dashboard?tab=history",
      },
      {
        id: "invite",
        label: "Invite Patient",
        description: "Send and manage invite access from the clinic",
        to: "/dashboard?tab=invite",
      },
    );
  }

  return (
    <section className="doctor-sidebar-section">
      <div className="doctor-history-header doctor-history-header-side">
        <h3>Workspace Views</h3>
        <span>{tabs.length} modes</span>
      </div>

      <div className="doctor-sidebar-tablist" role="tablist" aria-label="Dashboard views">
        {tabs.map((tab) => (
          <Link
            key={tab.id}
            className={`doctor-sidebar-tab ${activeTab === tab.id ? "doctor-sidebar-tab-active" : ""}`}
            to={tab.to}
          >
            <strong>{tab.label}</strong>
            <span>{tab.description}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
