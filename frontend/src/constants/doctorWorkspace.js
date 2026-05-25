export const CONTEXT_ITEMS = [
  {
    id: "c-001",
    label: "Focus",
    value: "Review required runtime fields, capture the dynamic variables, and start the agent conversation cleanly.",
  },
  {
    id: "c-002",
    label: "Care mode",
    value: "Backend-mediated Eigi integration with authenticated catalog access.",
  },
  {
    id: "c-003",
    label: "Guardrail",
    value: "Use dynamic variables to collect the required runtime values before starting a live interaction.",
  },
];

function normalizeStatus(agentType) {
  if (!agentType) {
    return "idle";
  }
  return String(agentType).toUpperCase() === "INBOUND" ? "active" : "idle";
}

export function toAgentCard(agent) {
  return {
    id: agent?.id || "",
    title: agent?.agent_name || "Clinical Assistant",
    specialty: agent?.agent_category || "General Care",
    description: agent?.agent_description || "Open the selected Eigi agent and continue the conversation.",
    status: normalizeStatus(agent?.agent_type),
    type: agent?.agent_type || "UNKNOWN",
  };
}

export function getAgentMeta(agentId, agents = []) {
  const selectedAgent = Array.isArray(agents) ? agents.find((agent) => agent.id === agentId) : null;

  if (!selectedAgent) {
    return {
      id: agentId,
      title: "Clinical Assistant",
      specialty: "General Care",
      description: "Open the selected Eigi agent and continue the conversation.",
      status: "idle",
      type: "UNKNOWN",
    };
  }

  return toAgentCard(selectedAgent);
}

export function getAgentVisualTone(agent) {
  const searchableText = `${agent?.agent_name || agent?.title || ""} ${agent?.agent_category || agent?.specialty || ""}`.toLowerCase();
  if (searchableText.includes("prescription") || searchableText.includes("pharmacy") || searchableText.includes("medication")) {
    return "prescription";
  }
  if (searchableText.includes("follow") || searchableText.includes("cardio") || searchableText.includes("heart")) {
    return "followup";
  }
  return "default";
}
