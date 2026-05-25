import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import DoctorSidebarTabs from "../components/DoctorSidebarTabs";
import DoctorWorkspaceLayout from "../components/DoctorWorkspaceLayout";
import { useAuth } from "../context/AuthContext";
import { agentService } from "../services/agentService";
import { campaignService } from "../services/campaignService";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatApiError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback;
}

function formatDateTime(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return { headers: [], rows: [] };

  const headers = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, ""));
  const rows = lines.slice(1).map((line) => {
    // Simple CSV split — handles quoted fields with commas
    const values = [];
    let current = "";
    let inQuotes = false;
    for (const ch of line) {
      if (ch === '"') { inQuotes = !inQuotes; continue; }
      if (ch === "," && !inQuotes) { values.push(current.trim()); current = ""; continue; }
      current += ch;
    }
    values.push(current.trim());

    return headers.reduce((obj, header, i) => {
      obj[header] = values[i] ?? "";
      return obj;
    }, {});
  });

  return { headers, rows };
}

function StatusBadge({ status }) {
  const colorMap = {
    pending:   "doctor-session-badge-pending",
    running:   "doctor-session-badge-voice",
    calling:   "doctor-session-badge-voice",
    completed: "doctor-session-badge-active",
    failed:    "doctor-session-badge-inactive",
    no_answer: "doctor-session-badge-inactive",
    cancelled: "doctor-session-badge-inactive",
  };
  const cls = colorMap[status] || "doctor-session-badge-pending";
  return <span className={`doctor-session-badge ${cls}`}>{status}</span>;
}

function downloadSampleCSV() {
  const rows = [
    ["name", "phone", "appointment_date", "reason"],
    ["Rahul Sharma",   "+919876543210", "2025-06-01", "Follow-up checkup"],
    ["Priya Singh",    "+919123456789", "2025-06-02", "Lab results review"],
    ["Amit Kumar",     "+918765432109", "2025-06-03", "Prescription renewal"],
    ["Neha Patel",     "+917654321098", "2025-06-04", "Post-surgery review"],
    ["Vikram Mehta",   "+916543210987", "2025-06-05", "Annual health check"],
  ];
  const csv = rows.map((row) => row.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sample_contacts.csv";
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function BulkCallsPage() {
  const { isAdmin } = useAuth();
  const navigate = useNavigate();

  // ── Agent picker ──────────────────────────────────────────────────────────
  const [agents, setAgents] = useState([]);
  const [agentsLoading, setAgentsLoading] = useState(true);

  // ── Create form state ─────────────────────────────────────────────────────
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [campaignName, setCampaignName] = useState("");
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [csvRows, setCsvRows] = useState([]);
  const [csvError, setCsvError] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const fileInputRef = useRef(null);

  // ── Campaign list ─────────────────────────────────────────────────────────
  const [campaigns, setCampaigns] = useState([]);
  const [campaignsLoading, setCampaignsLoading] = useState(true);
  const [expandedCampaignId, setExpandedCampaignId] = useState(null);
  const [expandedCampaign, setExpandedCampaign] = useState(null);
  const [expandedLoading, setExpandedLoading] = useState(false);
  const [cancellingId, setCancellingId] = useState(null);
  const pollTimerRef = useRef(null);

  // ── Load agents ───────────────────────────────────────────────────────────
  useEffect(() => {
    agentService
      .listAgents({ page: 1, page_size: 100 })
      .then((res) => setAgents(res.data || []))
      .catch(() => setAgents([]))
      .finally(() => setAgentsLoading(false));
  }, []);

  // ── Load campaign list ────────────────────────────────────────────────────
  const loadCampaigns = async () => {
    setCampaignsLoading(true);
    try {
      const res = await campaignService.listCampaigns();
      setCampaigns(res.data || []);
    } catch {
      setCampaigns([]);
    } finally {
      setCampaignsLoading(false);
    }
  };

  useEffect(() => {
    void loadCampaigns();
  }, []);

  // ── Poll expanded campaign while it is running ────────────────────────────
  useEffect(() => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    if (!expandedCampaignId) return;

    const poll = async () => {
      try {
        const data = await campaignService.getCampaign(expandedCampaignId);
        setExpandedCampaign(data);
        // Refresh list counts too
        setCampaigns((prev) =>
          prev.map((c) =>
            c.campaign_id === expandedCampaignId
              ? { ...c, status: data.status, completed_contacts: data.completed_contacts, failed_contacts: data.failed_contacts }
              : c
          )
        );
        if (!["running", "pending"].includes(data.status)) {
          clearInterval(pollTimerRef.current);
        }
      } catch {
        clearInterval(pollTimerRef.current);
      }
    };

    void poll();
    pollTimerRef.current = setInterval(poll, 10000);
    return () => clearInterval(pollTimerRef.current);
  }, [expandedCampaignId]);

  // ── CSV upload ────────────────────────────────────────────────────────────
  const handleFileChange = (e) => {
    setCsvError("");
    setCsvHeaders([]);
    setCsvRows([]);
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const { headers, rows } = parseCSV(ev.target.result);
        if (!headers.length) { setCsvError("Could not parse CSV headers."); return; }
        const hasPhone = headers.some((h) => ["phone", "phone_number"].includes(h.toLowerCase()));
        if (!hasPhone) { setCsvError("CSV must have a 'phone' or 'phone_number' column."); return; }
        if (!rows.length) { setCsvError("CSV has no data rows."); return; }
        // Normalize header names to lowercase
        const normHeaders = headers.map((h) => h.toLowerCase());
        const normRows = rows.map((row) => {
          const n = {};
          headers.forEach((h, i) => { n[normHeaders[i]] = row[h]; });
          return n;
        });
        setCsvHeaders(normHeaders);
        setCsvRows(normRows);
      } catch {
        setCsvError("Failed to read CSV file. Please check the format.");
      }
    };
    reader.readAsText(file);
  };

  // ── Create campaign ───────────────────────────────────────────────────────
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!selectedAgentId) { setCreateError("Please select an agent."); return; }
    if (!campaignName.trim()) { setCreateError("Please enter a campaign name."); return; }
    if (!csvRows.length) { setCreateError("Please upload a CSV file with at least one contact."); return; }

    setCreating(true);
    setCreateError("");
    try {
      const agent = agents.find((a) => a.id === selectedAgentId);
      await campaignService.createCampaign(
        selectedAgentId,
        agent?.agent_name || null,
        campaignName.trim(),
        csvRows,
      );
      // Reset form
      setSelectedAgentId("");
      setCampaignName("");
      setCsvHeaders([]);
      setCsvRows([]);
      setCsvError("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      await loadCampaigns();
    } catch (err) {
      setCreateError(formatApiError(err, "Failed to start the campaign."));
    } finally {
      setCreating(false);
    }
  };

  // ── Expand campaign ───────────────────────────────────────────────────────
  const toggleExpand = async (campaignId) => {
    if (expandedCampaignId === campaignId) {
      setExpandedCampaignId(null);
      setExpandedCampaign(null);
      return;
    }
    setExpandedCampaignId(campaignId);
    setExpandedLoading(true);
    try {
      const data = await campaignService.getCampaign(campaignId);
      setExpandedCampaign(data);
    } catch {
      setExpandedCampaign(null);
    } finally {
      setExpandedLoading(false);
    }
  };

  // ── Cancel campaign ───────────────────────────────────────────────────────
  const handleCancel = async (campaignId) => {
    setCancellingId(campaignId);
    try {
      await campaignService.cancelCampaign(campaignId);
      await loadCampaigns();
      if (expandedCampaignId === campaignId) {
        const data = await campaignService.getCampaign(campaignId);
        setExpandedCampaign(data);
      }
    } catch (err) {
      alert(formatApiError(err, "Failed to cancel campaign."));
    } finally {
      setCancellingId(null);
    }
  };

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  return (
    <DoctorWorkspaceLayout
      agents={agents}
      headerTitle="Bulk Outbound Calls"
      headerSubtitle="Upload a CSV of contacts and have an AI agent call each one sequentially."
      sidebarContent={<DoctorSidebarTabs activeTab="bulk-calls" isAdmin={isAdmin} />}
    >
      <div className="doctor-content-shell">
        <section className="doctor-chat-stream">

          {/* ── Create Campaign Form ─────────────────────────────────────── */}
          <section className="doctor-history-panel">
            <div className="doctor-history-header">
              <h2>New Campaign</h2>
              <span>Upload a CSV to start</span>
            </div>

            <form className="doctor-admin-form" onSubmit={handleCreate}>
              {/* Agent selector */}
              <label className="doctor-small-label" htmlFor="bulk-agent-select">
                Select Agent
              </label>
              <select
                id="bulk-agent-select"
                className="doctor-composer-input"
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                disabled={agentsLoading || creating}
              >
                <option value="">
                  {agentsLoading ? "Loading agents..." : "— Choose an agent —"}
                </option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.agent_name}
                  </option>
                ))}
              </select>

              {/* Campaign name */}
              <label className="doctor-small-label" htmlFor="bulk-campaign-name">
                Campaign Name
              </label>
              <input
                id="bulk-campaign-name"
                className="doctor-composer-input"
                type="text"
                placeholder="e.g. Appointment reminders — May 2025"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                disabled={creating}
              />

              {/* CSV upload */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem", marginBottom: "0.25rem" }}>
                <label className="doctor-small-label" htmlFor="bulk-csv-upload" style={{ margin: 0 }}>
                  Upload CSV <span style={{ fontWeight: 400 }}>(must have a <code>phone</code> column)</span>
                </label>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={downloadSampleCSV}
                  style={{ fontSize: "0.75rem", padding: "0.2rem 0.6rem", whiteSpace: "nowrap" }}
                >
                  ⬇ Download Sample CSV
                </button>
              </div>
              <input
                id="bulk-csv-upload"
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                className="doctor-composer-input"
                onChange={handleFileChange}
                disabled={creating}
              />
              {csvError ? <p className="error-text">{csvError}</p> : null}

              {/* CSV preview */}
              {csvRows.length > 0 ? (
                <div className="doctor-history-table-shell" style={{ marginTop: "0.75rem" }}>
                  <p className="doctor-small-label">
                    Preview — {csvRows.length} contact{csvRows.length !== 1 ? "s" : ""} detected
                  </p>
                  <div className="table-wrap">
                    <table className="doctor-history-table">
                      <thead>
                        <tr>
                          {csvHeaders.map((h) => (
                            <th key={h}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {csvRows.slice(0, 5).map((row, i) => (
                          <tr key={i}>
                            {csvHeaders.map((h) => (
                              <td key={h}>{row[h] ?? ""}</td>
                            ))}
                          </tr>
                        ))}
                        {csvRows.length > 5 ? (
                          <tr>
                            <td colSpan={csvHeaders.length} style={{ textAlign: "center", fontStyle: "italic" }}>
                              … and {csvRows.length - 5} more
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : null}

              {createError ? <p className="error-text">{createError}</p> : null}

              <button
                className="primary-button"
                type="submit"
                disabled={creating || !csvRows.length || !selectedAgentId || !campaignName.trim()}
              >
                {creating ? "Starting campaign…" : `Start Campaign (${csvRows.length} contacts)`}
              </button>
            </form>
          </section>

          {/* ── Campaign List ────────────────────────────────────────────── */}
          <section className="doctor-history-panel">
            <div className="doctor-history-header">
              <h2>Campaigns</h2>
              <button
                className="ghost-button"
                type="button"
                onClick={() => void loadCampaigns()}
                disabled={campaignsLoading}
              >
                {campaignsLoading ? "Refreshing…" : "Refresh"}
              </button>
            </div>

            {campaigns.length === 0 && !campaignsLoading ? (
              <p className="doctor-empty-copy">No campaigns yet. Create one above to get started.</p>
            ) : null}

            <div className="doctor-history-list">
              {campaigns.map((c) => (
                <article key={c.campaign_id} className="doctor-history-item">
                  {/* Summary row */}
                  <div className="doctor-history-row">
                    <strong>{c.campaign_name}</strong>
                    <StatusBadge status={c.status} />
                  </div>
                  <p style={{ margin: "0.25rem 0 0.5rem" }}>
                    Agent: <strong>{c.agent_name || c.agent_id}</strong> &nbsp;·&nbsp;
                    {c.total_contacts} contacts &nbsp;·&nbsp;
                    ✅ {c.completed_contacts} done &nbsp;·&nbsp;
                    ❌ {c.failed_contacts} failed
                  </p>
                  <div className="doctor-history-row doctor-history-meta">
                    <span>Created {formatDateTime(c.created_at)}</span>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      {["pending", "running"].includes(c.status) ? (
                        <button
                          className="doctor-mini-pill"
                          type="button"
                          disabled={cancellingId === c.campaign_id}
                          onClick={() => void handleCancel(c.campaign_id)}
                        >
                          {cancellingId === c.campaign_id ? "Cancelling…" : "Cancel"}
                        </button>
                      ) : null}
                      <button
                        className="doctor-inline-link"
                        type="button"
                        onClick={() => void toggleExpand(c.campaign_id)}
                      >
                        {expandedCampaignId === c.campaign_id ? "Hide details" : "View details"}
                      </button>
                    </div>
                  </div>

                  {/* Expanded contact table */}
                  {expandedCampaignId === c.campaign_id ? (
                    <div style={{ marginTop: "0.75rem" }}>
                      {expandedLoading ? (
                        <p className="doctor-empty-copy">Loading contacts…</p>
                      ) : expandedCampaign?.contacts?.length ? (
                        <div className="doctor-history-table-shell">
                          <div className="table-wrap">
                            <table className="doctor-history-table">
                              <thead>
                                <tr>
                                  <th>#</th>
                                  <th>Name</th>
                                  <th>Phone</th>
                                  <th>Status</th>
                                  <th>Started</th>
                                  <th>Ended</th>
                                  <th>Conversation ID</th>
                                </tr>
                              </thead>
                              <tbody>
                                {expandedCampaign.contacts.map((contact, idx) => (
                                  <tr key={contact.contact_id}>
                                    <td>{idx + 1}</td>
                                    <td>{contact.contact_name || "—"}</td>
                                    <td>{contact.phone_number}</td>
                                    <td><StatusBadge status={contact.status} /></td>
                                    <td>{formatDateTime(contact.call_started_at)}</td>
                                    <td>{formatDateTime(contact.call_ended_at)}</td>
                                    <td>
                                      {contact.conversation_id ? (
                                        <code className="doctor-history-code">{contact.conversation_id}</code>
                                      ) : "—"}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ) : (
                        <p className="doctor-empty-copy">No contacts found for this campaign.</p>
                      )}
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          </section>
        </section>
      </div>
    </DoctorWorkspaceLayout>
  );
}
