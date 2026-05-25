import { apiClient } from "./api";

export const adminService = {
  async stats() {
    const response = await apiClient.get("/admin/stats");
    return response.data;
  },
  async invites() {
    const response = await apiClient.get("/admin/invites");
    return response.data;
  },
  async userHistory({ page = 1, pageSize = 5 } = {}) {
    const response = await apiClient.get("/admin/user-history", {
      params: {
        page,
        page_size: pageSize,
      },
    });
    return response.data;
  },
  async getUserHistoryConversation(historyId) {
    const response = await apiClient.get(`/admin/user-history/${historyId}`);
    return response.data;
  },
  async createInvite(email) {
    const response = await apiClient.post("/admin/invites", { email });
    return response.data;
  },
  async revokeInvite(inviteId) {
    const response = await apiClient.delete(`/admin/invites/${inviteId}`);
    return response.data;
  },
};
