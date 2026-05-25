import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import DoctorSidebarTabs from "../components/DoctorSidebarTabs";
import DoctorWorkspaceLayout from "../components/DoctorWorkspaceLayout";
import { toAgentCard } from "../constants/doctorWorkspace";
import { useAuth } from "../context/AuthContext";
import { adminService } from "../services/adminService";
import { agentService } from "../services/agentService";

const DEFAULT_HISTORY_PAGE_SIZE = 5;
const DASHBOARD_TABS = new Set(["dashboard", "agents", "history", "invite"]);

function formatApiError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback;
}

function formatAgentTimestamp(value) {
  if (!value) {
    return "Recently synced";
  }
  return new Date(value).toLocaleString();
}

function formatHistoryTime(value) {
  if (!value) {
    return "Unavailable";
  }
  return new Date(value).toLocaleString();
}

function buildHistoryConversationLink(item) {
  const basePath = item.conversation_path || `/agents/${item.agent_id}`;
  const joiner = basePath.includes("?") ? "&" : "?";
  return `${basePath}${joiner}historyId=${encodeURIComponent(item.id)}`;
}

function getAllowedTab(tab, isAdmin) {
  if (!DASHBOARD_TABS.has(tab)) {
    return "dashboard";
  }
  if (!isAdmin && (tab === "history" || tab === "invite")) {
    return "dashboard";
  }
  return tab;
}

export default function DashboardPage() {
  const { user, isAdmin } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = getAllowedTab(searchParams.get("tab") || "dashboard", isAdmin);
  const [agents, setAgents] = useState([]);
  const [agentsLoading, setAgentsLoading] = useState(true);
  const [agentsError, setAgentsError] = useState("");
  const [stats, setStats] = useState(null);
  const [invites, setInvites] = useState([]);
  const [historyPage, setHistoryPage] = useState({
    items: [],
    total: 0,
    page: 1,
    page_size: DEFAULT_HISTORY_PAGE_SIZE,
    total_pages: 1,
  });
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteMessage, setInviteMessage] = useState("");
  const [inviteError, setInviteError] = useState("");
  const [inviteLoading, setInviteLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    const requestedTab = searchParams.get("tab") || "dashboard";
    const allowedTab = getAllowedTab(requestedTab, isAdmin);
    if (allowedTab !== requestedTab) {
      setSearchParams({ tab: allowedTab }, { replace: true });
    }
  }, [isAdmin, searchParams, setSearchParams]);

  const loadAgents = async () => {
    setAgentsLoading(true);
    setAgentsError("");
    try {
      const response = await agentService.listAgents({ page: 1, page_size: 50 });
      setAgents(response.data || []);
    } catch (error) {
      setAgents([]);
      setAgentsError(formatApiError(error, "Unable to load agents from Eigi."));
    } finally {
      setAgentsLoading(false);
    }
  };

  const loadAdminData = async (historyPageNumber = historyPage.page) => {
    if (!isAdmin) {
      setStats(null);
      setInvites([]);
      setHistoryPage({
        items: [],
        total: 0,
        page: 1,
        page_size: DEFAULT_HISTORY_PAGE_SIZE,
        total_pages: 1,
      });
      return;
    }

    setHistoryLoading(true);
    try {
      const [statsResponse, invitesResponse, historyResponse] = await Promise.all([
        adminService.stats(),
        adminService.invites(),
        adminService.userHistory({ page: historyPageNumber, pageSize: historyPage.page_size }),
      ]);
      setStats(statsResponse);
      setInvites(invitesResponse);
      setHistoryPage(historyResponse);
    } catch {
      setStats(null);
      setInvites([]);
      setHistoryPage((currentPage) => ({
        ...currentPage,
        items: [],
        total: 0,
        total_pages: 1,
      }));
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    void loadAgents();
  }, []);

  useEffect(() => {
    void loadAdminData();
  }, [isAdmin]);

  const featuredAgents = useMemo(() => agents.slice(0, 4), [agents]);
  const historyRows = historyPage.items;
  const agentNamesById = useMemo(
    () =>
      agents.reduce((accumulator, agent) => {
        accumulator[agent.id] = agent.agent_name;
        return accumulator;
      }, {}),
    [agents],
  );

  const createInvite = async (event) => {
    event.preventDefault();
    setInviteLoading(true);
    setInviteError("");
    setInviteMessage("");
    try {
      const response = await adminService.createInvite(inviteEmail);
      setInviteMessage(response.message);
      setInviteEmail("");
      await loadAdminData();
    } catch (error) {
      setInviteError(formatApiError(error, "Unable to send invite."));
    } finally {
      setInviteLoading(false);
    }
  };

  const revokeInvite = async (inviteId) => {
    setInviteError("");
    setInviteMessage("");
    try {
      await adminService.revokeInvite(inviteId);
      await loadAdminData();
    } catch (error) {
      setInviteError(formatApiError(error, "Unable to revoke invite."));
    }
  };

  const changeHistoryPage = async (nextPage) => {
    if (nextPage < 1 || nextPage > historyPage.total_pages || nextPage === historyPage.page) {
      return;
    }
    await loadAdminData(nextPage);
  };

  return (
    <DoctorWorkspaceLayout
      agents={agents}
      headerTitle="Clinical Command Center"
      headerSubtitle="Browse the Eigi agent catalog, open live chat workspaces, and manage patient access."
      sidebarContent={<DoctorSidebarTabs activeTab={activeTab} isAdmin={isAdmin} />}
    >
      <div className="doctor-content-shell doctor-dashboard-footer">
        <section className="doctor-chat-stream">
          {activeTab === "dashboard" ? (
            <>
              <article className="doctor-message-card doctor-message-card-assistant doctor-message-card-intro">
                <span className="doctor-message-author">Eigi Agent Proxy</span>
                <p>
                  Hello Dr. {user?.name?.split(" ")[0] || "Smith"}. Open any agent to fill its runtime variables and start
                  chatting directly from this workspace.
                </p>
                <time>{new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
              </article>

              <section className="doctor-history-panel">
                <div className="doctor-history-header">
                  <h2>Featured Agents</h2>
                  <span>{agentsLoading ? "Refreshing..." : `${agents.length} total agents`}</span>
                </div>
                {agentsError ? <p className="error-text">{agentsError}</p> : null}

                <div className="doctor-detail-grid">
                  <article className="doctor-detail-card">
                    <span className="doctor-small-label">Total agents</span>
                    <p>{agents.length}</p>
                  </article>
                  <article className="doctor-detail-card">
                    <span className="doctor-small-label">Inbound ready</span>
                    <p>{agents.filter((agent) => String(agent.agent_type).toUpperCase() === "INBOUND").length}</p>
                  </article>
                  {isAdmin && stats ? (
                    <article className="doctor-detail-card">
                      <span className="doctor-small-label">Active patients</span>
                      <p>{stats.active_patients}</p>
                    </article>
                  ) : null}
                  {isAdmin && stats ? (
                    <article className="doctor-detail-card">
                      <span className="doctor-small-label">Total invites</span>
                      <p>{stats.total_invites}</p>
                    </article>
                  ) : null}
                </div>

                {featuredAgents.length ? (
                  <div className="doctor-history-list">
                    {featuredAgents.map((agent) => {
                      const card = toAgentCard(agent);
                      return (
                        <article key={agent.id} className="doctor-history-item">
                          <div className="doctor-history-row">
                            <strong>{card.title}</strong>
                            <span className={`doctor-session-badge doctor-session-badge-${card.status}`}>{card.type}</span>
                          </div>
                          <p>{card.description}</p>
                          <div className="doctor-history-row doctor-history-meta">
                            <span>{card.specialty}</span>
                            <span>{formatAgentTimestamp(agent.updated_at || agent.created_at)}</span>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                ) : (
                  <p className="doctor-empty-copy">
                    {agentsLoading ? "Syncing agents from Eigi..." : "No agents were returned by the Eigi catalog yet."}
                  </p>
                )}
              </section>
            </>
          ) : null}

          {activeTab === "agents" ? (
            <section className="doctor-history-panel">
              <div className="doctor-history-header">
                <h2>Eigi Agents</h2>
                <span>{agentsLoading ? "Refreshing..." : `${agents.length} available`}</span>
              </div>
              {agentsError ? <p className="error-text">{agentsError}</p> : null}
              <div className="doctor-agent-launch-grid">
                {agents.map((agent) => {
                  const card = toAgentCard(agent);
                  return (
                    <Link key={agent.id} className="doctor-launch-card" to={`/agents/${agent.id}`}>
                      <div>
                        <strong>{card.title}</strong>
                        <span>{card.specialty}</span>
                      </div>
                      <p>{card.description}</p>
                      <span className="doctor-launch-link">Inspect agent</span>
                    </Link>
                  );
                })}
              </div>
              {!agentsLoading && !agents.length ? (
                <p className="doctor-empty-copy">No Eigi agents are available for inspection right now.</p>
              ) : null}
            </section>
          ) : null}

          {activeTab === "invite" ? (
            <section className="doctor-history-panel">
              <div className="doctor-history-header">
                <h2>Invite Patients</h2>
                <span>{invites.length} tracked invites</span>
              </div>
              {isAdmin ? (
                <>
                  <form className="doctor-admin-form" onSubmit={createInvite}>
                    <input
                      className="doctor-composer-input"
                      required
                      type="email"
                      value={inviteEmail}
                      onChange={(event) => setInviteEmail(event.target.value)}
                      placeholder="patient@example.com"
                    />
                    <button className="primary-button" disabled={inviteLoading} type="submit">
                      {inviteLoading ? "Sending..." : "Send invite"}
                    </button>
                  </form>

                  {inviteMessage ? <p className="doctor-success-copy">{inviteMessage}</p> : null}
                  {inviteError ? <p className="error-text">{inviteError}</p> : null}

                  {invites.length ? (
                    <div className="doctor-history-list">
                      {invites.map((invite) => (
                        <article key={invite.id} className="doctor-history-item doctor-history-item-admin">
                          <div className="doctor-history-row">
                            <strong>{invite.email}</strong>
                            <span className={`doctor-session-badge doctor-session-badge-${invite.status}`}>
                              {invite.status}
                            </span>
                          </div>
                          <p>Created {new Date(invite.created_at).toLocaleString()}</p>
                          <div className="doctor-history-row doctor-history-meta">
                            <span>{invite.status === "pending" ? "Awaiting activation" : "Updated"}</span>
                            <button className="doctor-inline-link" type="button" onClick={() => revokeInvite(invite.id)}>
                              Revoke
                            </button>
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="doctor-empty-copy">No invites yet. Send the first patient invite from here.</p>
                  )}
                </>
              ) : (
                <p className="doctor-empty-copy">Only admin users can invite patients.</p>
              )}
            </section>
          ) : null}

          {activeTab === "history" ? (
            <section className="doctor-history-panel">
              <div className="doctor-history-header">
                <h2>User History</h2>
                <span>{historyPage.total} tracked conversations</span>
              </div>
              {isAdmin ? (
                historyRows.length ? (
                  <>
                    <div className="doctor-history-table-shell">
                      <div className="table-wrap">
                        <table className="doctor-history-table">
                          <thead>
                            <tr>
                              <th>User</th>
                              <th>User ID</th>
                              <th>Agent</th>
                              <th>Type</th>
                              <th>Session</th>
                              <th>Last Activity</th>
                              <th>Conversation</th>
                            </tr>
                          </thead>
                          <tbody>
                            {historyRows.map((item) => (
                              <tr key={item.id}>
                                <td>
                                  <strong>{item.user_name}</strong>
                                  <div className="doctor-table-subcopy">{item.user_email || "No email saved"}</div>
                                </td>
                                <td>
                                  <code className="doctor-history-code">{item.user_id}</code>
                                </td>
                                <td>{item.agent_name || agentNamesById[item.agent_id] || item.agent_id}</td>
                                <td>
                                  <span className="doctor-history-type-pill">{item.session_type}</span>
                                </td>
                                <td>
                                  <code className="doctor-history-code">
                                    {item.session_id || item.conversation_id || "Unavailable"}
                                  </code>
                                </td>
                                <td>{formatHistoryTime(item.last_activity_at)}</td>
                                <td>
                                  <Link className="doctor-history-link" to={buildHistoryConversationLink(item)}>
                                    Open
                                  </Link>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <div className="doctor-pagination-row">
                      <span className="doctor-pagination-copy">
                        Page {historyPage.page} of {historyPage.total_pages}
                      </span>
                      <span className="doctor-pagination-copy">
                        Showing {historyRows.length} of {historyPage.total}
                      </span>
                      <div className="button-row">
                        <button
                          className="ghost-button"
                          type="button"
                          disabled={historyLoading || historyPage.page <= 1}
                          onClick={() => void changeHistoryPage(historyPage.page - 1)}
                        >
                          Previous
                        </button>
                        <button
                          className="ghost-button"
                          type="button"
                          disabled={historyLoading || historyPage.page >= historyPage.total_pages}
                          onClick={() => void changeHistoryPage(historyPage.page + 1)}
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="doctor-empty-copy">
                    {historyLoading ? "Loading user history..." : "No user conversation history has been recorded yet."}
                  </p>
                )
              ) : (
                <p className="doctor-empty-copy">Only admin users can view user history.</p>
              )}
            </section>
          ) : null}
        </section>
      </div>
    </DoctorWorkspaceLayout>
  );
}
