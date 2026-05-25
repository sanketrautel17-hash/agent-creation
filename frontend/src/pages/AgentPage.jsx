import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import AgentVoicePanel from "../components/AgentVoicePanel";
import DoctorSidebarTabs from "../components/DoctorSidebarTabs";
import DoctorWorkspaceLayout from "../components/DoctorWorkspaceLayout";
import { getAgentMeta } from "../constants/doctorWorkspace";
import { useAuth } from "../context/AuthContext";
import { adminService } from "../services/adminService";
import { agentService } from "../services/agentService";

const EIGI_MANAGED_CONTEXT_VARIABLES = new Set([
  "sender_id",
  "sender_channel",
  "sender_name",
  "previous_conversation_context",
]);

function formatApiError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback;
}

function formatTime(value = new Date()) {
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function buildInitialVariableValues(variables) {
  return variables.reduce((accumulator, item) => {
    accumulator[item.variable_name] = "";
    return accumulator;
  }, {});
}

function isManagedEigiAgent(agentPayload) {
  return Boolean(agentPayload?.additional_params?.is_eigi_agent);
}

function filterRuntimeDynamicVariables(agentPayload, variables) {
  if (!Array.isArray(variables)) {
    return [];
  }

  if (!isManagedEigiAgent(agentPayload)) {
    return variables;
  }

  return variables.filter((item) => !EIGI_MANAGED_CONTEXT_VARIABLES.has(item?.variable_name));
}

function normalizeConversationMetadata(values) {
  return Object.entries(values).reduce((accumulator, [key, value]) => {
    if (value === null || value === undefined) {
      return accumulator;
    }

    const normalizedValue = typeof value === "string" ? value.trim() : value;
    if (normalizedValue === "") {
      return accumulator;
    }

    accumulator[key] = normalizedValue;
    return accumulator;
  }, {});
}

function getInputType(fieldType) {
  switch (String(fieldType || "").toUpperCase()) {
    case "EMAIL":
      return "email";
    case "NUMBER":
      return "number";
    case "PHONE":
      return "tel";
    default:
      return "text";
  }
}

function getPromptAccessToken(agentPayload) {
  if (!agentPayload || typeof agentPayload !== "object") {
    return "";
  }

  const directToken = agentPayload.prompt_access_token || agentPayload.promptAccessToken;
  if (typeof directToken === "string" && directToken.trim()) {
    return directToken.trim();
  }

  const widgetToken = agentPayload.widget_config?.prompt_access_token || agentPayload.widget_config?.promptAccessToken;
  if (typeof widgetToken === "string" && widgetToken.trim()) {
    return widgetToken.trim();
  }

  const promptToken =
    agentPayload.prompt?.prompt_access_token ||
    agentPayload.prompt?.promptAccessToken ||
    agentPayload.prompt?.access_token ||
    agentPayload.prompt?.accessToken;
  if (typeof promptToken === "string" && promptToken.trim()) {
    return promptToken.trim();
  }

  return "";
}

export default function AgentPage() {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAdmin } = useAuth();
  const [agents, setAgents] = useState([]);
  const [agent, setAgent] = useState(null);
  const [dynamicVariables, setDynamicVariables] = useState([]);
  const [dynamicValues, setDynamicValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatDraft, setChatDraft] = useState("");
  const [chatError, setChatError] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [sessionLoading, setSessionLoading] = useState(false);
  const [messageSending, setMessageSending] = useState(false);
  const [assistantTyping, setAssistantTyping] = useState(false);
  const [showSetup, setShowSetup] = useState(false);
  const [showVoiceTools, setShowVoiceTools] = useState(false);
  const [callStartSignal, setCallStartSignal] = useState(0);
  const messageListBottomRef = useRef(null);
  const historyId = searchParams.get("historyId") || "";

  // Auto-scroll to the bottom of the chat list whenever messages change
  useEffect(() => {
    messageListBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  useEffect(() => {
    let cancelled = false;

    setAgent(null);
    setDynamicVariables([]);
    setDynamicValues({});
    setChatMessages([]);
    setChatDraft("");
    setChatError("");
    setSessionId("");

    const loadAgentWorkspace = async () => {
      setLoading(true);
      setErrorMessage("");
      try {
        const [catalogResponse, agentResponse, variableResponse] = await Promise.all([
          agentService.listAgents({ page: 1, page_size: 50 }),
          agentService.getAgent(agentId),
          agentService.getDynamicVariables(agentId),
        ]);

        if (cancelled) {
          return;
        }

        const runtimeVariables = filterRuntimeDynamicVariables(agentResponse, variableResponse.dynamic_variables || []);
        const baseDynamicValues = buildInitialVariableValues(runtimeVariables);
        setAgents(catalogResponse.data || []);
        setAgent(agentResponse);
        setDynamicVariables(runtimeVariables);
        setDynamicValues(baseDynamicValues);

        if (historyId && isAdmin) {
          try {
            const historyConversation = await adminService.getUserHistoryConversation(historyId);
            if (cancelled) {
              return;
            }

            const transcriptMessages = Array.isArray(historyConversation.transcript)
              ? historyConversation.transcript
                  .filter((entry) => entry?.role && entry?.content)
                  .map((entry, index) => ({
                    id: `history-${historyConversation.id}-${index}`,
                    role: entry.role === "assistant" ? "assistant" : "user",
                    content: entry.content,
                    timestamp: entry.timestamp ? formatTime(entry.timestamp) : "",
                  }))
              : [];

            setDynamicValues({
              ...baseDynamicValues,
              ...(historyConversation.metadata || {}),
            });
            setSessionId(historyConversation.session_id || "");
            setChatMessages(transcriptMessages);
            setShowSetup(false);
          } catch (historyError) {
            if (!cancelled) {
              setChatError(formatApiError(historyError, "Unable to load the saved conversation history."));
            }
          }
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        setAgents([]);
        setAgent(null);
        setDynamicVariables([]);
        setDynamicValues({});
        setErrorMessage(formatApiError(error, "Unable to load the selected Eigi agent."));
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadAgentWorkspace();

    return () => {
      cancelled = true;
    };
  }, [agentId, historyId, isAdmin]);

  const activeAgent = agent || agents.find((item) => item.id === agentId) || null;
  const activeMeta = useMemo(() => getAgentMeta(agentId, agents), [agentId, agents]);
  const conversationMetadata = useMemo(() => normalizeConversationMetadata(dynamicValues), [dynamicValues]);
  const linkedSessionId = searchParams.get("sessionId") || searchParams.get("voiceSessionId") || "";
  const linkedConversationId = searchParams.get("conversationId") || "";
  const requiredVariables = useMemo(
    () => dynamicVariables.filter((item) => item.required),
    [dynamicVariables],
  );
  const missingRequiredVariables = useMemo(
    () =>
      requiredVariables.filter((item) => {
        const value = dynamicValues[item.variable_name];
        return typeof value === "string" ? !value.trim() : !value;
      }),
    [dynamicValues, requiredVariables],
  );
  const filledVariableCount = useMemo(
    () =>
      dynamicVariables.filter((item) => {
        const value = dynamicValues[item.variable_name];
        return typeof value === "string" ? Boolean(value.trim()) : Boolean(value);
      }).length,
    [dynamicValues, dynamicVariables],
  );
  const headerTitle = activeAgent?.agent_name || activeMeta.title;
  const headerSubtitle =
    activeAgent?.agent_description || "Start a conversation once your runtime fields are ready.";
  const promptAccessToken = useMemo(() => getPromptAccessToken(activeAgent), [activeAgent]);
  const voiceEnabled = useMemo(
    () => Boolean(promptAccessToken || activeAgent?.voice_enabled),
    [promptAccessToken, activeAgent],
  );
  const voiceDisabledReason =
    activeAgent?.voice_disabled_reason || "Voice calls are not enabled for this agent. Use chat instead.";
  const setupRequired = Boolean(missingRequiredVariables.length);
  const statusLabel = loading
    ? "Loading"
    : setupRequired
      ? "Setup required"
      : sessionId
        ? "Connected"
        : "Ready";
  const showSetupPanel = dynamicVariables.length > 0 && (!sessionId || showSetup);

  const handleDynamicValueChange = (variableName, value) => {
    setDynamicValues((currentValues) => ({
      ...currentValues,
      [variableName]: value,
    }));
  };

  const initializeChatSession = async () => {
    if (sessionId) {
      return sessionId;
    }

    if (missingRequiredVariables.length) {
      setChatError(`Fill required fields first: ${missingRequiredVariables.map((item) => item.variable_name).join(", ")}`);
      return null;
    }

    setSessionLoading(true);
    setChatError("");
    try {
      const response = await agentService.initializeChat(agentId, conversationMetadata);
      setSessionId(response.session_id);
      if (response.first_message) {
        setChatMessages((currentMessages) => {
          if (currentMessages.length) {
            return currentMessages;
          }

          return [
            {
              id: `assistant-${response.session_id}-intro`,
              role: "assistant",
              content: response.first_message,
              timestamp: formatTime(),
            },
          ];
        });
      }
      setShowSetup(false);
      return response.session_id;
    } catch (error) {
      setChatError(formatApiError(error, "Unable to start the chat session."));
      return null;
    } finally {
      setSessionLoading(false);
    }
  };

  const sendMessageToAgent = async (rawMessage) => {
    const trimmedMessage = rawMessage.trim();
    if (!trimmedMessage || messageSending) {
      return "";
    }

    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = await initializeChatSession();
      if (!currentSessionId) {
        throw new Error("Unable to start the chat session.");
      }
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmedMessage,
      timestamp: formatTime(),
    };

    setChatError("");
    setChatMessages((currentMessages) => [...currentMessages, userMessage]);
    setMessageSending(true);
    setAssistantTyping(true);

    try {
      const response = await agentService.sendChatMessage(agentId, {
        message: trimmedMessage,
        session_id: currentSessionId,
        conversation_metadata: conversationMetadata,
      });

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      const assistantMessage = response.response_message || "No response received from the agent.";
      setChatMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: assistantMessage,
          timestamp: formatTime(),
        },
      ]);
      return assistantMessage;
    } catch (error) {
      const formattedError = formatApiError(error, "Unable to send the message to the agent.");
      setChatError(formattedError);
      throw new Error(formattedError);
    } finally {
      setMessageSending(false);
      setAssistantTyping(false);
    }
  };

  const handleSendMessage = async (event) => {
    event.preventDefault();

    const trimmedMessage = chatDraft.trim();
    if (!trimmedMessage || messageSending) {
      return;
    }

    setChatDraft("");
    try {
      await sendMessageToAgent(trimmedMessage);
    } catch {
      setChatDraft(trimmedMessage);
    }
  };

  const handleUserTranscript = (text) => {
    setChatMessages((currentMessages) => [
      ...currentMessages,
      {
        id: `user-voice-${Date.now()}-${Math.random()}`,
        role: "user",
        content: text,
        timestamp: formatTime(),
      },
    ]);
  };

  const handleBotTranscript = (text) => {
    setChatMessages((currentMessages) => {
      const lastMessage = currentMessages[currentMessages.length - 1];
      if (lastMessage?.role === "assistant" && lastMessage?.content === text) {
        return currentMessages;
      }
      return [
        ...currentMessages,
        {
          id: `assistant-voice-${Date.now()}-${Math.random()}`,
          role: "assistant",
          content: text,
          timestamp: formatTime(),
        },
      ];
    });
  };

  const handleOpenCall = async () => {
    if (setupRequired || loading || errorMessage) {
      setShowSetup(true);
      return;
    }

    if (!voiceEnabled) {
      setChatError(voiceDisabledReason);
      setShowVoiceTools(false);
      return;
    }

    if (!sessionId) {
      const nextSessionId = await initializeChatSession();
      if (!nextSessionId) {
        return;
      }
    }

    setShowVoiceTools(true);
    setCallStartSignal((current) => current + 1);
  };

  return (
    <DoctorWorkspaceLayout
      activeAgentId={agentId}
      agents={agents}
      headerTitle={headerTitle}
      headerSubtitle={headerSubtitle}
      sidebarContent={<DoctorSidebarTabs activeTab="agents" isAdmin={isAdmin} />}
    >
      <div className="doctor-content-shell doctor-agent-page-shell">
        <section className="doctor-chat-stream doctor-agent-simple-stream">
          {loading ? (
            <section className="doctor-history-panel">
              <p className="doctor-empty-copy">Loading the selected Eigi agent...</p>
            </section>
          ) : null}

          {!loading && errorMessage ? (
            <section className="doctor-history-panel">
              <article className="doctor-detail-card">
                <div className="doctor-history-header">
                  <h2>Agent lookup failed</h2>
                  <span>Unavailable</span>
                </div>
                <p className="error-text">{errorMessage}</p>
                <div className="doctor-composer-utility-row">
                  <button className="doctor-inline-link" type="button" onClick={() => navigate("/dashboard?tab=agents")}>
                    Return to agents
                  </button>
                </div>
              </article>
            </section>
          ) : null}

          {!loading && activeAgent ? (
            <section className="doctor-agent-simple-shell">
              <header className="doctor-agent-simple-header">
                <div className="doctor-agent-simple-heading">
                  <span className="doctor-agent-simple-avatar">{headerTitle.slice(0, 1).toUpperCase()}</span>
                  <h2>{headerTitle}</h2>
                  <p>{statusLabel}</p>
                </div>
                <div className="doctor-agent-simple-actions">
                  <button
                    className="doctor-agent-header-button"
                    type="button"
                    aria-label="Start call"
                    onClick={() => void handleOpenCall()}
                    disabled={!voiceEnabled}
                    title={!voiceEnabled ? voiceDisabledReason : "Start call"}
                  >
                    Call
                  </button>
                </div>
              </header>

              {historyId || linkedSessionId || linkedConversationId ? (
                <div className="doctor-agent-inline-meta">
                  <span>Opened from history</span>
                  {historyId ? <span>History: {historyId}</span> : null}
                  {linkedSessionId ? <span>Session: {linkedSessionId}</span> : null}
                  {linkedConversationId ? <span>Conversation: {linkedConversationId}</span> : null}
                </div>
              ) : null}

              {showSetupPanel ? (
                <section className="doctor-agent-setup-card">
                  <div className="doctor-history-header">
                    <h3>Session Setup</h3>
                    <span>
                      {filledVariableCount}/{dynamicVariables.length} fields
                    </span>
                  </div>

                  {dynamicVariables.length ? (
                    <div className="doctor-agent-setup-grid">
                      {dynamicVariables.map((item) => (
                        <label key={item.variable_name} className="doctor-agent-setup-field">
                          <span>
                            {item.variable_name}
                            {item.required ? " *" : ""}
                          </span>
                          <input
                            className="doctor-composer-input"
                            type={getInputType(item.field_type)}
                            value={dynamicValues[item.variable_name] || ""}
                            onChange={(event) => handleDynamicValueChange(item.variable_name, event.target.value)}
                            placeholder={item.description || `Enter ${item.variable_name}`}
                          />
                        </label>
                      ))}
                    </div>
                  ) : (
                    <p className="doctor-empty-copy">No setup fields are required for this agent.</p>
                  )}

                  <div className="doctor-agent-setup-footer">
                    <span className="doctor-composer-footnote">
                      {missingRequiredVariables.length
                        ? `Missing required fields: ${missingRequiredVariables.map((item) => item.variable_name).join(", ")}`
                        : sessionId
                          ? "Chat session is active."
                          : "Everything is ready to start."}
                    </span>
                    <button
                      className="primary-button"
                      type="button"
                      onClick={() => void initializeChatSession()}
                      disabled={sessionLoading || messageSending || Boolean(sessionId) || Boolean(missingRequiredVariables.length)}
                    >
                      {sessionLoading ? "Starting..." : sessionId ? "Connected" : "Start chat"}
                    </button>
                  </div>
                </section>
              ) : null}

              <section className="doctor-agent-message-surface">
                {showVoiceTools ? (
                  <section className="doctor-agent-voice-shell doctor-agent-voice-shell-inline">
                    <AgentVoicePanel
                      activeAgentName={activeAgent.agent_name}
                      agentId={agentId}
                      autoStartSignal={callStartSignal}
                      blockedReason={
                        missingRequiredVariables.length
                          ? `Missing required fields: ${missingRequiredVariables.map((item) => item.variable_name).join(", ")}`
                          : ""
                      }
                      canStart={!missingRequiredVariables.length}
                      compact
                      conversationMetadata={conversationMetadata}
                      disabled={loading || Boolean(errorMessage) || messageSending}
                      chatSessionId={sessionId}
                      onCallEnded={() => setShowVoiceTools(false)}
                      onUserTranscript={handleUserTranscript}
                      onBotTranscript={handleBotTranscript}
                      promptAccessToken={promptAccessToken}
                    />
                  </section>
                ) : null}

                {chatError ? <p className="error-text">{chatError}</p> : null}

                <div className="doctor-agent-message-list">
                  {chatMessages.length ? (
                    <>
                      {chatMessages.map((message) => (
                        <article
                          key={message.id}
                          className={`doctor-agent-bubble ${
                            message.role === "user" ? "doctor-agent-bubble-user" : "doctor-agent-bubble-assistant"
                          }`}
                        >
                          <p>{message.content}</p>
                          <time>{message.timestamp}</time>
                        </article>
                      ))}
                      {assistantTyping ? (
                        <article className="doctor-agent-bubble doctor-agent-bubble-assistant">
                          <p>Typing...</p>
                          <time>{formatTime()}</time>
                        </article>
                      ) : null}
                      <div ref={messageListBottomRef} />
                    </>
                  ) : (
                    <article className="doctor-agent-bubble doctor-agent-bubble-assistant">
                      <p>
                        Hello! I&apos;m your healthcare assistant. How can I help you today?
                      </p>
                    </article>
                  )}
                </div>

                <form className="doctor-agent-composer" onSubmit={handleSendMessage}>
                  <div className="doctor-agent-composer-actions">
                    <textarea
                      className="doctor-agent-composer-input"
                      value={chatDraft}
                      onChange={(event) => setChatDraft(event.target.value)}
                      placeholder="Send a message..."
                      disabled={loading || Boolean(errorMessage) || messageSending}
                    />
                    <button
                      className="doctor-agent-send-button"
                      type="submit"
                      disabled={loading || Boolean(errorMessage) || messageSending || !chatDraft.trim()}
                    >
                      {messageSending ? "..." : "Send"}
                    </button>
                  </div>
                </form>
              </section>
            </section>
          ) : null}
        </section>
      </div>
    </DoctorWorkspaceLayout>
  );
}
