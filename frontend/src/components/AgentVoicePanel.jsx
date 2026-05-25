import { useEffect, useRef, useState } from "react";

import { PipecatClient, RTVIEvent } from "@pipecat-ai/client-js";
import { PipecatClientAudio, PipecatClientProvider } from "@pipecat-ai/client-react";
import { DailyTransport } from "@pipecat-ai/daily-transport";

import { agentService } from "../services/agentService";

function createVoiceClient() {
  return new PipecatClient({
    transport: new DailyTransport({
      bufferLocalAudioUntilBotReady: true,
    }),
    enableMic: true,
    enableCam: false,
    disconnectOnBotDisconnect: true,
  });
}

function getCallStatus(callState, voiceError, muted) {
  if (voiceError) {
    return voiceError;
  }
  if (muted && callState === "active") {
    return "Call muted";
  }
  if (callState === "connecting") {
    return "Connecting call...";
  }
  if (callState === "connected") {
    return "Waiting for agent...";
  }
  if (callState === "active") {
    return "Call active";
  }
  if (callState === "ending") {
    return "Ending call...";
  }
  return "Call ended";
}




export default function AgentVoicePanel({
  activeAgentName,
  agentId,
  autoStartSignal = 0,
  blockedReason,
  canStart,
  compact = false,
  conversationMetadata = {},
  disabled,
  chatSessionId,
  onCallEnded,
  onUserTranscript,
  onBotTranscript,
  promptAccessToken = "",
}) {
  const [client] = useState(() => createVoiceClient());
  const [callState, setCallState] = useState("idle");
  const [muted, setMuted] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const endingNotifiedRef = useRef(false);
  const connectingRef = useRef(false);
  const lastAutoStartSignalRef = useRef(0);
  const connectionTimeoutRef = useRef(null);
  const disconnectPromiseRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (connectionTimeoutRef.current) {
        window.clearTimeout(connectionTimeoutRef.current);
      }
    };
  }, []);

  const safeDisconnect = async () => {
    if (disconnectPromiseRef.current) {
      return disconnectPromiseRef.current;
    }

    const currentState = client.state;
    if (currentState === "disconnected" || currentState === "disconnecting") {
      return Promise.resolve();
    }

    disconnectPromiseRef.current = client
      .disconnect()
      .catch(() => {
        // Ignore teardown errors from the transport.
      })
      .finally(() => {
        disconnectPromiseRef.current = null;
      });

    return disconnectPromiseRef.current;
  };

  useEffect(() => {
    const clearConnectionTimeout = () => {
      if (connectionTimeoutRef.current) {
        window.clearTimeout(connectionTimeoutRef.current);
        connectionTimeoutRef.current = null;
      }
    };

    const notifyEnded = () => {
      if (endingNotifiedRef.current) {
        return;
      }
      endingNotifiedRef.current = true;
      onCallEnded?.();
    };

    const handleConnected = () => {
      if (!mountedRef.current) {
        return;
      }
      disconnectPromiseRef.current = null;
      setVoiceError("");
      setCallState("connected");
    };

    const handleBotConnected = () => {
      if (!mountedRef.current) {
        return;
      }
      clearConnectionTimeout();
      connectingRef.current = false;
      setVoiceError("");
      setCallState("active");
    };

    const handleBotReady = () => {
      if (!mountedRef.current) {
        return;
      }
      clearConnectionTimeout();
      connectingRef.current = false;
      setVoiceError("");
      setCallState("active");
    };

    const handleDisconnected = () => {
      if (!mountedRef.current) {
        return;
      }
      clearConnectionTimeout();
      disconnectPromiseRef.current = null;
      connectingRef.current = false;
      setMuted(false);
      setCallState("idle");
      notifyEnded();
    };

    const handleBotDisconnected = () => {
      if (!mountedRef.current) {
        return;
      }
      clearConnectionTimeout();
      disconnectPromiseRef.current = null;
      connectingRef.current = false;
      setMuted(false);
      setCallState("idle");
      notifyEnded();
    };

    // Dedup ref: avoid adding the same bot text multiple times when
    // BotTranscript, BotTtsText, and BotOutput all fire for the same utterance.
    const lastBotTextRef = { current: "" };

    const handleUserTranscript = (data) => {
      if (!mountedRef.current) {
        return;
      }
      const text = typeof data === "string" ? data : data?.text || data?.transcript || "";
      const isFinal = typeof data === "object" ? data?.final ?? true : true;
      console.log("[Voice] UserTranscript", { text, isFinal, data });
      if (text && isFinal) {
        onUserTranscript?.(text);
      }
    };

    const handleBotTranscript = (data) => {
      if (!mountedRef.current) {
        return;
      }
      const text = typeof data === "string" ? data : data?.text || data?.transcript || "";
      console.log("[Voice] BotTranscript/BotTtsText", { text, data });
      if (text && text !== lastBotTextRef.current) {
        lastBotTextRef.current = text;
        onBotTranscript?.(text);
      }
    };

    const handleBotOutput = (data) => {
      if (!mountedRef.current) {
        return;
      }
      // BotOutput fires for all bot text — only use it if spoken (i.e. TTS output)
      const text = typeof data === "string" ? data : data?.text || "";
      const isSpoken = typeof data === "object" ? (data?.spoken ?? true) : true;
      console.log("[Voice] BotOutput", { text, isSpoken, data });
      if (text && isSpoken && text !== lastBotTextRef.current) {
        lastBotTextRef.current = text;
        onBotTranscript?.(text);
      }
    };

    const handleError = (error) => {
      if (!mountedRef.current) {
        return;
      }
      clearConnectionTimeout();
      connectingRef.current = false;
      const message =
        error instanceof Error
          ? error.message
          : typeof error === "object" && error && "message" in error
            ? String(error.message || "")
            : "";
      setVoiceError(message || "Unable to connect the voice call.");
      setCallState("idle");
    };

    client.on(RTVIEvent.Connected, handleConnected);
    client.on(RTVIEvent.BotConnected, handleBotConnected);
    client.on(RTVIEvent.BotReady, handleBotReady);
    client.on(RTVIEvent.Disconnected, handleDisconnected);
    client.on(RTVIEvent.BotDisconnected, handleBotDisconnected);
    client.on(RTVIEvent.UserTranscript, handleUserTranscript);
    client.on(RTVIEvent.BotTranscript, handleBotTranscript);
    client.on(RTVIEvent.BotTtsText, handleBotTranscript);
    client.on(RTVIEvent.BotOutput, handleBotOutput);
    client.on(RTVIEvent.Error, handleError);

    return () => {
      client.off(RTVIEvent.Connected, handleConnected);
      client.off(RTVIEvent.BotConnected, handleBotConnected);
      client.off(RTVIEvent.BotReady, handleBotReady);
      client.off(RTVIEvent.Disconnected, handleDisconnected);
      client.off(RTVIEvent.BotDisconnected, handleBotDisconnected);
      client.off(RTVIEvent.UserTranscript, handleUserTranscript);
      client.off(RTVIEvent.BotTranscript, handleBotTranscript);
      client.off(RTVIEvent.BotTtsText, handleBotTranscript);
      client.off(RTVIEvent.BotOutput, handleBotOutput);
      client.off(RTVIEvent.Error, handleError);
    };
  }, [client, onCallEnded, onUserTranscript, onBotTranscript]);

  useEffect(() => {
    return () => {
      void safeDisconnect();
    };
  }, [client]);

  const handleStartCall = async () => {
    if (!agentId || disabled || connectingRef.current || callState === "active" || callState === "connecting") {
      return;
    }

    if (!canStart) {
      setVoiceError(blockedReason || "Complete the required runtime fields before starting the call.");
      return;
    }

    connectingRef.current = true;
    endingNotifiedRef.current = false;
    setVoiceError("");
    setMuted(false);
    setCallState("connecting");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());

      if (client.state !== "disconnected" && client.state !== "error") {
        await safeDisconnect();
        await new Promise((resolve) => window.setTimeout(resolve, 500));
      }

      const voiceSession = await agentService.createVoiceSession(agentId, {
        conversation_metadata: {
          ...conversationMetadata,
          ...(chatSessionId ? { chat_session_id: chatSessionId } : {}),
        },
        conversation_config_type: "VOICE",
        prompt_access_token: promptAccessToken || undefined,
      });

      if (!voiceSession?.dailyRoom || !voiceSession?.dailyToken) {
        throw new Error("Voice session is missing connection details.");
      }

      await client.connect({
        url: voiceSession.dailyRoom,
        token: voiceSession.dailyToken,
      });

      connectionTimeoutRef.current = window.setTimeout(() => {
        if (!mountedRef.current || !connectingRef.current) {
          return;
        }
        connectingRef.current = false;
        setVoiceError("Agent is not responding yet. Please end the call and try again.");
        setCallState("idle");
        void safeDisconnect();
      }, 30000);
    } catch (error) {
      connectingRef.current = false;
      if (connectionTimeoutRef.current) {
        window.clearTimeout(connectionTimeoutRef.current);
        connectionTimeoutRef.current = null;
      }
      const detailMessage = error?.response?.data?.detail;
      const message =
        error?.name === "NotAllowedError"
          ? "Microphone access was denied. Allow microphone permissions and try again."
          : typeof detailMessage === "string" && detailMessage.includes("prompt access token")
            ? "Voice calls are not enabled for this agent yet. Use chat for now or update the agent's widget voice configuration."
          : error?.message || "Unable to start the voice call.";
      setVoiceError(message);
      setCallState("idle");
      await safeDisconnect();
    }
  };

  const handleEndCall = async () => {
    if (callState === "idle" && !connectingRef.current) {
      onCallEnded?.();
      return;
    }

    connectingRef.current = false;
    if (connectionTimeoutRef.current) {
      window.clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }
    setCallState("ending");
    setVoiceError("");
    setMuted(false);

    try {
      await safeDisconnect();
    } catch {
      // Ignore disconnect errors and let the UI close.
    } finally {
      if (mountedRef.current) {
        setCallState("idle");
      }
      if (
        client.state === "disconnected" &&
        !endingNotifiedRef.current
      ) {
        endingNotifiedRef.current = true;
        onCallEnded?.();
      }
    }
  };

  const handleToggleMute = () => {
    if (callState !== "active") {
      return;
    }

    const nextMutedState = !muted;
    client.enableMic(!nextMutedState);
    setMuted(nextMutedState);
  };

  useEffect(() => {
    if (!compact || !autoStartSignal || autoStartSignal === lastAutoStartSignalRef.current) {
      return;
    }
    lastAutoStartSignalRef.current = autoStartSignal;
    void handleStartCall();
  }, [autoStartSignal, compact]);

  const compactStatus = getCallStatus(callState, voiceError, muted);

  return (
    <PipecatClientProvider client={client}>
      <PipecatClientAudio />

      {compact ? (
        <div className="doctor-agent-callbar">
          <span className="doctor-agent-callbar-copy">{compactStatus}</span>
          <div className="doctor-agent-callbar-actions">
            <button
              className="doctor-agent-secondary-button"
              type="button"
              onClick={handleToggleMute}
              disabled={callState !== "active"}
            >
              {muted ? "Unmute" : "Mute"}
            </button>
            <button
              className="doctor-agent-endcall-button"
              type="button"
              onClick={() => void handleEndCall()}
              disabled={callState === "ending"}
            >
              End call
            </button>
          </div>
        </div>
      ) : (
        <article className="doctor-voice-card">
          <div className="doctor-history-header doctor-voice-header">
            <h3>Voice Call</h3>
            <span>{compactStatus}</span>
          </div>

          <p className="doctor-empty-copy">
            {callState === "active"
              ? `You are connected to ${activeAgentName || "the assistant"}.`
              : callState === "connected"
                ? "The call is connected. Waiting for the voice agent to become ready."
                : "Start the call and speak naturally. The voice agent will respond via audio."}
          </p>

          {voiceError ? <p className="error-text">{voiceError}</p> : null}

          <div className="doctor-voice-controls">
            <button
              className="primary-button"
              type="button"
              onClick={() => void handleStartCall()}
              disabled={disabled || callState === "connecting" || callState === "active"}
            >
              {callState === "active" ? "Call active" : callState === "connecting" ? "Connecting..." : "Start call"}
            </button>

            <button
              className="doctor-mini-pill"
              type="button"
              onClick={handleToggleMute}
              disabled={callState !== "active"}
            >
              {muted ? "Unmute" : "Mute"}
            </button>

            <button
              className="doctor-mini-pill"
              type="button"
              onClick={() => void handleEndCall()}
              disabled={callState === "idle" || callState === "ending"}
            >
              End call
            </button>
          </div>
        </article>
      )}
    </PipecatClientProvider>
  );
}
