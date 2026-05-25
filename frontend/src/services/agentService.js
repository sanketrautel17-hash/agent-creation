import { apiClient } from "./api";

export const agentService = {
  async listAgents(params = {}) {
    const response = await apiClient.get("/agents", { params });
    return response.data;
  },
  async getAgent(agentId) {
    const response = await apiClient.get(`/agents/${agentId}`);
    return response.data;
  },
  async getDynamicVariables(agentId) {
    const response = await apiClient.get(`/agents/${agentId}/dynamic-variables`);
    return response.data;
  },
  async initializeChat(agentId, conversationMetadata = {}) {
    const response = await apiClient.post(`/agents/${agentId}/chat/session`, {
      conversation_metadata: conversationMetadata,
    });
    return response.data;
  },
  async createVoiceSession(agentId, payload = {}) {
    const response = await apiClient.post(`/agents/${agentId}/voice/session`, payload);
    return response.data;
  },
  async sendChatMessage(agentId, payload) {
    const response = await apiClient.post(`/agents/${agentId}/chat/messages`, payload);
    return response.data;
  },
};
