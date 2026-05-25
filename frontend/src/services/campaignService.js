import { apiClient } from "./api";

export const campaignService = {
  async createCampaign(agentId, agentName, campaignName, contacts) {
    const payload = {
      agent_id: agentId,
      agent_name: agentName || null,
      campaign_name: campaignName,
      contacts,
    };
    console.log("[Campaign] POST /campaigns payload:", JSON.stringify(payload, null, 2));
    try {
      const response = await apiClient.post("/campaigns", payload);
      return response.data;
    } catch (err) {
      console.error("[Campaign] POST /campaigns error:", err?.response?.status, JSON.stringify(err?.response?.data, null, 2));
      throw err;
    }
  },

  async listCampaigns() {
    const response = await apiClient.get("/campaigns");
    return response.data;
  },

  async getCampaign(campaignId) {
    const response = await apiClient.get(`/campaigns/${campaignId}`);
    return response.data;
  },

  async cancelCampaign(campaignId) {
    const response = await apiClient.post(`/campaigns/${campaignId}/cancel`);
    return response.data;
  },
};
